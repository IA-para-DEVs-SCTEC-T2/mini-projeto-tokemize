# Requirements Document

## Introduction

O Tokemize é um agente inteligente de otimização de contexto para LLMs. O sistema resolve um problema crítico em agentes de desenvolvimento de software: o envio de contexto excessivo e irrelevante para modelos de linguagem, o que gera alto custo de tokens, respostas imprecisas e alucinações.

A solução é um pipeline composto por quatro camadas principais — Parser, Indexer, Selector e Optimizer — que analisa sintaticamente o código-fonte, indexa vetorialmente os artefatos relevantes e seleciona apenas o contexto necessário antes de cada chamada ao LLM. O sistema suporta múltiplos provedores de LLM (OpenAI e Anthropic) por meio de uma interface de abstração comum.

---

## Glossary

- **Tokemize**: O sistema completo de otimização de contexto descrito neste documento.
- **Pipeline**: A sequência ordenada de etapas de processamento: Parser → Indexer → Selector → Optimizer → LLM.
- **Parser**: Componente responsável por analisar sintaticamente arquivos de código-fonte usando Tree-sitter e extrair artefatos estruturados.
- **Artefato**: Unidade estrutural extraída do código-fonte, como uma função, classe, método, import ou símbolo.
- **Chunk**: Fragmento de código com metadados (nome, tipo, localização, linguagem) pronto para indexação e busca.
- **Indexer**: Componente responsável por gerar embeddings dos chunks e persistir/consultar o índice vetorial FAISS.
- **Embedding**: Representação vetorial numérica de um chunk de código, gerada via API de embeddings.
- **Índice FAISS**: Estrutura de dados vetorial persistida localmente, usada para busca por similaridade semântica.
- **Selector**: Componente responsável por buscar e ranquear os chunks mais relevantes para uma requisição, respeitando o budget de tokens.
- **Budget de Tokens**: Limite máximo de tokens que o contexto otimizado pode conter antes de ser enviado ao LLM.
- **Optimizer**: Orquestrador do pipeline completo; monta o contexto final compacto a partir dos chunks selecionados.
- **LLM_Client**: Interface de abstração comum para comunicação com provedores de LLM (OpenAI e Anthropic).
- **Provider**: Provedor de LLM configurado (OpenAI ou Anthropic).
- **Requisição**: Entrada do usuário contendo uma pergunta ou instrução técnica a ser respondida pelo LLM.
- **Contexto Otimizado**: Conjunto de chunks selecionados e formatados que será enviado ao LLM junto com a requisição.
- **Score de Relevância**: Valor numérico que representa a similaridade semântica entre um chunk e a requisição do usuário.

---

## Requirements

### Requirement 1: Análise Sintática de Código-Fonte

**User Story:** Como desenvolvedor, quero que o sistema analise sintaticamente meu código-fonte, para que artefatos estruturados (funções, classes, imports) sejam extraídos e disponibilizados para indexação.

#### Acceptance Criteria

1. WHEN um arquivo de código-fonte válido é fornecido ao Parser, THE Parser SHALL extrair todos os artefatos sintáticos presentes no arquivo, incluindo funções, classes, métodos e imports.
2. WHEN um arquivo de código-fonte é fornecido, THE Parser SHALL identificar a linguagem de programação do arquivo com base na extensão (`.py`, `.java`, `.js`, `.ts`) e aplicar o grammar Tree-sitter correspondente.
3. WHEN um artefato é extraído, THE Parser SHALL associar a ele os metadados: nome, tipo (função, classe, método, import), número de linha inicial, número de linha final e linguagem.
4. IF um arquivo de código-fonte contém erros de sintaxe, THEN THE Parser SHALL retornar os artefatos válidos extraídos até o ponto do erro e registrar o erro com a localização exata.
5. IF uma linguagem não suportada é fornecida ao Parser, THEN THE Parser SHALL retornar um erro descritivo indicando a linguagem não suportada.
6. THE Parser SHALL suportar as linguagens Python, Java, JavaScript e TypeScript.
7. WHEN o Parser extrai artefatos de um arquivo, THE Parser SHALL preservar o conteúdo textual original de cada artefato sem modificações.

---

### Requirement 2: Geração de Embeddings

**User Story:** Como desenvolvedor, quero que os artefatos extraídos sejam convertidos em representações vetoriais, para que a busca por similaridade semântica seja possível.

#### Acceptance Criteria

1. WHEN um conjunto de chunks é fornecido ao componente de Embeddings, THE Embeddings_Client SHALL gerar um vetor de embedding para cada chunk usando a API OpenAI text-embedding.
2. WHEN um embedding é gerado para um chunk, THE Embeddings_Client SHALL associar o vetor ao identificador único do chunk correspondente.
3. IF a API de embeddings retornar um erro, THEN THE Embeddings_Client SHALL realizar até 3 tentativas com backoff exponencial antes de propagar o erro.
4. THE Embeddings_Client SHALL processar chunks em lotes (batches) de até 100 itens por chamada à API, para respeitar os limites da API.
5. THE Embeddings_Client SHALL expor uma interface que permita a substituição do provedor de embeddings sem alteração nas camadas superiores do pipeline.

---

### Requirement 3: Indexação Vetorial com FAISS

**User Story:** Como desenvolvedor, quero que os embeddings dos artefatos sejam indexados e persistidos localmente, para que buscas por similaridade possam ser realizadas de forma eficiente entre sessões.

#### Acceptance Criteria

1. WHEN embeddings de chunks são fornecidos ao Indexer, THE Indexer SHALL adicionar os vetores ao índice FAISS e associar cada vetor aos metadados do chunk correspondente.
2. WHEN a indexação de um conjunto de chunks é concluída, THE Indexer SHALL persistir o índice FAISS em disco no diretório configurado.
3. WHEN o Indexer é inicializado e um índice persistido existe no diretório configurado, THE Indexer SHALL carregar o índice existente em vez de criar um novo.
4. WHEN um índice é carregado do disco, THE Indexer SHALL verificar a integridade do índice antes de disponibilizá-lo para consultas.
5. IF o arquivo de índice persistido estiver corrompido ou ilegível, THEN THE Indexer SHALL criar um novo índice vazio e registrar um aviso de log.
6. THE Indexer SHALL suportar a adição incremental de novos chunks ao índice sem necessidade de reindexação completa.
7. FOR ALL conjuntos de chunks indexados e depois recuperados por busca exata, THE Indexer SHALL retornar os chunks originais com seus metadados intactos (propriedade de round-trip).

---

### Requirement 4: Seleção e Ranqueamento de Contexto

**User Story:** Como desenvolvedor, quero que o sistema selecione automaticamente os chunks mais relevantes para minha requisição, para que o contexto enviado ao LLM seja preciso e dentro do budget de tokens.

#### Acceptance Criteria

1. WHEN uma requisição do usuário é fornecida ao Selector, THE Selector SHALL gerar um embedding da requisição e realizar uma busca por similaridade no índice FAISS.
2. WHEN a busca por similaridade é realizada, THE Selector SHALL retornar os chunks ordenados por score de relevância em ordem decrescente.
3. WHEN o Selector ranqueia os chunks, THE Selector SHALL incluir apenas chunks cujo score de relevância seja igual ou superior ao limiar mínimo configurado.
4. WHEN o Selector monta a lista de chunks selecionados, THE Selector SHALL respeitar o budget de tokens configurado, excluindo chunks que ultrapassariam o limite acumulado.
5. THE Selector SHALL calcular o número de tokens de cada chunk usando o tokenizador correspondente ao modelo LLM configurado.
6. IF nenhum chunk atingir o limiar mínimo de relevância, THEN THE Selector SHALL retornar uma lista vazia e registrar um aviso de log.
7. WHEN dois chunks possuem o mesmo score de relevância, THE Selector SHALL desempatar priorizando o chunk com menor número de tokens.
8. FOR ALL requisições processadas pelo Selector, o número total de tokens dos chunks selecionados SHALL ser menor ou igual ao budget de tokens configurado (invariante de budget).

---

### Requirement 5: Orquestração do Pipeline (Optimizer)

**User Story:** Como desenvolvedor, quero que o sistema orquestre automaticamente todas as etapas do pipeline, para que eu receba o contexto otimizado pronto para envio ao LLM sem precisar coordenar cada etapa manualmente.

#### Acceptance Criteria

1. WHEN uma requisição do usuário e um conjunto de arquivos de código-fonte são fornecidos ao Optimizer, THE Optimizer SHALL executar as etapas na ordem: Parser → Indexer → Selector e retornar o contexto otimizado.
2. WHEN o Optimizer conclui a seleção de contexto, THE Optimizer SHALL formatar os chunks selecionados em um único bloco de texto estruturado, incluindo o nome do artefato, a linguagem e o conteúdo.
3. WHEN o Optimizer é invocado com os mesmos arquivos de entrada em sessões diferentes, THE Optimizer SHALL reutilizar o índice FAISS persistido em vez de reindexar os arquivos.
4. IF qualquer etapa do pipeline retornar um erro, THEN THE Optimizer SHALL interromper a execução, registrar o erro com o nome da etapa que falhou e propagar uma exceção descritiva.
5. THE Optimizer SHALL expor uma interface única (`optimize(request, files, budget)`) que encapsula todo o pipeline.
6. WHEN o Optimizer é executado, THE Optimizer SHALL registrar em log o número de artefatos extraídos, o número de chunks indexados, o número de chunks selecionados e o total de tokens do contexto final.

---

### Requirement 6: Integração com Provedores de LLM

**User Story:** Como desenvolvedor, quero enviar o contexto otimizado para diferentes provedores de LLM (OpenAI e Anthropic) usando uma interface unificada, para que eu possa trocar de provedor sem alterar o restante do pipeline.

#### Acceptance Criteria

1. THE LLM_Client SHALL expor uma interface comum com o método `complete(context, request, model)` para todos os provedores suportados.
2. WHEN o provedor OpenAI é configurado, THE LLM_Client SHALL enviar a requisição para a API OpenAI usando o modelo especificado (GPT-4o ou GPT-4-turbo).
3. WHEN o provedor Anthropic é configurado, THE LLM_Client SHALL enviar a requisição para a API Anthropic usando o modelo especificado (Claude Sonnet ou Claude Opus).
4. WHEN uma resposta é recebida do provedor LLM, THE LLM_Client SHALL retornar o texto da resposta e os metadados de uso de tokens (tokens de entrada, tokens de saída, custo estimado).
5. IF a API do provedor LLM retornar um erro de rate limit (HTTP 429), THEN THE LLM_Client SHALL aguardar o tempo indicado no header `Retry-After` e retentar a requisição automaticamente.
6. IF a API do provedor LLM retornar um erro de autenticação (HTTP 401), THEN THE LLM_Client SHALL propagar imediatamente uma exceção descritiva sem realizar retentativas.
7. THE LLM_Client SHALL ler as chaves de API exclusivamente de variáveis de ambiente, nunca de valores hardcoded no código.
8. WHERE o provedor OpenAI está configurado, THE LLM_Client SHALL suportar a configuração de temperatura, max_tokens e system prompt via parâmetros opcionais.

---

### Requirement 7: Configuração e Variáveis de Ambiente

**User Story:** Como desenvolvedor, quero configurar o sistema por meio de variáveis de ambiente e um arquivo `.env`, para que credenciais e parâmetros operacionais sejam gerenciados de forma segura e flexível.

#### Acceptance Criteria

1. THE Config_Loader SHALL carregar todas as configurações do sistema a partir de variáveis de ambiente usando python-dotenv.
2. THE Config_Loader SHALL suportar as seguintes variáveis obrigatórias: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `EMBEDDING_MODEL`, `LLM_PROVIDER`, `LLM_MODEL`.
3. THE Config_Loader SHALL suportar as seguintes variáveis opcionais com valores padrão: `TOKEN_BUDGET` (padrão: 4096), `RELEVANCE_THRESHOLD` (padrão: 0.75), `FAISS_INDEX_PATH` (padrão: `./.tokemize_index`), `EMBEDDING_BATCH_SIZE` (padrão: 100).
4. IF uma variável de ambiente obrigatória não estiver definida, THEN THE Config_Loader SHALL lançar uma exceção descritiva no momento da inicialização, indicando o nome da variável ausente.
5. THE Config_Loader SHALL validar que o valor de `TOKEN_BUDGET` é um inteiro positivo maior que zero.
6. THE Config_Loader SHALL validar que o valor de `RELEVANCE_THRESHOLD` é um número de ponto flutuante no intervalo [0.0, 1.0].
7. IF um valor de configuração inválido for detectado, THEN THE Config_Loader SHALL lançar uma exceção descritiva indicando o nome da variável e o valor inválido recebido.

---

### Requirement 8: Modelos de Dados

**User Story:** Como desenvolvedor, quero que as estruturas de dados que trafegam entre as camadas do pipeline sejam bem definidas e tipadas, para que a integração entre componentes seja segura e previsível.

#### Acceptance Criteria

1. THE Models_Module SHALL definir um dataclass `Artifact` com os campos: `name: str`, `type: str`, `start_line: int`, `end_line: int`, `language: str`, `content: str`.
2. THE Models_Module SHALL definir um dataclass `Chunk` com os campos: `id: str`, `artifact: Artifact`, `token_count: int`, `embedding: list[float] | None`.
3. THE Models_Module SHALL definir um dataclass `OptimizedContext` com os campos: `chunks: list[Chunk]`, `total_tokens: int`, `formatted_text: str`.
4. THE Models_Module SHALL definir um dataclass `LLMResponse` com os campos: `text: str`, `input_tokens: int`, `output_tokens: int`, `model: str`, `provider: str`.
5. THE Models_Module SHALL definir um dataclass `PipelineMetrics` com os campos: `artifacts_extracted: int`, `chunks_indexed: int`, `chunks_selected: int`, `total_context_tokens: int`, `elapsed_seconds: float`.
6. WHEN um `Chunk` é criado sem embedding, THE Models_Module SHALL aceitar `None` como valor do campo `embedding` sem lançar exceção.
7. FOR ALL instâncias de `OptimizedContext`, o valor de `total_tokens` SHALL ser igual à soma dos `token_count` de todos os `Chunk` em `chunks` (invariante de consistência).

---

### Requirement 9: Observabilidade e Logging

**User Story:** Como desenvolvedor, quero que o sistema registre logs estruturados das operações do pipeline, para que eu possa monitorar o comportamento, diagnosticar falhas e auditar o uso de tokens.

#### Acceptance Criteria

1. THE Tokemize SHALL registrar logs usando o módulo `logging` padrão do Python com nível configurável via variável de ambiente `LOG_LEVEL` (padrão: `INFO`).
2. WHEN o pipeline é executado, THE Optimizer SHALL registrar um log de nível INFO ao início e ao fim da execução, incluindo as métricas do `PipelineMetrics`.
3. WHEN um erro ocorre em qualquer camada do pipeline, THE camada afetada SHALL registrar um log de nível ERROR com o nome da camada, a mensagem de erro e o stack trace.
4. WHEN o Selector descarta chunks por exceder o budget de tokens, THE Selector SHALL registrar um log de nível DEBUG indicando o número de chunks descartados e o total de tokens que excederia o limite.
5. THE Tokemize SHALL garantir que nenhum valor de chave de API seja incluído nos logs em nenhum nível de log.

---

### Requirement 10: Parsing e Serialização de Artefatos (Round-Trip)

**User Story:** Como desenvolvedor, quero que os artefatos extraídos pelo Parser possam ser serializados e desserializados sem perda de informação, para que o índice FAISS possa ser persistido e recarregado de forma confiável entre sessões.

#### Acceptance Criteria

1. THE Artifact_Serializer SHALL serializar instâncias de `Artifact` e `Chunk` para o formato JSON.
2. THE Artifact_Serializer SHALL desserializar JSON de volta para instâncias de `Artifact` e `Chunk`.
3. IF um JSON inválido ou com campos obrigatórios ausentes for fornecido ao Artifact_Serializer, THEN THE Artifact_Serializer SHALL retornar um erro descritivo indicando os campos ausentes ou inválidos.
4. FOR ALL instâncias válidas de `Artifact`, serializar e depois desserializar SHALL produzir um objeto equivalente ao original (propriedade de round-trip): `deserialize(serialize(artifact)) == artifact`.
5. FOR ALL instâncias válidas de `Chunk` com embedding não nulo, serializar e depois desserializar SHALL preservar o vetor de embedding com precisão de ponto flutuante de 32 bits.
