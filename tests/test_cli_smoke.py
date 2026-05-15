"""Smoke tests para a estrutura de arquivos e contratos de interface do Tokemize.

Verifica:
- Existência de arquivos e diretórios do projeto
- Assinaturas das funções dos módulos internos via inspect
- Importabilidade das dataclasses de tokemize.models
"""

import inspect
from pathlib import Path

ROOT = Path(__file__).parent.parent
PKG = ROOT / "src" / "tokemize"


# ---------------------------------------------------------------------------
# 1. Estrutura de arquivos e diretórios
# ---------------------------------------------------------------------------

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


def test_integrations_package_exists():
    assert (PKG / "integrations").is_dir()
    assert (PKG / "integrations" / "__init__.py").is_file()


def test_models_package_exists():
    assert (PKG / "models").is_dir()
    assert (PKG / "models" / "__init__.py").is_file()


def test_core_module_files_exist():
    assert (PKG / "core" / "selector" / "intelligent_selector.py").is_file()
    assert (PKG / "core" / "optimizer" / "context_saver.py").is_file()
    assert (PKG / "core" / "context_cache.py").is_file()


# ---------------------------------------------------------------------------
# 2. Assinaturas das funções dos módulos internos
# ---------------------------------------------------------------------------

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


def test_save_context_signature():
    from tokemize.core.optimizer.context_saver import save_context_model
    from tokemize.models import CompressedContext, SavedContext

    sig = inspect.signature(save_context_model)
    params = sig.parameters

    assert "compressed" in params
    assert params["compressed"].annotation is CompressedContext
    assert sig.return_annotation is SavedContext


def test_get_or_update_cache_signature():
    from tokemize.core.context_cache import get_or_update_cache
    from tokemize.models import CachedContext, SavedContext

    sig = inspect.signature(get_or_update_cache)
    params = sig.parameters

    assert "saved" in params
    assert params["saved"].annotation is SavedContext
    assert "task_description" in params
    assert params["task_description"].annotation is str
    assert sig.return_annotation is CachedContext


# ---------------------------------------------------------------------------
# 3. Importabilidade das dataclasses de tokemize.models
# ---------------------------------------------------------------------------

def test_models_importable():
    from tokemize.models import (  # noqa: F401
        CompressedContext,
        FileInfo,
        RepositoryStructure,
        SavedContext,
        SelectedContext,
    )


# ---------------------------------------------------------------------------
# 4. Importabilidade das funções a partir dos caminhos corretos
# ---------------------------------------------------------------------------

def test_select_relevant_files_importable_from_correct_path():
    from tokemize.core.selector.intelligent_selector import select_relevant_files  # noqa: F401
    assert callable(select_relevant_files)


def test_get_or_update_cache_importable_from_correct_path():
    from tokemize.core.context_cache import get_or_update_cache  # noqa: F401
    assert callable(get_or_update_cache)


def test_save_context_importable_from_correct_path():
    from tokemize.core.optimizer.context_saver import save_context  # noqa: F401
    assert callable(save_context)


# ---------------------------------------------------------------------------
# 5. Instanciação das dataclasses com campos obrigatórios
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


def test_saved_context_instantiation():
    from tokemize.models import SavedContext

    sc = SavedContext(
        task_description="implementar autenticação",
        compressed_content="resumo do contexto",
        token_count=42,
        context_file_path="outputs/context_pack.md",
    )
    assert sc.task_description == "implementar autenticação"
    assert sc.token_count == 42
    assert sc.context_file_path == "outputs/context_pack.md"
