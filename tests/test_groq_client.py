"""Testes unitários para GroqClient.

Cobre instanciação, resolução de model, validações de entrada,
comportamento do método complete() e exportação via __init__.py.
Todos os testes usam mocks do groq SDK — sem chamadas reais à API.
"""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_groq_cls(content: str | None = "resposta mock"):
    """Retorna (mock_groq_cls, mock_client) prontos para uso."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=content))]
    )
    mock_groq_cls = MagicMock(return_value=mock_client)
    return mock_groq_cls, mock_client


# ---------------------------------------------------------------------------
# Testes de instanciação
# ---------------------------------------------------------------------------

def test_groq_client_instantiation_with_valid_env():
    """Construção bem-sucedida quando GROQ_API_KEY está definida."""
    from tokemize.integrations.llm.groq_client import GroqClient

    mock_groq_cls, _ = _make_mock_groq_cls()
    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=False):
            client = GroqClient()

    assert isinstance(client, GroqClient)
    mock_groq_cls.assert_called_once_with(api_key="test-key")


def test_groq_client_uses_default_model_when_no_env():
    """Fallback para DEFAULT_MODEL quando GROQ_MODEL não está definida."""
    from tokemize.integrations.llm.groq_client import GroqClient, DEFAULT_MODEL

    mock_groq_cls, _ = _make_mock_groq_cls()
    env = {"GROQ_API_KEY": "test-key"}
    # Garante que GROQ_MODEL não está presente
    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", env, clear=False):
            with patch("os.getenv", side_effect=lambda k, *a: env.get(k)):
                client = GroqClient()

    assert client._model == DEFAULT_MODEL


def test_groq_client_uses_env_model_when_no_param():
    """Usa GROQ_MODEL do ambiente quando nenhum parâmetro é passado."""
    from tokemize.integrations.llm.groq_client import GroqClient

    mock_groq_cls, _ = _make_mock_groq_cls()
    env = {"GROQ_API_KEY": "test-key", "GROQ_MODEL": "mixtral-8x7b-32768"}
    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", env, clear=False):
            client = GroqClient()

    assert client._model == "mixtral-8x7b-32768"


def test_groq_client_uses_constructor_model_over_env():
    """Parâmetro model do construtor tem precedência sobre GROQ_MODEL env."""
    from tokemize.integrations.llm.groq_client import GroqClient

    mock_groq_cls, _ = _make_mock_groq_cls()
    env = {"GROQ_API_KEY": "test-key", "GROQ_MODEL": "llama3-70b-8192"}
    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", env, clear=False):
            client = GroqClient(model="llama3-8b-8192")

    assert client._model == "llama3-8b-8192"


# ---------------------------------------------------------------------------
# Testes de validação na construção
# ---------------------------------------------------------------------------

def test_missing_api_key_raises_environment_error():
    """EnvironmentError é lançado quando GROQ_API_KEY está ausente."""
    from tokemize.integrations.llm.groq_client import GroqClient

    mock_groq_cls, _ = _make_mock_groq_cls()
    # Remove GROQ_API_KEY do ambiente
    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
                GroqClient()


def test_empty_model_raises_value_error():
    """ValueError é lançado quando model='' é passado ao construtor."""
    from tokemize.integrations.llm.groq_client import GroqClient

    mock_groq_cls, _ = _make_mock_groq_cls()
    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=False):
            with pytest.raises(ValueError):
                GroqClient(model="")


# ---------------------------------------------------------------------------
# Testes do método complete()
# ---------------------------------------------------------------------------

def test_complete_sends_user_role_message():
    """O prompt é enviado como role='user' na chamada ao SDK."""
    from tokemize.integrations.llm.groq_client import GroqClient

    mock_groq_cls, mock_client = _make_mock_groq_cls()
    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=False):
            client = GroqClient()
            client.complete("olá mundo")

    call_kwargs = mock_client.chat.completions.create.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs["messages"]
    # Extrai messages independente de como foi passado (args ou kwargs)
    _, kwargs = mock_client.chat.completions.create.call_args
    messages = kwargs["messages"]
    assert messages == [{"role": "user", "content": "olá mundo"}]


def test_complete_returns_str():
    """complete() sempre retorna str quando o SDK retorna conteúdo válido."""
    from tokemize.integrations.llm.groq_client import GroqClient

    mock_groq_cls, _ = _make_mock_groq_cls(content="texto de resposta")
    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=False):
            client = GroqClient()
            result = client.complete("qualquer prompt")

    assert isinstance(result, str)
    assert result == "texto de resposta"


def test_complete_returns_empty_str_for_null_content():
    """Retorna '' quando choices[0].message.content é None."""
    from tokemize.integrations.llm.groq_client import GroqClient

    mock_groq_cls, _ = _make_mock_groq_cls(content=None)
    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=False):
            client = GroqClient()
            result = client.complete("prompt qualquer")

    assert result == ""
    assert isinstance(result, str)


def test_complete_propagates_sdk_exceptions():
    """Exceções lançadas pelo SDK são propagadas sem modificação."""
    from tokemize.integrations.llm.groq_client import GroqClient

    mock_groq_cls, mock_client = _make_mock_groq_cls()
    sdk_error = RuntimeError("erro simulado do SDK")
    mock_client.chat.completions.create.side_effect = sdk_error

    with patch("tokemize.integrations.llm.groq_client.groq.Groq", mock_groq_cls):
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=False):
            client = GroqClient()
            with pytest.raises(RuntimeError) as exc_info:
                client.complete("prompt")

    assert exc_info.value is sdk_error


# ---------------------------------------------------------------------------
# Teste de exportação
# ---------------------------------------------------------------------------

def test_groq_client_exported_from_init():
    """GroqClient é importável via from tokemize.integrations.llm import GroqClient."""
    from tokemize.integrations.llm import GroqClient as ImportedGroqClient
    from tokemize.integrations.llm.groq_client import GroqClient as DirectGroqClient

    assert ImportedGroqClient is DirectGroqClient
