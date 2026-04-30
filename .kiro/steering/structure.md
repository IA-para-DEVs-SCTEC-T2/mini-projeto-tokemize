---
title: Estrutura do Projeto
inclusion: always
---

# Estrutura de Diretórios
tokemize/
├── core/
│   ├── parser/         # Integração com Tree-sitter (análise sintática)
│   ├── indexer/        # Integração com FAISS (indexação e busca vetorial)
│   ├── selector/       # Lógica de seleção e ranqueamento de contexto
│   └── optimizer/      # Orquestrador do pipeline completo
├── integrations/
│   ├── llm/            # Clientes abstraídos para OpenAI e Anthropic
│   └── embeddings/     # Geração de embeddings para indexação
├── models/             # Dataclasses e schemas (contexto, chunk, resultado)
├── config/             # Configurações, constantes e carregamento de .env
├── tests/              # Testes unitários e de integração (pytest)
└── main.py             # Entrypoint principal

## Responsabilidade de cada camada

| Camada | Responsabilidade |
|---|---|
| `parser/` | Receber um arquivo ou trecho de código e retornar artefatos sintáticos (funções, classes, símbolos) |
| `indexer/` | Receber artefatos, gerar embeddings e persistir/consultar o índice FAISS |
| `selector/` | Dada uma query/requisição, buscar e ranquear os chunks mais relevantes |
| `optimizer/` | Orquestrar parser → indexer → selector e montar o contexto final otimizado |
| `integrations/llm/` | Enviar o contexto otimizado ao LLM escolhido e retornar a resposta |
| `models/` | Definir as estruturas de dados que trafegam entre as camadas |

## Convenções de Nomenclatura
- Arquivos: snake_case (ex: `context_selector.py`)
- Classes: PascalCase (ex: `ContextSelector`)
- Funções e variáveis: snake_case
- Constantes: UPPER_SNAKE_CASE
- Testes: prefixo `test_` espelhando o módulo testado (ex: `test_context_selector.py`)

## Fluxo Principal
Requisição do usuário
↓
Parser (Tree-sitter)
Extrai artefatos do código
↓
Indexer (FAISS)
Busca chunks relevantes por similaridade
↓
Selector
Ranqueia e filtra pelo budget de tokens
↓
Optimizer
Monta o contexto final compacto
↓
LLM (OpenAI / Anthropic)
Recebe apenas o necessário