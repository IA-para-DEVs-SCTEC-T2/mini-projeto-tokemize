# Requirements Document

## Introduction

A CLI do Tokemize é o ponto de entrada do sistema para o usuário final. Construída com a biblioteca Typer (Python 3.10+), ela expõe o comando `analyze`, que recebe um caminho de repositório e uma descrição de tarefa, valida as entradas, orquestra os módulos internos em sequência e exibe o resultado otimizado ao usuário. A CLI atua como camada de orquestração — ela não implementa a lógica de negócio, mas define os contratos de interface com cada módulo interno.

## Glossary

- **CLI**: Interface de linha de comando implementada com Typer em `cli.py`.
- **Repository_Path**: Caminho absoluto ou relativo para o diretório raiz do repositório a ser analisado.
- **Task_Description**: String fornecida pelo usuário descrevendo a tarefa técnica a ser executada (mínimo 10 caracteres).
- **Repository_Analyzer**: Módulo `tokemize.core.parser.repository_analyzer` responsável por mapear a estrutura do repositório.
- **Intelligent_Selector**: Módulo `tokemize.core.selector.intelligent_selector` responsável por selecionar os arquivos relevantes para a tarefa.
- **Compressor**: Módulo `tokemize.core.optimizer.compressor` responsável por resumir e comprimir o contexto selecionado.
- **Context_Cache**: Módulo `tokemize.core.context_cache` responsável por verificar e atualizar o cache de contexto.
- **LLM_Dispatcher**: Módulo `tokemize.integrations.llm.llm_dispatcher` responsável por enviar a requisição otimizada ao LLM.
- **Exit_Code**: Código numérico retornado ao sistema operacional ao encerrar o processo (0 = sucesso, 1 = erro de validação, 2 = erro de execução).
- **Pipeline**: Sequência ordenada de chamadas aos módulos internos executada após validação bem-sucedida das entradas.

## Requirements

### Requirement 1: Comando `analyze`

**User Story:** Como desenvolvedor, quero executar `tokemize analyze <repo_path> <task_description>` no terminal, para que o sistema processe meu repositório e envie uma requisição otimizada ao LLM.

#### Acceptance Criteria

1. THE CLI SHALL expor um comando chamado `analyze` como subcomando principal da aplicação Typer.
2. THE CLI SHALL declarar `repo_path` como argumento posicional obrigatório do tipo `str` no comando `analyze`.
3. THE CLI SHALL declarar `task_description` como argumento posicional obrigatório do tipo `str` no comando `analyze`.
4. WHEN o comando `analyze` for invocado sem argumentos, THE CLI SHALL exibir a mensagem de ajuda do Typer e encerrar com Exit_Code 0.
5. WHEN o comando `analyze` for invocado com a flag `--help`, THE CLI SHALL exibir descrições legíveis de cada argumento e encerrar com Exit_Code 0.

---

### Requirement 2: Validação do caminho do repositório

**User Story:** Como desenvolvedor, quero receber uma mensagem de erro clara quando informar um caminho inválido, para que eu possa corrigir a entrada sem precisar inspecionar logs internos.

#### Acceptance Criteria

1. WHEN o valor de `repo_path` não corresponder a um caminho existente no sistema de arquivos, THEN THE CLI SHALL exibir a mensagem `"Erro: o caminho '<repo_path>' não existe."` e encerrar com Exit_Code 1.
2. WHEN o valor de `repo_path` corresponder a um caminho existente mas não for um diretório, THEN THE CLI SHALL exibir a mensagem `"Erro: '<repo_path>' não é um diretório válido."` e encerrar com Exit_Code 1.
3. WHEN o valor de `repo_path` for um diretório válido e existente, THE CLI SHALL prosseguir para a validação de `task_description`.

---

### Requirement 3: Validação da descrição da tarefa

**User Story:** Como desenvolvedor, quero ser avisado quando minha descrição de tarefa for muito curta ou vazia, para que o sistema não processe entradas insuficientes para gerar contexto relevante.

#### Acceptance Criteria

1. WHEN o valor de `task_description` for uma string vazia ou contiver apenas espaços em branco, THEN THE CLI SHALL exibir a mensagem `"Erro: a descrição da tarefa não pode ser vazia."` e encerrar com Exit_Code 1.
2. WHEN o valor de `task_description` contiver menos de 10 caracteres não-brancos, THEN THE CLI SHALL exibir a mensagem `"Erro: a descrição da tarefa deve ter pelo menos 10 caracteres."` e encerrar com Exit_Code 1.
3. WHEN o valor de `task_description` contiver 10 ou mais caracteres não-brancos, THE CLI SHALL prosseguir para a execução do Pipeline.

---

### Requirement 4: Orquestração do Pipeline

**User Story:** Como desenvolvedor, quero que a CLI chame os módulos internos na ordem correta após validação, para que o contexto seja processado de forma consistente e previsível.

#### Acceptance Criteria

1. WHEN todas as validações forem bem-sucedidas, THE CLI SHALL chamar `Repository_Analyzer` como primeira etapa do Pipeline, passando `repo_path` como argumento.
2. WHEN `Repository_Analyzer` retornar com sucesso, THE CLI SHALL chamar `Intelligent_Selector`, passando o resultado de `Repository_Analyzer` e `task_description` como argumentos.
3. WHEN `Intelligent_Selector` retornar com sucesso, THE CLI SHALL chamar `Compressor`, passando o resultado de `Intelligent_Selector` como argumento.
4. WHEN `Compressor` retornar com sucesso, THE CLI SHALL chamar `Context_Cache`, passando o resultado de `Compressor` e `task_description` como argumentos.
5. WHEN `Context_Cache` retornar com sucesso, THE CLI SHALL chamar `LLM_Dispatcher`, passando o resultado de `Context_Cache` como argumento.
6. IF qualquer módulo do Pipeline lançar uma exceção, THEN THE CLI SHALL exibir a mensagem `"Erro na etapa '<nome_do_módulo>': <mensagem_da_exceção>"` e encerrar com Exit_Code 2.

---

### Requirement 5: Feedback de progresso ao usuário

**User Story:** Como desenvolvedor, quero ver mensagens de progresso no terminal durante a execução, para que eu saiba em qual etapa o sistema está e se está funcionando corretamente.

#### Acceptance Criteria

1. WHEN o Pipeline iniciar, THE CLI SHALL exibir a mensagem `"[1/5] Analisando repositório..."` antes de chamar `Repository_Analyzer`.
2. WHEN `Repository_Analyzer` retornar com sucesso, THE CLI SHALL exibir a mensagem `"[2/5] Selecionando arquivos relevantes..."` antes de chamar `Intelligent_Selector`.
3. WHEN `Intelligent_Selector` retornar com sucesso, THE CLI SHALL exibir a mensagem `"[3/5] Comprimindo contexto..."` antes de chamar `Compressor`.
4. WHEN `Compressor` retornar com sucesso, THE CLI SHALL exibir a mensagem `"[4/5] Verificando cache..."` antes de chamar `Context_Cache`.
5. WHEN `Context_Cache` retornar com sucesso, THE CLI SHALL exibir a mensagem `"[5/5] Enviando ao LLM..."` antes de chamar `LLM_Dispatcher`.
6. WHEN `LLM_Dispatcher` retornar com sucesso, THE CLI SHALL exibir o resultado final precedido da linha `"=== Resultado ==="`.

---

### Requirement 6: Contratos de interface dos módulos internos

**User Story:** Como desenvolvedor, quero que cada módulo interno exponha uma função com assinatura tipada e documentada, para que a CLI possa integrá-los sem depender de detalhes de implementação.

#### Acceptance Criteria

1. THE `Repository_Analyzer` SHALL expor a função `analyze_repository(repo_path: str) -> RepositoryStructure` onde `RepositoryStructure` é um tipo definido no pacote `tokemize.models`.
2. THE `Intelligent_Selector` SHALL expor a função `select_relevant_files(structure: RepositoryStructure, task_description: str) -> SelectedContext` onde `SelectedContext` é um tipo definido no pacote `tokemize.models`.
3. THE `Compressor` SHALL expor a função `compress_context(context: SelectedContext) -> CompressedContext` onde `CompressedContext` é um tipo definido no pacote `tokemize.models`.
4. THE `Context_Cache` SHALL expor a função `get_or_update_cache(compressed: CompressedContext, task_description: str) -> CachedContext` onde `CachedContext` é um tipo definido no pacote `tokemize.models`.
5. THE `LLM_Dispatcher` SHALL expor a função `dispatch(cached_context: CachedContext) -> str` retornando a resposta do LLM como string.
6. THE CLI SHALL importar todos os módulos internos exclusivamente a partir do pacote `tokemize/`.

---

### Requirement 7: Estrutura de arquivos do projeto

**User Story:** Como desenvolvedor, quero que o projeto siga uma estrutura de diretórios padronizada, para que a navegação e manutenção do código sejam previsíveis.

#### Acceptance Criteria

1. THE CLI SHALL ter seu ponto de entrada no arquivo `cli.py` na raiz do projeto.
2. THE CLI SHALL instanciar a aplicação Typer em `cli.py` e registrar o comando `analyze` nessa instância.
3. THE `tokemize/` SHALL conter os submódulos `core/parser/`, `core/selector/`, `core/optimizer/`, `core/`, `integrations/llm/` e `models/` conforme a estrutura definida no projeto.
4. WHERE o projeto for executado via `python cli.py`, THE CLI SHALL funcionar equivalentemente à execução via `typer run cli.py`.
