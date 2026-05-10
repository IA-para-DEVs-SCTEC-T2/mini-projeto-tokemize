# Arquitetura do Tokemize

## Visao Geral

O Tokemize é uma ferramenta de **Otimização de Contexto para LLMs**. Ele analisa um repositório local, seleciona os artefatos relevantes para uma tarefa técnica, compacta esse material e gera um prompt Markdown pronto para uso em chatbots de IDE ou outros LLMs.

O projeto nao atua mais como agente e nao executa chamada direta a provedores de LLM. A responsabilidade do Tokemize termina na preparacao do contexto e do prompt.

```
Usuario ──► Tokemize CLI ──► Analise ──► Selecao ──► Compactacao ──► Prompt otimizado
```

---

## Fluxo da Arquitetura

```
┌─────────┐     tarefa      ┌──────────────────────────────────────────┐
│ Usuario │ ─────────────► │                 Tokemize                 │
└─────────┘   + repo_path   │                                          │
                             │  ┌────────────────────┐                 │
                             │  │ Repository Analyzer│                 │
                             │  └─────────┬──────────┘                 │
                             │            │ artefatos do repositorio    │
                             │  ┌─────────▼──────────┐                 │
                             │  │ Intelligent Selector│                 │
                             │  └─────────┬──────────┘                 │
                             │            │ artefatos relevantes        │
                             │  ┌─────────▼──────────┐                 │
                             │  │     Compressor     │                 │
                             │  └─────────┬──────────┘                 │
                             │            │ contexto compacto           │
                             │  ┌─────────▼──────────┐                 │
                             │  │   Context Store    │                 │
                             │  └─────────┬──────────┘                 │
                             │            │ referencia local            │
                             │  ┌─────────▼──────────┐                 │
                             │  │   Prompt Builder   │                 │
                             │  └─────────┬──────────┘                 │
                             └────────────┼─────────────────────────────┘
                                          │ prompt otimizado
                             ┌────────────▼────────────┐
                             │ Clipboard / print / file │
                             └──────────────────────────┘
```

---

## Componentes

### 1. Repository Analyzer

Responsavel por mapear e analisar a estrutura do repositorio, extraindo metadados e artefatos relevantes dos arquivos.

- **Entrada:** caminho do repositorio
- **Saida:** analises de arquivos e artefatos estruturados
- **Status:** Concluido

### 2. Intelligent Selector

Recebe a descricao da tarefa e seleciona os artefatos mais relevantes entre os itens analisados.

- **Entrada:** analises do repositorio + descricao da tarefa
- **Saida:** artefatos relevantes para a tarefa
- **Status:** Concluido

### 3. Compressor

Compacta os artefatos selecionados em um contexto menor e mais facil de usar dentro de limites de tokens.

- **Entrada:** artefatos relevantes
- **Saida:** contexto compacto
- **Status:** Concluido

### 4. Context Store

Persiste o contexto compacto em `.tokemize/context/` quando possivel. Essa etapa e nao fatal: se a gravacao falhar, o prompt ainda pode ser gerado.

- **Entrada:** contexto compacto + descricao da tarefa + caminho do repositorio
- **Saida:** caminho do arquivo de contexto salvo
- **Status:** Concluido

### 5. Prompt Builder

Monta o prompt Markdown final com a tarefa, o contexto compacto e a referencia ao arquivo de contexto salvo.

- **Entrada:** contexto compacto + descricao da tarefa + caminho opcional do contexto
- **Saida:** prompt otimizado
- **Status:** Concluido

### 6. Clipboard / Output

Copia o prompt para a area de transferencia e, opcionalmente, imprime no terminal ou salva em arquivo.

- **Entrada:** prompt otimizado
- **Saida:** prompt disponivel para uso externo
- **Status:** Concluido

---

## Cache e Reuso de Contexto

O armazenamento local do contexto compacto permite auditoria, reuso e comparacao entre execucoes. Evolucoes futuras podem ampliar esse mecanismo para evitar recomputacao em tarefas repetitivas ou similares.

---

## Estrutura de Diretorios

```
mini-projeto-tokemize/
├── src/
│   └── tokemize/          # Codigo-fonte principal (Python)
├── tests/                 # Testes automatizados
├── docs/
│   ├── architecture.md    # Este arquivo
│   ├── technologies.md    # Stack e decisoes tecnicas
│   ├── roadmap.md         # Progresso e proximos passos
│   └── showcase/          # GitHub Pages - dashboard do projeto
└── pyproject.toml         # Configuracao do projeto Python
```
