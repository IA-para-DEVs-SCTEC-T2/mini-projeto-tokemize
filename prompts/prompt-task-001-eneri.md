# Tarefa: Eneri — Modelos de dados + pyproject.toml

## Contexto

Você está trabalhando no projeto **Tokemize**, uma ferramenta CLI em Python 3.11+ que analisa repositórios locais e gera prompts otimizados para chatbots de IDE (Copilot, Kiro, Cursor, Windsurf).

O projeto usa:
- `src/tokemize/` como pacote principal
- `pyproject.toml` para configuração e dependências
- `pytest` para testes

## Sua responsabilidade

Você é responsável pelos **modelos de dados** e pela **configuração do projeto**.

---

## 1. `pyproject.toml` — raiz do projeto

Substitua o conteúdo atual pelo seguinte:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "tokemize"
version = "0.1.0"
description = "Agente inteligente de otimização de contexto para LLMs"
requires-python = ">=3.11"
dependencies = [
    "tree-sitter==0.25.2",
    "tree-sitter-python",
    "tree-sitter-java",
    "tree-sitter-javascript",
    "tree-sitter-typescript",
    "python-dotenv",
    "typer==0.12.3",
    "pyperclip>=1.8.2",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.5",
    "pytest-cov==6.1.0",
    "hypothesis>=6.100.0",
]

[project.scripts]
toke = "tokemize.cli:app"
tokemize = "tokemize.cli:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "."]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --import-mode=importlib"

[tool.coverage.run]
source = ["src/tokemize"]
omit = ["tests/*"]
```

---

## 2. `src/tokemize/models/file_analysis.py` — arquivo novo

Crie este arquivo:

```python
"""Modelo de dados para o resultado da análise de um arquivo de código-fonte."""

from __future__ import annotations

from dataclasses import dataclass, field

from tokemize.models.artifact import Artifact


@dataclass
class FileAnalysis:
    """Resultado da análise de um arquivo de código-fonte.

    Representa a saída do Repository_Analyzer para um único arquivo,
    contendo os artefatos sintáticos extraídos pelo Tree-sitter e os
    metadados do arquivo.

    Attributes:
        relative_path: Caminho relativo à raiz do repositório.
        language: Linguagem detectada (ex: ``"python"``, ``"unknown"``).
        artifacts: Lista de artefatos extraídos pelo Tree-sitter (funções,
            classes, métodos e imports). Vazia se a linguagem não for
            suportada.
        line_count: Número de linhas do arquivo.
        size_bytes: Tamanho do arquivo em bytes.
    """

    relative_path: str
    language: str
    artifacts: list[Artifact] = field(default_factory=list)
    line_count: int = 0
    size_bytes: int = 0
```

---

## 3. `src/tokemize/models/optimized_prompt.py` — arquivo novo

Crie este arquivo:

```python
"""Modelo de dados para o prompt final gerado pelo Prompt_Builder."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OptimizedPrompt:
    """Prompt final em Markdown gerado pelo Prompt_Builder.

    Representa o resultado da etapa de geração de prompt, contendo o
    conteúdo completo em Markdown pronto para ser copiado para a área de
    transferência e colado no chatbot da IDE.

    Attributes:
        content: Texto completo do prompt em Markdown.
        task_description: Tarefa original preservada sem modificação.
        token_estimate: Estimativa de tokens do conteúdo, calculada como
            ``len(content.split())``.
    """

    content: str
    task_description: str
    token_estimate: int = 0
```

---

## 4. `src/tokemize/models/__init__.py` — atualizar

Localize o dataclass `CompressedContext` neste arquivo e adicione o campo `artifact_count: int = 0` caso ainda não exista:

```python
@dataclass
class CompressedContext:
    task_description: str
    compressed_content: str
    token_count: int
    artifact_count: int = 0
```

Adicione também os imports e exports de `FileAnalysis` e `OptimizedPrompt` no topo do arquivo:

```python
from tokemize.models.file_analysis import FileAnalysis
from tokemize.models.optimized_prompt import OptimizedPrompt
```

E inclua `"FileAnalysis"` e `"OptimizedPrompt"` na lista `__all__`.

---

## Verificação

Após implementar, rode:

```bash
python -c "from tokemize.models import FileAnalysis, OptimizedPrompt, CompressedContext, Artifact; print('OK')"
```

Deve imprimir `OK` sem erros.
