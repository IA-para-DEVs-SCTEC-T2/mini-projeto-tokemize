# PRD — Product Requirements Document

## Tokemize: Otimização de Contexto para LLMs

**Versão:** 1.0  
**Data:** 2025-05-13  
**Equipe:** Eneri da Costa Junior, Guilherme Valerio Mertens, Paulo Sergio, Samuel Magalhães Marques, Eduardo Notari

---

## 1. Visão Geral

O Tokemize é uma ferramenta de linha de comando que analisa repositórios de código-fonte e gera prompts otimizados para uso em chatbots de IDE e outras interfaces com LLMs. Ele atua como um pipeline local de otimização de contexto, entregando ao desenvolvedor apenas a informação relevante para uma tarefa técnica específica.

O Tokemize **não** chama provedores de LLM nem retorna respostas geradas por IA. Seu produto final é um prompt Markdown compacto, pronto para ser colado no chatbot da IDE escolhida pelo usuário.

---

## 2. Problema

Ferramentas de desenvolvimento assistidas por LLM sofrem com:

| Problema | Consequência |
|----------|-------------|
| Contexto excessivo enviado ao modelo | Alto custo de tokens por requisição |
| Informação irrelevante no prompt | Respostas imprecisas e alucinações |
| Falta de critério na seleção de contexto | Processamento ineficiente |
| Prompts longos e não reproduzíveis | Dificuldade de revisão e auditoria |

**Premissa central:** mais contexto não significa melhor resposta. A qualidade da resposta de um LLM depende diretamente da relevância e concisão do contexto fornecido.

---

## 3. Personas

### 3.1 Desenvolvedor Individual

- Usa chatbots de IDE (Kiro, Copilot, Cursor, Windsurf) no dia a dia.
- Precisa de respostas precisas sem gastar tempo montando prompts manualmente.
- Quer reduzir custo de tokens em planos pagos de LLM.

### 3.2 Tech Lead / Arquiteto

- Precisa garantir que o contexto enviado ao LLM seja auditável e reproduzível.
- Quer padronizar a forma como a equipe interage com ferramentas de IA.
- Valoriza rastreabilidade (contexto salvo em disco para comparação).

### 3.3 Equipe de Engenharia

- Trabalha em repositórios grandes com múltiplas linguagens.
- Precisa de uma ferramenta que funcione sem configuração complexa.
- Quer integrar otimização de contexto no workflow existente sem atrito.

---

## 4. Público-Alvo

Desenvolvedores e equipes de engenharia de software que utilizam agentes de IA ou chatbots de IDE no desenvolvimento e precisam:

- Reduzir custo de tokens por interação.
- Aumentar a precisão e relevância das respostas do LLM.
- Manter auditabilidade sobre o contexto enviado.
- Automatizar a preparação de prompts técnicos.

---

## 5. Funcionalidades Principais

### 5.1 Repository Analyzer

**O que faz:** Varre recursivamente um repositório local, identifica arquivos de código-fonte suportados e extrai artefatos sintáticos (funções, classes, métodos, imports) usando Tree-sitter.

**Linguagens suportadas:** Python, Java, JavaScript, TypeScript.

**Comportamento:**
- Ignora diretórios irrelevantes (`.git`, `node_modules`, `__pycache__`, `.venv`, etc.).
- Arquivos com linguagem não suportada recebem `artifacts=[]` sem erro.
- Coleta metadados: caminho, linguagem, tamanho, número de linhas.

---

### 5.2 Intelligent Selector

**O que faz:** Recebe a descrição da tarefa e a lista de artefatos extraídos, pontua cada artefato por relevância e retorna os N mais relevantes.

**Algoritmo de scoring:**
- +3 pontos se o token da tarefa aparece no nome do artefato.
- +2 pontos se aparece no caminho do arquivo.
- +1 ponto se aparece nas primeiras 200 caracteres do conteúdo.

**Fallback:** Se nenhum artefato pontuar acima de zero, retorna artefatos dos arquivos com maior número de artefatos.

---

### 5.3 Compressor

**O que faz:** Agrupa os artefatos selecionados por arquivo e gera um bloco Markdown compacto com tipo, nome e linhas de cada artefato.

**Saída:** `CompressedContext` com conteúdo Markdown, contagem de tokens e contagem de artefatos.

---

### 5.4 Context Store

**O que faz:** Persiste o contexto compacto em `.tokemize/context/<slug>-<YYYYMMDD>.md` dentro do repositório analisado.

**Comportamento:**
- Etapa não-fatal: falhas de I/O são capturadas e o pipeline continua.
- Gera slug normalizado a partir da descrição da tarefa (max 40 chars).
- Permite auditoria e reuso entre sessões.

---

### 5.5 Prompt Builder

**O que faz:** Monta o prompt final em Markdown estruturado com seções: Tarefa, Objetivo, Contexto Relevante, Instrução para a IDE e Arquivo de Contexto.

**Saída:** `OptimizedPrompt` com conteúdo completo, descrição da tarefa e estimativa de tokens.

---

### 5.6 Clipboard / Output

**O que faz:** Copia o prompt gerado para a área de transferência do sistema operacional. Opcionalmente imprime no terminal ou salva em arquivo.

**Fallback:** Se a cópia para clipboard falhar, informa o usuário e sugere `--print` ou `--output`.

---

## 6. Fluxo de Uso do Sistema

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FLUXO DO USUÁRIO                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Usuário executa:                                                 │
│     $ tokemize toke "corrija o fluxo de login" --repo .              │
│                                                                      │
│  2. CLI valida entradas (path existe? task >= 3 chars?)              │
│                                                                      │
│  3. Repository Analyzer varre o repositório                          │
│     → Extrai artefatos via Tree-sitter                               │
│                                                                      │
│  4. Intelligent Selector pontua e seleciona artefatos relevantes     │
│     → Retorna top 5 por score                                        │
│                                                                      │
│  5. Compressor agrupa e compacta em Markdown                         │
│     → Gera CompressedContext                                         │
│                                                                      │
│  6. Context Store salva em .tokemize/context/ (não-fatal)            │
│                                                                      │
│  7. Prompt Builder monta prompt final estruturado                    │
│                                                                      │
│  8. Clipboard copia o prompt para área de transferência               │
│                                                                      │
│  9. Usuário cola o prompt no chatbot da IDE                          │
│     → LLM recebe apenas contexto relevante                           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7. Requisitos Técnicos e Restrições

| Requisito | Especificação |
|-----------|--------------|
| Linguagem | Python 3.11+ |
| Parsing | Tree-sitter com grammars para Python, Java, JS, TS |
| CLI Framework | Typer 0.12.x |
| Clipboard | pyperclip >= 1.8.2 |
| Testes | pytest 8.x + hypothesis |
| SO suportados | Windows, macOS, Linux |
| Dependência de rede | Nenhuma (pipeline 100% local) |
| Dependência de LLM | Nenhuma (não faz chamadas a provedores) |

**Restrições:**
- O pipeline deve executar inteiramente offline.
- Nenhum dado do repositório deve ser enviado para serviços externos.
- O tempo de execução do pipeline deve ser aceitável para repositórios de até 10.000 arquivos.
- Variáveis sensíveis nunca devem ser hardcoded.

---

## 8. Requisitos Funcionais

| ID | Requisito | Prioridade |
|----|-----------|-----------|
| RF-01 | O sistema deve aceitar um caminho de repositório e uma descrição de tarefa como entrada | Alta |
| RF-02 | O sistema deve varrer recursivamente o repositório ignorando diretórios irrelevantes | Alta |
| RF-03 | O sistema deve extrair artefatos sintáticos (funções, classes, métodos, imports) via Tree-sitter | Alta |
| RF-04 | O sistema deve suportar Python, Java, JavaScript e TypeScript | Alta |
| RF-05 | O sistema deve selecionar os artefatos mais relevantes com base na descrição da tarefa | Alta |
| RF-06 | O sistema deve compactar os artefatos selecionados em formato Markdown | Alta |
| RF-07 | O sistema deve persistir o contexto compacto em `.tokemize/context/` | Média |
| RF-08 | O sistema deve gerar um prompt Markdown estruturado com seções padronizadas | Alta |
| RF-09 | O sistema deve copiar o prompt para a área de transferência | Alta |
| RF-10 | O sistema deve permitir impressão do prompt no terminal via `--print` | Média |
| RF-11 | O sistema deve permitir salvar o prompt em arquivo via `--output` | Média |
| RF-12 | O sistema deve validar que o caminho do repositório existe e é um diretório | Alta |
| RF-13 | O sistema deve validar que a descrição da tarefa tem pelo menos 3 caracteres | Alta |
| RF-14 | O sistema deve exibir progresso das etapas durante a execução | Baixa |
| RF-15 | O sistema deve tratar arquivos com linguagem não suportada sem propagar exceção | Alta |

---

## 9. Requisitos Não Funcionais

| ID | Requisito | Métrica |
|----|-----------|---------|
| RNF-01 | **Performance:** O pipeline deve completar em menos de 30 segundos para repositórios com até 1.000 arquivos | Tempo de execução medido com `time.perf_counter()` |
| RNF-02 | **Confiabilidade:** Falhas em etapas não-fatais (Context Store) não devem interromper o pipeline | Zero crashes por falha de I/O no Context Store |
| RNF-03 | **Portabilidade:** A CLI deve funcionar em Windows, macOS e Linux sem alteração de código | Testes passando nos 3 SOs |
| RNF-04 | **Manutenibilidade:** Código com type hints em todas as funções e docstrings Google Style | 100% de cobertura de type hints em funções públicas |
| RNF-05 | **Extensibilidade:** Novas linguagens devem ser adicionáveis sem alterar o pipeline principal | Apenas adição de grammar + extrator no TreeSitterAnalyzer |
| RNF-06 | **Segurança:** Nenhum dado do repositório deve ser transmitido para serviços externos | Zero chamadas de rede durante execução |
| RNF-07 | **Usabilidade:** O usuário deve conseguir gerar um prompt com um único comando | Máximo 1 comando para fluxo completo |
| RNF-08 | **Testabilidade:** Cobertura de testes unitários acima de 80% nos módulos core | Medido via pytest-cov |

---

## 10. Regras de Negócio

| ID | Regra |
|----|-------|
| RN-01 | O Tokemize nunca envia dados para provedores de LLM ou serviços externos |
| RN-02 | O número máximo de artefatos selecionados é configurável (padrão: 5) |
| RN-03 | Artefatos com score zero só são retornados no fallback (quando todos pontuam zero) |
| RN-04 | O Context Store é não-fatal: falhas de persistência geram aviso, não erro |
| RN-05 | O slug do arquivo de contexto é limitado a 40 caracteres |
| RN-06 | Diretórios como `.git`, `node_modules`, `__pycache__`, `.venv` são sempre ignorados |
| RN-07 | A descrição da tarefa deve ter no mínimo 3 caracteres após trim |
| RN-08 | O prompt gerado inclui referências no formato Kiro/Cursor (`#[[file:...]]`) e Copilot/Windsurf (`@...`) quando o contexto é salvo em disco |
| RN-09 | Arquivos com extensão não suportada pelo Tree-sitter são incluídos na estrutura com `artifacts=[]` |
| RN-10 | O pipeline deve ser determinístico: mesma entrada produz mesma saída (sort estável no selector) |

---

## 11. Critérios de Aceite por Funcionalidade

### 11.1 Repository Analyzer

| # | Critério |
|---|----------|
| CA-01 | Dado um repositório válido, retorna lista de `FileAnalysis` com artefatos extraídos |
| CA-02 | Diretórios da lista de ignore (`DEFAULT_IGNORE_DIRS`) não são varridos |
| CA-03 | Arquivos `.py`, `.java`, `.js`, `.ts` têm artefatos extraídos corretamente |
| CA-04 | Arquivos com extensão não suportada retornam `language="unknown"` e `artifacts=[]` |
| CA-05 | Symlinks recursivos não causam loop infinito |

### 11.2 Intelligent Selector

| # | Critério |
|---|----------|
| CA-06 | Dado uma tarefa e artefatos, retorna no máximo `top_n` artefatos com score > 0 |
| CA-07 | Se todos os scores forem zero, aplica fallback retornando artefatos dos arquivos com mais artefatos |
| CA-08 | A ordenação é estável (determinística em empates) |
| CA-09 | Tokens com menos de 2 caracteres são filtrados da tokenização |
| CA-10 | Acentos são normalizados antes da comparação |

### 11.3 Compressor

| # | Critério |
|---|----------|
| CA-11 | Dado uma lista de artefatos, retorna `CompressedContext` com Markdown agrupado por arquivo |
| CA-12 | Lista vazia retorna mensagem de fallback e contagens zeradas |
| CA-13 | O `token_count` é calculado como `len(compressed_content.split())` |
| CA-14 | Cada artefato aparece com tipo, nome e intervalo de linhas |

### 11.4 Context Store

| # | Critério |
|---|----------|
| CA-15 | Cria o diretório `.tokemize/context/` se não existir |
| CA-16 | Gera arquivo com nome `<slug>-<YYYYMMDD>.md` |
| CA-17 | Retorna o caminho relativo do arquivo salvo |
| CA-18 | Retorna `None` em caso de falha de I/O sem propagar exceção |
| CA-19 | O slug não contém caracteres especiais, apenas `[a-z0-9-]` |

### 11.5 Prompt Builder

| # | Critério |
|---|----------|
| CA-20 | O prompt contém as seções: Tarefa, Objetivo, Contexto Relevante, Instrução para a IDE |
| CA-21 | Quando `context_file_path` é fornecido, inclui seção "Arquivo de contexto" com referências nos formatos Kiro/Cursor e Copilot/Windsurf |
| CA-22 | A `task_description` é preservada verbatim no prompt |
| CA-23 | O `token_estimate` é calculado como `len(content.split())` |

### 11.6 Clipboard / Output

| # | Critério |
|---|----------|
| CA-24 | O prompt é copiado para a área de transferência com sucesso |
| CA-25 | Se o clipboard falhar, exibe aviso e sugere `--print` ou `--output` |
| CA-26 | Com `--print`, o prompt é exibido no stdout |
| CA-27 | Com `--output <path>`, o prompt é salvo no arquivo especificado |
| CA-28 | Diretórios intermediários do `--output` são criados automaticamente |

### 11.7 CLI (Validação)

| # | Critério |
|---|----------|
| CA-29 | Caminho inexistente retorna exit code 1 com mensagem de erro |
| CA-30 | Caminho que não é diretório retorna exit code 1 |
| CA-31 | Descrição vazia ou com menos de 3 caracteres retorna exit code 1 |
| CA-32 | Falha em etapa fatal retorna exit code 2 |

---

## 12. Próximos Passos / Roadmap

### Fase 3 — Qualidade da Otimização (Planejado)

| Item | Descrição |
|------|-----------|
| Indexação vetorial | Integrar FAISS para busca semântica sobre embeddings do código |
| Embeddings | Gerar embeddings via API (OpenAI text-embedding ou equivalente) para ranqueamento semântico |
| Budget de tokens | Implementar heurísticas de redução de contexto respeitando um limite configurável de tokens |
| Benchmarks | Medir tamanho do contexto, relevância dos artefatos selecionados e tempo de execução |

### Fase 4 — Produto Final (Planejado)

| Item | Descrição |
|------|-----------|
| Documentação de uso | Guias e exemplos para desenvolvedores |
| Testes E2E | Testes de integração de ponta a ponta cobrindo o pipeline completo |
| Distribuição | Empacotamento e publicação da CLI no PyPI |
| Dashboard | Atualização do GitHub Pages com métricas do projeto |

### Evolução de Longo Prazo

- Suporte a linguagens adicionais (Go, Rust, C#, Kotlin).
- Cache inteligente para evitar recomputação em tarefas similares.
- Integração direta com extensões de IDE (plugin VS Code).
- Modo watch para regenerar contexto automaticamente ao salvar arquivos.
- Suporte a monorepos com múltiplos contextos independentes.

---

## Referências

- [Arquitetura](architecture.md)
- [Tecnologias](technologies.md)
- [Roadmap](roadmap.md)
- [Diagrama de Sequência](diagramas/sequencia-pipeline.md)
- [Guia de Contribuição](../CONTRIBUTING.md)
