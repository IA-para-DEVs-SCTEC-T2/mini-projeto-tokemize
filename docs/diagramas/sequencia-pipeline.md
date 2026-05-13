# Diagrama de Sequência — Pipeline Tokemize

## Fluxo Principal (CLI)

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuário
    participant CLI as CLI (toke/prepare)
    participant RA as Repository_Analyzer
    participant Scanner as RepositoryScanner
    participant TSA as TreeSitterAnalyzer
    participant Selector as Intelligent_Selector
    participant Compressor as Compressor
    participant Store as Context_Store
    participant Builder as Prompt_Builder
    participant Clipboard as Clipboard

    User->>CLI: toke(repo_path, task_description)
    activate CLI

    Note over CLI: Validação de entradas<br/>(path existe? task >= 3 chars?)

    %% Etapa 1: Repository_Analyzer
    CLI->>RA: analyze_repository(repo_path)
    activate RA

    RA->>Scanner: scan(Path(repo_path))
    activate Scanner
    Scanner-->>RA: ScanResult(files: list[FileMetadata])
    deactivate Scanner

    loop Para cada FileMetadata
        RA->>TSA: analyze(file_path)
        activate TSA
        TSA-->>RA: list[Artifact]
        deactivate TSA
    end

    RA-->>CLI: RepositoryStructure(files, metadata[file_analyses])
    deactivate RA

    %% Etapa 2: Intelligent_Selector
    CLI->>Selector: select_relevant_artifacts(file_analyses, task_description, top_n=5)
    activate Selector

    Note over Selector: 1. Tokeniza task_description<br/>2. Pontua cada Artifact<br/>3. Ordena por score desc<br/>4. Retorna top_n com score > 0

    Selector-->>CLI: list[Artifact] (relevantes)
    deactivate Selector

    %% Etapa 3: Compressor
    CLI->>Compressor: compress_context(artifacts)
    activate Compressor

    Note over Compressor: Agrupa por file_path<br/>Gera blocos Markdown<br/>Calcula token_count

    Compressor-->>CLI: CompressedContext(compressed_content, token_count, artifact_count)
    deactivate Compressor

    %% Etapa 4: Context_Store (não-fatal)
    CLI->>Store: save_context(compressed_content, task_description, repo_path)
    activate Store

    Note over Store: Gera slug + data<br/>Salva em .tokemize/context/<slug>-<YYYYMMDD>.md

    Store-->>CLI: context_file_path: str | None
    deactivate Store

    %% Etapa 5: Prompt_Builder
    CLI->>Builder: build_prompt(compressed_ctx, task_description, context_file_path)
    activate Builder

    Note over Builder: Monta Markdown:<br/>## Tarefa<br/>## Objetivo<br/>## Contexto relevante<br/>## Instrução para a IDE<br/>## Arquivo de contexto

    Builder-->>CLI: OptimizedPrompt(content, task_description, token_estimate)
    deactivate Builder

    %% Etapa 6: Clipboard
    CLI->>Clipboard: copy_to_clipboard(prompt.content)
    activate Clipboard
    Clipboard-->>CLI: success / ClipboardError
    deactivate Clipboard

    CLI-->>User: ✅ Prompt copiado para a área de transferência
    deactivate CLI
```

## Descrição das Etapas

| # | Etapa | Componente | Entrada | Saída |
|---|-------|-----------|---------|-------|
| 1 | Análise do Repositório | `Repository_Analyzer` | `repo_path: str` | `RepositoryStructure` com `list[FileAnalysis]` |
| 2 | Seleção Inteligente | `Intelligent_Selector` | `list[FileAnalysis]`, `task_description` | `list[Artifact]` (top N relevantes) |
| 3 | Compressão | `Compressor` | `list[Artifact]` | `CompressedContext` (Markdown compacto) |
| 4 | Persistência | `Context_Store` | `compressed_content`, `task_description`, `repo_path` | Caminho do arquivo salvo (ou `None`) |
| 5 | Geração de Prompt | `Prompt_Builder` | `CompressedContext`, `task_description`, `context_file_path` | `OptimizedPrompt` |
| 6 | Clipboard | `Clipboard` | `prompt.content: str` | Cópia para área de transferência |

## Modelos de Dados Principais

- **`FileMetadata`** — Metadados de arquivo (path, linguagem, tamanho, linhas)
- **`Artifact`** — Unidade sintática extraída (nome, tipo, linhas, conteúdo, linguagem)
- **`FileAnalysis`** — Arquivo + seus artefatos extraídos
- **`CompressedContext`** — Contexto compactado em Markdown com contagem de tokens
- **`OptimizedPrompt`** — Prompt final pronto para o chatbot da IDE

## Notas

- A etapa **Context_Store** é **não-fatal**: falhas de I/O são capturadas e o pipeline continua.
- O **TreeSitterAnalyzer** suporta Python, Java, JavaScript e TypeScript.
- Arquivos com linguagem não suportada recebem `artifacts=[]` sem propagar exceção.
- O **Intelligent_Selector** usa heurística de palavras-chave (sem embeddings) para ranquear artefatos.
