# Arquitetura do Tokemize

## Visão Geral

O Tokemize é um **middleware inteligente** que atua entre o usuário e os LLMs (Large Language Models), otimizando o contexto enviado em cada requisição. Em vez de encaminhar o repositório ou o contexto bruto por inteiro, o Tokemize seleciona, resume e comprime apenas o que é relevante para cada consulta — reduzindo custos e aumentando a precisão das respostas.

```
Usuário ──► Tokemize ──► Seleção ──► Resumo ──► Otimização ──► LLM
```

---

## Fluxo da Arquitetura

```
┌─────────┐     entrada      ┌──────────────────────────────────────────┐
│ Usuário │ ───────────────► │                 Tokemize                 │
└─────────┘   (query/task)   │                                          │
                             │  ┌──────────┐   ┌──────────┐            │
                             │  │  Parser  │──►│ Indexer  │            │
                             │  └──────────┘   └────┬─────┘            │
                             │                      │ índice vetorial   │
                             │                 ┌────▼─────┐            │
                             │                 │ Selector │            │
                             │                 └────┬─────┘            │
                             │                      │ trechos relevantes│
                             │                 ┌────▼──────┐           │
                             │                 │ Optimizer │           │
                             │                 └────┬──────┘           │
                             └──────────────────────┼───────────────────┘
                                                    │ contexto otimizado
                                               ┌────▼────┐
                                               │   LLM   │
                                               └─────────┘
```

---

## Componentes

### 1. Parser

Responsável por mapear e analisar a estrutura do repositório. Utiliza **Tree-sitter** para realizar análise sintática (AST) do código-fonte, extraindo símbolos, funções, classes e dependências com precisão.

- **Entrada:** arquivos do repositório
- **Saída:** representação estruturada do código (AST + metadados)
- **Status:** ✅ Concluído

### 2. Indexer

Transforma os dados estruturados gerados pelo Parser em **vetores de embeddings** e os armazena em um índice **FAISS**, viabilizando buscas semânticas eficientes.

- **Entrada:** representação estruturada do Parser
- **Saída:** índice vetorial do repositório
- **Status:** 🔲 Planejado

### 3. Selector

Recebe a query do usuário e realiza uma **busca semântica** no índice vetorial para recuperar apenas os trechos de código mais relevantes para aquela consulta.

- **Entrada:** query do usuário + índice vetorial do Indexer
- **Saída:** conjunto de trechos de código relevantes
- **Status:** 🔄 Em desenvolvimento

### 4. Optimizer

Comprime e resume os trechos selecionados, aplicando redução semântica inteligente para maximizar a informação útil dentro do limite de tokens do LLM.

- **Entrada:** trechos relevantes do Selector
- **Saída:** contexto otimizado e comprimido
- **Status:** 🔲 Planejado

### 5. LLM Integration

Módulo de integração com os provedores de LLM (OpenAI, Anthropic, Groq). Encaminha o contexto otimizado e retorna a resposta ao usuário.

- **Entrada:** contexto otimizado do Optimizer + query original
- **Saída:** resposta do LLM
- **Status:** 🔲 Planejado

### 6. Embeddings

Módulo auxiliar que gera os embeddings utilizados pelo Indexer e pelo Selector, suportando múltiplos provedores de embeddings.

- **Status:** 🔲 Planejado

---

## Cache de Contexto

Para consultas repetitivas ou similares, o Tokemize implementará um **cache de contexto** que reutiliza índices e seleções já computadas, reduzindo latência e custos de processamento.

---

## Estrutura de Diretórios

```
mini-projeto-tokemize/
├── src/
│   └── tokemize/          # Código-fonte principal (Python)
├── tests/                 # Testes automatizados
├── docs/
│   ├── architecture.md    # Este arquivo
│   ├── technologies.md    # Stack e decisões técnicas
│   ├── roadmap.md         # Progresso e próximos passos
│   └── showcase/          # GitHub Pages — dashboard do projeto
└── pyproject.toml         # Configuração do projeto Python
```
