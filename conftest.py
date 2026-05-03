"""Configuração global do pytest.

Garante que ``src/`` seja o primeiro diretório no ``sys.path``, de modo que
``import tokemize`` resolva para ``src/tokemize/`` e não para o pacote stub
na raiz do repositório.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Insere src/ no início do sys.path para que src/tokemize tenha precedência
# sobre o pacote tokemize/ na raiz do repositório.
_src = str(Path(__file__).parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
