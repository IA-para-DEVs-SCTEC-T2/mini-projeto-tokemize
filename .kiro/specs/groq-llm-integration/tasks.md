# Implementation Plan: groq-llm-integration

## Overview

Implementação do `GroqClient` em Python 3.11+, seguindo o protocolo `LLMClientProtocol`
da camada `integrations/llm/`. O plano cobre: criação dos arquivos de estrutura,
implementação da classe, e cobertura por testes unitários e baseados em propriedades
com `pytest` + `hypothesis`.

## Tasks

- [x] 1. Criar estrutura de arquivos da camada integrations/llm/
  - Criar `src/tokemize/integrations/llm/__init__.py` exportando `LLMClientProtocol` e `GroqClient`
  - Criar `src/tokemize/integrations/llm/protocol.py` com a definição de `LLMClientProtocol`
  - Criar `src/tokemize/integrations/llm/groq_client.py` com o esqueleto da classe (constantes, imports, assinatura dos métodos)
  - _Requirements: 1.1, 1.2, 6.1, 6.2, 6.3_

- [ ] 2. Implementar `GroqClient.__init__` com validação fail-fast
  - [x] 2.1 Implementar carregamento de `GROQ_API_KEY` via `python-dotenv` e validação
    - Chamar `load_dotenv()` no início do `__init__`
    - Ler `os.getenv(ENV_API_KEY)` e lançar `EnvironmentError` se ausente ou vazio
    - Instanciar `groq.Groq(api_key=api_key)` e armazenar em `self._client`
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.2 Implementar resolução do `model` com precedência de três camadas
    - Validar que `model` não é string vazia (lançar `ValueError` se for)
    - Resolver: parâmetro → `GROQ_MODEL` env → `DEFAULT_MODEL` (`"llama3-8b-8192"`)
    - Armazenar em `self._model: str`
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 2.3 Escrever testes unitários para `__init__`
    - `test_groq_client_instantiation_with_valid_env` — construção bem-sucedida
    - `test_groq_client_uses_env_model_when_no_param` — resolução via `GROQ_MODEL`
    - `test_groq_client_uses_default_model_when_no_env` — fallback para `DEFAULT_MODEL`
    - `test_groq_client_uses_constructor_model_over_env` — parâmetro tem precedência
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 6.4_

  - [ ]* 2.4 Escrever property test: API key ausente lança EnvironmentError (Property 4)
    - **Property 4: API key ausente ou vazia lança EnvironmentError na construção**
    - **Validates: Requirements 2.2**

  - [ ]* 2.5 Escrever property test: model vazio lança ValueError (Property 5)
    - **Property 5: Model_ID vazio lança ValueError na construção**
    - **Validates: Requirements 3.3, 3.4**

  - [ ]* 2.6 Escrever property test: resolução do model segue precedência correta (Property 6)
    - **Property 6: Resolução do model segue precedência correta**
    - **Validates: Requirements 3.1, 3.2**

- [ ] 3. Implementar `GroqClient.complete`
  - [x] 3.1 Implementar chamada ao SDK e retorno da completion
    - Logar início da chamada via `logger.debug` (sem conteúdo do prompt)
    - Chamar `self._client.chat.completions.create(model=self._model, messages=[{"role": "user", "content": prompt}])`
    - Retornar `response.choices[0].message.content or ""`
    - Em caso de exceção: logar `logger.error("Falha em complete(): %s", type(exc).__name__)` e re-lançar
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3_

  - [ ]* 3.2 Escrever testes unitários para `complete`
    - `test_complete_sends_user_role_message` — prompt enviado como `role="user"`
    - `test_groq_client_exported_from_init` — importável via `from tokemize.integrations.llm import GroqClient`
    - _Requirements: 4.1, 4.3, 6.2_

  - [ ]* 3.3 Escrever property test: `complete()` sempre retorna `str` (Property 1)
    - **Property 1: Retorno de `complete()` é sempre `str`**
    - **Validates: Requirements 1.3, 4.2, 7.4**

  - [ ]* 3.4 Escrever property test: completion nula retorna string vazia (Property 2)
    - **Property 2: Completion nula ou vazia retorna string vazia**
    - **Validates: Requirements 4.4**

  - [ ]* 3.5 Escrever property test: exceções do SDK são propagadas sem modificação (Property 3)
    - **Property 3: Exceções do SDK são propagadas sem modificação**
    - **Validates: Requirements 4.5, 5.1, 5.2, 7.5**

- [x] 4. Checkpoint — Garantir que todos os testes passam
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [ ] 5. Implementar logging sem exposição de dados sensíveis e testes de segurança
  - [x] 5.1 Verificar e ajustar todos os pontos de log em `__init__` e `complete`
    - Confirmar que nenhum log registra o valor de `GROQ_API_KEY`
    - Confirmar que nenhum log registra o conteúdo do `prompt` ou da `completion`
    - _Requirements: 2.3, 5.3_

  - [ ]* 5.2 Escrever testes unitários de segurança de logs
    - `test_api_key_not_logged` — API key não aparece em nenhum registro de log
    - `test_prompt_content_not_logged` — conteúdo do prompt não aparece em logs
    - _Requirements: 2.3, 5.3_

  - [ ]* 5.3 Escrever property test: dados sensíveis não aparecem em logs (Property 7)
    - **Property 7: Dados sensíveis não aparecem em logs**
    - **Validates: Requirements 2.3, 5.3**

- [x] 6. Checkpoint final — Garantir que todos os testes passam
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Todos os testes usam mocks do `groq SDK` — nenhuma chamada real à API é feita
- Variáveis de ambiente são mockadas via `unittest.mock.patch.dict(os.environ, {...})`
- O `GroqClient` não herda explicitamente de `LLMClientProtocol` (duck typing)
- Property tests usam `hypothesis` (já instalado: 6.152.4) com `@given` e `settings`
