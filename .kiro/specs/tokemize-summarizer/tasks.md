# Implementation Plan: tokemize-summarizer

## Overview

Implementação incremental do módulo `summarizer.py` no pipeline Tokemize. O plano
segue a ordem: protocolo de integração → implementação do `Summarizer` → clientes
concretos de LLM → testes. Cada etapa é validada antes de avançar para a próxima.

## Tasks

- [x] 1. Criar o protocolo `LLMClientProtocol` e a estrutura de integração LLM
  - Criar o diretório `src/tokemize/integrations/llm/` com `__init__.py`
  - Criar `src/tokemize/integrations/llm/protocol.py` com a classe `LLMClientProtocol` como `typing.Protocol`
  - Definir o método `complete(self, prompt: str) -> str` com type hints e docstring Google Style
  - Exportar `LLMClientProtocol` no `__init__.py` do pacote `integrations/llm/`
  - Criar `src/tokemize/integrations/__init__.py` se não existir
  - _Requirements: 4.4, 5.3_

- [x] 2. Implementar os clientes concretos de LLM
  - [x] 2.1 Implementar `OpenAIClient` em `src/tokemize/integrations/llm/openai_client.py`
    - Carregar `OPENAI_API_KEY` via `python-dotenv` no construtor
    - Lançar `EnvironmentError` com mensagem descritiva se a variável não estiver definida
    - Implementar `complete(prompt: str) -> str` chamando a API OpenAI (GPT-4o)
    - Nunca logar o valor da API key
    - Docstrings Google Style em classe e métodos públicos
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 2.2 Implementar `AnthropicClient` em `src/tokemize/integrations/llm/anthropic_client.py`
    - Carregar `ANTHROPIC_API_KEY` via `python-dotenv` no construtor
    - Lançar `EnvironmentError` com mensagem descritiva se a variável não estiver definida
    - Implementar `complete(prompt: str) -> str` chamando a API Anthropic (Claude)
    - Nunca logar o valor da API key
    - Docstrings Google Style em classe e métodos públicos
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 2.3 Exportar `OpenAIClient` e `AnthropicClient` no `__init__.py` de `integrations/llm/`
    - _Requirements: 4.4_

- [x] 3. Implementar o módulo `Summarizer`
  - [x] 3.1 Criar `src/tokemize/summarizer.py` com as constantes do módulo
    - Definir `FALLBACK_MESSAGE: str` com mensagem de fallback controlada
    - Definir `SUMMARY_PROMPT_TEMPLATE: str` com o template de prompt de sumarização
    - _Requirements: 3.2, 1.2_

  - [x] 3.2 Implementar a classe `Summarizer` com injeção de dependência
    - Definir `__init__(self, llm_client: LLMClientProtocol, cache: FileCache | None = None) -> None`
    - Armazenar `llm_client` e `cache` como atributos privados
    - Configurar `logger = logging.getLogger(__name__)` no módulo
    - Docstring Google Style na classe
    - _Requirements: 2.4, 4.4, 5.3_

  - [x] 3.3 Implementar o método `summarize` com lógica de cache e chamada ao LLM
    - Assinatura: `summarize(self, file_path: str | Path, content: str) -> str`
    - Retornar `""` imediatamente se `content` for vazio (sem chamar o LLM)
    - Verificar cache via `cache.get_cached_file(file_path)` se cache não for `None`
    - Em cache hit (hash igual), logar e retornar `cached_entry["summary"]`
    - Em cache miss, construir o prompt com `SUMMARY_PROMPT_TEMPLATE`
    - Chamar `self._llm_client.complete(prompt)` dentro de bloco `try/except Exception`
    - Em sucesso: persistir via `cache.update_cached_file(file_path, summary=summary)` e `cache.save_cache()`
    - Em exceção: logar `logger.error(...)` com tipo da exceção (sem conteúdo do arquivo) e retornar `FALLBACK_MESSAGE`
    - Logar início da sumarização, cache hit, cache miss e resultado
    - Docstring Google Style no método
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.5, 3.1, 3.2, 3.3, 3.4, 5.1, 5.4_

- [x] 4. Checkpoint — Verificar estrutura e tipos
  - Garantir que `Summarizer` não instancia `LLMClientProtocol` diretamente
  - Garantir que todos os métodos públicos têm type hints completos e docstrings
  - Garantir que `FALLBACK_MESSAGE` é uma `str` não vazia
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Adicionar `hypothesis` como dependência de desenvolvimento e criar arquivo de testes
  - Adicionar `hypothesis>=6.100.0` em `[project.optional-dependencies] dev` no `pyproject.toml`
  - Criar `tests/test_summarizer.py` com imports necessários (`pytest`, `hypothesis`, `unittest.mock`)
  - Definir as estratégias Hypothesis reutilizáveis: `file_path_strategy`, `content_strategy`, `summary_strategy`
  - _Requirements: 5.1, 5.2_

- [x] 6. Implementar testes unitários do `Summarizer`
  - [x] 6.1 Escrever testes unitários concretos em `tests/test_summarizer.py`
    - `test_summarize_returns_str` — tipo de retorno é sempre `str`
    - `test_summarize_without_cache` — operação sem `FileCache` (cache=None) chama o LLM
    - `test_fallback_message_is_nonempty` — `FALLBACK_MESSAGE` não é vazia
    - `test_llm_client_injected_not_instantiated` — `Summarizer` não instancia LLM diretamente
    - Usar `MagicMock(spec=LLMClientProtocol)` e `MagicMock(spec=FileCache)` como mocks
    - _Requirements: 1.4, 2.4, 2.5, 3.2, 4.4_

  - [ ]* 6.2 Escrever teste unitário de logging
    - `test_summarize_logs_cache_hit` — logging de cache hit com `caplog` do pytest
    - `test_summarize_logs_cache_miss` — logging de cache miss com `caplog` do pytest
    - `test_api_key_not_logged` — verificar que nenhum log contém o valor da API key
    - _Requirements: 5.4, 4.3_

- [x] 7. Implementar testes baseados em propriedades (PBT) com Hypothesis
  - [ ]* 7.1 Escrever property test para Property 1: conteúdo vazio
    - `test_empty_content_returns_empty_no_llm_call`
    - `@given(file_path=file_path_strategy)` — qualquer file_path válido, content=""
    - Verificar retorno `""` e que `mock_llm.complete` não foi chamado
    - Anotar: `# Feature: tokemize-summarizer, Property 1: Conteúdo vazio retorna string vazia sem chamar o LLM`
    - **Property 1: Conteúdo vazio retorna string vazia sem chamar o LLM**
    - **Validates: Requirements 1.5**

  - [ ]* 7.2 Escrever property test para Property 2: cache hit evita chamada ao LLM
    - `test_cache_hit_skips_llm`
    - `@given(file_path=file_path_strategy, content=content_strategy, summary=summary_strategy)`
    - Configurar mock do cache para retornar entrada com hash igual ao do content
    - Verificar que `mock_llm.complete` não foi chamado e retorno é o summary cacheado
    - Anotar: `# Feature: tokemize-summarizer, Property 2: Cache hit evita chamada ao LLM`
    - **Property 2: Cache hit evita chamada ao LLM**
    - **Validates: Requirements 2.1**

  - [ ]* 7.3 Escrever property test para Property 3: resumo gerado é persistido no cache
    - `test_successful_summary_persisted_in_cache`
    - `@given(file_path=file_path_strategy, content=content_strategy, summary=summary_strategy)`
    - Configurar mock do cache para retornar `None` (cache miss)
    - Configurar `mock_llm.complete` para retornar `summary`
    - Verificar que `mock_cache.update_cached_file` foi chamado com `summary=summary`
    - Verificar que `mock_cache.save_cache` foi chamado
    - Anotar: `# Feature: tokemize-summarizer, Property 3: Resumo gerado é persistido no cache`
    - **Property 3: Resumo gerado é persistido no cache**
    - **Validates: Requirements 2.2**

  - [ ]* 7.4 Escrever property test para Property 4: falha do LLM retorna fallback sem propagar exceção
    - `test_llm_failure_returns_fallback_no_exception`
    - `@given(file_path=file_path_strategy, content=content_strategy)`
    - Configurar `mock_llm.complete` para lançar `Exception` arbitrária
    - Verificar que o retorno é `FALLBACK_MESSAGE` (str não vazia)
    - Verificar que nenhuma exceção é propagada
    - Verificar que `mock_cache.update_cached_file` não foi chamado
    - Anotar: `# Feature: tokemize-summarizer, Property 4: Falha do LLM retorna fallback sem propagar exceção`
    - **Property 4: Falha do LLM retorna fallback sem propagar exceção**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

  - [ ]* 7.5 Escrever property test para Property 5: invalidação de cache por mudança de conteúdo
    - `test_content_change_invalidates_cache`
    - `@given(file_path=file_path_strategy, content=content_strategy, summary=summary_strategy)`
    - Configurar mock do cache para retornar entrada com hash diferente do content atual
    - Verificar que `mock_llm.complete` foi chamado (cache invalidado)
    - Verificar que `mock_cache.update_cached_file` foi chamado com novo summary
    - Anotar: `# Feature: tokemize-summarizer, Property 5: Invalidação de cache por mudança de conteúdo`
    - **Property 5: Invalidação de cache por mudança de conteúdo**
    - **Validates: Requirements 2.3**

- [x] 8. Checkpoint final — Garantir cobertura e integração
  - Executar `pytest tests/test_summarizer.py -v` e garantir que todos os testes passam
  - Verificar que `Summarizer` é importável via `from tokemize.summarizer import Summarizer`
  - Verificar que `LLMClientProtocol` é importável via `from tokemize.integrations.llm import LLMClientProtocol`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada task referencia requisitos específicos para rastreabilidade
- Os clientes concretos (`OpenAIClient`, `AnthropicClient`) dependem de variáveis de ambiente — use mocks nos testes
- O `Summarizer` nunca instancia `LLMClientProtocol` diretamente; sempre recebe via construtor
- O `FileCache` existente em `src/tokemize/cache.py` já suporta o campo `summary` — não modificar sua estrutura
- Property tests usam `hypothesis` com estratégias de geração aleatória; cada propriedade é um teste independente
- A branch de trabalho é `feature/summarizer-llm` a partir de `develop`
