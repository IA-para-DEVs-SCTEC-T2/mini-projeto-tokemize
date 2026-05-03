# Requirements Document

## Introduction

O módulo `summarizer.py` é responsável por gerar resumos técnicos compactos de arquivos
de código-fonte relevantes usando LLMs (OpenAI GPT-4o ou Anthropic Claude). O resumo
substitui o conteúdo completo do arquivo quando o budget de tokens é limitado, reduzindo
o custo de chamadas ao LLM sem perder informação estrutural essencial.

O módulo integra-se ao pipeline existente do Tokemize: recebe um arquivo relevante com
seu conteúdo, consulta o cache antes de chamar a API, e retorna um resumo técnico
controlado mesmo em caso de falha da API.

## Glossary

- **Summarizer**: Componente responsável por gerar e cachear resumos técnicos de arquivos via LLM.
- **LLM_Client**: Abstração comum para chamadas a provedores de LLM (OpenAI, Anthropic). Nunca instanciado diretamente fora da camada de integração.
- **FileCache**: Componente existente em `src/tokemize/cache.py` que persiste entradas indexadas por hash de arquivo.
- **Summary**: Texto técnico compacto gerado pelo LLM descrevendo propósito, estruturas e dependências relevantes de um arquivo.
- **Cache_Entry**: Entrada no `FileCache` contendo o resumo previamente gerado para um arquivo com determinado hash de conteúdo.
- **API_Key**: Credencial de acesso ao provedor de LLM, carregada exclusivamente via variável de ambiente (nunca hardcoded).
- **Fallback_Message**: Mensagem de texto controlada retornada pelo Summarizer quando a chamada à API falha, permitindo que o pipeline continue.
- **File_Path**: Caminho absoluto ou relativo ao arquivo de código-fonte a ser resumido.
- **File_Content**: Conteúdo textual do arquivo de código-fonte fornecido ao Summarizer.

## Requirements

### Requirement 1: Geração de Resumo Técnico

**User Story:** Como desenvolvedor usando o pipeline Tokemize, quero que o Summarizer
gere um resumo técnico compacto de um arquivo de código-fonte, para que eu possa
incluir informação estrutural relevante no contexto do LLM sem enviar o arquivo completo.

#### Acceptance Criteria

1. WHEN um `File_Path` e um `File_Content` válidos são fornecidos ao `Summarizer`, THE `Summarizer` SHALL retornar um `Summary` não vazio descrevendo o propósito, estruturas principais e dependências do arquivo.
2. THE `Summarizer` SHALL gerar o `Summary` por meio de uma chamada ao `LLM_Client`, sem implementar lógica de sumarização diretamente.
3. THE `Summarizer` SHALL aceitar `File_Path` do tipo `str` ou `pathlib.Path` e `File_Content` do tipo `str` como parâmetros de entrada.
4. THE `Summarizer` SHALL retornar o `Summary` como uma `str`.
5. WHEN o `File_Content` está vazio, THE `Summarizer` SHALL retornar uma `str` vazia sem chamar o `LLM_Client`.

---

### Requirement 2: Cache de Resumos

**User Story:** Como desenvolvedor, quero que o Summarizer evite chamadas repetidas à
API para o mesmo arquivo sem alterações, para que o custo de tokens seja reduzido e
o pipeline seja mais rápido.

#### Acceptance Criteria

1. WHEN um resumo para o `File_Path` já existe no `FileCache` com o mesmo hash de conteúdo, THE `Summarizer` SHALL retornar o `Summary` cacheado sem chamar o `LLM_Client`.
2. WHEN um resumo é gerado com sucesso pelo `LLM_Client`, THE `Summarizer` SHALL persistir o `Summary` no `FileCache` associado ao hash atual do arquivo.
3. WHEN o conteúdo do arquivo é alterado (hash diferente), THE `Summarizer` SHALL invalidar o `Cache_Entry` anterior e gerar um novo `Summary` via `LLM_Client`.
4. THE `Summarizer` SHALL aceitar uma instância de `FileCache` via injeção de dependência no construtor, sem instanciar o `FileCache` internamente.
5. WHERE o `FileCache` não é fornecido, THE `Summarizer` SHALL operar sem cache, chamando o `LLM_Client` a cada invocação.

---

### Requirement 3: Tratamento de Falhas da API

**User Story:** Como desenvolvedor, quero que o Summarizer trate falhas da API de LLM
de forma controlada, para que o pipeline não seja interrompido quando o serviço estiver
indisponível ou retornar erro.

#### Acceptance Criteria

1. IF a chamada ao `LLM_Client` lança uma exceção, THEN THE `Summarizer` SHALL capturar a exceção, registrar o erro via `logging` e retornar uma `Fallback_Message` predefinida.
2. THE `Fallback_Message` SHALL ser uma `str` não vazia que indica a impossibilidade de gerar o resumo, sem expor detalhes internos da exceção ao chamador.
3. IF a chamada ao `LLM_Client` lança uma exceção, THEN THE `Summarizer` SHALL não persistir nenhuma entrada no `FileCache` para aquela chamada.
4. IF a chamada ao `LLM_Client` lança uma exceção, THEN THE `Summarizer` SHALL não propagar a exceção para o chamador.

---

### Requirement 4: Carregamento de Credenciais via Variáveis de Ambiente

**User Story:** Como desenvolvedor, quero que as credenciais de API sejam carregadas
exclusivamente via variáveis de ambiente, para que nenhuma chave seja hardcoded no
código-fonte ou exposta em logs.

#### Acceptance Criteria

1. THE `Summarizer` SHALL carregar a `API_Key` exclusivamente a partir de variáveis de ambiente, utilizando `python-dotenv` para leitura do arquivo `.env`.
2. IF a variável de ambiente correspondente à `API_Key` não está definida, THEN THE `Summarizer` SHALL lançar um `EnvironmentError` com mensagem descritiva indicando qual variável está ausente.
3. THE `Summarizer` SHALL nunca registrar o valor da `API_Key` em logs ou mensagens de erro.
4. THE `LLM_Client` SHALL ser instanciado exclusivamente dentro da camada de integração (`integrations/llm/`), nunca diretamente no `Summarizer`.

---

### Requirement 5: Interface e Integração com o Pipeline

**User Story:** Como desenvolvedor do pipeline Tokemize, quero que o Summarizer exponha
uma interface clara e tipada, para que ele possa ser integrado ao `ContextSelector` e
ao `Optimizer` sem acoplamento desnecessário.

#### Acceptance Criteria

1. THE `Summarizer` SHALL expor um método público `summarize(file_path: str | Path, content: str) -> str` com type hints completos.
2. THE `Summarizer` SHALL incluir docstrings no padrão Google Style em todas as classes e métodos públicos.
3. THE `Summarizer` SHALL aceitar o `LLM_Client` via injeção de dependência no construtor, tipado por uma interface ou protocolo abstrato.
4. THE `Summarizer` SHALL registrar via `logging` o início da sumarização, cache hit, cache miss e resultado de cada operação, sem registrar o conteúdo completo do arquivo ou o valor da `API_Key`.
