# Tecnologias Utilizadas

Este documento descreve a stack tecnologica do Tokemize, com justificativas para cada escolha.

---

## Back-end / CLI

### Python 3

- **Papel:** linguagem principal do projeto, responsavel pela CLI e pela orquestracao do pipeline de contexto.
- **Justificativa:** sintaxe expressiva, suporte nativo a tipos com anotacoes e bom ecossistema para analise de codigo, automacao e processamento textual.
- **Documentacao:** https://docs.python.org/3/

### Typer

- **Papel:** construcao dos comandos `tokemize` e `toke`.
- **Justificativa:** cria CLIs tipadas e simples de manter a partir de funcoes Python.
- **Documentacao:** https://typer.tiangolo.com/

### pyperclip

- **Papel:** copia do prompt otimizado para a area de transferencia.
- **Justificativa:** reduz atrito no fluxo de uso, permitindo colar o prompt diretamente no chatbot da IDE.
- **Documentacao:** https://pyperclip.readthedocs.io/

---

## Analise de Codigo

### Tree-sitter

- **Papel:** analise sintatica (parsing) do codigo-fonte dos repositorios.
- **Justificativa:** biblioteca de parsing incremental e eficiente que suporta dezenas de linguagens de programacao. Gera uma AST precisa, permitindo extrair simbolos, funcoes e estruturas sem depender apenas de heuristicas de texto.
- **Documentacao:** https://tree-sitter.github.io/tree-sitter/

---

## Indexacao e Busca Semantica

### FAISS

- **Papel:** tecnologia planejada para indexacao vetorial e busca semantica eficiente sobre embeddings gerados a partir do codigo.
- **Justificativa:** biblioteca open-source da Meta AI, otimizada para buscas de vizinhanca em espacos de alta dimensao. Pode ajudar a encontrar trechos de codigo similares a tarefa do usuario em tempo sub-linear.
- **Documentacao:** https://faiss.ai/index.html

---

## Otimizacao de Contexto

### Pipeline local

- **Papel:** analisar repositorio, selecionar artefatos, compactar contexto, salvar o contexto e gerar o prompt final.
- **Justificativa:** mantem o Tokemize independente de provedores de LLM. O usuario escolhe onde usar o prompt otimizado depois que ele e gerado.

---

## Showcase / Dashboard

### Vanilla JavaScript (ES Modules)

- **Papel:** front-end do dashboard do projeto (GitHub Pages).
- **Justificativa:** sem dependencia de framework, com manutencao simples e carregamento rapido.

### Vitest

- **Papel:** framework de testes unitarios do showcase.
- **Documentacao:** https://vitest.dev/

### fast-check

- **Papel:** biblioteca de property-based testing usada nos testes do showcase.
- **Documentacao:** https://fast-check.io/

---

## Qualidade e CI/CD

| Ferramenta | Proposito |
|---|---|
| GitHub Actions | Pipelines de CI/CD (validacao de branches, commits, metricas) |
| commitlint | Validacao de commits semanticos (Conventional Commits) |
| Gitflow | Estrategia de branches (`feature`, `fix`, `docs`, `hotfix`) |
