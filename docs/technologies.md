# Tecnologias Utilizadas

Este documento descreve a stack tecnológica do Tokemize, com justificativas para cada escolha.

---

## Back-end / Orquestração

### Python 3

- **Papel:** linguagem principal do projeto, responsável pela orquestração de todos os módulos.
- **Justificativa:** ecossistema rico para IA/ML (bibliotecas como FAISS, transformers, openai), sintaxe expressiva e suporte nativo a tipos com anotações.
- **Documentação:** https://docs.python.org/3/

---

## Análise de Código

### Tree-sitter

- **Papel:** análise sintática (parsing) do código-fonte dos repositórios.
- **Justificativa:** biblioteca de parsing incremental e eficiente que suporta dezenas de linguagens de programação. Gera uma AST (Abstract Syntax Tree) precisa, permitindo extrair símbolos, funções e estruturas sem depender de heurísticas de texto.
- **Documentação:** https://tree-sitter.github.io/tree-sitter/

---

## Indexação e Busca Semântica

### FAISS

- **Papel:** indexação vetorial e busca semântica eficiente sobre os embeddings gerados a partir do código.
- **Justificativa:** biblioteca open-source da Meta AI, otimizada para buscas de vizinhança em espaços de alta dimensão. Permite encontrar trechos de código semanticamente similares à query do usuário em tempo sub-linear.
- **Documentação:** https://faiss.ai/index.html

---

## Integrações com LLMs

### OpenAI API

- **Papel:** provedor de LLM (ex.: GPT-4, GPT-3.5) e de embeddings (ex.: `text-embedding-ada-002`).
- **Documentação:** https://platform.openai.com/docs

### Anthropic API

- **Papel:** provedor de LLM alternativo (ex.: Claude).
- **Documentação:** https://docs.anthropic.com

### Groq

- **Papel:** provedor de inferência de alta velocidade com modelos open-source (ex.: LLaMA 3, Mixtral).
- **Justificativa:** latência ultra-baixa via hardware LPU, útil para casos em que velocidade de resposta é crítica.
- **Documentação:** https://console.groq.com/docs/overview

---

## Showcase / Dashboard

### Vanilla JavaScript (ES Modules)

- **Papel:** front-end do dashboard do projeto (GitHub Pages).
- **Justificativa:** sem dependência de framework — manutenção simples e carregamento rápido.

### Vitest

- **Papel:** framework de testes unitários do showcase.
- **Documentação:** https://vitest.dev/

### fast-check

- **Papel:** biblioteca de property-based testing usada nos testes do showcase.
- **Documentação:** https://fast-check.io/

---

## Qualidade e CI/CD

| Ferramenta | Propósito |
|---|---|
| GitHub Actions | Pipelines de CI/CD (validação de branches, commits, métricas) |
| commitlint | Validação de commits semânticos (Conventional Commits) |
| Gitflow | Estratégia de branches (`feature`, `fix`, `docs`, `hotfix`) |
