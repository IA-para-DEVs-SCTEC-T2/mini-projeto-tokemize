"""Stub funcional da etapa de varredura do repositório.

Este módulo implementa a função `scan_repository`, responsável por percorrer
o diretório do repositório e retornar uma lista de arquivos com metadados
básicos.
"""

from __future__ import annotations

import os

from tokemize.models import ScannedFile, ScanOutput


def scan_repository(repo_path: str) -> ScanOutput:
    """Varre o repositório e retorna metadados dos arquivos encontrados.

    Args:
        repo_path: Caminho absoluto ou relativo para a raiz do repositório.

    Returns:
        ScanOutput com a lista de arquivos encontrados e contadores de
        totais. Se o diretório estiver vazio, retorna ``ScanOutput`` com
        ``files=[]``, ``total_files=0`` e ``skipped_files=0``.

    Raises:
        NotADirectoryError: Se ``repo_path`` não for um diretório válido.

    Example:
        >>> output = scan_repository("/path/to/repo")
        >>> output.total_files == len(output.files)
        True
    """
    if not os.path.isdir(repo_path):
        raise NotADirectoryError(
            f"O caminho fornecido não é um diretório válido: {repo_path!r}"
        )

    # Coleta arquivos no diretório (não recursivo no stub — apenas nível raiz)
    entries = [
        entry
        for entry in os.scandir(repo_path)
        if entry.is_file()
    ]

    if not entries:
        return ScanOutput(
            repo_path=repo_path,
            files=[],
            total_files=0,
            skipped_files=0,
        )

    # Stub: usa o primeiro arquivo real encontrado como representante fictício
    # estruturalmente válido para exercitar o pipeline ponta a ponta.
    stub_entry = entries[0]
    stub_file = ScannedFile(
        path=os.path.relpath(stub_entry.path, repo_path),
        absolute_path=os.path.abspath(stub_entry.path),
        language="python",
        extension=os.path.splitext(stub_entry.name)[1] or ".py",
        size_bytes=stub_entry.stat().st_size,
        line_count=42,
    )

    files = [stub_file]
    return ScanOutput(
        repo_path=repo_path,
        files=files,
        total_files=len(files),
        skipped_files=0,
    )
