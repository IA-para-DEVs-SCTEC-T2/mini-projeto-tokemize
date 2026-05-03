# Git & PR Workflow

## Abrindo Pull Requests

**SEMPRE** usar `--body-file` ao criar PRs com `gh pr create`. Nunca usar `--body` com texto inline — o bash quebra o conteúdo com escapes e caracteres inválidos.

### Procedimento obrigatório

1. Escrever o body do PR em um arquivo temporário
2. Usar `--body-file` apontando para esse arquivo
3. Deletar o arquivo temporário após o PR ser criado

```bash
# 1. Escrever o body em arquivo temporário
$prBody = @"
## Summary

Descrição do PR aqui.

## Changes

- item 1
- item 2

## Testing

```
pytest tests/ -v
```
"@
$prBody | Out-File -FilePath "pr_body.md" -Encoding utf8

# 2. Criar o PR com --body-file
gh pr create --base develop --head feature/minha-branch --title "feat: minha feature" --body-file pr_body.md

# 3. Limpar o arquivo temporário
Remove-Item pr_body.md
```

## Branch Naming

Seguir o padrão do workflow `branch-rules.yml`:
- Formato: `{prefix}/{nome-kebab-case}`
- Prefixos permitidos: `chore`, `feature`, `fix`, `hotfix`, `docs`, `refactor`
- Exemplos: `feature/groq-llm-integration`, `fix/cache-invalidation`

## Commit Messages

Seguir Conventional Commits (validado pelo `commitlint.yml`):
- `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
- Exemplo: `feat: add GroqClient integration with LLMClientProtocol`

## Target Branch

- PRs devem apontar para `develop` por padrão, nunca para `main`/`master` diretamente
