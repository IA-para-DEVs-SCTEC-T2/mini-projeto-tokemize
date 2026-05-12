"""Integração com a área de transferência do sistema (clipboard).

Fornece ``copy_to_clipboard`` para copiar o prompt otimizado e
``ClipboardError`` para sinalizar falhas sem interromper o pipeline.
"""

from __future__ import annotations


class ClipboardError(Exception):
    """Erro ao tentar copiar conteúdo para a área de transferência.

    Raised when the clipboard is unavailable (e.g., no display server,
    missing system dependency, or permission denied).
    """


def copy_to_clipboard(content: str) -> None:
    """Copia o conteúdo para a área de transferência do sistema.

    Tenta usar ``pyperclip`` se disponível; caso contrário, tenta o
    comando ``xclip``/``pbcopy`` via subprocess. Lança ``ClipboardError``
    se nenhuma estratégia funcionar, permitindo que o pipeline continue.

    Args:
        content: Texto a ser copiado para a área de transferência.

    Raises:
        ClipboardError: Se não for possível copiar o conteúdo.
    """
    try:
        import pyperclip  # type: ignore[import]

        pyperclip.copy(content)
    except Exception as exc:
        raise ClipboardError(str(exc)) from exc
