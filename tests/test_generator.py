"""Testes unitários para o módulo generator (Context Pack Generator).

Cobre smoke tests de importação, testes de exemplo concretos e testes de
propriedade com Hypothesis para `generate_context_pack`, `generate_prompt`
e `LLM_INSTRUCTION`.
"""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tokemize.generator import LLM_INSTRUCTION, generate_context_pack, generate_prompt
from tokemize.models import GeneratorOutput, SelectedFile, SelectionOutput, SummaryOutput


# ---------------------------------------------------------------------------
# Smoke tests de importação
# ---------------------------------------------------------------------------


class TestImports:
    """Smoke tests: verifica que os símbolos públicos são importáveis e callable."""

    def test_import_generate_context_pack(self):
        """generate_context_pack é importável e callable."""
        assert callable(generate_context_pack)

    def test_import_generate_prompt_compat(self):
        """generate_prompt é importável e callable."""
        assert callable(generate_prompt)


# ---------------------------------------------------------------------------
# Testes de exemplo concretos
# ---------------------------------------------------------------------------


class TestGenerateContextPackExamples:
    """Testes de exemplo concretos para generate_context_pack."""

    def test_creates_output_directory_automatically(self, tmp_path: Path):
        """Diretório pai inexistente é criado automaticamente."""
        output_path = tmp_path / "new_dir" / "subdir" / "context_pack.md"
        generate_context_pack(SummaryOutput(), "task", output_path)
        assert output_path.exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="chmod não funciona em Windows")
    def test_raises_ioerror_on_write_failure(self, tmp_path: Path):
        """IOError é lançado quando o diretório é somente leitura."""
        output_path = tmp_path / "context_pack.md"
        tmp_path.chmod(0o444)  # somente leitura
        try:
            with pytest.raises(IOError, match=str(output_path)):
                generate_context_pack(SummaryOutput(), "task", output_path)
        finally:
            # Restaura permissões para que o pytest possa limpar tmp_path
            tmp_path.chmod(0o755)

    def test_empty_selection_output_placeholder(self, tmp_path: Path):
        """SelectionOutput vazia gera placeholder '_Nenhum arquivo selecionado._'."""
        result = generate_context_pack(
            SummaryOutput(),
            "task",
            tmp_path / "out.md",
            SelectionOutput(),
        )
        assert "_Nenhum arquivo selecionado._" in result.prompt

    def test_zero_files_summarized_placeholder(self, tmp_path: Path):
        """SummaryOutput com files_summarized=0 gera placeholder '_Nenhum arquivo resumido._'."""
        result = generate_context_pack(
            SummaryOutput(files_summarized=0),
            "task",
            tmp_path / "out.md",
        )
        assert "_Nenhum arquivo resumido._" in result.prompt

    def test_empty_technical_context(self, tmp_path: Path):
        """Sem arquivos selecionados, Technical Context mostra 0 e '_nenhuma_'."""
        result = generate_context_pack(
            SummaryOutput(),
            "task",
            tmp_path / "out.md",
            SelectionOutput(),
        )
        assert "Total de arquivos selecionados: 0" in result.prompt
        assert "_nenhuma_" in result.prompt

    def test_llm_instruction_present(self, tmp_path: Path):
        """A seção '## LLM Instruction' está presente no output gerado."""
        result = generate_context_pack(
            SummaryOutput(),
            "task",
            tmp_path / "out.md",
        )
        assert "## LLM Instruction" in result.prompt

    def test_generate_prompt_compat_wrapper(self, tmp_path: Path, monkeypatch):
        """generate_prompt retorna GeneratorOutput com prompt não vazio e token_count >= 0."""
        # Redireciona o output padrão para tmp_path para não poluir outputs/
        default_path = Path("outputs/context_pack.md")
        monkeypatch.chdir(tmp_path)

        result = generate_prompt(SummaryOutput(), "task")

        assert isinstance(result, GeneratorOutput)
        assert isinstance(result.prompt, str)
        assert len(result.prompt) > 0
        assert result.token_count >= 0

    def test_logging_emits_expected_messages(self, tmp_path: Path, caplog):
        """O logger registra o output_path e o número de arquivos incluídos."""
        output_path = tmp_path / "context_pack.md"
        files = [
            SelectedFile(path="src/main.py", language="python", content="pass", relevance_score=1.0),
            SelectedFile(path="src/utils.py", language="python", content="pass", relevance_score=0.9),
        ]
        selection = SelectionOutput(selected_files=files)

        with caplog.at_level(logging.INFO, logger="tokemize.generator"):
            generate_context_pack(SummaryOutput(), "task", output_path, selection)

        messages = [record.message for record in caplog.records]
        # Verifica que o output_path aparece em alguma mensagem de log
        assert any(str(output_path) in msg for msg in messages)
        # Verifica que o número de arquivos (2) aparece em alguma mensagem de log
        assert any("2" in msg for msg in messages)


# ---------------------------------------------------------------------------
# Estratégias Hypothesis reutilizáveis
# ---------------------------------------------------------------------------

# Estratégia para SelectedFile — paths simples sem caracteres problemáticos
_sf_path = st.text(
    min_size=1,
    max_size=30,
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="/_.-",
    ),
).filter(lambda s: s.strip())

_sf_language = st.one_of(
    st.just("python"),
    st.just("javascript"),
    st.just("java"),
    st.just(""),
    st.just("unknown"),
)

_selected_file_strategy = st.builds(
    SelectedFile,
    path=_sf_path,
    language=_sf_language,
    content=st.text(min_size=0, max_size=100),
    relevance_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)

_selection_output_strategy = st.builds(
    SelectionOutput,
    task=st.text(min_size=1, max_size=50),
    selected_files=st.lists(_selected_file_strategy, min_size=0, max_size=5),
    total_candidates=st.integers(min_value=0, max_value=20),
)

_summary_output_strategy = st.builds(
    SummaryOutput,
    summarized_content=st.text(min_size=0, max_size=200),
    token_count=st.integers(min_value=0, max_value=500),
    files_summarized=st.integers(min_value=0, max_value=10),
)


# ---------------------------------------------------------------------------
# Testes de propriedade (Hypothesis)
# ---------------------------------------------------------------------------


class TestGeneratorProperties:
    """Testes baseados em propriedades do Context Pack Generator."""

    # Feature: context-pack-generator, Property 1: prompt equals file content
    @given(
        task=st.text(min_size=1, max_size=50),
        summary=_summary_output_strategy,
        selection=_selection_output_strategy,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_1_prompt_equals_file_content(
        self, task: str, summary: SummaryOutput, selection: SelectionOutput
    ):
        """Property 1: Round-trip do conteúdo — arquivo e GeneratorOutput são idênticos.

        Validates: Requirements 1.4
        """
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            result = generate_context_pack(summary, task, output_path, selection)
            # Lê o arquivo com newline="" para preservar line endings exatamente
            # como foram escritos (evita normalização de \r em Windows)
            assert result.prompt == output_path.read_text(encoding="utf-8", newline="")

    # Feature: context-pack-generator, Property 2: overwrite idempotent
    @given(
        task1=st.text(min_size=1, max_size=50),
        task2=st.text(min_size=1, max_size=50),
        summary1=_summary_output_strategy,
        summary2=_summary_output_strategy,
        selection1=_selection_output_strategy,
        selection2=_selection_output_strategy,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_2_overwrite_idempotent(
        self,
        task1: str,
        task2: str,
        summary1: SummaryOutput,
        summary2: SummaryOutput,
        selection1: SelectionOutput,
        selection2: SelectionOutput,
    ):
        """Property 2: Sobrescrita idempotente.

        Duas chamadas sequenciais ao mesmo path: o conteúdo final deve ser
        igual ao da segunda chamada.

        Validates: Requirements 1.3
        """
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            generate_context_pack(summary1, task1, output_path, selection1)
            result2 = generate_context_pack(summary2, task2, output_path, selection2)
            # Lê o arquivo com newline="" para preservar line endings exatamente
            # como foram escritos (evita normalização de \r em Windows)
            assert output_path.read_text(encoding="utf-8", newline="") == result2.prompt

    # Feature: context-pack-generator, Property 3: token_count is word count
    @given(
        task=st.text(min_size=1, max_size=50),
        summary=_summary_output_strategy,
        selection=_selection_output_strategy,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_3_token_count_is_word_count(
        self, task: str, summary: SummaryOutput, selection: SelectionOutput
    ):
        """Property 3: token_count é o número de palavras do prompt.

        Validates: Requirements 7.1, 7.2, 7.3
        """
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            result = generate_context_pack(summary, task, output_path, selection)
            assert result.token_count == len(result.prompt.split())

    # Feature: context-pack-generator, Property 4: task round-trip
    @given(
        task=st.text(min_size=1, max_size=50),
        summary=_summary_output_strategy,
        selected_files=st.lists(_selected_file_strategy, min_size=1, max_size=3),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_4_task_round_trip(
        self,
        task: str,
        summary: SummaryOutput,
        selected_files: list[SelectedFile],
    ):
        """Property 4: Round-trip da seção Task.

        Extrair o conteúdo entre '## Task\\n\\n' e o próximo '\\n\\n##' deve
        retornar exatamente a task fornecida.

        Validates: Requirements 2.1, 8.2
        """
        selection = SelectionOutput(
            task=task,
            selected_files=selected_files,
            total_candidates=len(selected_files),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            result = generate_context_pack(summary, task, output_path, selection)
            prompt = result.prompt
            # Extrai o conteúdo da seção ## Task
            task_marker = "## Task\n\n"
            start = prompt.index(task_marker) + len(task_marker)
            end = prompt.index("\n\n##", start)
            extracted_task = prompt[start:end]
            assert extracted_task == task

    # Feature: context-pack-generator, Property 5: code block count equals files
    @given(
        task=st.text(min_size=1, max_size=50),
        summary=_summary_output_strategy,
        selected_files=st.lists(_selected_file_strategy, min_size=0, max_size=5),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_5_code_block_count_equals_files(
        self,
        task: str,
        summary: SummaryOutput,
        selected_files: list[SelectedFile],
    ):
        """Property 5: Contagem de blocos de código equals número de SelectedFiles.

        O número de blocos de código (pares de ```) na seção ## Complete Files
        deve ser igual ao número de SelectedFiles.

        Validates: Requirements 2.2, 3.4, 8.3
        """
        selection = SelectionOutput(
            task=task,
            selected_files=selected_files,
            total_candidates=len(selected_files),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            result = generate_context_pack(summary, task, output_path, selection)
            prompt = result.prompt

            # Extrai a seção ## Complete Files
            cf_marker = "## Complete Files\n\n"
            cf_start = prompt.index(cf_marker) + len(cf_marker)
            # Usa "\n\n## " (com espaço) para não confundir com headers ### nível 3
            cf_end_search = prompt.find("\n\n## ", cf_start)
            if cf_end_search == -1:
                cf_section = prompt[cf_start:]
            else:
                cf_section = prompt[cf_start:cf_end_search]

            # Conta as aberturas de bloco de código (```language ou ```text)
            # Cada bloco começa com "```" seguido de letras (não de outro ```)
            import re
            opening_blocks = re.findall(r"^```\w", cf_section, re.MULTILINE)
            assert len(opening_blocks) == len(selected_files)

    # Feature: context-pack-generator, Property 6: section order preserved
    @given(
        task=st.text(min_size=1, max_size=50),
        summary=_summary_output_strategy,
        selection=_selection_output_strategy,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_6_section_order_preserved(
        self, task: str, summary: SummaryOutput, selection: SelectionOutput
    ):
        """Property 6: Ordem das seções é sempre preservada.

        Validates: Requirements 2.6
        """
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            result = generate_context_pack(summary, task, output_path, selection)
            prompt = result.prompt
            pos_task = prompt.index("## Task")
            pos_complete = prompt.index("## Complete Files")
            pos_summarized = prompt.index("## Summarized Files")
            pos_technical = prompt.index("## Technical Context")
            pos_llm = prompt.index("## LLM Instruction")
            assert pos_task < pos_complete < pos_summarized < pos_technical < pos_llm

    # Feature: context-pack-generator, Property 7: file path and language in output
    @given(
        task=st.text(min_size=1, max_size=50),
        summary=_summary_output_strategy,
        selected_files=st.lists(
            st.builds(
                SelectedFile,
                path=_sf_path,
                language=st.one_of(
                    st.just("python"),
                    st.just("javascript"),
                    st.just("java"),
                ),
                content=st.text(min_size=0, max_size=100),
                relevance_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            ),
            min_size=1,
            max_size=3,
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_7_file_path_and_language_in_output(
        self,
        task: str,
        summary: SummaryOutput,
        selected_files: list[SelectedFile],
    ):
        """Property 7: Formatação de arquivos — path e linguagem corretos.

        Para cada SelectedFile com language não vazio e não 'unknown', o prompt
        deve conter ### {path} e ```{language}.

        Validates: Requirements 3.1
        """
        selection = SelectionOutput(
            task=task,
            selected_files=selected_files,
            total_candidates=len(selected_files),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            result = generate_context_pack(summary, task, output_path, selection)
            prompt = result.prompt
            for sf in selected_files:
                assert f"### {sf.path}" in prompt
                assert f"```{sf.language}" in prompt

    # Feature: context-pack-generator, Property 8: unknown language fallback
    @given(
        task=st.text(min_size=1, max_size=50),
        summary=_summary_output_strategy,
        selected_files=st.lists(
            st.builds(
                SelectedFile,
                path=_sf_path,
                language=st.one_of(st.just(""), st.just("unknown")),
                content=st.text(min_size=0, max_size=100),
                relevance_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            ),
            min_size=1,
            max_size=3,
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_8_unknown_language_fallback(
        self,
        task: str,
        summary: SummaryOutput,
        selected_files: list[SelectedFile],
    ):
        """Property 8: Fallback de linguagem para 'text'.

        Para SelectedFile com language='' ou 'unknown', o bloco de código
        correspondente deve usar ```text.

        Validates: Requirements 3.3
        """
        selection = SelectionOutput(
            task=task,
            selected_files=selected_files,
            total_candidates=len(selected_files),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            result = generate_context_pack(summary, task, output_path, selection)
            prompt = result.prompt
            # Cada arquivo com language vazio ou unknown deve gerar ```text
            import re
            # Conta quantos blocos ```text existem na seção Complete Files
            cf_marker = "## Complete Files\n\n"
            cf_start = prompt.index(cf_marker) + len(cf_marker)
            # Usa "\n\n## " (com espaço) para não confundir com headers ### nível 3
            cf_end_search = prompt.find("\n\n## ", cf_start)
            if cf_end_search == -1:
                cf_section = prompt[cf_start:]
            else:
                cf_section = prompt[cf_start:cf_end_search]
            text_blocks = re.findall(r"^```text$", cf_section, re.MULTILINE)
            assert len(text_blocks) == len(selected_files)

    # Feature: context-pack-generator, Property 9: technical context metadata
    @given(
        task=st.text(min_size=1, max_size=50),
        summary=_summary_output_strategy,
        selected_files=st.lists(_selected_file_strategy, min_size=0, max_size=5),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_9_technical_context_metadata(
        self,
        task: str,
        summary: SummaryOutput,
        selected_files: list[SelectedFile],
    ):
        """Property 9: Technical Context — total e linguagens corretos.

        O prompt deve conter 'Total de arquivos selecionados: {n}' onde
        n = len(selected_files). As linguagens únicas (excluindo '' e 'unknown')
        em ordem alfabética devem aparecer após 'Linguagens: '.

        Validates: Requirements 4.1, 4.2, 4.3
        """
        selection = SelectionOutput(
            task=task,
            selected_files=selected_files,
            total_candidates=len(selected_files),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            result = generate_context_pack(summary, task, output_path, selection)
            prompt = result.prompt

            n = len(selected_files)
            assert f"Total de arquivos selecionados: {n}" in prompt

            unique_langs = sorted(
                {sf.language for sf in selected_files if sf.language and sf.language != "unknown"}
            )
            if unique_langs:
                expected_langs_str = ", ".join(unique_langs)
                assert f"Linguagens: {expected_langs_str}" in prompt
            else:
                assert "Linguagens: _nenhuma_" in prompt

    # Feature: context-pack-generator, Property 10: LLM instruction is static
    @given(
        task1=st.text(min_size=1, max_size=50),
        task2=st.text(min_size=1, max_size=50),
        summary1=_summary_output_strategy,
        summary2=_summary_output_strategy,
        selection1=_selection_output_strategy,
        selection2=_selection_output_strategy,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_10_llm_instruction_is_static(
        self,
        task1: str,
        task2: str,
        summary1: SummaryOutput,
        summary2: SummaryOutput,
        selection1: SelectionOutput,
        selection2: SelectionOutput,
    ):
        """Property 10: LLM Instruction é estática e idempotente.

        Para dois conjuntos de inputs distintos, a seção ## LLM Instruction
        extraída de cada prompt deve ser idêntica.

        Validates: Requirements 5.3
        """
        def extract_llm_section(prompt: str) -> str:
            marker = "## LLM Instruction\n\n"
            start = prompt.index(marker) + len(marker)
            return prompt[start:]

        with tempfile.TemporaryDirectory() as tmp1:
            out1 = Path(tmp1) / "cp1.md"
            result1 = generate_context_pack(summary1, task1, out1, selection1)

        with tempfile.TemporaryDirectory() as tmp2:
            out2 = Path(tmp2) / "cp2.md"
            result2 = generate_context_pack(summary2, task2, out2, selection2)

        llm_section1 = extract_llm_section(result1.prompt)
        llm_section2 = extract_llm_section(result2.prompt)
        assert llm_section1 == llm_section2

    # Feature: context-pack-generator, Property 11: section titles unique
    @given(
        task=st.text(min_size=1, max_size=50),
        summary=_summary_output_strategy,
        selection=_selection_output_strategy,
    )
    @settings(max_examples=100, deadline=None)
    def test_property_11_section_titles_unique(
        self, task: str, summary: SummaryOutput, selection: SelectionOutput
    ):
        """Property 11: Títulos de seção são únicos e identificáveis.

        Os títulos ## Task, ## Complete Files, ## Summarized Files,
        ## Technical Context, ## LLM Instruction devem aparecer exatamente
        uma vez cada no prompt.

        Validates: Requirements 8.1
        """
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "cp.md"
            result = generate_context_pack(summary, task, output_path, selection)
            prompt = result.prompt
            # Conta apenas headers de nível 2 (## Título) — precedidos por \n ou início
            # Usa \n## para evitar contar ocorrências de "## Task" dentro do corpo do texto
            # O primeiro header pode estar no início do documento após "# Context Pack\n\n"
            import re
            section_headers = re.findall(r"^## .+", prompt, re.MULTILINE)
            titles = [h.strip() for h in section_headers]
            assert titles.count("## Task") == 1
            assert titles.count("## Complete Files") == 1
            assert titles.count("## Summarized Files") == 1
            assert titles.count("## Technical Context") == 1
            assert titles.count("## LLM Instruction") == 1
