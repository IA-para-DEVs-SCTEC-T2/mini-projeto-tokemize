# Implementation Plan: Tokemize CLI

## Overview

Implementação incremental da CLI do Tokemize em Python 3.11+ com Typer. O plano segue a ordem natural do pipeline: estrutura do projeto → modelos de dados → validação de entradas → orquestração do pipeline → feedback de progresso → testes. Cada etapa é integrada à anterior antes de avançar.

## Tasks

- [x] 1. Configurar estrutura do projeto e dependências
  - Criar `pyproject.toml` (ou `requirements.txt`) com dependências: `typer`, `hypothesis`, `pytest`
  - Criar os diretórios `tokemize/core/parser/`, `tokemize/core/selector/`, `tokemize/core/optimizer/`, `tokemize/core/`, `tokemize/integrations/llm/`, `tokemize/models/`, `tests/`
  - Criar arquivos `__init__.py` em cada pacote para torná-los módulos Python importáveis
  - Criar `cli.py` na raiz do projeto com a instância `app = typer.Typer()` e bloco `if __name__ == "__main__": app()`
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 2. Implementar modelos de dados em `tokemize/models/`
  - [x] 2.1 Criar `tokemize/models/__init__.py` com as dataclasses `FileInfo`, `RepositoryStructure`, `SelectedContext`, `CompressedContext` e `CachedContext`
    - Cada dataclass deve ter type hints completos, `field(default_factory=...)` onde aplicável e docstrings no padrão Google Style
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x]* 2.2 Escrever smoke tests para os modelos de dados em `tests/test_cli_smoke.py`
    - Verificar que todas as dataclasses são importáveis de `tokemize.models`
    - Verificar que instâncias podem ser criadas com os campos obrigatórios
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 3. Implementar stubs dos módulos internos
  - [x] 3.1 Criar `tokemize/core/parser/repository_analyzer.py` com a função `analyze_repository(repo_path: str) -> RepositoryStructure`
    - Implementar como stub que retorna `RepositoryStructure(root_path=repo_path)` — a lógica real será implementada em outro spec
    - Incluir type hints completos e docstring Google Style
    - _Requirements: 6.1_

  - [x] 3.2 Criar `tokemize/core/selector/intelligent_selector.py` com a função `select_relevant_files(structure: RepositoryStructure, task_description: str) -> SelectedContext`
    - Implementar como stub que retorna `SelectedContext(task_description=task_description)`
    - Incluir type hints completos e docstring Google Style
    - _Requirements: 6.2_

  - [x] 3.3 Criar `tokemize/core/optimizer/compressor.py` com a função `compress_context(context: SelectedContext) -> CompressedContext`
    - Implementar como stub que retorna `CompressedContext(task_description=context.task_description, compressed_content="", token_count=0)`
    - Incluir type hints completos e docstring Google Style
    - _Requirements: 6.3_

  - [x] 3.4 Criar `tokemize/core/context_cache.py` com a função `get_or_update_cache(compressed: CompressedContext, task_description: str) -> CachedContext`
    - Implementar como stub que retorna `CachedContext(task_description=task_description, content=compressed.compressed_content, cache_hit=False, token_count=compressed.token_count)`
    - Incluir type hints completos e docstring Google Style
    - _Requirements: 6.4_

  - [x] 3.5 Criar `tokemize/integrations/llm/llm_dispatcher.py` com a função `dispatch(cached_context: CachedContext) -> str`
    - Implementar como stub que retorna `cached_context.content`
    - Incluir type hints completos e docstring Google Style
    - _Requirements: 6.5_

  - [x]* 3.6 Escrever smoke tests para os contratos de interface em `tests/test_cli_smoke.py`
    - Usar `inspect.signature` para verificar assinaturas de cada função pública dos módulos internos
    - Verificar que cada função é importável a partir do caminho correto em `tokemize/`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 4. Implementar validação de entradas em `cli.py`
  - [x] 4.1 Implementar `_validate_repo_path(repo_path: str) -> None` em `cli.py`
    - Usar `pathlib.Path` para verificar existência e tipo do caminho
    - Exibir mensagem `"Erro: o caminho '<repo_path>' não existe."` e `raise typer.Exit(code=1)` se não existir
    - Exibir mensagem `"Erro: '<repo_path>' não é um diretório válido."` e `raise typer.Exit(code=1)` se não for diretório
    - _Requirements: 2.1, 2.2, 2.3_

  - [x]* 4.2 Escrever property test para Property 1 (caminhos inexistentes) em `tests/test_cli_properties.py`
    - **Property 1: Caminhos inexistentes são sempre rejeitados com Exit_Code 1**
    - **Validates: Requirements 2.1**
    - Usar `@given(st.text(min_size=1).filter(lambda p: not Path(p).exists()))` com `@settings(max_examples=100)`
    - Verificar `result.exit_code == 1` e que o caminho aparece na saída

  - [x]* 4.3 Escrever property test para Property 2 (arquivos não-diretórios) em `tests/test_cli_properties.py`
    - **Property 2: Arquivos (não-diretórios) são sempre rejeitados com Exit_Code 1**
    - **Validates: Requirements 2.2**
    - Criar arquivo temporário com `tmp_path` do pytest, invocar CLI com esse caminho
    - Verificar `result.exit_code == 1` e que o caminho aparece na saída

  - [x] 4.4 Implementar `_validate_task_description(task_description: str) -> None` em `cli.py`
    - Calcular `stripped = task_description.strip()` e rejeitar se vazio com mensagem `"Erro: a descrição da tarefa não pode ser vazia."` e `raise typer.Exit(code=1)`
    - Calcular `non_whitespace` removendo espaços, tabs e newlines; rejeitar se `< 10` com mensagem `"Erro: a descrição da tarefa deve ter pelo menos 10 caracteres."` e `raise typer.Exit(code=1)`
    - _Requirements: 3.1, 3.2, 3.3_

  - [x]* 4.5 Escrever property test para Property 3 (whitespace puro) em `tests/test_cli_properties.py`
    - **Property 3: Strings de whitespace puro são sempre rejeitadas como task_description**
    - **Validates: Requirements 3.1**
    - Usar `@given(st.text(alphabet=" \t\n\r", min_size=0))` com `@settings(max_examples=100)`
    - Verificar `result.exit_code == 1` e `"não pode ser vazia"` na saída

  - [x]* 4.6 Escrever property test para Property 4 (descrição muito curta) em `tests/test_cli_properties.py`
    - **Property 4: Descrições com menos de 10 caracteres não-brancos são sempre rejeitadas**
    - **Validates: Requirements 3.2**
    - Usar `@given(st.text(min_size=1))` filtrado para strings com 1–9 chars não-brancos, com `@settings(max_examples=100)`
    - Verificar `result.exit_code == 1` e `"pelo menos 10 caracteres"` na saída

  - [x]* 4.7 Escrever property test para Property 5 (descrições válidas passam) em `tests/test_cli_properties.py`
    - **Property 5: Descrições válidas nunca são bloqueadas pela validação**
    - **Validates: Requirements 3.3**
    - Usar `@given(st.text(min_size=10))` filtrado para strings com ≥ 10 chars não-brancos, com `@settings(max_examples=100)`
    - Mockar todos os módulos do pipeline; verificar que `result.exit_code != 1` por motivo de validação de entrada

- [x] 5. Checkpoint — Garantir que validações estão corretas
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [ ] 6. Implementar orquestração do pipeline em `cli.py`
  - [x] 6.1 Implementar `_run_step(step_name: str, fn: Callable, *args: Any) -> Any` em `cli.py`
    - Envolver a chamada em `try/except Exception as exc`
    - Exibir `f"Erro na etapa '{step_name}': {exc}"` e `raise typer.Exit(code=2)` em caso de exceção
    - _Requirements: 4.6_

  - [x]* 6.2 Escrever property test para Property 6 (exceções do pipeline) em `tests/test_cli_properties.py`
    - **Property 6: Exceções do pipeline sempre produzem Exit_Code 2 com mensagem contendo nome do módulo e mensagem da exceção**
    - **Validates: Requirements 4.6**
    - Usar `@given(st.sampled_from(MODULE_NAMES), st.text(min_size=1))` com `@settings(max_examples=100)`
    - Mockar o módulo sorteado para lançar `Exception(error_message)`; verificar `result.exit_code == 2`, nome do módulo e mensagem na saída

  - [x] 6.3 Implementar o comando `analyze` completo em `cli.py`
    - Importar todos os módulos internos exclusivamente de `tokemize/`
    - Definir `STEP_NAMES` com os nomes literais dos módulos para mensagens de erro
    - Chamar `_validate_repo_path` e `_validate_task_description` antes do pipeline
    - Chamar cada módulo via `_run_step` na ordem: `Repository_Analyzer` → `Intelligent_Selector` → `Compressor` → `Context_Cache` → `LLM_Dispatcher`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.6_

  - [x]* 6.4 Escrever example tests para ordem do pipeline em `tests/test_cli_examples.py`
    - Mockar todos os módulos do pipeline com `unittest.mock.patch`
    - Verificar que os mocks são chamados na ordem correta com os argumentos corretos
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 7. Implementar feedback de progresso em `cli.py`
  - [x] 7.1 Adicionar chamadas `typer.echo(f"[N/5] ...")` antes de cada etapa do pipeline no comando `analyze`
    - `"[1/5] Analisando repositório..."` antes de `Repository_Analyzer`
    - `"[2/5] Selecionando arquivos relevantes..."` antes de `Intelligent_Selector`
    - `"[3/5] Comprimindo contexto..."` antes de `Compressor`
    - `"[4/5] Verificando cache..."` antes de `Context_Cache`
    - `"[5/5] Enviando ao LLM..."` antes de `LLM_Dispatcher`
    - Exibir `"=== Resultado ==="` seguido da resposta do LLM após `LLM_Dispatcher` retornar com sucesso
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x]* 7.2 Escrever property test para Property 7 (cabeçalho do resultado) em `tests/test_cli_properties.py`
    - **Property 7: O resultado do LLM é sempre exibido precedido do cabeçalho correto**
    - **Validates: Requirements 5.6**
    - Usar `@given(st.text())` com `@settings(max_examples=100)`
    - Mockar pipeline completo com `LLM_Dispatcher` retornando a string gerada; verificar `"=== Resultado ==="` e a string na saída

  - [x]* 7.3 Escrever example tests para mensagens de progresso em `tests/test_cli_examples.py`
    - Mockar todos os módulos do pipeline; verificar que `"[1/5]"` a `"[5/5]"` aparecem na saída na ordem correta
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 8. Implementar smoke tests e example tests restantes
  - [x] 8.1 Completar `tests/test_cli_smoke.py` com verificações de estrutura de arquivos
    - Verificar existência de `cli.py`, `tokemize/`, e todos os submódulos definidos em 7.3 dos requisitos
    - Verificar que o comando `analyze` está registrado na instância `app` do Typer
    - _Requirements: 7.1, 7.2, 7.3_

  - [x]* 8.2 Escrever example tests para `--help` e invocação sem argumentos em `tests/test_cli_examples.py`
    - Invocar `runner.invoke(app, ["analyze"])` → verificar `exit_code == 0` e texto de ajuda na saída
    - Invocar `runner.invoke(app, ["analyze", "--help"])` → verificar `exit_code == 0` e descrições dos argumentos na saída
    - _Requirements: 1.4, 1.5_

- [x] 9. Checkpoint final — Garantir que todos os testes passam
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

## Notes

- Tasks marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada task referencia os requisitos específicos para rastreabilidade
- Os stubs dos módulos internos (task 3) permitem testar a CLI de ponta a ponta sem implementar a lógica de negócio real
- Property tests usam Hypothesis com `max_examples=100` conforme definido na estratégia de testes do design
- Os checkpoints garantem validação incremental antes de avançar para a próxima fase
