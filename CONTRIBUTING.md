# Guia de Contribuição

Obrigado por considerar contribuir com o Tokemize! Este documento descreve como configurar o ambiente, seguir as convenções do projeto e abrir Pull Requests de forma produtiva.

O projeto está em desenvolvimento inicial — toda contribuição é bem-vinda, desde correções de typo até novos módulos do pipeline.

---

## Visão Geral

O Tokemize é uma ferramenta CLI que analisa repositórios de código e gera prompts otimizados para chatbots de IDE. Contribuições podem incluir:

- Correções de bugs
- Novos módulos ou melhorias no pipeline
- Suporte a novas linguagens no Tree-sitter
- Melhorias na documentação
- Testes unitários e de integração

---

## Pré-requisitos

- **Python 3.11+** instalado
- **pip** (gerenciador de pacotes)
- **Git** configurado com nome e email
- (Opcional) **GitHub CLI** (`gh`) para criar PRs via terminal

---

## Configuração do Ambiente Local

```bash
# 1. Clone o repositório
git clone https://github.com/IA-para-DEVs-SCTEC-T2/mini-projeto-tokemize.git
cd mini-projeto-tokemize

# 2. Crie e ative um ambiente virtual
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# 3. Instale o projeto em modo editável com dependências de desenvolvimento
pip install -e ".[dev]"
```

Após a instalação, os comandos `tokemize` e `toke` estarão disponíveis no terminal.

---

## Instalação de Dependências

As dependências estão declaradas no `pyproject.toml`:

- **Produção:** `pip install -e .`
- **Desenvolvimento (inclui pytest, hypothesis, pytest-cov):** `pip install -e ".[dev]"`

Não use `requirements.txt` — o `pyproject.toml` é a fonte de verdade.

---

## Rodando a CLI Localmente

```bash
# Analisar o repositório atual e gerar prompt
tokemize toke "corrija o fluxo de login" --repo .

# Exibir o prompt no terminal em vez de copiar para clipboard
tokemize toke "explique a autenticação" --repo . --print

# Salvar o prompt em arquivo
tokemize prepare ./meu-projeto "adicione paginação" --output prompt.md
```

---

## Nomenclatura de Branches

### Formato obrigatório

```
<tipo>/<descricao-em-kebab-case>
```

### Tipos permitidos

| Tipo       | Quando usar                                              | PR deve apontar para |
|------------|----------------------------------------------------------|----------------------|
| `feature`  | Nova funcionalidade                                      | `develop`            |
| `fix`      | Correção de bug                                          | `develop`            |
| `refactor` | Refatoração de código sem mudança de comportamento       | `develop`            |
| `docs`     | Documentação                                             | `develop`            |
| `chore`    | Tarefas de build, configuração, dependências             | `develop`            |
| `hotfix`   | Correção urgente em produção                             | `main`               |

### Regras

- Apenas letras minúsculas, números e hífens na descrição
- Comprimento total: mínimo **5** e máximo **50** caracteres
- As branches `main`, `master` e `develop` são protegidas

### Exemplos

```
✅ feature/user-authentication
✅ fix/null-pointer-on-login
✅ refactor/extract-token-service
✅ docs/update-contributing-guide
✅ hotfix/critical-payment-error

❌ Feature/UserAuth         (maiúsculas não permitidas)
❌ minha-branch             (sem prefixo de tipo)
❌ feature/x                (muito curto)
❌ feature/NOVA_FUNCIONALIDADE  (underscores e maiúsculas)
```

---

## Fluxo de Branches (Gitflow)

```
feature/*  ──┐
fix/*      ──┤──► develop ──► main
refactor/* ──┤
docs/*     ──┘
chore/*    ──┘

hotfix/*   ──────────────────► main
```

- Branches `feature/*`, `fix/*`, `refactor/*`, `docs/*` e `chore/*` **só podem abrir PR para `develop`**
- A branch `develop` **só pode abrir PR para `main`**
- Branches `hotfix/*` **só podem abrir PR para `main`**

---

## Commits Semânticos

Este projeto segue o padrão [Conventional Commits](https://www.conventionalcommits.org/). Todos os commits são validados automaticamente pelo `commitlint` via GitHub Actions.

### Formato obrigatório

```
<tipo>(<escopo opcional>): <descrição curta>
```

### Tipos permitidos

| Tipo       | Quando usar                                                        |
|------------|--------------------------------------------------------------------|
| `feat`     | Adição de nova funcionalidade                                      |
| `fix`      | Correção de bug                                                    |
| `docs`     | Alterações apenas em documentação                                  |
| `style`    | Formatação, ponto e vírgula, espaços — sem mudança de lógica       |
| `refactor` | Refatoração de código sem adicionar feature ou corrigir bug        |
| `test`     | Adição ou correção de testes                                       |
| `chore`    | Tarefas de build, configuração, dependências — sem mudança no src  |
| `perf`     | Melhoria de performance                                            |
| `ci`       | Mudanças em arquivos de CI/CD                                      |
| `revert`   | Reversão de um commit anterior                                     |

### Regras

- A descrição deve estar em **letras minúsculas**
- Sem ponto final no final da descrição
- Use o imperativo: "add", "fix", "update" — não "added", "fixed", "updated"
- Máximo recomendado de 72 caracteres na linha do assunto

### Exemplos

```
✅ feat: add token optimization pipeline
✅ fix: handle null context on LLM request
✅ docs: add contributing guide
✅ refactor: extract context selector to separate module
✅ chore: update commitlint dependencies
✅ feat(parser): add kotlin grammar support

❌ Added new feature          (sem tipo, verbo no passado)
❌ feat: Added new feature.   (verbo no passado e ponto final)
❌ WIP                        (não descritivo)
❌ fix stuff                  (sem tipo)
```

### Breaking Changes

Para mudanças que quebram compatibilidade:

```
feat!: redesign context selection API

BREAKING CHANGE: select_relevant_artifacts() agora requer top_n como argumento obrigatório.
```

---

## Rodando os Testes

Antes de abrir um PR, garanta que todos os testes passam:

```bash
# Rodar todos os testes
python -m pytest tests/ -v

# Rodar com cobertura
python -m pytest tests/ --cov=src/tokemize --cov-report=term-missing

# Rodar apenas testes de um módulo específico
python -m pytest tests/test_compressor.py -v

# Rodar testes rápidos (sem hypothesis)
python -m pytest tests/ -v -m "not slow"
```

**Regras de teste:**
- Novos módulos devem ter testes correspondentes em `tests/`.
- Nomeie arquivos de teste como `test_<modulo>.py`.
- Use `pytest` + `hypothesis` para property-based testing quando aplicável.
- Mantenha cobertura acima de 80% nos módulos core.

---

## Como Abrir uma Pull Request

### Passo a passo

1. Crie uma branch a partir de `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/minha-feature
   ```

2. Faça suas alterações e commits semânticos.

3. Rode os testes localmente:
   ```bash
   python -m pytest tests/ -v
   ```

4. Faça push da branch:
   ```bash
   git push -u origin feature/minha-feature
   ```

5. Abra o PR apontando para `develop`.

### O que o PR precisa ter

- [ ] Nome da branch no padrão `tipo/descricao-em-kebab-case`
- [ ] PR apontando para a branch correta (`develop` ou `main` para hotfix)
- [ ] Todos os commits seguindo Conventional Commits
- [ ] Descrição clara do que foi feito e por quê
- [ ] Testes passando (CI verde)
- [ ] Sem arquivos desnecessários (`.env`, `__pycache__`, `.venv`, etc.)
- [ ] Type hints em todas as funções públicas
- [ ] Docstrings no padrão Google Style para funções novas

### Template de PR

O repositório possui um template em `.github/pull_request_template.md` que será carregado automaticamente ao abrir o PR.

---

## Reportando Bugs

Abra uma [Issue](https://github.com/IA-para-DEVs-SCTEC-T2/mini-projeto-tokemize/issues/new) com:

- **Título claro:** descreva o problema em uma frase
- **Passos para reproduzir:** comandos exatos que causam o bug
- **Comportamento esperado:** o que deveria acontecer
- **Comportamento atual:** o que acontece de fato
- **Ambiente:** SO, versão do Python, versão do Tokemize
- **Logs/Traceback:** se aplicável, cole a saída de erro

---

## Sugerindo Melhorias

Abra uma [Issue](https://github.com/IA-para-DEVs-SCTEC-T2/mini-projeto-tokemize/issues/new) com:

- **Título:** `[Sugestão] Descrição breve`
- **Contexto:** qual problema ou limitação motiva a sugestão
- **Proposta:** como você imagina a solução
- **Alternativas consideradas:** outras abordagens possíveis

---

## Estrutura do Projeto

```
mini-projeto-tokemize/
├── src/
│   └── tokemize/
│       ├── core/
│       │   ├── parser/
│       │   │   ├── scanner.py              # Varredura de repositório
│       │   │   ├── tree_sitter_analyzer.py # Extração de artefatos via Tree-sitter
│       │   │   └── repository_analyzer.py  # Orquestração scanner + analyzer
│       │   ├── selector/
│       │   │   └── intelligent_selector.py # Seleção por relevância
│       │   ├── optimizer/
│       │   │   └── compressor.py           # Compactação de contexto
│       │   ├── context_store.py            # Persistência em disco
│       │   └── prompt_builder.py           # Geração do prompt final
│       ├── integrations/
│       │   ├── llm/                        # Clientes de LLM (protocolo + implementações)
│       │   ├── clipboard.py                # Cópia para área de transferência
│       │   └── embeddings/                 # Geração de embeddings (planejado)
│       ├── models/                         # Dataclasses e schemas
│       │   ├── artifact.py
│       │   ├── file_analysis.py
│       │   └── optimized_prompt.py
│       ├── config/                         # Configurações e .env
│       ├── cli.py                          # Entrypoint CLI (Typer)
│       └── orchestrator.py                 # Pipeline legado (7 etapas)
├── tests/                                  # Testes unitários (pytest + hypothesis)
├── docs/                                   # Documentação do projeto
│   ├── architecture.md
│   ├── technologies.md
│   ├── roadmap.md
│   ├── PRD.md
│   └── diagramas/
├── .github/
│   └── workflows/                          # CI/CD (commitlint, branch rules, deploy)
├── pyproject.toml                          # Configuração do projeto e dependências
└── CONTRIBUTING.md                         # Este arquivo
```

### Responsabilidade de cada camada

| Camada | O que faz |
|--------|-----------|
| `core/parser/` | Varre o repositório e extrai artefatos sintáticos |
| `core/selector/` | Seleciona artefatos relevantes para a tarefa |
| `core/optimizer/` | Compacta o contexto selecionado |
| `core/context_store.py` | Persiste o contexto em disco |
| `core/prompt_builder.py` | Monta o prompt Markdown final |
| `integrations/llm/` | Abstração para clientes de LLM |
| `integrations/clipboard.py` | Cópia para área de transferência |
| `models/` | Estruturas de dados compartilhadas entre camadas |
| `cli.py` | Comandos `toke` e `prepare` via Typer |

---

## Convenções de Código

- **Type hints** em todas as funções e classes
- **Docstrings** no padrão Google Style
- **Arquivos:** `snake_case.py`
- **Classes:** `PascalCase`
- **Funções e variáveis:** `snake_case`
- **Constantes:** `UPPER_SNAKE_CASE`
- **Testes:** prefixo `test_` espelhando o módulo (ex: `test_compressor.py`)
- **Variáveis de ambiente:** via `python-dotenv`, nunca hardcoded

---

## Dúvidas?

Abra uma issue ou entre em contato com a equipe pelo repositório do projeto.
