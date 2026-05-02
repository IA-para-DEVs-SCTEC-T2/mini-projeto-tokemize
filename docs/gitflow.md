# Gitflow — Fluxo de Trabalho do Projeto

## Visão Geral

Este projeto adota uma versão simplificada do Gitflow, com duas branches principais e branches de trabalho com prefixos padronizados.

## Branches Principais

| Branch | Propósito |
|---|---|
| `main` | Código em produção. Recebe merges de `develop` e `hotfix/*`. |
| `develop` | Branch de integração. Recebe merges de `feature/*`, `fix/*`, `docs/*` e `refactor/*`. |

## Branches de Trabalho

| Prefixo | Uso | Destino do PR |
|---|---|---|
| `feature/` | Nova funcionalidade | `develop` |
| `fix/` | Correção de bug não crítico | `develop` |
| `docs/` | Documentação | `develop` |
| `refactor/` | Refatoração sem mudança de comportamento | `develop` |
| `hotfix/` | Correção crítica em produção | `main` |
| `chore/` | Tarefas de manutenção (deps, config) | `develop` |

## Fluxo Principal

```
feature/* ──┐
fix/*       ├──► develop ──► main
docs/*      │
refactor/*  ┘

hotfix/* ──────────────────► main
```

### Feature / Fix / Docs / Refactor

1. Crie a branch a partir de `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/nome-da-tarefa
   ```
2. Desenvolva e faça commits seguindo o padrão [Conventional Commits](https://www.conventionalcommits.org/).
3. Abra um Pull Request de `feature/nome-da-tarefa` → `develop`.
4. Após aprovação e merge, delete a branch.

### Release (develop → main)

1. Abra um Pull Request de `develop` → `main`.
2. Descreva as mudanças incluídas no PR.
3. Após aprovação e merge, crie uma tag de versão:
   ```bash
   git tag -a v1.x.0 -m "Release v1.x.0"
   git push origin v1.x.0
   ```

### Hotfix

1. Crie a branch a partir de `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/descricao-do-problema
   ```
2. Corrija o problema e abra um Pull Request de `hotfix/*` → `main`.
3. Após o merge em `main`, faça o backport para `develop`:
   ```bash
   git checkout develop
   git merge main
   git push origin develop
   ```

## Padrão de Nomenclatura de Branches

- Formato: `<prefixo>/<descricao-em-kebab-case>`
- Prefixos permitidos: `feature`, `fix`, `hotfix`, `docs`, `refactor`, `chore`
- Comprimento: mínimo 5, máximo 50 caracteres
- Apenas letras minúsculas, números e hífens na descrição

**Exemplos válidos:**
```
feature/adicionar-autenticacao
fix/corrigir-calculo-tokens
hotfix/vulnerabilidade-xss
docs/atualizar-readme
refactor/extrair-servico-cache
chore/atualizar-dependencias
```

**Exemplos inválidos:**
```
Feature/MinhaFeature   # maiúsculas não permitidas
minha-branch           # sem prefixo
feature/x              # muito curto
```

## Padrão de Commits

Os commits seguem o padrão [Conventional Commits](https://www.conventionalcommits.org/), validado automaticamente via `commitlint`:

```
<tipo>(escopo opcional): descrição curta

feat: adicionar endpoint de autenticação
fix: corrigir cálculo de budget de tokens
docs: atualizar guia de contribuição
refactor: extrair lógica de cache para módulo separado
chore: atualizar versão do tree-sitter
```

## Checklist de Pull Request

Todo PR deve seguir o template em `.github/pull_request_template.md`:

- [ ] A branch segue o padrão correto (`prefixo/descricao`)
- [ ] O PR está apontando para a branch correta (`develop` ou `main`)
- [ ] Testes foram executados
- [ ] Não há arquivos desnecessários

## Validações Automáticas

Os seguintes workflows do GitHub Actions validam o fluxo automaticamente:

| Workflow | Arquivo | O que valida |
|---|---|---|
| Branch Naming Rules | `branch-rules.yml` | Formato e prefixo da branch |
| Gitflow Rules | `gitflow-rules.yml` | Branch de destino do PR |
| Commitlint | `commitlint.yml` | Formato das mensagens de commit |
