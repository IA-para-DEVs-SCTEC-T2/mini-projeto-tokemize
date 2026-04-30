# Guia de Contribuição

Este documento descreve as convenções de **nomenclatura de branches** e **commits semânticos** adotadas neste projeto. Essas regras são validadas automaticamente por workflows do GitHub Actions em todo Pull Request — descumpri-las bloqueia o merge.

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
| `hotfix`   | Correção urgente em produção                             | `main`               |

### Regras adicionais

- Apenas letras minúsculas, números e hífens na descrição
- Comprimento total: mínimo **5** e máximo **50** caracteres
- As branches `main`, `master` e `develop` são ignoradas pela validação (são branches base)

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

hotfix/*   ──────────────────► main
```

- Branches `feature/*`, `fix/*`, `refactor/*` e `docs/*` **só podem abrir PR para `develop`**
- A branch `develop` **só pode abrir PR para `main`**
- Branches `hotfix/*` **só podem abrir PR para `main`**

---

## Commits Semânticos

Este projeto segue o padrão [Conventional Commits](https://www.conventionalcommits.org/). Todos os commits de um PR são validados automaticamente pelo `commitlint`.

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
✅ feat(auth): add JWT validation middleware
✅ fix(cache): prevent stale context on repeated queries

❌ Added new feature          (sem tipo, verbo no passado)
❌ feat: Added new feature.   (verbo no passado e ponto final)
❌ WIP                        (não descritivo)
❌ fix stuff                  (sem tipo)
```

### Breaking Changes

Para mudanças que quebram compatibilidade, adicione `!` após o tipo ou inclua `BREAKING CHANGE:` no rodapé:

```
feat!: redesign context selection API

BREAKING CHANGE: the `selectContext()` function now requires an options object as second argument.
```

---

## Checklist antes de abrir um PR

- [ ] O nome da branch segue o padrão `tipo/descricao-em-kebab-case`
- [ ] O PR está apontando para a branch correta conforme o Gitflow
- [ ] Todos os commits seguem o padrão Conventional Commits
- [ ] Não há arquivos desnecessários no commit (`.env`, arquivos de build, etc.)
