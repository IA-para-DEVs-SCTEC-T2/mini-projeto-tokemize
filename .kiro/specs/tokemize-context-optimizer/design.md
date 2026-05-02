# Design Document — Tokemize Context Optimizer

## Overview

O Tokemize é um pipeline de otimização de contexto para LLMs composto por quatro camadas principais orquestradas em sequência: **Parser → Indexer → Selector → Optimizer**. O objetivo central é reduzir o custo de tokens e aumentar a precisão das respostas de LLMs ao enviar apenas os artefatos de código mais relevantes para cada requisição.

O sistema resolve o problema de "context stuffing" — a prática de enviar arquivos inteiros ou repositórios completos para o LLM — substituindo-a por uma seleção semântica precisa baseada em similaridade vetorial. O resultado é um bloco de contexto compacto, estruturado e dentro de um budget de tokens configurável.

### Princípios de Design

- **Separação de responsabilidades**: cada camada tem uma única responsabilidade bem definida e se comunica com as demais exclusivamente por meio de dataclasses tipadas.
- **Substituibilidade de provedores**: tanto o provedor de embeddings quanto o provedor de LLM são abstraídos por interfaces, permitindo troca sem alteração do pipeline.
- **Persistência entre sessões**: o índice FAISS é persistido em disco, evitando reindexação desnecessária em execuções subsequentes sobre os mesmos arquivos.
- **Observabilidade**: todas as etapas emitem logs estruturados; métricas de execução são coletadas e expostas via `PipelineMetrics`.
- **Segurança de credenciais**: chaves de API são lidas exclusivamente de variáveis de ambiente; nenhum valor sensível é logado.

---

## Architecture

O diagrama abaixo representa o fluxo de dados entre os componentes do sistema:

```mermaid
flowchart TD
    User([Usuário]) -->|request + files + budget| Optimizer

    subgraph core["tokemize/core/"]
        Optimizer["Optimizer\n(optimizer/)"]
        Parser["Parser\n(parser/)"]
        Indexer["Indexer\n(indexer/)"]
        Selector["Selector\n(selector/)"]
    end

    subgraph integrations["tokemize/integrations/"]
        EmbClient["EmbeddingsClient\n(embeddings/)"]
        LLMClient["LLMClient\n(llm/)"]
    end

    subgraph external["APIs Externas"]
        OpenAIEmb["OpenAI\nEmbeddings API"]
        OpenAILLM["OpenAI\nChat API"]
        AnthropicLLM["Anthropic\nMessages API"]
    end

    subgraph persistence["Persistência Local"]
        FAISSFile[("FAISS Index\n(.tokemize_index/)")]
    end

    subgraph models["tokemize/models/"]
        Artifact["Artifact"]
        Chunk["Chunk"]
        OptCtx["OptimizedContext"]
        LLMResp["LLMResponse"]
        Metrics["PipelineMetrics"]
    end

    Optimizer --> Parser
    Parser -->|list[Artifact]| Optimizer
    Optimizer --> EmbClient
    EmbClient -->|list[float]| Optimizer
    Optimizer --> Indexer
    Indexer <-->|read/write| FAISSFile
    Indexer -->|list[Chunk]| Optimizer
    Optimizer --> Selector
    Selector --> EmbClient
    EmbClient --> OpenAIEmb
    Selector -->|OptimizedContext| Optimizer
    Optimizer -->|OptimizedContext| User
    User -->|OptimizedContext + request| LLMClient
    LLMClient --> OpenAILLM
    LLMClient --> AnthropicLLM
    LLMClient -->|LLMResponse| User
```

### Fluxo de Dados Principal

```
Requisição do usuário + arquivos de código-fonte + budget
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  Optimizer.optimize(request, files, budget)             │
│                                                         │
│  1. Parser.parse(file) → list[Artifact]                 │
│  2. EmbeddingsClient.embed(chunks) → list[list[float]]  │
│  3. Indexer.add(chunks) + Indexer.save()                │
│  4. Selector.select(request, budget) → OptimizedContext │
│  5. Formatar contexto final                             │
│  6. Emitir PipelineMetrics                              │
└─────────────────────────────────────────────────────────┘
        │
        ▼
OptimizedContext (chunks selecionados + formatted_text + total_tokens)
        │
        ▼
LLMClient.complete(context, request, model) → LLMResponse
```

---

## Components and Interfaces

### 2.1 Parser (`tokemize/core/parser/`)

Responsável por analisar sintaticamente arquivos de código-fonte usando Tree-sitter e extrair artefatos estruturados.

**Arquivo principal:** `tokemize/core/parser/code_parser.py`

```python
from pathlib import Path
from tokemize.models.artifact import Artifact

SUPPORTED_LANGUAGES: dict[str, str] = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
}

class CodeParser:
    """Analisa sintaticamente arquivos de código-fonte usando Tree-sitter.

    Args:
        language_map: Mapeamento de extensão de arquivo para nome de linguagem.
            Usa SUPPORTED_LANGUAGES por padrão.
    """

    def __init__(self, language_map: dict[str, str] | None = None) -> None: ...

    def parse(self, file_path: Path) -> list[Artifact]:
        """Extrai artefatos sintáticos de um arquivo de código-fonte.

        Args:
            file_path: Caminho absoluto ou relativo para o arquivo a ser analisado.

        Returns:
            Lista de Artifact extraídos do arquivo. Pode ser parcial se houver
            erros de sintaxe — os artefatos válidos são retornados mesmo assim.

        Raises:
            UnsupportedLanguageError: Se a extensão do arquivo não for suportada.
            FileNotFoundError: Se o arquivo não existir no caminho fornecido.
        """
        ...

    def parse_many(self, file_paths: list[Path]) -> list[Artifact]:
        """Extrai artefatos de múltiplos arquivos.

        Args:
            file_paths: Lista de caminhos de arquivos a serem analisados.

        Returns:
            Lista concatenada de todos os artefatos extraídos.
        """
        ...

    def _detect_language(self, file_path: Path) -> str:
        """Detecta a linguagem com base na extensão do arquivo."""
        ...

    def _extract_artifacts(
        self, tree: object, source: bytes, language: str, file_path: Path
    ) -> list[Artifact]:
        """Percorre a AST e extrai nós relevantes como artefatos."""
        ...
```

**Exceções:**

```python
class UnsupportedLanguageError(ValueError):
    """Lançada quando a extensão do arquivo não tem grammar Tree-sitter mapeado."""
    ...

class ParseError(RuntimeError):
    """Lançada quando o Tree-sitter falha ao processar o arquivo."""
    ...
```

**Decisão de design:** O Parser não cria `Chunk` diretamente — ele retorna `Artifact`. A conversão de `Artifact` para `Chunk` (incluindo contagem de tokens) é responsabilidade do Optimizer, que tem acesso ao modelo LLM configurado para usar o tokenizador correto.

---

### 2.2 EmbeddingsClient (`tokemize/integrations/embeddings/`)

Gera representações vetoriais de chunks usando a API OpenAI text-embedding.

**Arquivo principal:** `tokemize/integrations/embeddings/embeddings_client.py`

```python
from tokemize.models.chunk import Chunk

class EmbeddingsClient:
    """Cliente para geração de embeddings via API OpenAI.

    Args:
        api_key: Chave de API OpenAI. Lida de OPENAI_API_KEY se não fornecida.
        model: Nome do modelo de embedding (ex: "text-embedding-3-small").
        batch_size: Número máximo de chunks por chamada à API. Padrão: 100.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        batch_size: int = 100,
    ) -> None: ...

    def embed_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Gera embeddings para uma lista de chunks e retorna chunks atualizados.

        Processa em lotes de até `batch_size` itens. Realiza até 3 tentativas
        com backoff exponencial em caso de falha da API.

        Args:
            chunks: Lista de Chunk sem embedding (embedding=None).

        Returns:
            Lista de Chunk com o campo `embedding` preenchido.

        Raises:
            EmbeddingAPIError: Se todas as tentativas falharem.
        """
        ...

    def embed_text(self, text: str) -> list[float]:
        """Gera embedding para um texto arbitrário (usado pelo Selector para a query).

        Args:
            text: Texto a ser convertido em vetor.

        Returns:
            Vetor de embedding como lista de floats.

        Raises:
            EmbeddingAPIError: Se a chamada à API falhar após retentativas.
        """
        ...

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Chama a API para um lote de textos. Implementa retry com backoff."""
        ...
```

**Exceções:**

```python
class EmbeddingAPIError(RuntimeError):
    """Lançada quando a API de embeddings falha após todas as tentativas."""
    ...
```

---

### 2.3 Indexer (`tokemize/core/indexer/`)

Gerencia o índice FAISS: adição de vetores, persistência em disco e busca por similaridade.

**Arquivo principal:** `tokemize/core/indexer/faiss_indexer.py`

```python
from pathlib import Path
from tokemize.models.chunk import Chunk

class FAISSIndexer:
    """Gerencia o índice vetorial FAISS para busca por similaridade.

    Args:
        index_path: Diretório onde o índice será persistido.
        dimension: Dimensão dos vetores de embedding. Padrão: 1536 (text-embedding-3-small).
    """

    def __init__(self, index_path: Path, dimension: int = 1536) -> None: ...

    def add(self, chunks: list[Chunk]) -> None:
        """Adiciona chunks ao índice FAISS.

        Suporta adição incremental — não requer reindexação completa.

        Args:
            chunks: Lista de Chunk com embedding preenchido.

        Raises:
            ValueError: Se algum chunk não tiver embedding.
            IndexDimensionError: Se a dimensão do vetor não corresponder ao índice.
        """
        ...

    def search(self, query_vector: list[float], top_k: int = 20) -> list[tuple[Chunk, float]]:
        """Busca os chunks mais similares ao vetor de query.

        Args:
            query_vector: Vetor de embedding da requisição do usuário.
            top_k: Número máximo de resultados a retornar.

        Returns:
            Lista de tuplas (Chunk, score) ordenadas por score decrescente.

        Raises:
            EmptyIndexError: Se o índice estiver vazio.
        """
        ...

    def save(self) -> None:
        """Persiste o índice FAISS e o mapeamento de metadados em disco."""
        ...

    def load(self) -> None:
        """Carrega o índice FAISS do disco.

        Verifica a integridade antes de disponibilizar para consultas.
        Se o arquivo estiver corrompido, cria um novo índice vazio e loga aviso.
        """
        ...

    def is_loaded(self) -> bool:
        """Retorna True se o índice está carregado e pronto para consultas."""
        ...

    def _verify_integrity(self) -> bool:
        """Verifica se o índice carregado é consistente com os metadados."""
        ...
```

**Estratégia de persistência:**

O Indexer persiste dois arquivos no diretório `FAISS_INDEX_PATH`:
- `index.faiss` — o índice vetorial binário FAISS (`faiss.write_index`)
- `metadata.json` — mapeamento de `int` (posição no índice FAISS) → `Chunk` serializado

A verificação de integridade consiste em confirmar que o número de vetores no índice FAISS corresponde ao número de entradas no `metadata.json`.

**Exceções:**

```python
class EmptyIndexError(RuntimeError):
    """Lançada quando uma busca é realizada em um índice vazio."""
    ...

class IndexDimensionError(ValueError):
    """Lançada quando a dimensão do vetor não corresponde ao índice existente."""
    ...
```

---

### 2.4 Selector (`tokemize/core/selector/`)

Busca e ranqueia os chunks mais relevantes para uma requisição, respeitando o budget de tokens.

**Arquivo principal:** `tokemize/core/selector/context_selector.py`

```python
from tokemize.core.indexer.faiss_indexer import FAISSIndexer
from tokemize.integrations.embeddings.embeddings_client import EmbeddingsClient
from tokemize.models.context import OptimizedContext

class ContextSelector:
    """Seleciona e ranqueia chunks relevantes respeitando o budget de tokens.

    Args:
        indexer: Instância do FAISSIndexer com índice carregado.
        embeddings_client: Cliente para gerar embedding da query.
        relevance_threshold: Score mínimo de relevância (0.0–1.0). Padrão: 0.75.
        top_k: Número de candidatos a recuperar do FAISS antes de filtrar.
    """

    def __init__(
        self,
        indexer: FAISSIndexer,
        embeddings_client: EmbeddingsClient,
        relevance_threshold: float = 0.75,
        top_k: int = 20,
    ) -> None: ...

    def select(self, request: str, token_budget: int) -> OptimizedContext:
        """Seleciona os chunks mais relevantes dentro do budget de tokens.

        Etapas:
        1. Gera embedding da requisição.
        2. Busca top_k candidatos no FAISS.
        3. Filtra por relevance_threshold.
        4. Ordena por score decrescente; desempata por menor token_count.
        5. Acumula chunks até atingir token_budget.
        6. Retorna OptimizedContext com os chunks selecionados.

        Args:
            request: Texto da requisição do usuário.
            token_budget: Limite máximo de tokens para o contexto.

        Returns:
            OptimizedContext com chunks selecionados, total_tokens e formatted_text.
        """
        ...

    def _accumulate_within_budget(
        self,
        ranked_chunks: list[tuple["Chunk", float]],
        token_budget: int,
    ) -> list["Chunk"]:
        """Acumula chunks em ordem de relevância até o budget ser atingido."""
        ...
```

---

### 2.5 Optimizer (`tokemize/core/optimizer/`)

Orquestrador do pipeline completo. Coordena Parser → EmbeddingsClient → Indexer → Selector e monta o contexto final.

**Arquivo principal:** `tokemize/core/optimizer/pipeline_optimizer.py`

```python
from pathlib import Path
from tokemize.models.context import OptimizedContext
from tokemize.models.metrics import PipelineMetrics

class PipelineOptimizer:
    """Orquestrador do pipeline de otimização de contexto.

    Args:
        parser: Instância de CodeParser.
        indexer: Instância de FAISSIndexer.
        selector: Instância de ContextSelector.
        embeddings_client: Instância de EmbeddingsClient.
        llm_model: Nome do modelo LLM (usado para tokenização).
    """

    def __init__(
        self,
        parser: "CodeParser",
        indexer: "FAISSIndexer",
        selector: "ContextSelector",
        embeddings_client: "EmbeddingsClient",
        llm_model: str,
    ) -> None: ...

    def optimize(
        self,
        request: str,
        files: list[Path],
        budget: int,
    ) -> tuple[OptimizedContext, PipelineMetrics]:
        """Executa o pipeline completo e retorna o contexto otimizado.

        Reutiliza o índice FAISS persistido se os arquivos já foram indexados.
        Registra logs de início, fim e métricas de execução.

        Args:
            request: Requisição do usuário.
            files: Lista de arquivos de código-fonte a serem analisados.
            budget: Budget máximo de tokens para o contexto.

        Returns:
            Tupla (OptimizedContext, PipelineMetrics).

        Raises:
            PipelineError: Se qualquer etapa do pipeline falhar, com o nome
                da etapa que originou o erro.
        """
        ...

    def _artifacts_to_chunks(
        self, artifacts: list["Artifact"], model: str
    ) -> list["Chunk"]:
        """Converte Artifacts em Chunks, calculando token_count para o modelo."""
        ...

    def _format_context(self, chunks: list["Chunk"]) -> str:
        """Formata os chunks selecionados em um bloco de texto estruturado."""
        ...
```

**Formato do contexto formatado:**

```
### [language] — artifact_name
```artifact_language
artifact_content
```

### [python] — calculate_similarity
```python
def calculate_similarity(a: list[float], b: list[float]) -> float:
    ...
```
```

---

### 2.6 LLMClient (`tokemize/integrations/llm/`)

Interface de abstração para comunicação com provedores de LLM.

**Arquivo principal:** `tokemize/integrations/llm/base_client.py`

```python
from abc import ABC, abstractmethod
from tokemize.models.llm_response import LLMResponse

class BaseLLMClient(ABC):
    """Interface abstrata para clientes de LLM.

    Todos os provedores devem implementar esta interface.
    """

    @abstractmethod
    def complete(
        self,
        context: str,
        request: str,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Envia contexto + requisição ao LLM e retorna a resposta.

        Args:
            context: Contexto otimizado formatado.
            request: Requisição do usuário.
            model: Identificador do modelo a ser usado.
            temperature: Temperatura de amostragem (0.0–2.0).
            max_tokens: Limite de tokens na resposta.
            system_prompt: Prompt de sistema opcional.

        Returns:
            LLMResponse com texto, contagem de tokens e metadados.

        Raises:
            LLMAuthError: Se a chave de API for inválida (HTTP 401).
            LLMRateLimitError: Se o rate limit for atingido e o retry falhar.
            LLMAPIError: Para outros erros da API.
        """
        ...
```

**Implementações concretas:**

```python
# tokemize/integrations/llm/openai_client.py
class OpenAIClient(BaseLLMClient):
    """Cliente para a API OpenAI (GPT-4o, GPT-4-turbo).

    Args:
        api_key: Chave de API OpenAI. Lida de OPENAI_API_KEY.
    """
    def __init__(self, api_key: str) -> None: ...
    def complete(self, context, request, model, **kwargs) -> LLMResponse: ...

# tokemize/integrations/llm/anthropic_client.py
class AnthropicClient(BaseLLMClient):
    """Cliente para a API Anthropic (Claude Sonnet, Claude Opus).

    Args:
        api_key: Chave de API Anthropic. Lida de ANTHROPIC_API_KEY.
    """
    def __init__(self, api_key: str) -> None: ...
    def complete(self, context, request, model, **kwargs) -> LLMResponse: ...
```

**Exceções:**

```python
class LLMAuthError(RuntimeError):
    """Lançada em erro HTTP 401. Não realiza retentativas."""
    ...

class LLMRateLimitError(RuntimeError):
    """Lançada quando o rate limit é atingido e o retry esgota."""
    ...

class LLMAPIError(RuntimeError):
    """Erro genérico da API do provedor LLM."""
    ...
```

---

### 2.7 Config (`tokemize/config/`)

Carrega e valida todas as configurações do sistema a partir de variáveis de ambiente.

**Arquivo principal:** `tokemize/config/config_loader.py`

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class TokemizeConfig:
    """Configuração imutável do sistema Tokemize.

    Attributes:
        openai_api_key: Chave de API OpenAI.
        anthropic_api_key: Chave de API Anthropic.
        embedding_model: Modelo de embedding (ex: "text-embedding-3-small").
        llm_provider: Provedor LLM ("openai" ou "anthropic").
        llm_model: Modelo LLM (ex: "gpt-4o", "claude-3-5-sonnet-20241022").
        token_budget: Budget máximo de tokens. Padrão: 4096.
        relevance_threshold: Limiar mínimo de relevância [0.0, 1.0]. Padrão: 0.75.
        faiss_index_path: Diretório do índice FAISS. Padrão: "./.tokemize_index".
        embedding_batch_size: Tamanho do lote de embeddings. Padrão: 100.
        log_level: Nível de log. Padrão: "INFO".
    """
    openai_api_key: str
    anthropic_api_key: str
    embedding_model: str
    llm_provider: str
    llm_model: str
    token_budget: int = 4096
    relevance_threshold: float = 0.75
    faiss_index_path: Path = Path("./.tokemize_index")
    embedding_batch_size: int = 100
    log_level: str = "INFO"


def load_config(env_file: Path | None = None) -> TokemizeConfig:
    """Carrega e valida a configuração a partir de variáveis de ambiente.

    Args:
        env_file: Caminho para o arquivo .env. Usa ".env" por padrão.

    Returns:
        TokemizeConfig validado e imutável.

    Raises:
        MissingConfigError: Se uma variável obrigatória não estiver definida.
        InvalidConfigError: Se um valor de configuração for inválido.
    """
    ...
```

**Exceções:**

```python
class MissingConfigError(ValueError):
    """Lançada quando uma variável de ambiente obrigatória não está definida."""
    ...

class InvalidConfigError(ValueError):
    """Lançada quando um valor de configuração é inválido."""
    ...
```

---

### 2.8 Artifact Serializer (`tokemize/models/`)

Serializa e desserializa `Artifact` e `Chunk` para/de JSON.

**Arquivo principal:** `tokemize/models/serializer.py`

```python
import json
from tokemize.models.artifact import Artifact
from tokemize.models.chunk import Chunk

class ArtifactSerializer:
    """Serializa e desserializa Artifact e Chunk para JSON."""

    @staticmethod
    def serialize_artifact(artifact: Artifact) -> str:
        """Serializa um Artifact para string JSON."""
        ...

    @staticmethod
    def deserialize_artifact(data: str | dict) -> Artifact:
        """Desserializa JSON para um Artifact.

        Raises:
            DeserializationError: Se o JSON for inválido ou campos obrigatórios
                estiverem ausentes.
        """
        ...

    @staticmethod
    def serialize_chunk(chunk: Chunk) -> str:
        """Serializa um Chunk para string JSON. Vetores float32 são preservados."""
        ...

    @staticmethod
    def deserialize_chunk(data: str | dict) -> Chunk:
        """Desserializa JSON para um Chunk.

        Raises:
            DeserializationError: Se o JSON for inválido ou campos obrigatórios
                estiverem ausentes.
        """
        ...
```

---

## Data Models

Todos os modelos são definidos em `tokemize/models/` como `dataclass` Python com type hints completos.

```python
# tokemize/models/artifact.py
from dataclasses import dataclass

@dataclass
class Artifact:
    """Unidade estrutural extraída do código-fonte pelo Parser.

    Attributes:
        name: Nome do artefato (ex: nome da função ou classe).
        type: Tipo do artefato: "function", "class", "method", "import".
        start_line: Número da linha inicial (1-indexed).
        end_line: Número da linha final (1-indexed).
        language: Linguagem de programação (ex: "python", "java").
        content: Conteúdo textual original do artefato, sem modificações.
    """
    name: str
    type: str
    start_line: int
    end_line: int
    language: str
    content: str
```

```python
# tokemize/models/chunk.py
from __future__ import annotations
from dataclasses import dataclass, field
from tokemize.models.artifact import Artifact

@dataclass
class Chunk:
    """Artefato enriquecido com metadados de indexação.

    Attributes:
        id: Identificador único do chunk (UUID ou hash do conteúdo).
        artifact: Artifact de origem.
        token_count: Número de tokens do conteúdo para o modelo LLM configurado.
        embedding: Vetor de embedding float32. None antes da indexação.
    """
    id: str
    artifact: Artifact
    token_count: int
    embedding: list[float] | None = field(default=None)
```

```python
# tokemize/models/context.py
from dataclasses import dataclass
from tokemize.models.chunk import Chunk

@dataclass
class OptimizedContext:
    """Contexto otimizado pronto para envio ao LLM.

    Invariante: total_tokens == sum(c.token_count for c in chunks)

    Attributes:
        chunks: Lista de chunks selecionados pelo Selector.
        total_tokens: Soma dos token_count de todos os chunks.
        formatted_text: Representação textual estruturada dos chunks.
    """
    chunks: list[Chunk]
    total_tokens: int
    formatted_text: str
```

```python
# tokemize/models/llm_response.py
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """Resposta recebida do provedor LLM.

    Attributes:
        text: Texto da resposta gerada pelo modelo.
        input_tokens: Tokens consumidos no prompt (contexto + requisição).
        output_tokens: Tokens gerados na resposta.
        model: Identificador do modelo usado.
        provider: Nome do provedor ("openai" ou "anthropic").
    """
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str
```

```python
# tokemize/models/metrics.py
from dataclasses import dataclass

@dataclass
class PipelineMetrics:
    """Métricas de execução do pipeline de otimização.

    Attributes:
        artifacts_extracted: Total de artefatos extraídos pelo Parser.
        chunks_indexed: Total de chunks adicionados ao índice FAISS.
        chunks_selected: Total de chunks selecionados pelo Selector.
        total_context_tokens: Total de tokens no contexto final.
        elapsed_seconds: Tempo total de execução do pipeline em segundos.
    """
    artifacts_extracted: int
    chunks_indexed: int
    chunks_selected: int
    total_context_tokens: int
    elapsed_seconds: float
```

### Invariantes dos Modelos

- `OptimizedContext.total_tokens == sum(c.token_count for c in chunks)` — consistência de contagem de tokens.
- `Chunk.token_count >= 0` — contagem de tokens nunca negativa.
- `Artifact.start_line <= Artifact.end_line` — localização válida no arquivo.
- `Chunk.embedding` é `None` antes da chamada a `EmbeddingsClient.embed_chunks()` e uma lista de floats depois.

---


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

As propriedades abaixo foram derivadas das acceptance criteria dos requisitos. Para cada critério, foi avaliado se ele é testável como propriedade universal (PBT), exemplo específico, edge case ou smoke test. Apenas os critérios com comportamento que varia significativamente com a entrada e que testam a lógica do próprio sistema foram convertidos em propriedades.

---

### Property 1: Artefatos extraídos possuem todos os metadados obrigatórios

*For any* arquivo de código-fonte válido em uma linguagem suportada, todos os artefatos retornados pelo Parser devem ter: `name` não vazio, `type` pertencente ao conjunto `{"function", "class", "method", "import"}`, `start_line >= 1`, `end_line >= start_line`, `language` igual à linguagem detectada, e `content` não vazio.

**Validates: Requirements 1.1, 1.3**

---

### Property 2: Conteúdo dos artefatos preserva o texto original

*For any* arquivo de código-fonte válido, para cada `Artifact` retornado pelo Parser, o campo `artifact.content` deve ser idêntico ao trecho correspondente do arquivo original (do byte da linha `start_line` ao byte da linha `end_line`), sem modificações.

**Validates: Requirements 1.7**

---

### Property 3: Linguagem não suportada sempre levanta UnsupportedLanguageError

*For any* caminho de arquivo cuja extensão não esteja em `SUPPORTED_LANGUAGES`, a chamada a `parse()` deve levantar `UnsupportedLanguageError` com uma mensagem descritiva contendo a extensão não suportada.

**Validates: Requirements 1.5**

---

### Property 4: Embeddings preservam identidade e completude dos chunks

*For any* lista de N chunks fornecida a `embed_chunks()`, a lista retornada deve ter exatamente N elementos, cada elemento deve ter o mesmo `id` do chunk de entrada correspondente, e o campo `embedding` de cada chunk deve ser uma lista de floats com dimensão igual à dimensão do modelo configurado (não `None`).

**Validates: Requirements 2.1, 2.2**

---

### Property 5: Batching respeita o tamanho máximo configurado

*For any* lista de N chunks e qualquer `batch_size` B > 0, o número de chamadas à API de embeddings deve ser exatamente `ceil(N / B)`. Nenhum lote deve conter mais de B itens.

**Validates: Requirements 2.4**

---

### Property 6: Round-trip de indexação preserva metadados dos chunks

*For any* `Chunk` com embedding não nulo adicionado ao `FAISSIndexer`, uma busca com o vetor exato do embedding desse chunk (`search(chunk.embedding, top_k=1)`) deve retornar esse mesmo chunk com todos os campos de `Artifact` intactos: `name`, `type`, `start_line`, `end_line`, `language`, `content`.

**Validates: Requirements 3.1, 3.7**

---

### Property 7: Adição incremental é equivalente à adição em lote

*For any* dois conjuntos disjuntos de chunks A e B, adicionar A ao índice e depois adicionar B deve produzir um índice com os mesmos resultados de busca que adicionar A ∪ B de uma só vez. A ordem de adição não deve afetar a recuperabilidade dos chunks.

**Validates: Requirements 3.6**

---

### Property 8: Persistência e recarga do índice preservam os chunks

*For any* conjunto de chunks indexados, após `save()` e recriação de uma nova instância de `FAISSIndexer` seguida de `load()`, todos os chunks originais devem ser recuperáveis por busca com seus vetores exatos.

**Validates: Requirements 3.3**

---

### Property 9: Chunks selecionados respeitam o limiar de relevância

*For any* conjunto de candidatos `(chunk, score)` retornados pelo FAISS e qualquer `relevance_threshold` T ∈ [0.0, 1.0], nenhum chunk com `score < T` deve aparecer no `OptimizedContext` retornado pelo Selector.

**Validates: Requirements 4.3**

---

### Property 10: Invariante de budget de tokens

*For any* conjunto de chunks candidatos com `token_count` variados e qualquer `token_budget` B > 0, o `OptimizedContext.total_tokens` retornado pelo Selector deve ser sempre menor ou igual a B.

**Validates: Requirements 4.4, 4.8**

---

### Property 11: Desempate por menor número de tokens

*For any* dois chunks com scores de relevância iguais mas `token_count` diferentes, o chunk com menor `token_count` deve aparecer antes na lista de chunks do `OptimizedContext`.

**Validates: Requirements 4.7**

---

### Property 12: Contexto formatado contém todos os campos dos chunks selecionados

*For any* lista de chunks selecionados, o `formatted_text` do `OptimizedContext` deve conter o `artifact.name`, o `artifact.language` e o `artifact.content` de cada chunk. Nenhum chunk selecionado pode estar ausente do texto formatado.

**Validates: Requirements 5.2**

---

### Property 13: Erros em qualquer etapa do pipeline levantam PipelineError com o nome da etapa

*For any* etapa do pipeline (parser, embeddings, indexer, selector) que levante uma exceção, o `PipelineOptimizer.optimize()` deve levantar `PipelineError` com uma mensagem que inclua o nome da etapa que falhou.

**Validates: Requirements 5.4**

---

### Property 14: LLMResponse contém todos os campos de uso de tokens

*For any* resposta da API do provedor LLM (mockada) com valores variados de `input_tokens`, `output_tokens` e `text`, o `LLMResponse` retornado deve ter todos os campos preenchidos: `text`, `input_tokens`, `output_tokens`, `model`, `provider`.

**Validates: Requirements 6.4**

---

### Property 15: Parâmetros opcionais do OpenAI são repassados à API

*For any* combinação válida de `temperature` ∈ [0.0, 2.0], `max_tokens` > 0 e `system_prompt` (string ou None), a chamada à API OpenAI deve incluir exatamente esses valores nos parâmetros da requisição.

**Validates: Requirements 6.8**

---

### Property 16: Variáveis obrigatórias ausentes levantam MissingConfigError com o nome da variável

*For any* subconjunto das variáveis obrigatórias (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `EMBEDDING_MODEL`, `LLM_PROVIDER`, `LLM_MODEL`) que esteja ausente do ambiente, `load_config()` deve levantar `MissingConfigError` com uma mensagem que inclua o nome exato da variável ausente.

**Validates: Requirements 7.2, 7.4**

---

### Property 17: Valores inválidos de configuração levantam InvalidConfigError com nome e valor

*For any* valor de `TOKEN_BUDGET` que seja ≤ 0 ou não inteiro, ou qualquer valor de `RELEVANCE_THRESHOLD` fora do intervalo [0.0, 1.0], `load_config()` deve levantar `InvalidConfigError` com uma mensagem que inclua o nome da variável e o valor inválido recebido.

**Validates: Requirements 7.5, 7.6, 7.7**

---

### Property 18: Invariante de consistência de total_tokens em OptimizedContext

*For any* lista de chunks com `token_count` variados, o `OptimizedContext.total_tokens` deve ser sempre igual à soma de `c.token_count` para todos os chunks em `OptimizedContext.chunks`.

**Validates: Requirements 8.7**

---

### Property 19: Logs de erro nunca expõem valores de chaves de API

*For any* execução do pipeline com chaves de API conhecidas configuradas nas variáveis de ambiente, nenhuma saída de log em nenhum nível (`DEBUG`, `INFO`, `WARNING`, `ERROR`) deve conter o valor literal de `OPENAI_API_KEY` ou `ANTHROPIC_API_KEY`.

**Validates: Requirements 9.5**

---

### Property 20: Round-trip de serialização de Artifact

*For any* instância válida de `Artifact`, `deserialize_artifact(serialize_artifact(artifact))` deve produzir um objeto com todos os campos iguais ao original: `name`, `type`, `start_line`, `end_line`, `language`, `content`.

**Validates: Requirements 10.1, 10.2, 10.4**

---

### Property 21: Round-trip de serialização de Chunk preserva embedding com precisão float32

*For any* instância válida de `Chunk` com `embedding` não nulo, `deserialize_chunk(serialize_chunk(chunk))` deve produzir um objeto com todos os campos iguais ao original, e cada valor do vetor `embedding` deve ser igual ao original dentro da precisão de ponto flutuante de 32 bits (diferença absoluta ≤ `numpy.finfo(numpy.float32).eps`).

**Validates: Requirements 10.5**

---

### Property 22: Desserialização de JSON inválido levanta DeserializationError com campos ausentes

*For any* string JSON que esteja faltando um ou mais campos obrigatórios de `Artifact` ou `Chunk`, `deserialize_artifact()` ou `deserialize_chunk()` deve levantar `DeserializationError` com uma mensagem que liste os campos ausentes ou inválidos.

**Validates: Requirements 10.3**

---

## Error Handling

### Estratégia Geral

O sistema adota uma estratégia de **fail-fast com propagação descritiva**: erros são detectados o mais cedo possível, logados com contexto completo (camada, mensagem, stack trace) e propagados como exceções tipadas que permitem ao chamador distinguir o tipo de falha.

### Hierarquia de Exceções

```
TokemizeError (base)
├── PipelineError          # Falha em qualquer etapa do pipeline (inclui nome da etapa)
├── UnsupportedLanguageError  # Extensão de arquivo não suportada pelo Parser
├── ParseError             # Falha interna do Tree-sitter
├── EmbeddingAPIError      # Falha na API de embeddings após retentativas
├── EmptyIndexError        # Busca em índice FAISS vazio
├── IndexDimensionError    # Dimensão do vetor incompatível com o índice
├── DeserializationError   # JSON inválido ou campos ausentes
├── MissingConfigError     # Variável de ambiente obrigatória ausente
├── InvalidConfigError     # Valor de configuração inválido
├── LLMAuthError           # HTTP 401 do provedor LLM
├── LLMRateLimitError      # HTTP 429 após esgotamento de retentativas
└── LLMAPIError            # Outros erros da API do provedor LLM
```

### Políticas de Retry

| Componente | Condição | Política |
|---|---|---|
| `EmbeddingsClient` | Qualquer erro da API | 3 tentativas, backoff exponencial (1s, 2s, 4s) |
| `LLMClient` | HTTP 429 (rate limit) | Aguarda `Retry-After` header, 1 retentativa |
| `LLMClient` | HTTP 401 (auth) | Falha imediata, sem retentativas |
| `FAISSIndexer` | Índice corrompido | Cria novo índice vazio, loga WARNING |
| `CodeParser` | Erro de sintaxe parcial | Retorna artefatos válidos, loga WARNING |

### Tratamento por Camada

**Parser:**
- Arquivo não encontrado → `FileNotFoundError` (nativo Python)
- Extensão não suportada → `UnsupportedLanguageError` com a extensão recebida
- Erro de sintaxe parcial → retorna artefatos válidos + loga `WARNING` com localização do erro

**EmbeddingsClient:**
- Falha da API após 3 tentativas → `EmbeddingAPIError` com detalhes da última falha
- Chunk sem embedding passado para indexação → `ValueError` descritivo

**FAISSIndexer:**
- Índice corrompido → loga `WARNING`, cria índice vazio, continua
- Busca em índice vazio → `EmptyIndexError`
- Dimensão incompatível → `IndexDimensionError`

**ContextSelector:**
- Nenhum chunk acima do limiar → retorna `OptimizedContext` vazio + loga `WARNING`
- Chunks descartados por budget → loga `DEBUG` com contagem

**PipelineOptimizer:**
- Qualquer exceção de qualquer etapa → captura, loga `ERROR` com nome da etapa e stack trace, relança como `PipelineError(stage="nome_da_etapa", cause=original_exception)`

**LLMClient:**
- HTTP 401 → `LLMAuthError` imediato
- HTTP 429 → aguarda `Retry-After`, retenta uma vez; se falhar novamente → `LLMRateLimitError`
- Outros erros HTTP → `LLMAPIError`

**Config:**
- Variável obrigatória ausente → `MissingConfigError("Missing required env var: NOME_VAR")`
- Valor inválido → `InvalidConfigError("Invalid value for NOME_VAR: 'valor_recebido'")`

### Segurança nos Logs

O sistema implementa um `logging.Filter` customizado (`SensitiveDataFilter`) que é aplicado a todos os handlers do logger raiz. O filtro verifica se o valor de qualquer chave de API conhecida aparece na mensagem de log e, se sim, substitui pelo placeholder `[REDACTED]`.

---

## Testing Strategy

### Abordagem Dual

O Tokemize adota uma abordagem de testes em duas camadas complementares:

1. **Testes unitários** — verificam comportamentos específicos, edge cases e condições de erro com exemplos concretos.
2. **Testes de propriedade (PBT)** — verificam propriedades universais que devem valer para qualquer entrada válida, usando geração aleatória de dados.

### Biblioteca de PBT

**[Hypothesis](https://hypothesis.readthedocs.io/)** — biblioteca de property-based testing para Python. Integra-se nativamente com pytest e suporta geração de strings, listas, dataclasses e tipos customizados via `@given` e `st.*` strategies.

```bash
pip install hypothesis
```

### Configuração dos Testes de Propriedade

Cada teste de propriedade deve:
- Usar o decorator `@given` do Hypothesis com strategies apropriadas
- Executar no mínimo **100 iterações** (configurado via `settings(max_examples=100)`)
- Incluir um comentário de tag no formato:
  ```python
  # Feature: tokemize-context-optimizer, Property N: <texto da propriedade>
  ```

Exemplo de estrutura:

```python
from hypothesis import given, settings
import hypothesis.strategies as st

# Feature: tokemize-context-optimizer, Property 20: Round-trip de serialização de Artifact
@given(st.builds(Artifact, ...))
@settings(max_examples=100)
def test_artifact_serialization_round_trip(artifact: Artifact) -> None:
    result = ArtifactSerializer.deserialize_artifact(
        ArtifactSerializer.serialize_artifact(artifact)
    )
    assert result == artifact
```

### Mapeamento de Propriedades para Testes

| Propriedade | Arquivo de Teste | Strategy Principal |
|---|---|---|
| P1 — Metadados de artefatos | `test_code_parser.py` | `st.sampled_from(valid_source_files)` |
| P2 — Conteúdo preservado | `test_code_parser.py` | `st.sampled_from(valid_source_files)` |
| P3 — Linguagem não suportada | `test_code_parser.py` | `st.text()` filtrado por extensões inválidas |
| P4 — Embeddings completos | `test_embeddings_client.py` | `st.lists(st.builds(Chunk, ...), min_size=1)` |
| P5 — Batching correto | `test_embeddings_client.py` | `st.integers(min_value=1)` para N e B |
| P6 — Round-trip de indexação | `test_faiss_indexer.py` | `st.lists(st.builds(Chunk, ...), min_size=1)` |
| P7 — Adição incremental | `test_faiss_indexer.py` | `st.lists(...)` particionados em A e B |
| P8 — Persistência e recarga | `test_faiss_indexer.py` | `st.lists(st.builds(Chunk, ...), min_size=1)` |
| P9 — Limiar de relevância | `test_context_selector.py` | `st.floats(0.0, 1.0)` para threshold |
| P10 — Budget de tokens | `test_context_selector.py` | `st.integers(min_value=1)` para budget |
| P11 — Desempate por tokens | `test_context_selector.py` | `st.builds(Chunk, ...)` com scores iguais |
| P12 — Contexto formatado | `test_pipeline_optimizer.py` | `st.lists(st.builds(Chunk, ...), min_size=1)` |
| P13 — PipelineError com etapa | `test_pipeline_optimizer.py` | `st.sampled_from(pipeline_stages)` |
| P14 — LLMResponse completo | `test_llm_clients.py` | `st.builds(MockAPIResponse, ...)` |
| P15 — Parâmetros OpenAI | `test_openai_client.py` | `st.floats(0.0, 2.0)`, `st.integers(min_value=1)` |
| P16 — MissingConfigError | `test_config_loader.py` | `st.sampled_from(REQUIRED_VARS)` |
| P17 — InvalidConfigError | `test_config_loader.py` | `st.integers(max_value=0)`, `st.floats()` fora de [0,1] |
| P18 — Invariante total_tokens | `test_models.py` | `st.lists(st.builds(Chunk, ...), min_size=0)` |
| P19 — Logs sem API keys | `test_logging.py` | `st.text()` para requests e file contents |
| P20 — Round-trip Artifact | `test_serializer.py` | `st.builds(Artifact, ...)` |
| P21 — Round-trip Chunk float32 | `test_serializer.py` | `st.builds(Chunk, ...)` com embeddings |
| P22 — DeserializationError | `test_serializer.py` | `st.fixed_dictionaries({})` com campos removidos |

### Testes Unitários (Exemplos e Edge Cases)

Além dos testes de propriedade, os seguintes testes unitários devem ser implementados:

| Cenário | Arquivo | Tipo |
|---|---|---|
| Parser com erro de sintaxe parcial | `test_code_parser.py` | EDGE_CASE |
| Suporte às 4 linguagens | `test_code_parser.py` | SMOKE |
| Retry com backoff na API de embeddings | `test_embeddings_client.py` | EXAMPLE |
| Índice corrompido cria novo índice | `test_faiss_indexer.py` | EDGE_CASE |
| Selector retorna lista vazia quando nenhum chunk atinge o limiar | `test_context_selector.py` | EDGE_CASE |
| Optimizer reutiliza índice persistido | `test_pipeline_optimizer.py` | EXAMPLE |
| Optimizer loga métricas ao início e fim | `test_pipeline_optimizer.py` | EXAMPLE |
| OpenAI client roteia para endpoint correto | `test_openai_client.py` | EXAMPLE |
| Anthropic client roteia para endpoint correto | `test_anthropic_client.py` | EXAMPLE |
| HTTP 401 levanta LLMAuthError sem retry | `test_llm_clients.py` | EDGE_CASE |
| HTTP 429 aguarda Retry-After e retenta | `test_llm_clients.py` | EDGE_CASE |
| Config com apenas variáveis obrigatórias usa defaults | `test_config_loader.py` | EXAMPLE |
| Chunk criado com embedding=None | `test_models.py` | EDGE_CASE |
| Selector loga DEBUG ao descartar chunks | `test_context_selector.py` | EXAMPLE |

### Estrutura de Diretórios de Testes

```
tokemize/tests/
├── conftest.py                    # Fixtures compartilhadas (config, mocks)
├── test_code_parser.py            # Parser (P1, P2, P3)
├── test_embeddings_client.py      # EmbeddingsClient (P4, P5)
├── test_faiss_indexer.py          # FAISSIndexer (P6, P7, P8)
├── test_context_selector.py       # ContextSelector (P9, P10, P11)
├── test_pipeline_optimizer.py     # PipelineOptimizer (P12, P13)
├── test_openai_client.py          # OpenAIClient (P15)
├── test_anthropic_client.py       # AnthropicClient
├── test_llm_clients.py            # BaseLLMClient (P14)
├── test_config_loader.py          # Config (P16, P17)
├── test_models.py                 # Models (P18)
├── test_serializer.py             # ArtifactSerializer (P20, P21, P22)
└── test_logging.py                # Logging (P19)
```

### Cobertura Mínima Esperada

- Cobertura de linhas: ≥ 85% em todos os módulos de `core/` e `integrations/`
- Todos os 22 testes de propriedade devem passar com `max_examples=100`
- Todos os testes de smoke devem passar antes de qualquer PR ser mergeado
