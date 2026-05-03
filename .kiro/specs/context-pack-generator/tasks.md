# Implementation Plan: Context Pack Generator

## Overview

Implementar o módulo `src/tokemize/generator.py` que substitui o stub em
`tokemize/generator.py`, gerando um documento Markdown estruturado (`outputs/context_pack.md`)
com tarefa, arquivos completos, arquivos resumidos, contexto técnico e instrução ao LLM.
A função `generate_prompt(summary_output, task)` do orquestrador continua funcionando
sem alterações via wrapper de compatibilidade.

## Tasks

- [x] 1. Criar o módulo `src/tokemize/generator.py` com funções auxiliares de formatação
  - Criar o arquivo `src/tokemize/generator.py` com a constante `LLM_INSTRUCTION`
  - Implementar `_format_task_section(task: str) -> str`
  - Implementar `_format_complete_files_section(selected_files: list[SelectedFile]) -> str`
    - Usar `### {path}` como cabeçalho de cada arquivo
    - Usar `text` como fallback quando `language` for vazio ou `"unknown"`
    - Separar arquivos por linha em branco
  - Implementar `_format_summarized_files_section(summary_output: SummaryOutput) -> str`
    - Exibir `_Nenhum arquivo resumido._` quando `files_summarized == 0`
  - Implementar `_format_technical_context_section(selected_files: list[SelectedFile]) -> str`
    - Incluir `Total de arquivos selecionados: {n}`
    - Incluir linguagens únicas em ordem alfabética
    - Exibir `_nenhuma_` quando lista estiver vazia
  - Implementar `_format_llm_instruction_section() -> str`
  - Adicionar docstrings Google Style e type hints em todas as funções
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3_

- [x] 2. Implementar `_build_context_pack`, `_count_tokens`, `_write_output` e `generate_context_pack`
  - Implementar `_build_context_pack(summary_output, task, selected_files) -> str`
    - Orquestrar as 5 funções de formatação na ordem correta
  - Implementar `_count_tokens(content: str) -> int` como `len(content.split())`
  - Implementar `_write_output(content: str, output_path: Path) -> None`
    - Criar diretório pai com `mkdir(parents=True, exist_ok=True)`
    - Capturar `OSError` e relançar como `IOError` com mensagem descritiva
  - Implementar `generate_context_pack(summary_output, task, output_path, selection_output) -> GeneratorOutput`
    - Registrar via `logging`: início, output_path, número de arquivos, conclusão
    - Não registrar conteúdo dos arquivos nem da task
    - Retornar `GeneratorOutput(prompt=content, token_count=n)`
  - Implementar `generate_prompt(summary_output, task) -> GeneratorOutput` como wrapper de compatibilidade
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3_

- [x] 3. Criar `tests/test_generator.py` com smoke tests e testes de exemplo
  - [x] 3.1 Escrever smoke tests de importação
    - `test_import_generate_context_pack`: verifica que `generate_context_pack` é importável
    - `test_import_generate_prompt_compat`: verifica que `generate_prompt` é importável
    - _Requirements: 6.3_
  - [ ]* 3.2 Escrever testes de exemplo concretos
    - `test_creates_output_directory_automatically`: diretório criado automaticamente
    - `test_raises_ioerror_on_write_failure`: `IOError` com path na mensagem
    - `test_empty_selection_output_placeholder`: texto `_Nenhum arquivo selecionado._`
    - `test_zero_files_summarized_placeholder`: texto `_Nenhum arquivo resumido._`
    - `test_empty_technical_context`: `Total de arquivos selecionados: 0` e `_nenhuma_`
    - `test_llm_instruction_present`: seção `## LLM Instruction` presente no output
    - `test_generate_prompt_compat_wrapper`: wrapper retorna `GeneratorOutput` válido
    - `test_logging_emits_expected_messages`: log registra path e número de arquivos
    - _Requirements: 1.2, 1.5, 2.7, 2.8, 4.4, 5.3, 6.4_

- [x] 4. Checkpoint — Garantir que smoke tests e testes de exemplo passam
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Escrever testes de propriedade com Hypothesis para as Properties 1–5
  - [x] 5.1 Implementar `test_property_1_prompt_equals_file_content`
    - **Property 1: Round-trip do conteúdo — arquivo e GeneratorOutput são idênticos**
    - **Validates: Requirements 1.4**
  - [x]* 5.2 Implementar `test_property_2_overwrite_idempotent`
    - **Property 2: Sobrescrita idempotente**
    - **Validates: Requirements 1.3**
  - [x]* 5.3 Implementar `test_property_3_token_count_is_word_count`
    - **Property 3: token_count é o número de palavras do prompt**
    - **Validates: Requirements 7.1, 7.2, 7.3**
  - [x]* 5.4 Implementar `test_property_4_task_round_trip`
    - **Property 4: Round-trip da seção Task**
    - **Validates: Requirements 2.1, 8.2**
  - [x]* 5.5 Implementar `test_property_5_code_block_count_equals_files`
    - **Property 5: Contagem de blocos de código equals número de SelectedFiles**
    - **Validates: Requirements 2.2, 3.4, 8.3**

- [x] 6. Escrever testes de propriedade com Hypothesis para as Properties 6–11
  - [x] 6.1 Implementar `test_property_6_section_order_preserved`
    - **Property 6: Ordem das seções é sempre preservada**
    - **Validates: Requirements 2.6**
  - [x]* 6.2 Implementar `test_property_7_file_path_and_language_in_output`
    - **Property 7: Formatação de arquivos — path e linguagem corretos**
    - **Validates: Requirements 3.1**
  - [x]* 6.3 Implementar `test_property_8_unknown_language_fallback`
    - **Property 8: Fallback de linguagem para `text`**
    - **Validates: Requirements 3.3**
  - [x]* 6.4 Implementar `test_property_9_technical_context_metadata`
    - **Property 9: Technical Context — total e linguagens corretos**
    - **Validates: Requirements 4.1, 4.2, 4.3**
  - [x]* 6.5 Implementar `test_property_10_llm_instruction_is_static`
    - **Property 10: LLM Instruction é estática e idempotente**
    - **Validates: Requirements 5.3**
  - [x]* 6.6 Implementar `test_property_11_section_titles_unique`
    - **Property 11: Títulos de seção são únicos e identificáveis**
    - **Validates: Requirements 8.1**

- [x] 7. Checkpoint final — Garantir que todos os testes passam
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Os checkpoints garantem validação incremental
- Os testes de propriedade validam invariantes universais com Hypothesis (`max_examples=100`)
- Os testes de exemplo validam comportamentos específicos e casos de borda
- O wrapper `generate_prompt` mantém compatibilidade total com `tokemize/orchestrator.py` sem alterações
- Estratégias Hypothesis para `SelectedFile`, `SelectionOutput` e `SummaryOutput` devem ser definidas no topo do arquivo de testes e reutilizadas entre os testes de propriedade
