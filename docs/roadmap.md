# Roadmap

Este documento apresenta o progresso atual dos módulos do Tokemize e os próximos passos planejados.

---

## Status dos Módulos

| Módulo | Descrição | Status |
|---|---|---|
| **Parser** | Análise sintática do repositório com Tree-sitter | ✅ Concluído |
| **Selector** | Seleção semântica dos trechos mais relevantes | 🔄 Em desenvolvimento |
| **Indexer** | Indexação vetorial com FAISS | 🔲 Planejado |
| **Optimizer** | Compressão e resumo semântico do contexto | 🔲 Planejado |
| **LLM Integration** | Integração com OpenAI, Anthropic e Groq | 🔲 Planejado |
| **Embeddings** | Geração de embeddings multi-provedor | 🔲 Planejado |

---

## Fases

### Fase 1 — Fundação ✅

- [x] Definição da arquitetura e dos componentes
- [x] Criação da estrutura do repositório
- [x] Configuração de CI/CD (commitlint, branch rules, gitflow)
- [x] Parser: mapeamento e análise sintática do código-fonte

### Fase 2 — Núcleo Semântico 🔄

- [x] Selector: busca semântica por trechos relevantes *(em desenvolvimento)*
- [ ] Indexer: geração e armazenamento de embeddings com FAISS
- [ ] Embeddings: módulo de geração de embeddings multi-provedor

### Fase 3 — Otimização e Integração 🔲

- [ ] Optimizer: compressão e resumo semântico do contexto selecionado
- [ ] LLM Integration: integração com OpenAI, Anthropic e Groq
- [ ] Cache de contexto para consultas repetitivas

### Fase 4 — Produto Final 🔲

- [ ] CLI ou SDK público para integração com ferramentas externas
- [ ] Documentação de uso e exemplos para desenvolvedores
- [ ] Testes de integração e benchmarks de custo/qualidade

---

## Legenda

| Símbolo | Significado |
|---|---|
| ✅ | Concluído |
| 🔄 | Em desenvolvimento |
| 🔲 | Planejado |
