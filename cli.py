"""Entrypoint raiz da CLI do Tokemize.

Delega para ``tokemize.cli`` onde toda a lógica está definida.
"""

from tokemize.cli import app

if __name__ == "__main__":
    app()
