"""Testes unitários para o RepositoryScanner.

Cobre:
- Varredura básica de diretório
- Aplicação de lista de ignores
- Coleta de metadados (linguagem, extensão, tamanho, linhas)
- Arquivos com extensão não suportada são ignorados
- Diretórios ignorados por padrão (.git, node_modules, etc.)
- Diretórios ignorados customizados
- Arquivo maior que o limite é ignorado
- Diretório inválido levanta NotADirectoryError
- Propriedades do scanner (ignore_dirs, supported_extensions)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tokemize.core.parser.scanner import (
    DEFAULT_IGNORE_DIRS,
    EXTENSION_TO_LANGUAGE,
    SUPPORTED_EXTENSIONS,
    FileMetadata,
    RepositoryScanner,
    ScanResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """Cria um repositório fake com estrutura variada para testes.

    Estrutura:
        repo/
        ├── main.py          (python)
        ├── utils.py         (python)
        ├── App.java         (java)
        ├── index.js         (javascript)
        ├── types.ts         (typescript)
        ├── README.md        (ignorado — extensão não suportada)
        ├── .git/
        │   └── config       (ignorado — dir .git)
        ├── node_modules/
        │   └── lib.js       (ignorado — dir node_modules)
        ├── dist/
        │   └── bundle.js    (ignorado — dir dist)
        ├── build/
        │   └── output.py    (ignorado — dir build)
        └── src/
            └── helper.py    (python)
    """
    root = tmp_path / "repo"
    root.mkdir()

    # Arquivos válidos
    (root / "main.py").write_text("def main(): pass\n")
    (root / "utils.py").write_text("import os\n\ndef helper(): pass\n")
    (root / "App.java").write_text("public class App {}\n")
    (root / "index.js").write_text("function init() {}\n")
    (root / "types.ts").write_text("interface IFoo { bar(): void; }\n")

    # Arquivo com extensão não suportada
    (root / "README.md").write_text("# Readme\n")

    # Diretórios ignorados
    git_dir = root / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("[core]\n")

    nm_dir = root / "node_modules"
    nm_dir.mkdir()
    (nm_dir / "lib.js").write_text("module.exports = {};\n")

    dist_dir = root / "dist"
    dist_dir.mkdir()
    (dist_dir / "bundle.js").write_text("(function(){})()\n")

    build_dir = root / "build"
    build_dir.mkdir()
    (build_dir / "output.py").write_text("x = 1\n")

    # Subdiretório válido
    src_dir = root / "src"
    src_dir.mkdir()
    (src_dir / "helper.py").write_text("def helper(): return 42\n")

    return root


@pytest.fixture()
def scanner() -> RepositoryScanner:
    """Scanner com configuração padrão."""
    return RepositoryScanner()


# ---------------------------------------------------------------------------
# Testes de varredura básica
# ---------------------------------------------------------------------------


class TestScanBasic:
    """Testes de varredura básica do repositório."""

    def test_scan_returns_scan_result(self, scanner: RepositoryScanner, repo: Path) -> None:
        """scan() deve retornar uma instância de ScanResult."""
        result = scanner.scan(repo)
        assert isinstance(result, ScanResult)

    def test_scan_root_is_resolved(self, scanner: RepositoryScanner, repo: Path) -> None:
        """ScanResult.root deve ser o caminho resolvido (absoluto)."""
        result = scanner.scan(repo)
        assert result.root == repo.resolve()

    def test_scan_finds_all_valid_files(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Deve encontrar exatamente os arquivos com extensão suportada fora de dirs ignorados."""
        result = scanner.scan(repo)
        names = {f.relative_path.name for f in result.files}
        assert names == {"main.py", "utils.py", "App.java", "index.js", "types.ts", "helper.py"}

    def test_scan_total_files_count(self, scanner: RepositoryScanner, repo: Path) -> None:
        """total_files deve refletir o número de arquivos válidos encontrados."""
        result = scanner.scan(repo)
        assert result.total_files == len(result.files)
        assert result.total_files == 6

    def test_scan_skipped_files_count(self, scanner: RepositoryScanner, repo: Path) -> None:
        """skipped_files deve contar arquivos com extensão não suportada."""
        result = scanner.scan(repo)
        # README.md é ignorado por extensão
        assert result.skipped_files >= 1

    def test_scan_invalid_directory_raises(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        """scan() deve levantar NotADirectoryError para caminho inválido."""
        fake_path = tmp_path / "nao_existe"
        with pytest.raises(NotADirectoryError, match="nao_existe"):
            scanner.scan(fake_path)

    def test_scan_file_path_raises(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        """scan() deve levantar NotADirectoryError se o caminho for um arquivo."""
        file_path = tmp_path / "arquivo.py"
        file_path.write_text("x = 1")
        with pytest.raises(NotADirectoryError):
            scanner.scan(file_path)


# ---------------------------------------------------------------------------
# Testes de diretórios ignorados
# ---------------------------------------------------------------------------


class TestIgnoreDirs:
    """Testes de aplicação da lista de diretórios ignorados."""

    def test_git_dir_is_ignored(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Arquivos dentro de .git não devem aparecer no resultado."""
        result = scanner.scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any(".git" in p for p in paths)

    def test_node_modules_is_ignored(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Arquivos dentro de node_modules não devem aparecer no resultado."""
        result = scanner.scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any("node_modules" in p for p in paths)

    def test_dist_is_ignored(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Arquivos dentro de dist não devem aparecer no resultado."""
        result = scanner.scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any("dist" in p for p in paths)

    def test_build_is_ignored(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Arquivos dentro de build não devem aparecer no resultado."""
        result = scanner.scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any("build" in p for p in paths)

    def test_custom_ignore_dir(self, repo: Path) -> None:
        """Diretório customizado deve ser ignorado quando adicionado à lista."""
        custom_dir = repo / "meu_cache"
        custom_dir.mkdir()
        (custom_dir / "cached.py").write_text("x = 1\n")

        scanner = RepositoryScanner(ignore_dirs={"meu_cache"})
        result = scanner.scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any("meu_cache" in p for p in paths)

    def test_custom_ignore_merges_with_defaults(self, repo: Path) -> None:
        """Ignorar customizado deve mesclar com DEFAULT_IGNORE_DIRS."""
        scanner = RepositoryScanner(ignore_dirs={"extra_dir"})
        # .git ainda deve ser ignorado
        assert ".git" in scanner.ignore_dirs
        assert "extra_dir" in scanner.ignore_dirs

    def test_ignored_dirs_reported_in_result(self, scanner: RepositoryScanner, repo: Path) -> None:
        """ScanResult.ignored_dirs deve conter os diretórios que foram pulados."""
        result = scanner.scan(repo)
        assert ".git" in result.ignored_dirs or "node_modules" in result.ignored_dirs

    def test_pycache_is_ignored(self, repo: Path) -> None:
        """__pycache__ deve ser ignorado por padrão."""
        cache_dir = repo / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "main.cpython-311.pyc").write_bytes(b"\x00\x00")

        scanner = RepositoryScanner()
        result = scanner.scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any("__pycache__" in p for p in paths)


# ---------------------------------------------------------------------------
# Testes de metadados dos arquivos
# ---------------------------------------------------------------------------


class TestFileMetadata:
    """Testes de coleta de metadados dos arquivos."""

    def test_metadata_language_python(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Arquivo .py deve ter linguagem 'python'."""
        result = scanner.scan(repo)
        py_files = [f for f in result.files if f.extension == ".py"]
        assert all(f.language == "python" for f in py_files)

    def test_metadata_language_java(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Arquivo .java deve ter linguagem 'java'."""
        result = scanner.scan(repo)
        java_files = [f for f in result.files if f.extension == ".java"]
        assert all(f.language == "java" for f in java_files)

    def test_metadata_language_javascript(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Arquivo .js deve ter linguagem 'javascript'."""
        result = scanner.scan(repo)
        js_files = [f for f in result.files if f.extension == ".js"]
        assert all(f.language == "javascript" for f in js_files)

    def test_metadata_language_typescript(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Arquivo .ts deve ter linguagem 'typescript'."""
        result = scanner.scan(repo)
        ts_files = [f for f in result.files if f.extension == ".ts"]
        assert all(f.language == "typescript" for f in ts_files)

    def test_metadata_size_bytes_positive(self, scanner: RepositoryScanner, repo: Path) -> None:
        """size_bytes deve ser maior que zero para arquivos não vazios."""
        result = scanner.scan(repo)
        assert all(f.size_bytes > 0 for f in result.files)

    def test_metadata_line_count_positive(self, scanner: RepositoryScanner, repo: Path) -> None:
        """line_count deve ser maior que zero para arquivos não vazios."""
        result = scanner.scan(repo)
        assert all(f.line_count > 0 for f in result.files)

    def test_metadata_line_count_accuracy(self, tmp_path: Path) -> None:
        """line_count deve refletir o número real de linhas do arquivo."""
        root = tmp_path / "proj"
        root.mkdir()
        content = "line1\nline2\nline3\n"
        (root / "test.py").write_text(content)

        scanner = RepositoryScanner()
        result = scanner.scan(root)
        assert len(result.files) == 1
        assert result.files[0].line_count == 3

    def test_metadata_relative_path(self, scanner: RepositoryScanner, repo: Path) -> None:
        """relative_path deve ser relativo à raiz do repositório."""
        result = scanner.scan(repo)
        for f in result.files:
            assert not f.relative_path.is_absolute()
            assert str(f.relative_path) != str(f.path)

    def test_metadata_absolute_path_exists(self, scanner: RepositoryScanner, repo: Path) -> None:
        """path deve ser absoluto e o arquivo deve existir."""
        result = scanner.scan(repo)
        for f in result.files:
            assert f.path.is_absolute()
            assert f.path.exists()

    def test_metadata_extension_matches_suffix(self, scanner: RepositoryScanner, repo: Path) -> None:
        """extension deve corresponder ao sufixo do arquivo."""
        result = scanner.scan(repo)
        for f in result.files:
            assert f.extension == f.path.suffix.lower()

    def test_metadata_is_file_metadata_instance(self, scanner: RepositoryScanner, repo: Path) -> None:
        """Cada item em result.files deve ser uma instância de FileMetadata."""
        result = scanner.scan(repo)
        assert all(isinstance(f, FileMetadata) for f in result.files)


# ---------------------------------------------------------------------------
# Testes de limite de tamanho de arquivo
# ---------------------------------------------------------------------------


class TestFileSizeLimit:
    """Testes de limite de tamanho de arquivo."""

    def test_file_exceeding_size_limit_is_skipped(self, tmp_path: Path) -> None:
        """Arquivo maior que max_file_size_bytes deve ser ignorado."""
        root = tmp_path / "proj"
        root.mkdir()
        big_file = root / "big.py"
        big_file.write_bytes(b"x = 1\n" * 200)  # ~1200 bytes

        scanner = RepositoryScanner(max_file_size_bytes=100)
        result = scanner.scan(root)
        assert result.total_files == 0
        assert result.skipped_files == 1

    def test_file_within_size_limit_is_included(self, tmp_path: Path) -> None:
        """Arquivo dentro do limite deve ser incluído normalmente."""
        root = tmp_path / "proj"
        root.mkdir()
        small_file = root / "small.py"
        small_file.write_text("x = 1\n")

        scanner = RepositoryScanner(max_file_size_bytes=1024)
        result = scanner.scan(root)
        assert result.total_files == 1


# ---------------------------------------------------------------------------
# Testes de extensões suportadas
# ---------------------------------------------------------------------------


class TestSupportedExtensions:
    """Testes de filtragem por extensão."""

    def test_unsupported_extension_is_skipped(self, tmp_path: Path) -> None:
        """Arquivos com extensão não suportada devem ser ignorados."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "notes.txt").write_text("hello\n")
        (root / "data.json").write_text("{}\n")
        (root / "style.css").write_text("body {}\n")

        scanner = RepositoryScanner()
        result = scanner.scan(root)
        assert result.total_files == 0
        assert result.skipped_files == 3

    def test_custom_supported_extensions(self, tmp_path: Path) -> None:
        """Scanner com extensões customizadas deve respeitar a lista fornecida."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "script.rb").write_text("puts 'hello'\n")
        (root / "main.py").write_text("print('hi')\n")

        scanner = RepositoryScanner(supported_extensions={".rb"})
        result = scanner.scan(root)
        names = {f.relative_path.name for f in result.files}
        assert names == {"script.rb"}

    def test_all_supported_extensions_are_found(self, tmp_path: Path) -> None:
        """Todas as extensões suportadas devem ser detectadas."""
        root = tmp_path / "proj"
        root.mkdir()
        for ext in SUPPORTED_EXTENSIONS:
            (root / f"file{ext}").write_text("// code\n")

        scanner = RepositoryScanner()
        result = scanner.scan(root)
        found_exts = {f.extension for f in result.files}
        assert found_exts == SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------------------
# Testes de propriedades do scanner
# ---------------------------------------------------------------------------


class TestScannerProperties:
    """Testes das propriedades públicas do scanner."""

    def test_ignore_dirs_contains_defaults(self) -> None:
        """ignore_dirs deve conter todos os diretórios padrão."""
        scanner = RepositoryScanner()
        for d in [".git", "node_modules", "dist", "build", ".cache", "__pycache__"]:
            assert d in scanner.ignore_dirs

    def test_supported_extensions_contains_defaults(self) -> None:
        """supported_extensions deve conter as extensões padrão."""
        scanner = RepositoryScanner()
        for ext in [".py", ".java", ".js", ".ts"]:
            assert ext in scanner.supported_extensions

    def test_ignore_dirs_is_frozenset(self) -> None:
        """ignore_dirs deve ser imutável (frozenset)."""
        scanner = RepositoryScanner()
        assert isinstance(scanner.ignore_dirs, frozenset)

    def test_supported_extensions_is_frozenset(self) -> None:
        """supported_extensions deve ser imutável (frozenset)."""
        scanner = RepositoryScanner()
        assert isinstance(scanner.supported_extensions, frozenset)


# ---------------------------------------------------------------------------
# Testes de diretório vazio
# ---------------------------------------------------------------------------


class TestEmptyDirectory:
    """Testes com diretório vazio ou sem arquivos suportados."""

    def test_empty_directory_returns_empty_result(self, tmp_path: Path) -> None:
        """Diretório vazio deve retornar ScanResult com zero arquivos."""
        root = tmp_path / "empty"
        root.mkdir()

        scanner = RepositoryScanner()
        result = scanner.scan(root)
        assert result.total_files == 0
        assert result.files == []

    def test_directory_with_only_ignored_files(self, tmp_path: Path) -> None:
        """Diretório com apenas arquivos não suportados deve retornar zero arquivos válidos."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "README.md").write_text("# Docs\n")
        (root / "config.yaml").write_text("key: value\n")

        scanner = RepositoryScanner()
        result = scanner.scan(root)
        assert result.total_files == 0
