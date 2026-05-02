# Implementation Plan: tokemize-orchestrator

## Overview

Implementar o módulo orquestrador do Tokemize em Python, criando os modelos de dados compartilhados, os stubs funcionais de cada etapa do pipeline e o orquestrador central que coordena as 7 etapas sequenciais. Os testes unitários e de propriedade (Hypothesis) são criados em paralelo com a implementação para validação incremental.

## Tasks

- [x] 1. Criar modelos de dados compartilhados (`tokemize/models.py`)
  - Definir todos os dataclasses do pipeline: `ScannedFile`, `ScanOutput`, `AnalyzedFile`, `AnalysisOutput`, `EmbeddedFile`, `EmbeddingsOutput`, `SelectedFile`, `SelectionOutput`, `SummaryOutput`, `GeneratorOutput`, `PipelineResult`
  - Usar `dataclasses.dataclass` com `field(default_factory=list)` para todos os campos de lista
  - Incluir `Optional[str]` para `failed_stage` e `error_message` em `PipelineResult`
  - Adicionar docstrings no padrão Google Style para cada dataclass
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12_

- [x] 2. Implementar stubs funcionais das etapas do pipeline
  - [x] 2.1 Criar stub `tokemize/scanner.py` com `scan_repository(repo_path: str) -> ScanOutput`
    - Retornar `ScanOutput` com pelo menos um `ScannedFile` fictício mas estruturalmente válido
    - Lançar `NotADirectoryError` se `repo_path` não for um diretório válido
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 13.1_

  - [x] 2.2 Criar stub `tokemize/analyzer.py` com `analyze_files(scan_output: ScanOutput) -> AnalysisOutput`
    - Retornar `AnalysisOutput` com um `AnalyzedFile` por arquivo em `scan_output.files`
    - Retornar `AnalysisOutput(analyzed_files=[])` se `scan_output.files` estiver vazio
    - _Requirements: 7.1, 7.2, 7.4, 7.5, 13.2_

  - [x] 2.3 Criar stub `tokemize/embeddings.py` com `generate_embeddings(analysis_output: AnalysisOutput) -> EmbeddingsOutput`
    - Retornar `EmbeddingsOutput` com um `EmbeddedFile` por arquivo em `analysis_output.analyzed_files`
    - Garantir que `total_embedded + total_failed == len(embedded_files)`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 13.3_

  - [x] 2.4 Criar stub `tokemize/selector.py` com `select_relevant(embeddings_output: EmbeddingsOutput, task: str) -> SelectionOutput`
    - Retornar `SelectionOutput` com pelo menos um `SelectedFile` e `task` preservada no output
    - Garantir que `selected_files` esteja ordenado por `relevance_score` decrescente
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 13.4_

  - [x] 2.5 Criar stub `tokemize/summarizer.py` com `summarize_selected(selection_output: SelectionOutput) -> SummaryOutput`
    - Retornar `SummaryOutput` com `summarized_content` não-vazio quando há arquivos selecionados
    - Retornar `SummaryOutput(summarized_content="", token_count=0)` se `selected_files` estiver vazio
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 13.5_

  - [x] 2.6 Criar stub `tokemize/generator.py` com `generate_prompt(summary_output: SummaryOutput, task: str) -> GeneratorOutput`
    - Retornar `GeneratorOutput(prompt=task, token_count=0)` quando `summarized_content` estiver vazio
    - Retornar `GeneratorOutput` com `prompt` contendo contexto e task quando `summarized_content` não estiver vazio
    - _Requirements: 11.1, 11.2, 11.3, 13.6_

  - [x] 2.7 Criar stub `tokemize/reporter.py` com `format_result(generator_output: GeneratorOutput) -> PipelineResult`
    - Retornar `PipelineResult(success=True, prompt=generator_output.prompt, failed_stage=None, error_message=None)`
    - Nunca lançar exceção para nenhum input, incluindo `prompt=""`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 13.7_

- [x] 3. Implementar o orquestrador (`tokemize/orchestrator.py`)
  - [x] 3.1 Criar a função `run_pipeline(repo_path: str, task: str) -> PipelineResult`
    - Definir a sequência de 7 etapas com seus nomes e funções correspondentes
    - Usar `time.perf_counter()` para medir `elapsed_seconds`
    - Usar `logging.getLogger(__name__)` para logging estruturado
    - _Requirements: 1.1, 1.5, 4.4_

  - [x] 3.2 Implementar a lógica de execução sequencial e propagação de dados
    - Invocar cada etapa na ordem: scanner → analyzer → embeddings → selector → summarizer → generator → reporter
    - Passar `ScanOutput` ao analyzer, `AnalysisOutput` ao embeddings, `EmbeddingsOutput` ao selector (com `task`), `SelectionOutput` ao summarizer, `SummaryOutput` ao generator (com `task`), `GeneratorOutput` ao reporter
    - Augmentar o `PipelineResult` final com `elapsed_seconds` e `stages_completed`
    - _Requirements: 1.2, 1.3, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 3.3 Implementar captura de exceções e retorno de falha estruturado
    - Capturar qualquer `Exception` em qualquer etapa com `try/except`
    - Definir `failed_stage` com o nome da etapa que falhou
    - Definir `error_message` com `str(exc)`
    - Definir `stages_completed` com as etapas concluídas antes da falha
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 3.4 Implementar logging estruturado em cada etapa
    - Emitir `INFO` no início de cada etapa com o nome da etapa
    - Emitir `INFO` na conclusão de cada etapa com nome e tempo decorrido
    - Emitir `ERROR` com `exc_info=True` em caso de falha
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 4. Checkpoint — Verificar integração ponta a ponta com stubs
  - Garantir que `run_pipeline(".", "qualquer tarefa válida")` retorna `PipelineResult(success=True)` com `prompt` não-vazio
  - Garantir que todos os testes existentes continuam passando
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Criar testes unitários e de propriedade (`tests/test_orchestrator.py`)
  - [x] 5.1 Escrever testes unitários para o orquestrador
    - `test_run_pipeline_success`: pipeline completo com stubs retorna `PipelineResult(success=True)` com `prompt` não-vazio
    - `test_run_pipeline_fails_at_each_stage`: parametrizado para cada uma das 7 etapas — verifica `success=False`, `failed_stage` correto e `error_message` não-vazio
    - `test_stages_completed_on_partial_failure`: `stages_completed` contém exatamente as etapas anteriores à falha
    - `test_elapsed_seconds_is_positive`: `elapsed_seconds > 0` após execução bem-sucedida
    - `test_pipeline_result_on_empty_scan`: scanner retorna `ScanOutput(files=[])` → pipeline conclui com `success=True`
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x]* 5.2 Escrever property test — Property 1: `run_pipeline` nunca propaga exceção
    - **Property 1: run_pipeline nunca propaga exceção**
    - Para qualquer `repo_path` e `task` (incluindo strings vazias e arbitrárias), `run_pipeline` SHALL sempre retornar um `PipelineResult` e nunca lançar exceção
    - **Validates: Requirements 3.5, 14.1**

  - [x]* 5.3 Escrever property test — Property 2: Invariante de sucesso
    - **Property 2: Invariante de sucesso — campos nulos em caso de sucesso**
    - Para qualquer execução com `success=True`, `failed_stage` SHALL ser `None` e `error_message` SHALL ser `None`
    - **Validates: Requirements 1.4, 14.2**

  - [x]* 5.4 Escrever property test — Property 3: Invariante de falha — `failed_stage` pertence ao conjunto válido
    - **Property 3: Invariante de falha — failed_stage pertence ao conjunto válido**
    - Para qualquer execução com `success=False`, `failed_stage` SHALL ser um dos 7 nomes válidos: `"scanner"`, `"analyzer"`, `"embeddings"`, `"selector"`, `"summarizer"`, `"generator"`, `"reporter"`
    - **Validates: Requirements 3.2, 14.3**

  - [x]* 5.5 Escrever property test — Property 4: `elapsed_seconds` é sempre não-negativo
    - **Property 4: elapsed_seconds é sempre não-negativo**
    - Para qualquer execução, `PipelineResult.elapsed_seconds` SHALL ser `>= 0.0`
    - **Validates: Requirements 1.5, 3.6, 14.4**

  - [x]* 5.6 Escrever property test — Property 5: `stages_completed` é prefixo ordenado da sequência de etapas
    - **Property 5: stages_completed é prefixo ordenado da sequência de etapas**
    - Para qualquer execução, `stages_completed` SHALL ser um prefixo da lista `["scanner", "analyzer", "embeddings", "selector", "summarizer", "generator", "reporter"]` com comprimento `<= 7`
    - **Validates: Requirements 1.6, 3.4, 14.5, 14.6**

  - [x]* 5.7 Escrever property test — Property 6: Falha em etapa N preserva `stages_completed` das etapas anteriores
    - **Property 6: Falha em etapa N preserva stages_completed das etapas anteriores**
    - Para qualquer pipeline onde a etapa de índice N lança exceção, `stages_completed` SHALL conter exatamente os nomes das N etapas anteriores, na ordem de execução
    - **Validates: Requirements 3.4, 14.6**

- [x] 6. Criar testes unitários para os stubs das etapas
  - [x] 6.1 Escrever testes unitários para `scanner.py`
    - `test_scan_repository_returns_valid_scan_output`: verifica estrutura do `ScanOutput` retornado
    - `test_scan_repository_raises_not_a_directory_error`: verifica `NotADirectoryError` para caminho inválido
    - `test_scan_repository_total_files_consistent`: `total_files == len(files)`
    - _Requirements: 6.1, 6.3, 6.5_

  - [x]* 5.8 Escrever property test — Property 8: Scanner — `total_files` é consistente com `files`
    - **Property 8: Scanner — total_files é consistente com files**
    - Para qualquer `ScanOutput` retornado por `scan_repository`, `total_files` SHALL ser igual a `len(files)`
    - **Validates: Requirements 6.5**

  - [x]* 5.9 Escrever property test — Property 9: Scanner — `NotADirectoryError` para caminhos inválidos
    - **Property 9: Scanner — NotADirectoryError para caminhos inválidos**
    - Para qualquer string que não corresponda a um diretório válido, `scan_repository` SHALL lançar `NotADirectoryError`
    - **Validates: Requirements 6.3**

  - [x] 6.2 Escrever testes unitários para `embeddings.py`
    - `test_generate_embeddings_counters_consistent`: `total_embedded + total_failed == len(embedded_files)`
    - `test_generate_embeddings_empty_input`: retorna `EmbeddingsOutput(embedded_files=[])` para input vazio
    - _Requirements: 8.2, 8.4, 8.5_

  - [x]* 5.10 Escrever property test — Property 10: Embeddings — contadores são consistentes com a lista
    - **Property 10: Embeddings — contadores são consistentes com a lista**
    - Para qualquer `EmbeddingsOutput`, `total_embedded + total_failed` SHALL ser igual a `len(embedded_files)`
    - **Validates: Requirements 8.4, 8.5**

  - [x] 6.3 Escrever testes unitários para `selector.py`
    - `test_select_relevant_ordered_by_score`: `selected_files` ordenados por `relevance_score` decrescente
    - `test_select_relevant_task_preserved`: `SelectionOutput.task == task` passado como argumento
    - `test_select_relevant_empty_input`: retorna `SelectionOutput(selected_files=[])` para input vazio
    - _Requirements: 9.1, 9.2, 9.4_

  - [x]* 5.11 Escrever property test — Property 11: Selector — arquivos ordenados por relevância decrescente
    - **Property 11: Selector — arquivos ordenados por relevância decrescente**
    - Para qualquer `SelectionOutput` com dois ou mais arquivos, `relevance_score` SHALL estar em ordem não-crescente
    - **Validates: Requirements 9.1**

  - [x]* 5.12 Escrever property test — Property 12: Selector — `task` preservada no output
    - **Property 12: Selector — task preservada no output**
    - Para qualquer chamada a `select_relevant(embeddings_output, task)`, `SelectionOutput.task` SHALL ser igual à string `task` passada como argumento
    - **Validates: Requirements 9.4**

  - [x] 6.4 Escrever testes unitários para `generator.py`
    - `test_generate_prompt_fallback_to_task_when_empty_context`: `prompt == task` quando `summarized_content` é vazio
    - `test_generate_prompt_contains_context_and_task`: prompt contém contexto e task quando `summarized_content` não é vazio
    - _Requirements: 11.1, 11.2_

  - [x]* 5.13 Escrever property test — Property 13: Generator — fallback para `task` quando contexto vazio
    - **Property 13: Generator — fallback para task quando contexto vazio**
    - Para qualquer chamada com `summarized_content` vazio, `GeneratorOutput.prompt` SHALL ser igual à string `task`
    - **Validates: Requirements 11.2**

  - [x] 6.5 Escrever testes unitários para `reporter.py`
    - `test_format_result_success_with_prompt`: retorna `PipelineResult(success=True, prompt=generator_output.prompt)`
    - `test_format_result_success_with_empty_prompt`: retorna `PipelineResult(success=True, prompt="")` para `prompt=""`
    - `test_format_result_never_raises`: nunca lança exceção para nenhum input
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [x]* 5.14 Escrever property test — Property 14: Reporter — nunca lança exceção
    - **Property 14: Reporter — nunca lança exceção**
    - Para qualquer `GeneratorOutput` (incluindo `prompt=""` e valores extremos), `format_result` SHALL sempre retornar um `PipelineResult` válido e nunca lançar exceção
    - **Validates: Requirements 12.3**

  - [x]* 5.15 Escrever property test — Property 15: Reporter — round-trip do prompt
    - **Property 15: Reporter — round-trip do prompt**
    - Para qualquer `GeneratorOutput` com `prompt` não-vazio, `format_result(generator_output).prompt` SHALL ser igual a `generator_output.prompt`
    - **Validates: Requirements 12.1**

- [x] 7. Checkpoint final — Garantir que todos os testes passam
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- O design usa Python com dataclasses e stdlib apenas — sem dependências externas novas
- Os stubs são implementações funcionais reais (não mocks), substituíveis por implementações reais sem alterar o orquestrador
- Os property tests usam Hypothesis (já presente em `pyproject.toml` como dependência de dev)
- O pacote `tokemize/` na raiz é distinto de `src/tokemize/` — os novos arquivos vão em `tokemize/` (raiz)
- Cada property test referencia explicitamente a propriedade correspondente do design document
