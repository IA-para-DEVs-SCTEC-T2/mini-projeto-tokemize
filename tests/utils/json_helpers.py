"""Funções auxiliares para manipulação de JSON nos testes.

Fornece utilitários para leitura e escrita de arquivos JSON, comparação
profunda de estruturas JSON e carregamento de fixtures localizadas em
tests/fixtures/.

Requirements: 2.1–2.9
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Diretório raiz dos fixtures de teste
_FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Leitura e escrita de JSON
# ---------------------------------------------------------------------------


def read_json(path: str | Path) -> Any:
    """Lê e desserializa um arquivo JSON.

    Args:
        path: Caminho para o arquivo JSON a ser lido.

    Returns:
        Objeto Python desserializado do JSON (dict, list, etc.).

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        json.JSONDecodeError: Se o conteúdo não for JSON válido.

    Example:
        >>> data = read_json("tests/fixtures/config-sample.json")
        >>> isinstance(data, dict)
        True
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any, *, indent: int = 2) -> None:
    """Serializa e escreve dados em um arquivo JSON.

    Cria os diretórios pai automaticamente se não existirem.

    Args:
        path: Caminho de destino para o arquivo JSON.
        data: Objeto Python a ser serializado (dict, list, etc.).
        indent: Número de espaços para indentação. Padrão: 2.

    Example:
        >>> import tempfile, os
        >>> with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        ...     tmp = f.name
        >>> write_json(tmp, {"key": "value"})
        >>> read_json(tmp)
        {'key': 'value'}
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(data, indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )


def json_round_trip(data: Any) -> Any:
    """Serializa e desserializa dados via JSON (round-trip).

    Útil para verificar que um objeto é serializável e que os tipos
    são preservados corretamente após a serialização.

    Args:
        data: Objeto Python a ser submetido ao round-trip JSON.

    Returns:
        Objeto Python após serialização e desserialização.

    Example:
        >>> original = {"totalTests": 42, "coverage": 85.5}
        >>> result = json_round_trip(original)
        >>> result == original
        True
    """
    return json.loads(json.dumps(data, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Comparação profunda de estruturas JSON
# ---------------------------------------------------------------------------


def deep_equals(a: Any, b: Any) -> bool:
    """Compara duas estruturas JSON por igualdade profunda.

    Realiza a comparação via round-trip JSON para normalizar tipos
    (ex: floats com precisão diferente, None vs null).

    Args:
        a: Primeira estrutura a comparar.
        b: Segunda estrutura a comparar.

    Returns:
        True se as estruturas forem equivalentes após normalização JSON.

    Example:
        >>> deep_equals({"a": 1, "b": [2, 3]}, {"a": 1, "b": [2, 3]})
        True
        >>> deep_equals({"a": 1}, {"a": 2})
        False
    """
    return json_round_trip(a) == json_round_trip(b)


def assert_json_subset(subset: dict[str, Any], full: dict[str, Any]) -> None:
    """Verifica que todas as chaves e valores de 'subset' estão presentes em 'full'.

    Útil para verificar que um merge preservou campos específicos sem
    precisar comparar o objeto inteiro.

    Args:
        subset: Dict cujas chaves e valores devem estar presentes em 'full'.
        full: Dict que deve conter todas as entradas de 'subset'.

    Raises:
        AssertionError: Se alguma chave de 'subset' estiver ausente em 'full'
            ou se os valores não forem iguais.

    Example:
        >>> assert_json_subset({"status": "passing"}, {"status": "passing", "total": 10})
        >>> # Não levanta exceção
    """
    for key, expected_value in subset.items():
        assert key in full, f"Chave '{key}' ausente no dict completo"
        actual_value = full[key]
        assert deep_equals(actual_value, expected_value), (
            f"Valor divergente para chave '{key}': "
            f"esperado {expected_value!r}, obtido {actual_value!r}"
        )


def assert_keys_preserved(
    original: dict[str, Any],
    updated: dict[str, Any],
    keys: list[str],
) -> None:
    """Verifica que chaves específicas foram preservadas após uma atualização.

    Args:
        original: Dict com os valores originais de referência.
        updated: Dict após a atualização (merge, etc.).
        keys: Lista de chaves que devem ter sido preservadas.

    Raises:
        AssertionError: Se alguma chave estiver ausente ou com valor alterado.

    Example:
        >>> orig = {"repoStats": {"stars": 42}, "testMetrics": {"total": 0}}
        >>> upd = {"repoStats": {"stars": 42}, "testMetrics": {"total": 10}}
        >>> assert_keys_preserved(orig, upd, ["repoStats"])
        >>> # Não levanta exceção
    """
    for key in keys:
        assert key in updated, f"Chave '{key}' foi removida após a atualização"
        assert deep_equals(original[key], updated[key]), (
            f"Chave '{key}' foi alterada: "
            f"original={original[key]!r}, atualizado={updated[key]!r}"
        )


# ---------------------------------------------------------------------------
# Carregamento de fixtures
# ---------------------------------------------------------------------------


def load_fixture(filename: str) -> Any:
    """Carrega e desserializa um arquivo de fixture de tests/fixtures/.

    Args:
        filename: Nome do arquivo de fixture (ex: "config-sample.json").

    Returns:
        Objeto Python desserializado do arquivo de fixture.

    Raises:
        FileNotFoundError: Se o arquivo de fixture não existir.
        json.JSONDecodeError: Se o conteúdo não for JSON válido.

    Example:
        >>> config = load_fixture("config-sample.json")
        >>> "repoStats" in config
        True
    """
    fixture_path = _FIXTURES_DIR / filename
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Fixture '{filename}' não encontrada em {_FIXTURES_DIR}"
        )
    return read_json(fixture_path)


def load_pytest_report_fixture() -> dict[str, Any]:
    """Carrega o fixture de relatório pytest de exemplo.

    Returns:
        Dict com o conteúdo de tests/fixtures/pytest-report-sample.json.
    """
    return load_fixture("pytest-report-sample.json")


def load_coverage_fixture() -> dict[str, Any]:
    """Carrega o fixture de relatório de cobertura de exemplo.

    Returns:
        Dict com o conteúdo de tests/fixtures/coverage-sample.json.
    """
    return load_fixture("coverage-sample.json")


def load_config_fixture() -> dict[str, Any]:
    """Carrega o fixture de config.json de exemplo.

    Returns:
        Dict com o conteúdo de tests/fixtures/config-sample.json.
    """
    return load_fixture("config-sample.json")


def fixtures_dir() -> Path:
    """Retorna o caminho absoluto para o diretório tests/fixtures/.

    Returns:
        Path para o diretório de fixtures.
    """
    return _FIXTURES_DIR
