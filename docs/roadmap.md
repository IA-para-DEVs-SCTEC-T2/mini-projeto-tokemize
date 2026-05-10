# Roadmap

Este documento apresenta o progresso atual dos modulos do Tokemize e os proximos passos planejados.

---

## Status dos Modulos

| Modulo | Descricao | Status |
|---|---|---|
| **Repository Analyzer** | Analise do repositorio e extracao de artefatos | Concluido |
| **Intelligent Selector** | Selecao dos artefatos mais relevantes para a tarefa | Concluido |
| **Compressor** | Compactacao do contexto selecionado | Concluido |
| **Context Store** | Persistencia local do contexto compacto | Concluido |
| **Prompt Builder** | Geracao do prompt otimizado em Markdown | Concluido |
| **Clipboard/Output** | Copia, impressao ou escrita do prompt gerado | Concluido |
| **Indexer** | Indexacao vetorial para busca semantica | Planejado |
| **Embeddings** | Geracao de embeddings para melhorar selecao futura | Planejado |

---

## Fases

### Fase 1 - Fundacao

- [x] Definicao da arquitetura e dos componentes
- [x] Criacao da estrutura do repositorio
- [x] Configuracao de CI/CD (commitlint, branch rules, gitflow)
- [x] Analise do repositorio e extracao de artefatos

### Fase 2 - Pipeline Local de Contexto

- [x] Selecao de artefatos relevantes por tarefa
- [x] Compactacao do contexto selecionado
- [x] Persistencia local em `.tokemize/context/`
- [x] Geracao de prompt otimizado
- [x] Copia para area de transferencia, impressao e escrita em arquivo

### Fase 3 - Qualidade da Otimizacao

- [ ] Indexacao vetorial com FAISS
- [ ] Embeddings para ranqueamento semantico
- [ ] Heuristicas de reducao de contexto por budget de tokens
- [ ] Benchmarks de tamanho, relevancia e tempo de execucao

### Fase 4 - Produto Final

- [ ] Documentacao de uso e exemplos para desenvolvedores
- [ ] Testes de integracao de ponta a ponta
- [ ] Empacotamento e distribuicao da CLI
- [ ] Dashboard do projeto atualizado no GitHub Pages

---

## Legenda

| Status | Significado |
|---|---|
| Concluido | Modulo implementado |
| Em desenvolvimento | Modulo em evolucao |
| Planejado | Modulo ainda nao implementado |
