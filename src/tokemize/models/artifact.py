"""Modelo de dados para artefatos extraídos do código-fonte."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any


@dataclass
class Artifact:
    """Unidade estrutural extraída do código-fonte pelo Parser.

    Attributes:
        name: Nome do artefato (ex: nome da função ou classe).
        type: Tipo do artefato: "function", "class", "method", "import".
        start_line: Número da linha inicial (1-indexed).
        end_line: Número da linha final (1-indexed).
        language: Linguagem de programação (ex: "python", "java").
        content: Conteúdo textual original do artefato, sem modificações.
        file_path: Caminho do arquivo de origem.
    """

    name: str
    type: str
    start_line: int
    end_line: int
    language: str
    content: str
    file_path: str = ""

    def __post_init__(self) -> None:
        """Valida invariantes do artefato.

        Raises:
            ValueError: Se start_line > end_line ou tipo inválido.
        """
        if self.start_line > self.end_line:
            raise ValueError(
                f"start_line ({self.start_line}) não pode ser maior que "
                f"end_line ({self.end_line})"
            )
        valid_types = {"function", "class", "method", "import"}
        if self.type not in valid_types:
            raise ValueError(
                f"Tipo inválido '{self.type}'. Tipos válidos: {valid_types}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serializa o artefato para um dicionário consumível pelo próximo módulo.

        Permite integração direta com o Indexer, Selector e qualquer camada
        downstream que precise de uma representação estruturada do artefato.

        Returns:
            Dicionário com todos os campos do artefato.

        Example:
            >>> artifact.to_dict()
            {
                "name": "my_func",
                "type": "function",
                "start_line": 1,
                "end_line": 5,
                "language": "python",
                "content": "def my_func(): ...",
                "file_path": "src/module.py"
            }
        """
        return dataclasses.asdict(self)
