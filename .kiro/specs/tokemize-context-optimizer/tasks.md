# Implementation Plan: Tokemize Context Optimizer

## Overview

Este plano de implementação detalha as tarefas necessárias para construir o Tokemize — um agente inteligente de otimização de contexto para LLMs. O sistema é composto por quatro camadas principais (Parser → Indexer → Selector → Optimizer) que trabalham em conjunto para reduzir o custo de tokens e aumentar a precisão das respostas de LLMs.

A implementação seguirá uma abordagem incremental, começando pelos modelos de dados e componentes de infraestrutura, depois construindo cada camada do pipeline, e finalmente integrando tudo com testes de propriedade (Hypothesis) e testes unitários.

**Linguagem:** Python 3.11+  
**Stack:** Tree-sitter, FAISS, OpenAI API, Anthropic API, Hypothesis, pytest

---

## Tasks

- [ ] 1. Setup inicial do projeto
  - Criar estrutura de diretórios conforme especificação
  - Configurar Poetry ou requirements.txt com dependências
  - Configurar pytest e Hypothesis
  - Criar arquivo `.env.example` com variáveis de ambiente necessárias
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 2. Implementar modelos de dados (dataclasses)
  - [ ] 2.1 Criar `tokemize/models/artifact.py` com dataclass `Artifact`
    - Implementar campos: name, type, start_line, end_line, language, content
    - Adicionar validação de invariante: start_line <= end_line
    - _Requirements: 8.1_
  
  - [ ] 2.2 Criar `tokemize/models/chunk.py` com dataclass `Chunk`
    - Implementar campos: id, artifact, token_count, embedding
    - Suportar embedding=None para chunks não indexados
    - _Requirements: 8.2, 8.6_
  
  - [ ] 2.3 Criar `tokemize/models/context.py` com dataclass `OptimizedContext`
    - Implementar campos: chunks, total_tokens, formatted_text
    - Adicionar validação de invariante: total_tokens == sum(c.token_count for c in chunks)
    - _Requirements: 8.3, 8.7_
  
  - [ ] 2.4 Criar `tokemize/models/llm_response.py` com dataclass `LLMResponse`
    - Implementar campos: text, input_tokens, output_tokens, model, provider
    - _Requirements: 8.4_
  
  - [ ] 2.5 Criar `tokemize/models/metrics.py` com dataclass `PipelineMetrics`
    - Implementar campos: artifacts_extracted, chunks_indexed, chunks_selected, total_context_tokens, elapsed_seconds
    - _Requirements: 8.5_

- [ ] 3. Implementar serialização de artefatos
  - [ ] 3.1 Criar `tokemize/models/serializer.py` com classe `ArtifactSerializer`
    - Implementar `serialize_artifact()` e `deserialize_artifact()`
    - Implementar `serialize_chunk()` e `deserialize_chunk()`
    - Preservar precisão float32 para embeddings
    - _Requirements: 10.1, 10.2, 10.5_
  
  - [ ]* 3.2 Escrever teste de propriedade para serialização de Artifact
    - **Property 20: Round-trip de serialização de Artifact**
    - **Valida: Requirements 10.1, 10.2, 10.4**
  
  - [ ]* 3.3 Escrever teste de propriedade para serialização de Chunk
    - **Property 21: Round-trip de serialização de Chunk preserva embedding com precisão float32**
    - **Valida: Requirements 10.5**
  
  - [ ]* 3.4 Escrever teste de propriedade para desserialização de JSON inválido
    - **Property 22: Desserialização de JSON inválido levanta DeserializationError com campos ausentes**
    - **Valida: Requirements 10.3**

- [ ] 4. Implementar configuração e carregamento de variáveis de ambiente
  - [ ] 4.1 Criar `tokemize/config/config_loader.py` com dataclass `TokemizeConfig`
    - Implementar função `load_config()` usando python-dotenv
    - Carregar variáveis obrigatórias: OPENAI_API_KEY, ANTHROPIC_API_KEY, EMBEDDING_MODEL, LLM_PROVIDER, LLM_MODEL
    - Carregar variáveis opcionais com defaults: TOKEN_BUDGET (4096), RELEVANCE_THRESHOLD (0.75), FAISS_INDEX_PATH, EMBEDDING_BATCH_SIZE (100), LOG_LEVEL (INFO)
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [ ] 4.2 Adicionar validação de configuração
    - Validar TOKEN_BUDGET > 0 e inteiro
    - Validar RELEVANCE_THRESHOLD ∈ [0.0, 1.0]
    - Levantar MissingConfigError para variáveis obrigatórias ausentes
    - Levantar InvalidConfigError para valores inválidos
    - _Requirements: 7.4, 7.5, 7.6, 7.7_
  
  - [ ]* 4.3 Escrever teste de propriedade para variáveis obrigatórias ausentes
    - **Property 16: Variáveis obrigatórias ausentes levantam MissingConfigError com o nome da variável**
    - **Valida: Requirements 7.2, 7.4**
  
  - [ ]* 4.4 Escrever teste de propriedade para valores inválidos de configuração
    - **Property 17: Valores inválidos de configuração levantam InvalidConfigError com nome e valor**
    - **Valida: Requirements 7.5, 7.6, 7.7**
  
  - [ ]* 4.5 Escrever teste unitário para config com apenas variáveis obrigatórias
    - Verificar que defaults são aplicados corretamente

- [ ] 5. Checkpoint - Verificar modelos e configuração
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implementar Parser com Tree-sitter
  - [ ] 6.1 Criar `tokemize/core/parser/code_parser.py` com classe `CodeParser`
    - Implementar `__init__()` com language_map (SUPPORTED_LANGUAGES)
    - Implementar `_detect_language()` para detectar linguagem por extensão
    - Suportar Python, Java, JavaScript, TypeScript
    - _Requirements: 1.2, 1.6_
  
  - [ ] 6.2 Implementar método `parse()` para análise de arquivo único
    - Carregar arquivo e detectar linguagem
    - Usar Tree-sitter para gerar AST
    - Extrair artefatos: funções, classes, métodos, imports
    - Associar metadados: name, type, start_line, end_line, language, content
    - Preservar conteúdo textual original sem modificações
    - _Requirements: 1.1, 1.3, 1.7_
  
  - [ ] 6.3 Implementar tratamento de erros no Parser
    - Levantar UnsupportedLanguageError para extensões não suportadas
    - Retornar artefatos válidos em caso de erro de sintaxe parcial
    - Logar WARNING com localização do erro de sintaxe
    - _Requirements: 1.4, 1.5_
  
  - [ ] 6.4 Implementar método `parse_many()` para múltiplos arquivos
    - Concatenar artefatos de todos os arquivos
  
  - [ ]* 6.5 Escrever teste de propriedade para metadados de artefatos
    - **Property 1: Artefatos extraídos possuem todos os metadados obrigatórios**
    - **Valida: Requirements 1.1, 1.3**
  
  - [ ]* 6.6 Escrever teste de propriedade para preservação de conteúdo
    - **Property 2: Conteúdo dos artefatos preserva o texto original**
    - **Valida: Requirements 1.7**
  
  - [ ]* 6.7 Escrever teste de propriedade para linguagem não suportada
    - **Property 3: Linguagem não suportada sempre levanta UnsupportedLanguageError**
    - **Valida: Requirements 1.5**
  
  - [ ]* 6.8 Escrever testes unitários para Parser
    - Teste de smoke para as 4 linguagens suportadas
    - Teste de edge case para erro de sintaxe parcial

- [ ] 7. Implementar EmbeddingsClient
  - [ ] 7.1 Criar `tokemize/integrations/embeddings/embeddings_client.py` com classe `EmbeddingsClient`
    - Implementar `__init__()` com api_key, model, batch_size
    - Ler OPENAI_API_KEY de variável de ambiente se não fornecida
    - _Requirements: 2.1_
  
  - [ ] 7.2 Implementar método `embed_text()` para embedding de texto único
    - Chamar API OpenAI text-embedding
    - Retornar vetor de embedding como list[float]
    - _Requirements: 2.1_
  
  - [ ] 7.3 Implementar método `embed_chunks()` para lote de chunks
    - Processar em lotes de até batch_size itens
    - Associar embedding ao chunk correspondente
    - Retornar lista de chunks com embedding preenchido
    - _Requirements: 2.1, 2.2, 2.4_
  
  - [ ] 7.4 Implementar retry com backoff exponencial
    - Realizar até 3 tentativas em caso de erro da API
    - Backoff: 1s, 2s, 4s
    - Levantar EmbeddingAPIError após esgotamento
    - _Requirements: 2.3_
  
  - [ ]* 7.5 Escrever teste de propriedade para embeddings completos
    - **Property 4: Embeddings preservam identidade e completude dos chunks**
    - **Valida: Requirements 2.1, 2.2**
  
  - [ ]* 7.6 Escrever teste de propriedade para batching
    - **Property 5: Batching respeita o tamanho máximo configurado**
    - **Valida: Requirements 2.4**
  
  - [ ]* 7.7 Escrever teste unitário para retry com backoff
    - Mockar API com falhas e verificar tentativas

- [ ] 8. Implementar FAISSIndexer
  - [ ] 8.1 Criar `tokemize/core/indexer/faiss_indexer.py` com classe `FAISSIndexer`
    - Implementar `__init__()` com index_path e dimension (default 1536)
    - Inicializar índice FAISS vazio
    - Criar estrutura de metadados (mapeamento int → Chunk)
    - _Requirements: 3.1_
  
  - [ ] 8.2 Implementar método `add()` para adicionar chunks ao índice
    - Validar que chunks têm embedding não nulo
    - Validar dimensão dos vetores
    - Adicionar vetores ao índice FAISS
    - Atualizar mapeamento de metadados
    - Suportar adição incremental
    - _Requirements: 3.1, 3.6_
  
  - [ ] 8.3 Implementar método `search()` para busca por similaridade
    - Buscar top_k chunks mais similares ao query_vector
    - Retornar lista de tuplas (Chunk, score) ordenadas por score decrescente
    - Levantar EmptyIndexError se índice vazio
    - _Requirements: 3.1_
  
  - [ ] 8.4 Implementar persistência do índice
    - Implementar `save()` para persistir index.faiss e metadata.json
    - Implementar `load()` para carregar índice do disco
    - Implementar `_verify_integrity()` para verificar consistência
    - Criar novo índice vazio se arquivo corrompido (logar WARNING)
    - _Requirements: 3.2, 3.3, 3.4, 3.5_
  
  - [ ]* 8.5 Escrever teste de propriedade para round-trip de indexação
    - **Property 6: Round-trip de indexação preserva metadados dos chunks**
    - **Valida: Requirements 3.1, 3.7**
  
  - [ ]* 8.6 Escrever teste de propriedade para adição incremental
    - **Property 7: Adição incremental é equivalente à adição em lote**
    - **Valida: Requirements 3.6**
  
  - [ ]* 8.7 Escrever teste de propriedade para persistência e recarga
    - **Property 8: Persistência e recarga do índice preservam os chunks**
    - **Valida: Requirements 3.3**
  
  - [ ]* 8.8 Escrever teste unitário para índice corrompido
    - Verificar que cria novo índice vazio e loga WARNING

- [ ] 9. Checkpoint - Verificar Parser, Embeddings e Indexer
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implementar ContextSelector
  - [ ] 10.1 Criar `tokemize/core/selector/context_selector.py` com classe `ContextSelector`
    - Implementar `__init__()` com indexer, embeddings_client, relevance_threshold, top_k
    - _Requirements: 4.1_
  
  - [ ] 10.2 Implementar método `select()` para seleção de contexto
    - Gerar embedding da requisição usando embeddings_client
    - Buscar top_k candidatos no FAISS
    - Filtrar por relevance_threshold
    - Ordenar por score decrescente
    - Desempatar por menor token_count
    - Acumular chunks até atingir token_budget
    - Retornar OptimizedContext
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7_
  
  - [ ] 10.3 Implementar tratamento de casos especiais
    - Retornar OptimizedContext vazio se nenhum chunk atinge o limiar (logar WARNING)
    - Logar DEBUG ao descartar chunks por exceder budget
    - _Requirements: 4.6_
  
  - [ ]* 10.4 Escrever teste de propriedade para limiar de relevância
    - **Property 9: Chunks selecionados respeitam o limiar de relevância**
    - **Valida: Requirements 4.3**
  
  - [ ]* 10.5 Escrever teste de propriedade para invariante de budget
    - **Property 10: Invariante de budget de tokens**
    - **Valida: Requirements 4.4, 4.8**
  
  - [ ]* 10.6 Escrever teste de propriedade para desempate por tokens
    - **Property 11: Desempate por menor número de tokens**
    - **Valida: Requirements 4.7**
  
  - [ ]* 10.7 Escrever teste unitário para lista vazia quando nenhum chunk atinge limiar
    - Verificar que retorna OptimizedContext vazio e loga WARNING
  
  - [ ]* 10.8 Escrever teste unitário para log DEBUG ao descartar chunks

- [ ] 11. Implementar PipelineOptimizer
  - [ ] 11.1 Criar `tokemize/core/optimizer/pipeline_optimizer.py` com classe `PipelineOptimizer`
    - Implementar `__init__()` com parser, indexer, selector, embeddings_client, llm_model
    - _Requirements: 5.5_
  
  - [ ] 11.2 Implementar método auxiliar `_artifacts_to_chunks()`
    - Converter lista de Artifact em lista de Chunk
    - Calcular token_count usando tokenizador do modelo LLM configurado
    - Gerar UUID ou hash para chunk.id
    - _Requirements: 5.1_
  
  - [ ] 11.3 Implementar método auxiliar `_format_context()`
    - Formatar chunks selecionados em bloco de texto estruturado
    - Formato: ### [language] — artifact_name + bloco de código
    - _Requirements: 5.2_
  
  - [ ] 11.4 Implementar método `optimize()` para orquestração do pipeline
    - Logar INFO no início da execução
    - Executar Parser.parse_many(files) → list[Artifact]
    - Converter Artifacts em Chunks com token_count
    - Gerar embeddings com EmbeddingsClient.embed_chunks()
    - Adicionar chunks ao Indexer e persistir
    - Reutilizar índice persistido se arquivos já indexados
    - Executar Selector.select(request, budget) → OptimizedContext
    - Logar INFO no fim com PipelineMetrics
    - _Requirements: 5.1, 5.3, 5.6_
  
  - [ ] 11.5 Implementar tratamento de erros do pipeline
    - Capturar exceções de qualquer etapa
    - Logar ERROR com nome da etapa e stack trace
    - Levantar PipelineError com nome da etapa e causa original
    - _Requirements: 5.4_
  
  - [ ]* 11.6 Escrever teste de propriedade para contexto formatado
    - **Property 12: Contexto formatado contém todos os campos dos chunks selecionados**
    - **Valida: Requirements 5.2**
  
  - [ ]* 11.7 Escrever teste de propriedade para PipelineError
    - **Property 13: Erros em qualquer etapa do pipeline levantam PipelineError com o nome da etapa**
    - **Valida: Requirements 5.4**
  
  - [ ]* 11.8 Escrever teste unitário para reutilização de índice persistido
    - Verificar que não reindexar arquivos já indexados
  
  - [ ]* 11.9 Escrever teste unitário para logging de métricas
    - Verificar logs INFO no início e fim com PipelineMetrics

- [ ] 12. Checkpoint - Verificar pipeline completo
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implementar interface base de LLMClient
  - [ ] 13.1 Criar `tokemize/integrations/llm/base_client.py` com classe abstrata `BaseLLMClient`
    - Definir método abstrato `complete()` com parâmetros: context, request, model, temperature, max_tokens, system_prompt
    - _Requirements: 6.1_
  
  - [ ] 13.2 Definir exceções customizadas para LLM
    - Criar LLMAuthError (HTTP 401, sem retry)
    - Criar LLMRateLimitError (HTTP 429, após esgotamento de retry)
    - Criar LLMAPIError (outros erros)
    - _Requirements: 6.5, 6.6_

- [ ] 14. Implementar OpenAIClient
  - [ ] 14.1 Criar `tokemize/integrations/llm/openai_client.py` com classe `OpenAIClient`
    - Herdar de BaseLLMClient
    - Implementar `__init__()` com api_key (ler de OPENAI_API_KEY)
    - _Requirements: 6.2, 6.7_
  
  - [ ] 14.2 Implementar método `complete()` para OpenAI
    - Enviar requisição para API OpenAI Chat Completions
    - Suportar modelos: gpt-4o, gpt-4-turbo
    - Suportar parâmetros opcionais: temperature, max_tokens, system_prompt
    - Retornar LLMResponse com text, input_tokens, output_tokens, model, provider
    - _Requirements: 6.2, 6.4, 6.8_
  
  - [ ] 14.3 Implementar tratamento de erros para OpenAI
    - HTTP 401 → LLMAuthError imediato
    - HTTP 429 → aguardar Retry-After, retentar uma vez, depois LLMRateLimitError
    - Outros erros → LLMAPIError
    - _Requirements: 6.5, 6.6_
  
  - [ ]* 14.4 Escrever teste de propriedade para parâmetros OpenAI
    - **Property 15: Parâmetros opcionais do OpenAI são repassados à API**
    - **Valida: Requirements 6.8**
  
  - [ ]* 14.5 Escrever teste unitário para roteamento de endpoint OpenAI
    - Verificar que chama endpoint correto
  
  - [ ]* 14.6 Escrever teste unitário para HTTP 401 sem retry
    - Verificar que levanta LLMAuthError imediatamente
  
  - [ ]* 14.7 Escrever teste unitário para HTTP 429 com retry
    - Verificar que aguarda Retry-After e retenta

- [ ] 15. Implementar AnthropicClient
  - [ ] 15.1 Criar `tokemize/integrations/llm/anthropic_client.py` com classe `AnthropicClient`
    - Herdar de BaseLLMClient
    - Implementar `__init__()` com api_key (ler de ANTHROPIC_API_KEY)
    - _Requirements: 6.3, 6.7_
  
  - [ ] 15.2 Implementar método `complete()` para Anthropic
    - Enviar requisição para API Anthropic Messages
    - Suportar modelos: claude-3-5-sonnet-20241022, claude-3-opus-20240229
    - Retornar LLMResponse com text, input_tokens, output_tokens, model, provider
    - _Requirements: 6.3, 6.4_
  
  - [ ] 15.3 Implementar tratamento de erros para Anthropic
    - HTTP 401 → LLMAuthError imediato
    - HTTP 429 → aguardar Retry-After, retentar uma vez, depois LLMRateLimitError
    - Outros erros → LLMAPIError
    - _Requirements: 6.5, 6.6_
  
  - [ ]* 15.4 Escrever teste de propriedade para LLMResponse completo
    - **Property 14: LLMResponse contém todos os campos de uso de tokens**
    - **Valida: Requirements 6.4**
  
  - [ ]* 15.5 Escrever teste unitário para roteamento de endpoint Anthropic
    - Verificar que chama endpoint correto

- [ ] 16. Implementar logging e observabilidade
  - [ ] 16.1 Criar `tokemize/config/logging_config.py` com configuração de logging
    - Configurar logger raiz com nível configurável via LOG_LEVEL
    - Criar SensitiveDataFilter para redação de chaves de API
    - Aplicar filtro a todos os handlers
    - _Requirements: 9.1, 9.5_
  
  - [ ] 16.2 Adicionar logs estruturados em todas as camadas
    - Optimizer: INFO no início e fim com PipelineMetrics
    - Todas as camadas: ERROR com nome da camada, mensagem e stack trace
    - Selector: DEBUG ao descartar chunks por budget
    - Parser: WARNING ao encontrar erro de sintaxe parcial
    - Indexer: WARNING ao criar novo índice por corrupção
    - _Requirements: 9.2, 9.3, 9.4_
  
  - [ ]* 16.3 Escrever teste de propriedade para logs sem API keys
    - **Property 19: Logs de erro nunca expõem valores de chaves de API**
    - **Valida: Requirements 9.5**

- [ ] 17. Checkpoint - Verificar integração com LLMs e logging
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Implementar testes de propriedade para modelos
  - [ ]* 18.1 Escrever teste de propriedade para invariante de total_tokens
    - **Property 18: Invariante de consistência de total_tokens em OptimizedContext**
    - **Valida: Requirements 8.7**
  
  - [ ]* 18.2 Escrever teste unitário para Chunk com embedding=None
    - Verificar que aceita None sem exceção

- [ ] 19. Criar entrypoint principal
  - [ ] 19.1 Criar `tokemize/main.py` com função `main()`
    - Carregar configuração com load_config()
    - Instanciar todos os componentes do pipeline
    - Instanciar LLMClient apropriado (OpenAI ou Anthropic)
    - Expor interface CLI ou função programática
    - _Requirements: 5.5, 6.1_
  
  - [ ] 19.2 Adicionar tratamento de erros no entrypoint
    - Capturar MissingConfigError e InvalidConfigError
    - Exibir mensagens de erro amigáveis
    - Retornar códigos de saída apropriados

- [ ] 20. Criar documentação
  - [ ] 20.1 Criar README.md com instruções de instalação e uso
    - Descrever o problema que o Tokemize resolve
    - Listar dependências e requisitos
    - Fornecer exemplos de uso
    - Documentar variáveis de ambiente
  
  - [ ] 20.2 Criar CONTRIBUTING.md com guia de desenvolvimento
    - Descrever estrutura do projeto
    - Explicar como executar testes
    - Documentar convenções de código
  
  - [ ] 20.3 Adicionar docstrings em todos os módulos públicos
    - Usar padrão Google Style
    - Documentar parâmetros, retornos e exceções

- [ ] 21. Checkpoint final - Verificar sistema completo
  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia os requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental do progresso
- Testes de propriedade validam propriedades universais de corretude
- Testes unitários validam exemplos específicos e edge cases
- O sistema usa Python 3.11+ conforme especificado no design
- Todas as 22 propriedades de corretude estão mapeadas para tarefas de teste
