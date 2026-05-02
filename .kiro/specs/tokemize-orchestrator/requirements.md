# Requirements Document

## Introduction

O `tokemize-orchestrator` é o módulo central de coordenação do Tokemize. Ele expõe a função pública `run_pipeline(repo_path, task) -> PipelineResult` que a CLI invoca para executar o pipeline completo de otimização de contexto para LLMs. O orquestrador coordena 7 etapas sequenciais — scanner, analyzer, embeddings, selector, summarizer, generator e reporter — propagando dados entre elas, capturando falhas com logging estruturado e retornando um `PipelineResult` com o resultado final e metadados de execução.

---

## Glossary

- **Orchestrator**: O módulo `tokemize/orchestrator.py` responsável por coordenar a execução sequencial das etapas do pipeline.
- **Pipeline**: Sequência ordenada de 7 etapas de processamento: scanner → analyzer → embeddings → selector → summarizer → generator → reporter.
- **PipelineResult**: Dataclass que encapsula o resultado completo da execução do pipeline, incluindo status de sucesso, prompt gerado, etapa de falha, mensagem de erro, tempo decorrido e lista de etapas concluídas.
- **Scanner**: Módulo `tokemize/scanner.py` responsável por percorrer o repositório e listar arquivos com metadados básicos.
- **Analyzer**: Módulo `tokemize/analyzer.py` responsável por analisar a estrutura dos arquivos e classificá-los por tipo e relevância potencial.
- **Embeddings**: Módulo `tokemize/embeddings.py` responsável por gerar representações vetoriais dos arquivos analisados.
- **Selector**: Módulo `tokemize/selector.py` responsável por selecionar os arquivos mais relevantes para a tarefa usando similaridade semântica.
- **Summarizer**: Módulo `tokemize/summarizer.py` responsável por resumir e comprimir o conteúdo dos arquivos selecionados.
- **Generator**: Módulo `tokemize/generator.py` responsável por montar o prompt final combinando contexto resumido e descrição da tarefa.
- **Reporter**: Módulo `tokemize/reporter.py` responsável por formatar e estruturar o resultado final para retorno à CLI.
- **ScanOutput**: Dataclass com a lista de arquivos encontrados e metadados da varredura.
- **AnalysisOutput**: Dataclass com arquivos enriquecidos com tipo, artefatos extraídos e score de relevância potencial.
- **EmbeddingsOutput**: Dataclass com arquivos e seus vetores de embedding associados.
- **SelectionOutput**: Dataclass com arquivos selecionados e scores de relevância, ordenados por relevância decrescente.
- **SummaryOutput**: Dataclass com conteúdo resumido e estimativa de tokens.
- **GeneratorOutput**: Dataclass com o prompt final formatado e contagem de tokens.
- **Stage**: Uma das 7 etapas nomeadas do pipeline: `"scanner"`, `"analyzer"`, `"embeddings"`, `"selector"`, `"summarizer"`, `"generator"`, `"reporter"`.
- **repo_path**: Caminho para a raiz do repositório a ser analisado.
- **task**: Descrição textual da tarefa técnica fornecida pelo usuário.

---

## Requirements

### Requirement 1: Execução do Pipeline Completo

**User Story:** As a developer, I want to call a single function `run_pipeline(repo_path, task)` that executes all 7 pipeline stages in sequence, so that I can obtain an optimized LLM prompt without managing individual stages.

#### Acceptance Criteria

1. THE Orchestrator SHALL expose a public function `run_pipeline(repo_path: str, task: str) -> PipelineResult`.
2. WHEN `run_pipeline` is called with a non-empty `repo_path` and a non-empty `task`, THE Orchestrator SHALL execute all 7 stages in the fixed order: scanner → analyzer → embeddings → selector → summarizer → generator → reporter.
3. WHEN all 7 stages complete without error, THE Orchestrator SHALL return a `PipelineResult` with `success=True` and a non-empty `prompt`.
4. WHEN all 7 stages complete without error, THE Orchestrator SHALL set `failed_stage` to `None` and `error_message` to `None` in the returned `PipelineResult`.
5. THE Orchestrator SHALL record the total execution time in `PipelineResult.elapsed_seconds` using `time.perf_counter()`.
6. WHEN all 7 stages complete without error, THE Orchestrator SHALL set `stages_completed` to the list of all 7 stage names in execution order.

---

### Requirement 2: Propagação de Dados entre Etapas

**User Story:** As a developer, I want each pipeline stage to receive the output of the previous stage as its input, so that data flows correctly through the pipeline without manual wiring.

#### Acceptance Criteria

1. WHEN the scanner stage completes, THE Orchestrator SHALL pass the `ScanOutput` as the sole argument to the analyzer stage.
2. WHEN the analyzer stage completes, THE Orchestrator SHALL pass the `AnalysisOutput` as the sole argument to the embeddings stage.
3. WHEN the embeddings stage completes, THE Orchestrator SHALL pass the `EmbeddingsOutput` as the sole argument to the selector stage.
4. WHEN the selector stage completes, THE Orchestrator SHALL pass the `SelectionOutput` and the original `task` string as arguments to the summarizer stage.
5. WHEN the summarizer stage completes, THE Orchestrator SHALL pass the `SummaryOutput` as the sole argument to the generator stage.
6. WHEN the generator stage completes, THE Orchestrator SHALL pass the `GeneratorOutput` and the original `task` string as arguments to the reporter stage.
7. WHEN the reporter stage completes, THE Orchestrator SHALL use the returned `PipelineResult` as the final result, augmenting it with `elapsed_seconds` and `stages_completed`.

---

### Requirement 3: Tratamento de Falhas no Pipeline

**User Story:** As a developer, I want the orchestrator to catch any exception from any stage and return a structured failure result, so that the CLI always receives a `PipelineResult` and never an unhandled exception.

#### Acceptance Criteria

1. WHEN any stage raises an `Exception`, THE Orchestrator SHALL catch it and return a `PipelineResult` with `success=False`.
2. WHEN a stage fails, THE Orchestrator SHALL set `PipelineResult.failed_stage` to the name of the failing stage.
3. WHEN a stage fails, THE Orchestrator SHALL set `PipelineResult.error_message` to the string representation of the exception.
4. WHEN a stage fails, THE Orchestrator SHALL set `PipelineResult.stages_completed` to the list of stage names that completed successfully before the failure.
5. THE Orchestrator SHALL never propagate an exception to the caller — `run_pipeline` SHALL always return a `PipelineResult`.
6. WHEN a stage fails, THE Orchestrator SHALL set `PipelineResult.elapsed_seconds` to the time elapsed from the start of `run_pipeline` until the failure.

---

### Requirement 4: Logging Estruturado

**User Story:** As a developer, I want the orchestrator to emit structured log messages at each stage boundary and on failures, so that I can trace pipeline execution and diagnose issues.

#### Acceptance Criteria

1. WHEN a stage begins execution, THE Orchestrator SHALL emit an `INFO` log message containing the stage name.
2. WHEN a stage completes successfully, THE Orchestrator SHALL emit an `INFO` log message containing the stage name and elapsed time for that stage.
3. WHEN a stage raises an exception, THE Orchestrator SHALL emit an `ERROR` log message containing the stage name, the exception message, and the full traceback (`exc_info=True`).
4. THE Orchestrator SHALL use Python's standard `logging` module with a named logger (e.g., `logging.getLogger(__name__)`).

---

### Requirement 5: Modelos de Dados Compartilhados

**User Story:** As a developer, I want all pipeline stages to share a common set of typed dataclasses, so that data contracts between stages are explicit and type-safe.

#### Acceptance Criteria

1. THE Models module SHALL define the `ScannedFile` dataclass with fields: `path: str`, `absolute_path: str`, `language: str`, `extension: str`, `size_bytes: int`, `line_count: int`.
2. THE Models module SHALL define the `ScanOutput` dataclass with fields: `repo_path: str`, `files: list[ScannedFile]`, `total_files: int`, `skipped_files: int`.
3. THE Models module SHALL define the `AnalyzedFile` dataclass with fields: `path: str`, `language: str`, `size_bytes: int`, `line_count: int`, `file_type: str`, `artifact_count: int`, `content: str`, `relevance_hint: float`.
4. THE Models module SHALL define the `AnalysisOutput` dataclass with fields: `analyzed_files: list[AnalyzedFile]`, `total_analyzed: int`, `total_skipped: int`.
5. THE Models module SHALL define the `EmbeddedFile` dataclass with fields: `path: str`, `language: str`, `content: str`, `embedding: list[float]`.
6. THE Models module SHALL define the `EmbeddingsOutput` dataclass with fields: `embedded_files: list[EmbeddedFile]`, `total_embedded: int`, `total_failed: int`.
7. THE Models module SHALL define the `SelectedFile` dataclass with fields: `path: str`, `language: str`, `content: str`, `relevance_score: float`.
8. THE Models module SHALL define the `SelectionOutput` dataclass with fields: `task: str`, `selected_files: list[SelectedFile]`, `total_candidates: int`.
9. THE Models module SHALL define the `SummaryOutput` dataclass with fields: `summarized_content: str`, `token_count: int`, `files_summarized: int`.
10. THE Models module SHALL define the `GeneratorOutput` dataclass with fields: `prompt: str`, `token_count: int`.
11. THE Models module SHALL define the `PipelineResult` dataclass with fields: `success: bool`, `prompt: str`, `failed_stage: Optional[str]`, `error_message: Optional[str]`, `elapsed_seconds: float`, `stages_completed: list[str]`.
12. THE Models module SHALL use Python `dataclasses.dataclass` with `field(default_factory=list)` for all list fields to avoid mutable default arguments.

---

### Requirement 6: Comportamento do Scanner

**User Story:** As a developer, I want the scanner to traverse a repository directory and return a list of files with metadata, so that subsequent stages have the file inventory they need.

#### Acceptance Criteria

1. WHEN `scan_repository(repo_path)` is called with a valid directory path, THE Scanner SHALL return a `ScanOutput` containing at least the files found at that path.
2. WHEN the target directory is empty or contains no accessible files, THE Scanner SHALL return `ScanOutput(files=[], total_files=0, skipped_files=0)`.
3. IF `repo_path` is not a valid directory, THEN THE Scanner SHALL raise `NotADirectoryError`.
4. THE Scanner SHALL populate each `ScannedFile` with `path`, `absolute_path`, `language`, `extension`, `size_bytes`, and `line_count`.
5. THE Scanner SHALL set `ScanOutput.total_files` to the count of files in `ScanOutput.files`.

---

### Requirement 7: Comportamento do Analyzer

**User Story:** As a developer, I want the analyzer to enrich each scanned file with structural metadata, so that the selector can make informed relevance decisions.

#### Acceptance Criteria

1. WHEN `analyze_files(scan_output)` is called with a non-empty `ScanOutput`, THE Analyzer SHALL return an `AnalysisOutput` with one `AnalyzedFile` per successfully analyzed file.
2. WHEN `scan_output.files` is empty, THE Analyzer SHALL return `AnalysisOutput(analyzed_files=[])`.
3. IF a single file fails analysis, THEN THE Analyzer SHALL log a `WARNING` for that file and continue processing the remaining files.
4. THE Analyzer SHALL set `file_type` to one of: `"source"`, `"config"`, `"test"`, `"doc"`, `"unknown"`.
5. THE Analyzer SHALL set `relevance_hint` to a float value in the range `[0.0, 1.0]`.

---

### Requirement 8: Comportamento do Embeddings

**User Story:** As a developer, I want the embeddings module to generate vector representations for each analyzed file, so that semantic similarity search is possible in the selector stage.

#### Acceptance Criteria

1. WHEN `generate_embeddings(analysis_output)` is called with a non-empty `AnalysisOutput`, THE Embeddings module SHALL return an `EmbeddingsOutput` with one `EmbeddedFile` per input file.
2. WHEN `analysis_output.analyzed_files` is empty, THE Embeddings module SHALL return `EmbeddingsOutput(embedded_files=[])`.
3. IF embedding generation fails for a single file, THEN THE Embeddings module SHALL log a `WARNING` and include that file in the output with `embedding=[]`.
4. THE Embeddings module SHALL set `EmbeddingsOutput.total_embedded` to the count of files with a non-empty embedding.
5. THE Embeddings module SHALL set `EmbeddingsOutput.total_failed` to the count of files with `embedding=[]`.

---

### Requirement 9: Comportamento do Selector

**User Story:** As a developer, I want the selector to rank and filter files by semantic relevance to the task, so that only the most pertinent files are passed to the summarizer.

#### Acceptance Criteria

1. WHEN `select_relevant(embeddings_output, task)` is called with a non-empty `EmbeddingsOutput` and a non-empty `task`, THE Selector SHALL return a `SelectionOutput` with files ordered by `relevance_score` in descending order.
2. WHEN `embeddings_output.embedded_files` is empty or no file meets the minimum relevance threshold, THE Selector SHALL return `SelectionOutput(selected_files=[])`.
3. THE Selector SHALL set `relevance_score` to a float value in the range `[0.0, 1.0]` for each selected file.
4. THE Selector SHALL set `SelectionOutput.task` to the `task` string passed as input.
5. THE Selector SHALL set `SelectionOutput.total_candidates` to the total number of files evaluated before filtering.

---

### Requirement 10: Comportamento do Summarizer

**User Story:** As a developer, I want the summarizer to compress selected file contents to fit within the LLM context budget, so that the generator receives a concise and token-efficient context.

#### Acceptance Criteria

1. WHEN `summarize_selected(selection_output)` is called with a non-empty `SelectionOutput`, THE Summarizer SHALL return a `SummaryOutput` with non-empty `summarized_content`.
2. WHEN `selection_output.selected_files` is empty, THE Summarizer SHALL return `SummaryOutput(summarized_content="", token_count=0)`.
3. THE Summarizer SHALL set `SummaryOutput.token_count` to a non-negative integer representing the estimated token count of `summarized_content`.
4. THE Summarizer SHALL set `SummaryOutput.files_summarized` to the count of files whose content was included in `summarized_content`.

---

### Requirement 11: Comportamento do Generator

**User Story:** As a developer, I want the generator to assemble the final optimized prompt by combining the summarized context with the task description, so that the LLM receives a well-structured and complete prompt.

#### Acceptance Criteria

1. WHEN `generate_prompt(summary_output, task)` is called with non-empty `summarized_content` and a non-empty `task`, THE Generator SHALL return a `GeneratorOutput` with a `prompt` that contains both the summarized context and the task description.
2. WHEN `summary_output.summarized_content` is empty, THE Generator SHALL return `GeneratorOutput(prompt=task, token_count=0)`.
3. THE Generator SHALL set `GeneratorOutput.token_count` to a non-negative integer representing the estimated token count of the generated prompt.

---

### Requirement 12: Comportamento do Reporter

**User Story:** As a developer, I want the reporter to format the generator output into a structured `PipelineResult`, so that the CLI receives a consistent and complete result object.

#### Acceptance Criteria

1. WHEN `format_result(generator_output)` is called with a non-empty `GeneratorOutput.prompt`, THE Reporter SHALL return a `PipelineResult` with `success=True` and `prompt` equal to `generator_output.prompt`.
2. WHEN `generator_output.prompt` is empty, THE Reporter SHALL return a `PipelineResult` with `success=True` and `prompt=""`.
3. THE Reporter SHALL never raise an exception — it SHALL always return a valid `PipelineResult`.
4. THE Reporter SHALL set `PipelineResult.failed_stage` to `None` and `PipelineResult.error_message` to `None` in the returned result.

---

### Requirement 13: Stubs Funcionais para Cada Módulo

**User Story:** As a developer, I want each pipeline stage to have a functional stub implementation, so that the full pipeline can be exercised end-to-end before real implementations are available.

#### Acceptance Criteria

1. THE Scanner stub SHALL accept `repo_path: str` and return a structurally valid `ScanOutput` with at least one `ScannedFile`.
2. THE Analyzer stub SHALL accept `ScanOutput` and return a structurally valid `AnalysisOutput` with one `AnalyzedFile` per input file.
3. THE Embeddings stub SHALL accept `AnalysisOutput` and return a structurally valid `EmbeddingsOutput` with one `EmbeddedFile` per input file.
4. THE Selector stub SHALL accept `EmbeddingsOutput` and `task: str` and return a structurally valid `SelectionOutput` with at least one `SelectedFile`.
5. THE Summarizer stub SHALL accept `SelectionOutput` and return a structurally valid `SummaryOutput` with non-empty `summarized_content`.
6. THE Generator stub SHALL accept `SummaryOutput` and `task: str` and return a structurally valid `GeneratorOutput` with a non-empty `prompt`.
7. THE Reporter stub SHALL accept `GeneratorOutput` and return a `PipelineResult` with `success=True`.
8. WHEN the full pipeline is executed with all stubs, THE Orchestrator SHALL return `PipelineResult(success=True)` with a non-empty `prompt`.

---

### Requirement 14: Invariantes do PipelineResult

**User Story:** As a developer, I want `PipelineResult` to always satisfy a set of structural invariants, so that callers can rely on consistent and predictable result semantics.

#### Acceptance Criteria

1. THE Orchestrator SHALL always return a `PipelineResult` from `run_pipeline`, regardless of what happens during execution.
2. WHEN `PipelineResult.success` is `True`, THE Orchestrator SHALL ensure `failed_stage` is `None` and `error_message` is `None`.
3. WHEN `PipelineResult.success` is `False`, THE Orchestrator SHALL ensure `failed_stage` is one of the 7 valid stage names: `"scanner"`, `"analyzer"`, `"embeddings"`, `"selector"`, `"summarizer"`, `"generator"`, `"reporter"`.
4. THE Orchestrator SHALL ensure `PipelineResult.elapsed_seconds` is greater than or equal to `0.0`.
5. THE Orchestrator SHALL ensure `len(PipelineResult.stages_completed)` is less than or equal to 7.
6. THE Orchestrator SHALL ensure `PipelineResult.stages_completed` contains only valid stage names and is ordered by execution sequence.
