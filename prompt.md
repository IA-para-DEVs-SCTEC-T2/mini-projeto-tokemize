# Project Context & Rules (Kiro Standard)

> **Gerado com:** [Kiro](https://kiro.dev) — AI-powered development environment  
> **Metodologia:** Spec-Driven Vibe Coding  
> **Versão:** 1.0.0  
> **Repositório:** [IA-para-DEVs-SCTEC-T2/mini-projeto-tokemize](https://github.com/IA-para-DEVs-SCTEC-T2/mini-projeto-tokemize)

---

## Por que este arquivo existe?

Este `prompt.md` é o **contrato de contexto compartilhado** do projeto Tokemize.
Diferente de um prompt pessoal e descartável, ele é versionado no repositório para que
todo o time — humanos e agentes de IA — operem na mesma frequência.

### Princípios que guiam este arquivo

| Princípio | Descrição |
|---|---|
| **Versionamento de Contexto** | O prompt evolui junto com o código via Git. Cada mudança de arquitetura reflete aqui. |
| **Spec-Driven Development** | O código é gerado a partir de specs técnicas rigorosas (`.kiro/specs/`), não de conversas informais. |
| **Single Source of Truth** | Stack, padrões e regras definidos uma vez, seguidos por todos. |
| **Bibliotecas Comunitárias** | Preferência por pacotes amplamente adotados e mantidos ativamente pela comunidade. |

---

## 🎯 Visão Geral

**Projeto:** Tokemize  
**Objetivo:** Middleware inteligente que otimiza o contexto enviado a LLMs, selecionando apenas o que é relevante para cada requisição técnica — reduzindo custo de tokens e aumentando a precisão das respostas.  
**Público-alvo:** Desenvolvedores e equipes que utilizam agentes de IA no desenvolvimento de software.  
**Repositório:** `git@github.com:IA-para-DEVs-SCTEC-T2/mini-projeto-tokemize.git`

### O problema que resolve

```
Contexto bruto (repositório inteiro) ──► LLM  =  💸 caro + 📉 impreciso
Contexto otimizado (Tokemize)        ──► LLM  =  ✅ barato + 🎯 preciso
```

---

## 💻 Tech Stack (Single Source of Truth)

| Camada | Tecnologia | Versão | Justificativa |
|---|---|---|---|
| **Runtime** | Python | 3.11+ | Orquestração principal, tipagem estática, ecossistema de IA |
| **Análise Sintática** | Tree-sitter | 0.25.2 | Parser incremental, suporte a 40+ linguagens, API declarativa |
| **Grammars** | tree-sitter-python / java / javascript / typescript | latest | Grammars oficiais mantidos pela comunidade Tree-sitter |
| **Indexação Vetorial** | FAISS | latest | Busca por similaridade semântica de alta performance (Meta AI) |
| **LLM — OpenAI** | GPT-4o / GPT-4-turbo | API | Provedor primário de LLM |
| **LLM — Anthropic** | Claude Sonnet / Opus | API | Provedor alternativo de LLM |
| **CLI** | Typer | 0.12.3 | Interface de linha de comando idiomática para Python |
| **Config** | python-dotenv | latest | Variáveis de ambiente via `.env`, nunca hardcoded |
| **Testes** | pytest + pytest-cov | 8.3.5 / 6.1.0 | Framework padrão Python, cobertura integrada |
| **Testes de Propriedade** | Hypothesis | 6.100+ | Property-based testing para invariantes do pipeline |

---

## 🏗️ Arquitetura do Pipeline

```
Usuário (query + repositório)
        │
        ▼
┌───────────────────────────────────────────────────┐
│                    Tokemize                       │
│                                                   │
│  RepositoryScanner ──► TreeSitterAnalyzer         │
│  (varredura + metadados)  (AST + artefatos)       │
│                │                                  │
│                ▼                                  │
│         RepositoryParser                          │
│         (orquestrador Scanner + Analyzer)         │
│                │                                  │
│                ▼                                  │
│  Indexer (FAISS) ──► Selector ──► Optimizer       │
│  (embeddings)       (relevância)  (compressão)    │
└───────────────────────────────────────────────────┘
        │
        ▼
   LLM (OpenAI / Anthropic)
        │
        ▼
   Resposta otimizada
```

---

## 📂 Estrutura de Diretórios

```
mini-projeto-tokemize/
├── src/tokemize/               # Pacote principal (instalável via pip)
│   ├── core/
│   │   └── parser/             # Scanner, TreeSitterAnalyzer, RepositoryParser
│   ├── integrations/
│   │   └── llm/                # Clientes OpenAI e Anthropic (protocol.py)
│   ├── models/                 # Dataclasses: Artifact, Chunk, etc.
│   ├── scanner.py              # Módulo público (re-export)
│   ├── tree_sitter_analyzer.py # Módulo público (re-export)
│   ├── repository_parser.py    # Módulo público (re-export)
│   ├── selector.py             # Seleção semântica de contexto
│   ├── summarizer.py           # Sumarização com LLM
│   └── cache.py                # Cache de contexto
├── tests/                      # Testes unitários e de integração
├── docs/                       # Documentação técnica
│   ├── architecture.md
│   ├── roadmap.md
│   └── technologies.md
├── .kiro/
│   ├── specs/                  # Specs técnicas (Spec-Driven Development)
│   │   ├── tokemize-context-optimizer/
│   │   └── tokemize-cli/
│   └── steering/               # Regras de contexto para o agente Kiro
│       ├── product.md
│       ├── structure.md
│       └── tech.md
├── cli.py                      # Entrypoint CLI (Typer)
├── pyproject.toml              # Configuração do projeto
└── prompt.md                   # Este arquivo
```

**Responsabilidade de cada camada:**

| Módulo | Responsabilidade |
|---|---|
| `core/parser/scanner.py` | Percorre o repositório, aplica ignores, coleta metadados |
| `core/parser/tree_sitter_analyzer.py` | Extrai classes, funções, métodos e imports via Tree-sitter |
| `core/parser/repository_parser.py` | Orquestra Scanner → Analyzer, retorna `RepositoryParseResult` |
| `integrations/llm/` | Clientes abstraídos para OpenAI e Anthropic |
| `models/` | Dataclasses tipadas que trafegam entre camadas |
| `selector.py` | Busca semântica no índice FAISS |
| `summarizer.py` | Compressão e resumo semântico via LLM |
| `cache.py` | Cache de contexto para consultas repetitivas |

---

## 🛠️ Padrões de Desenvolvimento (Vibe Code)

### Código

- **Tipagem estática:** type hints obrigatórios em todas as funções e classes
- **Docstrings:** padrão Google Style em todos os módulos públicos
- **Modularidade:** separação estrita de responsabilidades por camada — parser não conhece indexer, indexer não conhece selector
- **Error Handling:** blocos `try/except` com logs estruturados via `logging` padrão Python
- **Variáveis de ambiente:** exclusivamente via `python-dotenv` (`.env`), nunca hardcoded
- **Dataclasses:** modelos de dados como `@dataclass` com validação em `__post_init__`

### Qualidade

- **No Ghost Code:** sem código comentado ou funções não utilizadas
- **Refactor First:** antes de criar algo novo, verificar se já existe utilitário similar
- **Cobertura mínima:** 90%+ nos módulos de `core/` e `models/`
- **Testes de propriedade:** invariantes críticos validados com Hypothesis

### Integração com Kiro

- **Specs:** toda nova feature começa com um spec em `.kiro/specs/` (requirements → design → tasks)
- **Steering:** regras de contexto em `.kiro/steering/` garantem que o agente siga a arquitetura
- **Hooks:** automações de lint, testes e validação configuradas via Kiro Hooks

---

## 📜 Regras de Colaboração (Time)

### Branches (Gitflow)

```
feature/*  ──┐
fix/*      ──┤──► develop ──► main
refactor/* ──┤
docs/*     ──┘
hotfix/*   ──────────────────► main
```

Formato obrigatório: `<tipo>/<descricao-em-kebab-case>`

### Commits (Conventional Commits)

```
feat(parser): add char_count to FileMetadata
fix(analyzer): handle decorated functions correctly
refactor(scanner): replace os.walk with iter_files lazy generator
docs: update architecture diagram
test(integration): add end-to-end repository parse tests
```

Tipos: `feat` | `fix` | `docs` | `style` | `refactor` | `test` | `chore` | `perf` | `ci` | `revert`

### Pull Requests

- PR sempre aponta para `develop` (exceto `hotfix/*` → `main`)
- Título segue Conventional Commits (máx. 70 caracteres)
- Checklist obrigatório: branch correta, testes executados, sem arquivos desnecessários
- Validação automática via GitHub Actions (commitlint + branch-rules)

---

## 🤖 Instruções para o Agente de IA (Kiro)

Ao trabalhar neste projeto, o agente deve:

1. **Ler os specs** em `.kiro/specs/` antes de implementar qualquer feature
2. **Seguir a separação de camadas** — nunca misturar lógica de parsing com seleção de contexto
3. **Nunca instanciar clientes de LLM** fora de `integrations/llm/`
4. **Nunca enviar contexto raw** sem passar pelo pipeline de otimização
5. **Sempre adicionar type hints** e docstrings Google Style
6. **Rodar os testes** após qualquer mudança: `python -m pytest tests/`
7. **Commits semânticos** em toda entrega, mesmo incremental
8. **Branch correta** — feature → develop, nunca direto na main

---

## 🚀 Roadmap de Contexto

### Fase 1 — Fundação ✅
- [x] Arquitetura e estrutura do repositório
- [x] CI/CD: commitlint, branch-rules, gitflow
- [x] `RepositoryScanner` — varredura com ignores, metadados, lazy streaming
- [x] `TreeSitterAnalyzer` — extração de artefatos (Python, Java, JS, TS)
- [x] `RepositoryParser` — integração Scanner + Analyzer
- [x] Modelos de dados: `Artifact` com `to_dict()` e validação
- [x] 155 testes passando, cobertura 92%

### Fase 2 — Núcleo Semântico 🔄
- [x] `selector.py` — seleção semântica (em desenvolvimento)
- [x] `summarizer.py` — sumarização com LLM (em desenvolvimento)
- [x] `cache.py` — cache de contexto (em desenvolvimento)
- [ ] `Indexer` — indexação vetorial com FAISS
- [ ] `EmbeddingsClient` — geração de embeddings multi-provedor

### Fase 3 — Otimização e Integração 🔲
- [ ] `Optimizer` — compressão e resumo semântico
- [ ] `LLMClient` — integração OpenAI + Anthropic com retry e rate limit
- [ ] Pipeline completo: Scanner → Indexer → Selector → Optimizer → LLM

### Fase 4 — Produto Final 🔲
- [ ] CLI público (`tokemize query "..."`)
- [ ] SDK para integração com ferramentas externas
- [ ] Benchmarks de custo/qualidade
- [ ] Documentação de uso e exemplos

---

## 👥 Equipe

| Membro | GitHub | Responsabilidade |
|---|---|---|
| Eneri da Costa Junior | [@jrcosta](https://github.com/jrcosta) | — |
| Guilherme Valerio Mertens | [@gvmertens](https://github.com/gvmertens) | — |
| Paulo Sergio | [@PauloSergioLR](https://github.com/PauloSergioLR) | — |
| Samuel Magalhães Marques | [@samuelmarquesgit](https://github.com/samuelmarquesgit) | Parser + Tree-sitter |
| Eduardo Notari | [@edunotari](https://github.com/edunotari) | — |

---

## 📚 Referências

- [Kiro — AI-powered development environment](https://kiro.dev)
- [Spec-Driven Vibe Coding](https://vivekhaldar.com/articles/spec-driven-vibe-coding/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- [FAISS](https://faiss.ai/)
- [Vibe Coding Prompt Template (KhazP)](https://github.com/KhazP/vibe-coding-prompt-template)

---

*Content was rephrased for compliance with licensing restrictions.*  
*Este arquivo é mantido pelo time e atualizado a cada sprint.*
