"""Módulo de geração do Context Pack para o pipeline Tokemize.

Este módulo é responsável por montar o documento Markdown estruturado
(`context_pack.md`) com todo o contexto otimizado: tarefa do usuário,
arquivos completos, arquivos resumidos, contexto técnico do repositório
e instrução ao LLM.

A função pública principal é `generate_context_pack`. O wrapper
`generate_prompt` mantém compatibilidade retroativa com o orquestrador
existente.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tokemize.models import (
    GeneratorOutput,
    SelectedFile,
    SelectionOutput,
    SummaryOutput,
)

logger = logging.getLogger(__name__)

# ── Constante de instrução ao LLM ─────────────────────────────────────────────

LLM_INSTRUCTION: str = (
    "Você é um assistente de desenvolvimento de software especializado. "
    "Analise cuidadosamente o contexto fornecido nas seções acima — "
    "incluindo os arquivos completos, os resumos e o contexto técnico do "
    "repositório — e responda à tarefa descrita na seção '## Task'. "
    "Baseie sua resposta exclusivamente no contexto fornecido. "
    "Seja preciso, objetivo e forneça código funcional quando aplicável."
)


# ── Funções auxiliares privadas de formatação ─────────────────────────────────


def _format_task_section(task: str) -> str:
    """Formata a seção ``## Task`` do Context Pack.

    Args:
        task: Descrição textual da tarefa técnica fornecida pelo usuário.

    Returns:
        String Markdown com o cabeçalho ``## Task`` seguido do conteúdo
        da tarefa em um parágrafo separado por linha em branco.

    Example:
        >>> _format_task_section("Adicionar testes unitários")
        '## Task\\n\\nAdicionar testes unitários'
    """
    return f"## Task\n\n{task}"


def _format_complete_files_section(selected_files: list[SelectedFile]) -> str:
    """Formata a seção ``## Complete Files`` do Context Pack.

    Cada arquivo é apresentado com um cabeçalho ``### {path}`` seguido de
    um bloco de código Markdown com o identificador de linguagem. Arquivos
    com ``language`` vazio ou ``"unknown"`` usam ``text`` como fallback.
    Os arquivos são separados por uma linha em branco entre si.

    Args:
        selected_files: Lista de arquivos selecionados a serem incluídos
            integralmente na seção. Pode ser vazia.

    Returns:
        String Markdown com a seção ``## Complete Files``. Quando
        ``selected_files`` está vazio, retorna a seção com o placeholder
        ``_Nenhum arquivo selecionado._``.

    Example:
        >>> from tokemize.models import SelectedFile
        >>> files = [SelectedFile(path="src/main.py", language="python",
        ...                       content="print('hello')", relevance_score=1.0)]
        >>> section = _format_complete_files_section(files)
        >>> "### src/main.py" in section
        True
        >>> "```python" in section
        True
    """
    if not selected_files:
        return "## Complete Files\n\n_Nenhum arquivo selecionado._"

    file_blocks: list[str] = []
    for sf in selected_files:
        language = sf.language if sf.language and sf.language != "unknown" else "text"
        block = f"### {sf.path}\n\n```{language}\n{sf.content}\n```"
        file_blocks.append(block)

    files_content = "\n\n".join(file_blocks)
    return f"## Complete Files\n\n{files_content}"


def _format_summarized_files_section(summary_output: SummaryOutput) -> str:
    """Formata a seção ``## Summarized Files`` do Context Pack.

    Quando ``files_summarized`` é zero, exibe um placeholder indicando
    que nenhum arquivo foi resumido. Caso contrário, exibe o conteúdo
    resumido produzido pela etapa de sumarização.

    Args:
        summary_output: Resultado da etapa de sumarização contendo
            ``summarized_content`` e ``files_summarized``.

    Returns:
        String Markdown com a seção ``## Summarized Files``. Quando
        ``files_summarized == 0``, retorna a seção com o placeholder
        ``_Nenhum arquivo resumido._``.

    Example:
        >>> from tokemize.models import SummaryOutput
        >>> _format_summarized_files_section(SummaryOutput(files_summarized=0))
        '## Summarized Files\\n\\n_Nenhum arquivo resumido._'
    """
    if summary_output.files_summarized == 0:
        return "## Summarized Files\n\n_Nenhum arquivo resumido._"

    return f"## Summarized Files\n\n{summary_output.summarized_content}"


def _format_technical_context_section(selected_files: list[SelectedFile]) -> str:
    """Formata a seção ``## Technical Context`` do Context Pack.

    Inclui o total de arquivos selecionados e a lista de linguagens únicas
    presentes nos arquivos, ordenadas alfabeticamente. Quando não há
    arquivos, exibe ``_nenhuma_`` na lista de linguagens.

    Args:
        selected_files: Lista de arquivos selecionados cujos metadados
            serão usados para compor o contexto técnico.

    Returns:
        String Markdown com a seção ``## Technical Context`` contendo
        ``Total de arquivos selecionados: {n}`` e
        ``Linguagens: {lang1}, {lang2}, ...`` (ou ``_nenhuma_`` quando
        a lista estiver vazia).

    Example:
        >>> from tokemize.models import SelectedFile
        >>> files = [
        ...     SelectedFile("a.py", "python", "", 1.0),
        ...     SelectedFile("b.js", "javascript", "", 0.9),
        ...     SelectedFile("c.py", "python", "", 0.8),
        ... ]
        >>> section = _format_technical_context_section(files)
        >>> "Total de arquivos selecionados: 3" in section
        True
        >>> "javascript, python" in section
        True
    """
    n = len(selected_files)

    if not selected_files:
        languages_str = "_nenhuma_"
    else:
        unique_languages = sorted(
            {sf.language for sf in selected_files if sf.language and sf.language != "unknown"}
        )
        if not unique_languages:
            languages_str = "_nenhuma_"
        else:
            languages_str = ", ".join(unique_languages)

    return (
        f"## Technical Context\n\n"
        f"Total de arquivos selecionados: {n}\n"
        f"Linguagens: {languages_str}"
    )


def _format_llm_instruction_section() -> str:
    """Formata a seção ``## LLM Instruction`` do Context Pack.

    Retorna a seção com a constante estática ``LLM_INSTRUCTION``, que
    orienta o LLM a usar o contexto fornecido para responder à tarefa
    descrita na seção ``## Task``.

    Returns:
        String Markdown com o cabeçalho ``## LLM Instruction`` seguido
        do conteúdo da constante ``LLM_INSTRUCTION``.

    Example:
        >>> section = _format_llm_instruction_section()
        >>> section.startswith("## LLM Instruction")
        True
        >>> "## Task" in section
        True
    """
    return f"## LLM Instruction\n\n{LLM_INSTRUCTION}"


# ── Funções de orquestração e I/O ─────────────────────────────────────────────


def _build_context_pack(
    summary_output: SummaryOutput,
    task: str,
    selected_files: list[SelectedFile],
) -> str:
    """Orquestra as 5 funções de formatação e monta o Context Pack completo.

    Chama as funções de formatação na ordem definida pelo design:
    Task → Complete Files → Summarized Files → Technical Context →
    LLM Instruction. As seções são unidas com ``\\n\\n`` e precedidas pelo
    cabeçalho ``# Context Pack``.

    Args:
        summary_output: Resultado da etapa de sumarização contendo
            ``summarized_content`` e ``files_summarized``.
        task: Descrição textual da tarefa técnica fornecida pelo usuário.
        selected_files: Lista de arquivos selecionados a serem incluídos
            integralmente na seção ``## Complete Files``.

    Returns:
        String Markdown completa do Context Pack, iniciando com
        ``# Context Pack`` e contendo as 5 seções na ordem correta.

    Example:
        >>> from tokemize.models import SummaryOutput
        >>> content = _build_context_pack(SummaryOutput(), "minha tarefa", [])
        >>> content.startswith("# Context Pack")
        True
        >>> "## Task" in content
        True
    """
    sections = [
        "# Context Pack",
        _format_task_section(task),
        _format_complete_files_section(selected_files),
        _format_summarized_files_section(summary_output),
        _format_technical_context_section(selected_files),
        _format_llm_instruction_section(),
    ]
    return "\n\n".join(sections)


def _count_tokens(content: str) -> int:
    """Estima o número de tokens no conteúdo como contagem de palavras.

    Usa ``len(content.split())`` como estimativa simples e eficiente do
    número de tokens. Retorna zero para conteúdo vazio ou composto apenas
    de espaços em branco.

    Args:
        content: String cujo número de tokens será estimado.

    Returns:
        Número inteiro de palavras em ``content``, ou ``0`` se ``content``
        estiver vazio ou contiver apenas espaços em branco.

    Example:
        >>> _count_tokens("hello world foo")
        3
        >>> _count_tokens("")
        0
        >>> _count_tokens("   ")
        0
    """
    return len(content.split())


def _write_output(content: str, output_path: Path) -> None:
    """Persiste o conteúdo do Context Pack em disco.

    Cria o diretório pai de ``output_path`` automaticamente se não existir
    (incluindo toda a hierarquia necessária). Sobrescreve o arquivo se já
    existir. Captura ``OSError`` e relança como ``IOError`` com mensagem
    descritiva contendo o caminho e a causa original.

    Args:
        content: Conteúdo Markdown do Context Pack a ser escrito.
        output_path: Caminho do arquivo de saída onde o conteúdo será
            persistido.

    Raises:
        IOError: Se o arquivo não puder ser escrito por falta de permissão
            ou outro erro de I/O. A mensagem inclui o caminho e a causa.

    Example:
        >>> from pathlib import Path
        >>> import tempfile, os
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     p = Path(tmp) / "sub" / "out.md"
        ...     _write_output("# Context Pack", p)
        ...     p.read_text(encoding="utf-8")
        '# Context Pack'
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8", newline="")
    except OSError as exc:
        raise IOError(
            f"Falha ao escrever Context Pack em '{output_path}': {exc}"
        ) from exc


def generate_context_pack(
    summary_output: SummaryOutput,
    task: str,
    output_path: str | Path = "outputs/context_pack.md",
    selection_output: SelectionOutput | None = None,
) -> GeneratorOutput:
    """Gera o Context Pack, persiste em disco e retorna o resultado.

    Orquestra a montagem do documento Markdown estruturado com todas as
    seções (Task, Complete Files, Summarized Files, Technical Context e
    LLM Instruction), persiste o arquivo no ``output_path`` informado e
    retorna um ``GeneratorOutput`` com o conteúdo gerado e a estimativa
    de tokens.

    Registra via ``logging`` o início da geração, o ``output_path``
    utilizado, o número de arquivos incluídos e a conclusão bem-sucedida.
    Nunca registra o conteúdo dos arquivos nem o texto da ``task``.

    Args:
        summary_output: Resultado da etapa de sumarização. Contém
            ``summarized_content``, ``token_count`` e ``files_summarized``.
        task: Descrição textual da tarefa técnica fornecida pelo usuário.
        output_path: Caminho do arquivo de saída. O diretório pai é criado
            automaticamente se não existir. Padrão:
            ``"outputs/context_pack.md"``.
        selection_output: Resultado opcional da etapa de seleção. Quando
            fornecido, os ``SelectedFile`` são incluídos na seção
            ``## Complete Files``. Quando ``None``, a seção exibe o
            placeholder ``_Nenhum arquivo selecionado._``.

    Returns:
        GeneratorOutput com ``prompt`` igual ao conteúdo completo do
        Context Pack gerado e ``token_count`` igual ao número de palavras
        em ``prompt`` (``len(prompt.split())``).

    Raises:
        IOError: Se o arquivo não puder ser escrito por falta de permissão
            ou outro erro de I/O. A mensagem inclui o caminho e a causa.

    Example:
        >>> import tempfile
        >>> from pathlib import Path
        >>> from tokemize.models import SummaryOutput
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     out = Path(tmp) / "context_pack.md"
        ...     result = generate_context_pack(SummaryOutput(), "tarefa", out)
        ...     isinstance(result.token_count, int)
        True
    """
    output_path = Path(output_path)

    selected_files: list[SelectedFile] = (
        selection_output.selected_files if selection_output is not None else []
    )

    logger.info("Iniciando geração do Context Pack")
    logger.info("Output path: %s", output_path)
    logger.info("Número de arquivos incluídos: %d", len(selected_files))

    content = _build_context_pack(summary_output, task, selected_files)
    _write_output(content, output_path)
    token_count = _count_tokens(content)

    logger.info("Context Pack gerado com sucesso em '%s'", output_path)

    return GeneratorOutput(prompt=content, token_count=token_count)


def generate_prompt(
    summary_output: SummaryOutput,
    task: str,
) -> GeneratorOutput:
    """Wrapper de compatibilidade com o orquestrador existente.

    Delega para ``generate_context_pack`` com o ``output_path`` padrão
    (``"outputs/context_pack.md"``) e sem ``selection_output``, mantendo
    compatibilidade total com a assinatura da etapa ``generator`` no
    orquestrador (``generate_prompt(summary_output, task)``).

    Args:
        summary_output: Resultado da etapa de sumarização. Contém
            ``summarized_content``, ``token_count`` e ``files_summarized``.
        task: Descrição textual da tarefa técnica fornecida pelo usuário.

    Returns:
        GeneratorOutput com ``prompt`` igual ao conteúdo completo do
        Context Pack gerado e ``token_count`` estimado como número de
        palavras no ``prompt``.

    Example:
        >>> from tokemize.models import SummaryOutput
        >>> result = generate_prompt(SummaryOutput(), "minha tarefa")
        >>> isinstance(result.prompt, str)
        True
    """
    return generate_context_pack(summary_output, task)
