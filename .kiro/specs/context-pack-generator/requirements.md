# Requirements Document

## Introduction

O módulo `generator.py` em `src/tokemize/` é responsável por montar o arquivo final
de contexto otimizado (`outputs/context_pack.md`) a partir dos resultados das etapas
anteriores do pipeline Tokemize: seleção de arquivos relevantes e sumarização.

O `Context_Pack_Generator` recebe a descrição da tarefa, os arquivos selecionados
(completos e resumidos) e o contexto técnico do repositório, e produz um documento
Markdown estruturado e legível, pronto para ser enviado ao LLM. O arquivo gerado
inclui: a tarefa do usuário, os arquivos completos relevantes, os arquivos resumidos,
o contexto técnico do repositório e uma instrução sugerida para o LLM.

O módulo integra-se ao pipeline existente como a etapa `generator`, substituindo o
stub atual em `tokemize/generator.py` por uma implementação completa em
`src/tokemize/generator.py`.

## Glossary

- **Context_Pack_Generator**: Componente responsável por montar e persistir o arquivo
  final de contexto otimizado em Markdown.
- **Context_Pack**: Documento Markdown gerado pelo `Context_Pack_Generator` contendo
  todos os elementos necessários para uma chamada ao LLM: tarefa, arquivos completos,
  arquivos resumidos, contexto técnico e instrução sugerida.
- **Task**: Descrição textual da tarefa técnica fornecida pelo usuário, incluída como
  primeira seção do `Context_Pack`.
- **Complete_File**: Arquivo selecionado pelo `Selector` cujo conteúdo completo cabe
  no budget de tokens e é incluído integralmente no `Context_Pack`.
- **Summarized_File**: Arquivo selecionado pelo `Selector` cujo conteúdo foi resumido
  pelo `Summarizer` e é incluído no `Context_Pack` como resumo técnico.
- **Technical_Context**: Metadados estruturais do repositório incluídos no
  `Context_Pack`, como linguagens detectadas, total de arquivos analisados e
  distribuição por tipo de arquivo.
- **LLM_Instruction**: Instrução sugerida ao LLM incluída ao final do `Context_Pack`,
  orientando o modelo a usar o contexto fornecido para responder à tarefa.
- **Output_Path**: Caminho do arquivo de saída onde o `Context_Pack` é persistido.
  Padrão: `outputs/context_pack.md`.
- **GeneratorInput**: Dataclass que agrega os dados de entrada do
  `Context_Pack_Generator`: `task`, `selection_output` e `summary_output`.
- **GeneratorOutput**: Dataclass existente em `tokemize/models.py` que representa o
  resultado da etapa de geração, contendo `prompt` (conteúdo do `Context_Pack`) e
  `token_count`.
- **SelectionOutput**: Dataclass existente em `tokemize/models.py` contendo a lista
  de `SelectedFile` com `path`, `language`, `content` e `relevance_score`.
- **SummaryOutput**: Dataclass existente em `tokemize/models.py` contendo
  `summarized_content`, `token_count` e `files_summarized`.

## Requirements

### Requirement 1: Geração do Arquivo Context Pack

**User Story:** Como desenvolvedor usando o pipeline Tokemize, quero que o
`Context_Pack_Generator` produza um arquivo `context_pack.md` estruturado em Markdown,
para que eu possa inspecionar o contexto otimizado enviado ao LLM e reutilizá-lo em
chamadas futuras.

#### Acceptance Criteria

1. WHEN o `Context_Pack_Generator` é invocado com uma `Task`, uma `SelectionOutput`
   e uma `SummaryOutput` válidas, THE `Context_Pack_Generator` SHALL gerar um arquivo
   `context_pack.md` no `Output_Path` configurado.
2. THE `Context_Pack_Generator` SHALL criar o diretório `outputs/` automaticamente
   caso ele não exista, sem lançar exceção.
3. WHEN o arquivo `context_pack.md` já existe no `Output_Path`, THE
   `Context_Pack_Generator` SHALL sobrescrever o arquivo existente com o novo conteúdo.
4. THE `Context_Pack_Generator` SHALL retornar um `GeneratorOutput` com `prompt` igual
   ao conteúdo completo do `Context_Pack` gerado e `token_count` estimado como o
   número de palavras no `prompt`.
5. IF o `Output_Path` não puder ser escrito por falta de permissão ou outro erro de
   I/O, THEN THE `Context_Pack_Generator` SHALL lançar um `IOError` com mensagem
   descritiva indicando o caminho e a causa da falha.

---

### Requirement 2: Estrutura e Seções do Context Pack

**User Story:** Como desenvolvedor, quero que o `context_pack.md` seja organizado em
seções Markdown bem definidas, para que o conteúdo seja legível por humanos e
interpretável pelo LLM sem ambiguidade.

#### Acceptance Criteria

1. THE `Context_Pack_Generator` SHALL incluir uma seção `## Task` contendo a `Task`
   fornecida pelo usuário como primeiro elemento do `Context_Pack`.
2. THE `Context_Pack_Generator` SHALL incluir uma seção `## Complete Files` contendo
   cada `Complete_File` formatado em bloco de código Markdown com a linguagem
   detectada como identificador do bloco.
3. THE `Context_Pack_Generator` SHALL incluir uma seção `## Summarized Files`
   contendo o `summarized_content` da `SummaryOutput` quando `files_summarized > 0`.
4. THE `Context_Pack_Generator` SHALL incluir uma seção `## Technical Context`
   contendo os metadados estruturais derivados da `SelectionOutput`: total de arquivos
   selecionados, linguagens presentes e distribuição por linguagem.
5. THE `Context_Pack_Generator` SHALL incluir uma seção `## LLM Instruction` ao final
   do `Context_Pack` com uma instrução padrão orientando o LLM a usar o contexto
   fornecido para responder à `Task`.
6. THE `Context_Pack_Generator` SHALL manter a ordem das seções: `Task` →
   `Complete Files` → `Summarized Files` → `Technical Context` → `LLM Instruction`.
7. WHEN a `SelectionOutput` não contém `SelectedFile`, THE `Context_Pack_Generator`
   SHALL incluir a seção `## Complete Files` com o texto `_Nenhum arquivo selecionado._`
   em vez de omitir a seção.
8. WHEN a `SummaryOutput` tem `files_summarized` igual a zero, THE
   `Context_Pack_Generator` SHALL incluir a seção `## Summarized Files` com o texto
   `_Nenhum arquivo resumido._` em vez de omitir a seção.

---

### Requirement 3: Formatação dos Arquivos Completos

**User Story:** Como desenvolvedor, quero que cada arquivo completo no `context_pack.md`
seja apresentado com seu caminho, linguagem e conteúdo em bloco de código, para que
o LLM identifique claramente a origem e o tipo de cada trecho de código.

#### Acceptance Criteria

1. WHEN um `Complete_File` é incluído no `Context_Pack`, THE `Context_Pack_Generator`
   SHALL formatar cada arquivo com um cabeçalho `### {path}` seguido de um bloco de
   código Markdown com o identificador de linguagem igual ao campo `language` do
   `SelectedFile`.
2. THE `Context_Pack_Generator` SHALL separar cada `Complete_File` formatado por uma
   linha em branco para garantir legibilidade.
3. WHEN o campo `language` de um `SelectedFile` está vazio ou é `"unknown"`, THE
   `Context_Pack_Generator` SHALL usar `text` como identificador do bloco de código.
4. THE `Context_Pack_Generator` SHALL incluir todos os `SelectedFile` da
   `SelectionOutput` na seção `## Complete Files`, na ordem em que aparecem em
   `selected_files`.

---

### Requirement 4: Contexto Técnico do Repositório

**User Story:** Como desenvolvedor, quero que o `context_pack.md` inclua metadados
estruturais do repositório, para que o LLM tenha visibilidade sobre o escopo do
código analisado sem precisar inferir essas informações do conteúdo dos arquivos.

#### Acceptance Criteria

1. THE `Context_Pack_Generator` SHALL incluir no `Technical_Context` o total de
   arquivos selecionados como `Total de arquivos selecionados: {n}`.
2. THE `Context_Pack_Generator` SHALL incluir no `Technical_Context` a lista de
   linguagens únicas presentes nos `SelectedFile`, formatada como
   `Linguagens: {lang1}, {lang2}, ...` em ordem alfabética.
3. WHEN todos os `SelectedFile` têm a mesma linguagem, THE `Context_Pack_Generator`
   SHALL incluir apenas essa linguagem na lista de linguagens do `Technical_Context`.
4. WHEN a `SelectionOutput` não contém `SelectedFile`, THE `Context_Pack_Generator`
   SHALL incluir no `Technical_Context` `Total de arquivos selecionados: 0` e
   `Linguagens: _nenhuma_`.

---

### Requirement 5: Instrução Sugerida para o LLM

**User Story:** Como desenvolvedor, quero que o `context_pack.md` inclua uma instrução
padrão ao LLM ao final do documento, para que o modelo saiba como usar o contexto
fornecido para responder à tarefa sem necessidade de prompt adicional.

#### Acceptance Criteria

1. THE `Context_Pack_Generator` SHALL incluir na seção `## LLM Instruction` uma
   instrução em linguagem natural orientando o LLM a analisar o contexto fornecido
   e responder à `Task` descrita na seção `## Task`.
2. THE `LLM_Instruction` SHALL referenciar explicitamente a `Task` do usuário na
   instrução gerada, sem reproduzir o conteúdo completo da `Task`.
3. THE `LLM_Instruction` SHALL ser uma `str` estática predefinida no módulo, sem
   depender de chamadas externas ou geração dinâmica por LLM.

---

### Requirement 6: Interface e Integração com o Pipeline

**User Story:** Como desenvolvedor do pipeline Tokemize, quero que o
`Context_Pack_Generator` exponha uma interface tipada compatível com o orquestrador
existente, para que ele possa substituir o stub atual sem alterar a assinatura da
etapa `generator` no pipeline.

#### Acceptance Criteria

1. THE `Context_Pack_Generator` SHALL expor uma função pública
   `generate_context_pack(summary_output: SummaryOutput, task: str, output_path: str | Path = "outputs/context_pack.md") -> GeneratorOutput`
   com type hints completos em todos os parâmetros e no retorno.
2. THE `Context_Pack_Generator` SHALL incluir docstrings no padrão Google Style em
   todas as funções e classes públicas do módulo.
3. THE `Context_Pack_Generator` SHALL ser importável via
   `from tokemize.generator import generate_context_pack` sem erros de importação.
4. THE `Context_Pack_Generator` SHALL registrar via `logging` o início da geração,
   o `Output_Path` utilizado, o número de arquivos incluídos e a conclusão bem-sucedida,
   sem registrar o conteúdo completo dos arquivos ou da `Task`.
5. THE `Context_Pack_Generator` SHALL usar apenas a `SummaryOutput` e a `Task` como
   parâmetros obrigatórios, mantendo compatibilidade com a assinatura atual da etapa
   `generator` no orquestrador (`generate_prompt(summary_output, task)`).

---

### Requirement 7: Estimativa de Tokens

**User Story:** Como desenvolvedor, quero que o `GeneratorOutput` retornado pelo
`Context_Pack_Generator` inclua uma estimativa do número de tokens do `Context_Pack`
gerado, para que o orquestrador e a CLI possam reportar o custo estimado da chamada
ao LLM.

#### Acceptance Criteria

1. THE `Context_Pack_Generator` SHALL calcular o `token_count` do `GeneratorOutput`
   como o número de palavras (separadas por espaço em branco) no conteúdo do
   `Context_Pack` gerado.
2. WHEN o `Context_Pack` gerado está vazio, THE `Context_Pack_Generator` SHALL
   retornar `token_count` igual a zero no `GeneratorOutput`.
3. THE `Context_Pack_Generator` SHALL incluir no `token_count` o conteúdo de todas
   as seções do `Context_Pack`, incluindo cabeçalhos, blocos de código e a
   `LLM_Instruction`.

---

### Requirement 8: Parsing e Serialização do Context Pack

**User Story:** Como desenvolvedor, quero que o conteúdo do `context_pack.md` possa
ser parseado de volta para suas seções constituintes, para que ferramentas de
inspeção e testes possam verificar a estrutura do documento gerado.

#### Acceptance Criteria

1. THE `Context_Pack_Generator` SHALL gerar o `Context_Pack` de forma que cada seção
   de nível 2 (`##`) seja identificável por seu título exato, sem ambiguidade entre
   seções.
2. FOR ALL `Context_Pack` gerados com pelo menos um `SelectedFile`, o conteúdo da
   seção `## Task` SHALL ser igual à `Task` fornecida como entrada (propriedade de
   round-trip: geração → extração da seção `## Task` → comparação com input).
3. FOR ALL `Context_Pack` gerados, o número de blocos de código na seção
   `## Complete Files` SHALL ser igual ao número de `SelectedFile` em
   `SelectionOutput.selected_files` (propriedade de contagem).
