#!/usr/bin/env python3
"""Script para rodar os testes do orquestrador.

Uso:
    python run_tests.py              # Roda todos os testes
    python run_tests.py --optional   # Roda também os testes opcionais (property tests)
"""

import sys
import subprocess

# Argumentos para pytest
args = ["pytest", "tests/test_orchestrator.py", "tests/test_stubs.py", "-v"]

# Se --optional foi passado, remove o marker que pula testes opcionais
if "--optional" in sys.argv:
    print("Rodando TODOS os testes (incluindo property tests opcionais)...")
else:
    print("Rodando testes obrigatórios (pulando property tests opcionais)...")
    args.extend(["-m", "not optional"])

# Roda pytest
result = subprocess.run(args)
sys.exit(result.returncode)
