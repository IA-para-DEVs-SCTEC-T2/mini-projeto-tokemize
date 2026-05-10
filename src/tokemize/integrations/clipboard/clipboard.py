"""Módulo de integração com a área de transferência do sistema operacional."""


class ClipboardError(RuntimeError):
    """Lançada quando pyperclip não consegue acessar a área de transferência.

    Attributes:
        Herda todos os atributos de RuntimeError.
    """


def copy_to_clipboard(text: str) -> None:
    """Copia text para a área de transferência do sistema operacional.

    Args:
        text: Texto a ser copiado.

    Raises:
        ClipboardError: Se pyperclip não conseguir acessar a área de
            transferência (ex: ambiente headless sem display).
    """
    try:
        import pyperclip

        pyperclip.copy(text)
    except Exception as exc:
        raise ClipboardError(
            "Não foi possível copiar o prompt para a área de transferência. "
            "Use a opção --print ou --output para acessar o conteúdo gerado."
        ) from exc
