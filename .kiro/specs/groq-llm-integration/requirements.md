# Requirements Document

## Introduction

O módulo `groq_client.py` implementa o cliente concreto para o provedor de LLM
[Groq](https://groq.com), integrando-o ao pipeline Tokemize por meio do protocolo
`LLMClientProtocol`. O Groq oferece inferência de alta velocidade (LPU — Language
Processing Unit) para modelos como `llama3-8b-8192`, `llama3-70b-8192` e
`mixtral-8x7b-32768`, sendo uma alternativa de baixa latência aos provedores OpenAI
e Anthropic já previstos na arquitetura.

O `GroqClient` segue exatamente o mesmo padrão dos demais clientes da camada
`integrations/llm/`: carrega credenciais via variável de ambiente, implementa o
método `complete(prompt: str) -> str`, e nunca é instanciado fora dessa camada.

## Glossary

- **GroqClient**: Implementação concreta de `LLMClientProtocol` para o provedor Groq.
- **LLMClientProtocol**: Protocolo (`typing.Protocol`) que define a interface comum para todos os clientes de LLM no Tokemize. Método obrigatório: `complete(prompt: str) -> str`.
- **Groq_API_Key**: Credencial de acesso à API Groq, carregada exclusivamente via variável de ambiente `GROQ_API_KEY`.
- **Model_ID**: Identificador do modelo Groq a ser utilizado (ex: `llama3-8b-8192`). Configurável via variável de ambiente ou parâmetro de construção.
- **Prompt**: Texto de entrada enviado ao modelo Groq para geração de resposta.
- **Completion**: Texto de resposta retornado pelo modelo Groq para um dado `Prompt`.
- **groq SDK**: Biblioteca oficial Python do Groq (`groq`), usada para comunicação com a API.
- **EnvironmentError**: Exceção Python padrão lançada quando uma variável de ambiente obrigatória não está definida.
- **Fallback**: Comportamento controlado do pipeline quando o `GroqClient` lança exceção — tratado pela camada chamadora (ex: `Summarizer`), não pelo `GroqClient`.

## Requirements

### Requirement 1: Implementação do Protocolo LLMClientProtocol

**User Story:** Como desenvolvedor do pipeline Tokemize, quero que o `GroqClient`
implemente o `LLMClientProtocol`, para que ele possa ser usado de forma intercambiável
com os demais clientes de LLM sem alterar o pipeline.

#### Acceptance Criteria

1. THE `GroqClient` SHALL implementar o método `complete(prompt: str) -> str` conforme definido pelo `LLMClientProtocol`.
2. THE `GroqClient` SHALL ser estruturalmente compatível com `LLMClientProtocol` (duck typing via `typing.Protocol`), sem herança explícita obrigatória.
3. WHEN `complete(prompt)` é chamado com um `Prompt` não vazio, THE `GroqClient` SHALL retornar a `Completion` como uma `str`.
4. THE `GroqClient` SHALL incluir type hints completos em todos os métodos e atributos públicos.
5. THE `GroqClient` SHALL incluir docstrings no padrão Google Style em todas as classes e métodos públicos.

---

### Requirement 2: Carregamento de Credenciais via Variável de Ambiente

**User Story:** Como desenvolvedor, quero que a `Groq_API_Key` seja carregada
exclusivamente via variável de ambiente, para que nenhuma credencial seja hardcoded
no código-fonte ou exposta em logs.

#### Acceptance Criteria

1. THE `GroqClient` SHALL carregar a `Groq_API_Key` exclusivamente a partir da variável de ambiente `GROQ_API_KEY`, utilizando `python-dotenv` para leitura do arquivo `.env`.
2. IF a variável de ambiente `GROQ_API_KEY` não está definida ou está vazia, THEN THE `GroqClient` SHALL lançar um `EnvironmentError` com mensagem descritiva indicando o nome da variável ausente.
3. THE `GroqClient` SHALL nunca registrar o valor da `Groq_API_Key` em logs, mensagens de erro ou qualquer saída.
4. THE `GroqClient` SHALL ser instanciado exclusivamente dentro da camada `integrations/llm/`, nunca diretamente em outros módulos do pipeline.

---

### Requirement 3: Configuração do Modelo

**User Story:** Como desenvolvedor, quero poder configurar qual modelo Groq é utilizado,
para que eu possa escolher entre velocidade e capacidade conforme a necessidade do
pipeline.

#### Acceptance Criteria

1. THE `GroqClient` SHALL aceitar um `Model_ID` como parâmetro opcional no construtor, com valor padrão configurável.
2. WHERE o `Model_ID` não é fornecido no construtor, THE `GroqClient` SHALL utilizar o valor da variável de ambiente `GROQ_MODEL` se definida, ou o valor padrão `"llama3-8b-8192"` caso contrário.
3. THE `GroqClient` SHALL validar que o `Model_ID` é uma `str` não vazia no momento da construção.
4. IF o `Model_ID` fornecido é uma `str` vazia, THEN THE `GroqClient` SHALL lançar um `ValueError` com mensagem descritiva.

---

### Requirement 4: Chamada à API Groq

**User Story:** Como desenvolvedor do pipeline Tokemize, quero que o `GroqClient`
envie o prompt ao modelo Groq e retorne a resposta como string, para que o pipeline
possa usar a `Completion` no contexto otimizado.

#### Acceptance Criteria

1. WHEN `complete(prompt)` é chamado, THE `GroqClient` SHALL enviar o `Prompt` à API Groq utilizando o `groq SDK` oficial.
2. WHEN a API Groq retorna uma resposta bem-sucedida, THE `GroqClient` SHALL retornar o texto da `Completion` como uma `str`.
3. THE `GroqClient` SHALL enviar o `Prompt` como mensagem do papel `"user"` na estrutura de `messages` da API Groq.
4. IF a API Groq retorna uma resposta com `Completion` vazia ou nula, THEN THE `GroqClient` SHALL retornar uma `str` vazia.
5. THE `GroqClient` SHALL propagar exceções lançadas pelo `groq SDK` sem capturá-las, permitindo que a camada chamadora (ex: `Summarizer`) aplique o tratamento de fallback adequado.

---

### Requirement 5: Tratamento de Erros de Autenticação e Rede

**User Story:** Como desenvolvedor, quero que erros de autenticação e falhas de rede
sejam propagados com clareza, para que o pipeline possa identificar e tratar a causa
raiz sem ambiguidade.

#### Acceptance Criteria

1. IF a API Groq retorna um erro de autenticação (chave inválida ou expirada), THEN THE `GroqClient` SHALL propagar a exceção original do `groq SDK` sem modificá-la.
2. IF a chamada à API Groq falha por erro de rede ou timeout, THEN THE `GroqClient` SHALL propagar a exceção original do `groq SDK` sem modificá-la.
3. THE `GroqClient` SHALL registrar via `logging` o início de cada chamada a `complete()` e o resultado (sucesso ou tipo de exceção), sem registrar o conteúdo do `Prompt` ou o valor da `Groq_API_Key`.

---

### Requirement 6: Conformidade Estrutural com a Camada de Integração

**User Story:** Como desenvolvedor do pipeline Tokemize, quero que o `GroqClient`
siga as mesmas convenções dos demais clientes de LLM, para que a camada de integração
seja consistente e fácil de manter.

#### Acceptance Criteria

1. THE `GroqClient` SHALL residir em `src/tokemize/integrations/llm/groq_client.py`.
2. THE `GroqClient` SHALL ser exportado pelo `__init__.py` da camada `integrations/llm/`.
3. THE `GroqClient` SHALL utilizar o `groq SDK` (`groq`) como única dependência externa para comunicação com a API Groq.
4. THE `GroqClient` SHALL ser testável de forma isolada por meio de mocks do `groq SDK`, sem necessidade de credenciais reais nos testes.

---

### Requirement 7: Testes Automatizados

**User Story:** Como desenvolvedor, quero que o `GroqClient` seja coberto por testes
automatizados com pytest e hypothesis, para que o comportamento seja verificável e
regressões sejam detectadas automaticamente.

#### Acceptance Criteria

1. THE `GroqClient` SHALL ser coberto por testes unitários em `tests/test_groq_client.py`, espelhando o módulo `src/tokemize/integrations/llm/groq_client.py`.
2. THE `GroqClient` SHALL ser coberto por testes baseados em propriedades (PBT) usando `hypothesis` para verificar invariantes do método `complete()`.
3. WHEN testes são executados, THE `GroqClient` SHALL ser testado com mocks do `groq SDK`, sem realizar chamadas reais à API Groq.
4. FOR ALL `Prompt` não vazio fornecido ao `GroqClient` com mock configurado para retornar uma `str`, `complete(prompt)` SHALL retornar uma `str`.
5. FOR ALL `Prompt` fornecido ao `GroqClient` com mock configurado para lançar exceção, `complete(prompt)` SHALL propagar a exceção sem modificá-la.
