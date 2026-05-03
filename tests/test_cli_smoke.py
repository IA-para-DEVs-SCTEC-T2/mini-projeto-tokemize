"""Smoke tests para a estrutura de arquivos e contratos de interface do Tokemize CLI.

Verifica:
- Existência de arquivos e diretórios do projeto
- Registro do comando `analyze` na instância Typer
- Assinaturas das funções dos módulos internos via `inspect`
- Importabilidade das dataclasses de `tokemize.models`
"""

import inspect
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. Estrutura de arquivos e diretórios
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
# Pacote canônico em src/tokemize/ (pythonpath = ["src"])
PKG = ROOT / "src" / "tokemize"


def test_cli_py_exists():
    assert (ROOT / "cli.py").is_file()


def test_tokemize_package_exists():
    assert PKG.is_dir()
    assert (PKG / "__init__.py").is_file()


def test_core_package_exists():
    assert (PKG / "core").is_dir()
    assert (PKG / "core" / "__init__.py").is_file()


def test_parser_package_exists():
    assert (PKG / "core" / "parser").is_dir()
    assert (PKG / "core" / "parser" / "__init__.py").is_file()


def test_selector_package_exists():
    assert (PKG / "core" / "selector").is_dir()
    assert (PKG / "core" / "selector" / "__init__.py").is_file()


def test_optimizer_package_exists():
    assert (PKG / "core" / "optimizer").is_dir()
    assert (PKG / "core" / "optimizer" / "__init__.py").is_file()


def test_integrations_llm_package_exists():
    assert (PKG / "integrations").is_dir()
    assert (PKG / "integrations" / "__init__.py").is_file()
    assert (PKG / "integrations" / "llm").is_dir()
    assert (PKG / "integrations" / "llm" / "__init__.py").is_file()


def test_models_package_exists():
    assert (PKG / "models").is_dir()
    assert (PKG / "models" / "__init__.py").is_file()


def test_stub_module_files_exist():
    assert (PKG / "core" / "parser" / "repository_analyzer.py").is_file()
    assert (PKG / "core" / "selector" / "intelligent_selector.py").is_file()
    assert (PKG / "core" / "optimizer" / "compressor.py").is_file()
    assert (PKG / "core" / "context_cache.py").is_file()
    assert (PKG / "integrations" / "llm" / "llm_dispatcher.py").is_file()


# ---------------------------------------------------------------------------
# 2. Registro do comando `analyze` na instância Typer
# ---------------------------------------------------------------------------

def test_analyze_command_registered():
    from cli import app

    # When @app.command() is used without an explicit name, Typer stores None
    # in registered_commands and derives the name from the callback function.
    # We check both the explicit name (if set) and the callback function name.
    registered_names = set()
    for cmd in app.registered_commands:
        if cmd.name is not None:
            registered_names.add(cmd.name)
        if cmd.callback is not None:
            registered_names.add(cmd.callback.__name__)

    assert "analyze" in registered_names


# ---------------------------------------------------------------------------
# 3. Assinaturas das funções dos módulos internos
# ---------------------------------------------------------------------------

def test_analyze_repository_signature():
    from tokemize.core.parser.repository_analyzer import analyze_repository
    from tokemize.models import RepositoryStructure

    sig = inspect.signature(analyze_repository)
    params = sig.parameters

    assert "repo_path" in params
    assert params["repo_path"].annotation is str
    assert sig.return_annotation is RepositoryStructure


def test_select_relevant_files_signature():
    from tokemize.core.selector.intelligent_selector import select_relevant_files
    from tokemize.models import RepositoryStructure, SelectedContext

    sig = inspect.signature(select_relevant_files)
    params = sig.parameters

    assert "structure" in params
    assert params["structure"].annotation is RepositoryStructure
    assert "task_description" in params
    assert params["task_description"].annotation is str
    assert sig.return_annotation is SelectedContext


def test_compress_context_signature():
    from tokemize.core.optimizer.compressor import compress_context
    from tokemize.models import CompressedContext, SelectedContext

    sig = inspect.signature(compress_context)
    params = sig.parameters

    assert "context" in params
    assert params["context"].annotation is SelectedContext
    assert sig.return_annotation is CompressedContext


def test_get_or_update_cache_signature():
    from tokemize.core.context_cache import get_or_update_cache
    from tokemize.models import CachedContext, CompressedContext

    sig = inspect.signature(get_or_update_cache)
    params = sig.parameters

    assert "compressed" in params
    assert params["compressed"].annotation is CompressedContext
    assert "task_description" in params
    assert params["task_description"].annotation is str
    assert sig.return_annotation is CachedContext


def test_dispatch_signature():
    from tokemize.integrations.llm.llm_dispatcher import dispatch
    from tokemize.models import CachedContext

    sig = inspect.signature(dispatch)
    params = sig.parameters

    assert "cached_context" in params
    assert params["cached_context"].annotation is CachedContext
    assert sig.return_annotation is str


# ---------------------------------------------------------------------------
# 4. Importabilidade das dataclasses de tokemize.models
# ---------------------------------------------------------------------------

def test_models_importable():
    from tokemize.models import (  # noqa: F401
        CachedContext,
        CompressedContext,
        FileInfo,
        RepositoryStructure,
        SelectedContext,
    )


# ---------------------------------------------------------------------------
# 5. Importabilidade das funções a partir dos caminhos corretos em tokemize/
# ---------------------------------------------------------------------------

def test_analyze_repository_importable_from_correct_path():
    from tokemize.core.parser.repository_analyzer import analyze_repository  # noqa: F401

    assert callable(analyze_repository)


def test_select_relevant_files_importable_from_correct_path():
    from tokemize.core.selector.intelligent_selector import select_relevant_files  # noqa: F401

    assert callable(select_relevant_files)


def test_compress_context_importable_from_correct_path():
    from tokemize.core.optimizer.compressor import compress_context  # noqa: F401

    assert callable(compress_context)


def test_get_or_update_cache_importable_from_correct_path():
    from tokemize.core.context_cache import get_or_update_cache  # noqa: F401

    assert callable(get_or_update_cache)


def test_dispatch_importable_from_correct_path():
    from tokemize.integrations.llm.llm_dispatcher import dispatch  # noqa: F401

    assert callable(dispatch)


# ---------------------------------------------------------------------------
# 6. Instanciação das dataclasses com campos obrigatórios (task 2.2)
# ---------------------------------------------------------------------------

def test_fileinfo_instantiation():
    from tokemize.models import FileInfo

    f = FileInfo(path="src/main.py", language="python", size_bytes=1024)
    assert f.path == "src/main.py"
    assert f.language == "python"
    assert f.size_bytes == 1024


def test_repository_structure_instantiation():
    from tokemize.models import RepositoryStructure

    rs = RepositoryStructure(root_path="/repo")
    assert rs.root_path == "/repo"
    assert rs.files == []
    assert rs.metadata == {}


def test_selected_context_instantiation():
    from tokemize.models import SelectedContext

    sc = SelectedContext(task_description="implementar autenticação")
    assert sc.task_description == "implementar autenticação"
    assert sc.selected_files == []
    assert sc.relevance_scores == {}


def test_compressed_context_instantiation():
    from tokemize.models import CompressedContext

    cc = CompressedContext(
        task_description="implementar autenticação",
        compressed_content="resumo do contexto",
        token_count=42,
    )
    assert cc.task_description == "implementar autenticação"
    assert cc.compressed_content == "resumo do contexto"
    assert cc.token_count == 42


def test_cached_context_instantiation():
    from tokemize.models import CachedContext

    ctx = CachedContext(
        task_description="implementar autenticação",
        content="conteúdo final",
        cache_hit=True,
        token_count=42,
    )
    assert ctx.task_description == "implementar autenticação"
    assert ctx.content == "conteúdo final"
    assert ctx.cache_hit is True
    assert ctx.token_count == 42
