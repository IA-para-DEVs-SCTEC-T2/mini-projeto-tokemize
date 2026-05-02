"""Testes unitários para o RepositoryScanner.

Cobre:
- Varredura básica de diretório
- Aplicação de lista de ignores (parametrizado)
- Coleta de metadados (linguagem, extensão, tamanho, linhas) (parametrizado)
- Arquivos com extensão não suportada são ignorados
- Diretórios ignorados por padrão (.git, node_modules, etc.)
- Diretórios ignorados customizados
- Arquivo maior que o limite é ignorado
- Diretório inválido levanta NotADirectoryError
- Proteção contra symlinks
- PermissionError tratado sem quebrar a varredura
- iter_files() lazy/streaming
- Propriedades do scanner (ignore_dirs, supported_extensions)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

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

    (root / "main.py").write_text("def main(): pass\n")
    (root / "utils.py").write_text("import os\n\ndef helper(): pass\n")
    (root / "App.java").write_text("public class App {}\n")
    (root / "index.js").write_text("function init() {}\n")
    (root / "types.ts").write_text("interface IFoo { bar(): void; }\n")
    (root / "README.md").write_text("# Readme\n")

    for ignored_dir in (".git", "node_modules", "dist", "build"):
        d = root / ignored_dir
        d.mkdir()
        (d / "file.js").write_text("// ignored\n")

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
        assert result.skipped_files >= 1

    def test_scan_invalid_directory_raises(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        """scan() deve levantar NotADirectoryError para caminho inválido."""
        with pytest.raises(NotADirectoryError, match="nao_existe"):
            scanner.scan(tmp_path / "nao_existe")

    def test_scan_file_path_raises(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        """scan() deve levantar NotADirectoryError se o caminho for um arquivo."""
        f = tmp_path / "arquivo.py"
        f.write_text("x = 1")
        with pytest.raises(NotADirectoryError):
            scanner.scan(f)


# ---------------------------------------------------------------------------
# Testes de diretórios ignorados — parametrizado
# ---------------------------------------------------------------------------


class TestIgnoreDirs:
    """Testes de aplicação da lista de diretórios ignorados."""

    @pytest.mark.parametrize("ignored_dir", [".git", "node_modules", "dist", "build"])
    def test_default_ignored_dirs_are_excluded(
        self, scanner: RepositoryScanner, repo: Path, ignored_dir: str
    ) -> None:
        """Diretórios padrão ignorados não devem aparecer nos resultados."""
        result = scanner.scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any(ignored_dir in p for p in paths)

    def test_custom_ignore_dir(self, repo: Path) -> None:
        """Diretório customizado deve ser ignorado quando adicionado à lista."""
        custom_dir = repo / "meu_cache"
        custom_dir.mkdir()
        (custom_dir / "cached.py").write_text("x = 1\n")

        scanner = RepositoryScanner(ignore_dirs={"meu_cache"})
        result = scanner.scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any("meu_cache" in p for p in paths)

    def test_custom_ignore_merges_with_defaults(self) -> None:
        """Ignorar customizado deve mesclar com DEFAULT_IGNORE_DIRS."""
        scanner = RepositoryScanner(ignore_dirs={"extra_dir"})
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

        result = RepositoryScanner().scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any("__pycache__" in p for p in paths)

    def test_egg_info_wildcard_is_ignored(self, repo: Path) -> None:
        """Diretórios com padrão *.egg-info devem ser ignorados."""
        egg_dir = repo / "mypackage.egg-info"
        egg_dir.mkdir()
        (egg_dir / "PKG-INFO").write_text("Name: mypackage\n")
        (egg_dir / "setup.py").write_text("# setup\n")

        result = RepositoryScanner().scan(repo)
        paths = [str(f.relative_path) for f in result.files]
        assert not any("egg-info" in p for p in paths)


# ---------------------------------------------------------------------------
# Testes de metadados — parametrizado por linguagem
# ---------------------------------------------------------------------------


class TestFileMetadata:
    """Testes de coleta de metadados dos arquivos."""

    @pytest.mark.parametrize(
        "extension, expected_language",
        [
            (".py", "python"),
            (".java", "java"),
            (".js", "javascript"),
            (".ts", "typescript"),
        ],
    )
    def test_metadata_language_by_extension(
        self,
        scanner: RepositoryScanner,
        repo: Path,
        extension: str,
        expected_language: str,
    ) -> None:
        """Cada extensão deve mapear para a linguagem correta nos metadados."""
        result = scanner.scan(repo)
        files = [f for f in result.files if f.extension == extension]
        assert len(files) > 0, f"Nenhum arquivo {extension} encontrado"
        assert all(f.language == expected_language for f in files)

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
        (root / "test.py").write_text("line1\nline2\nline3\n")

        result = RepositoryScanner().scan(root)
        assert len(result.files) == 1
        assert result.files[0].line_count == 3

    def test_metadata_relative_path_is_not_absolute(self, scanner: RepositoryScanner, repo: Path) -> None:
        """relative_path deve ser relativo à raiz do repositório."""
        result = scanner.scan(repo)
        for f in result.files:
            assert not f.relative_path.is_absolute()

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
        (root / "big.py").write_bytes(b"x = 1\n" * 200)

        scanner = RepositoryScanner(max_file_size_bytes=100)
        result = scanner.scan(root)
        assert result.total_files == 0
        assert result.skipped_files == 1

    def test_file_within_size_limit_is_included(self, tmp_path: Path) -> None:
        """Arquivo dentro do limite deve ser incluído normalmente."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "small.py").write_text("x = 1\n")

        result = RepositoryScanner(max_file_size_bytes=1024).scan(root)
        assert result.total_files == 1


# ---------------------------------------------------------------------------
# Testes de extensões suportadas — parametrizado
# ---------------------------------------------------------------------------


class TestSupportedExtensions:
    """Testes de filtragem por extensão."""

    @pytest.mark.parametrize("unsupported_file", ["notes.txt", "data.json", "style.css"])
    def test_unsupported_extension_is_skipped(self, tmp_path: Path, unsupported_file: str) -> None:
        """Arquivos com extensão não suportada devem ser ignorados."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / unsupported_file).write_text("content\n")

        result = RepositoryScanner().scan(root)
        assert result.total_files == 0
        assert result.skipped_files == 1

    def test_custom_supported_extensions(self, tmp_path: Path) -> None:
        """Scanner com extensões customizadas deve respeitar a lista fornecida."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "script.rb").write_text("puts 'hello'\n")
        (root / "main.py").write_text("print('hi')\n")

        result = RepositoryScanner(supported_extensions={".rb"}).scan(root)
        names = {f.relative_path.name for f in result.files}
        assert names == {"script.rb"}

    def test_all_supported_extensions_are_found(self, tmp_path: Path) -> None:
        """Todas as extensões suportadas devem ser detectadas."""
        root = tmp_path / "proj"
        root.mkdir()
        for ext in SUPPORTED_EXTENSIONS:
            (root / f"file{ext}").write_text("// code\n")

        result = RepositoryScanner().scan(root)
        found_exts = {f.extension for f in result.files}
        assert found_exts == SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------------------
# Testes de PermissionError
# ---------------------------------------------------------------------------


class TestPermissionError:
    """Testes de tratamento de erros de permissão."""

    def test_permission_error_on_file_does_not_crash_scanner(self, tmp_path: Path) -> None:
        """PermissionError ao ler um arquivo não deve interromper a varredura."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "readable.py").write_text("def ok(): pass\n")
        (root / "unreadable.py").write_text("def secret(): pass\n")

        original_stat = Path.stat

        def mock_stat(self: Path, **kwargs: object) -> object:
            if self.name == "unreadable.py":
                raise PermissionError(f"Acesso negado: {self}")
            return original_stat(self, **kwargs)

        with patch.object(Path, "stat", mock_stat):
            result = RepositoryScanner().scan(root)

        # O arquivo legível deve ser encontrado
        names = {f.relative_path.name for f in result.files}
        assert "readable.py" in names
        # O arquivo sem permissão deve ser contado como ignorado
        assert result.skipped_files >= 1

    def test_permission_error_on_count_lines_returns_zero(self, tmp_path: Path) -> None:
        """PermissionError ao contar linhas deve retornar 0 sem lançar exceção."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "file.py").write_text("x = 1\n")

        original_open = open

        def mock_open(path: object, mode: str = "r", **kwargs: object) -> object:
            if mode == "rb" and "file.py" in str(path):
                raise PermissionError("Acesso negado")
            return original_open(path, mode, **kwargs)  # type: ignore[call-overload]

        with patch("builtins.open", mock_open):
            result = RepositoryScanner().scan(root)

        # O arquivo deve aparecer com line_count = 0
        assert len(result.files) == 1
        assert result.files[0].line_count == 0


# ---------------------------------------------------------------------------
# Testes de symlinks
# ---------------------------------------------------------------------------


class TestSymlinks:
    """Testes de proteção contra symlinks."""

    @pytest.mark.skipif(sys.platform == "win32", reason="Symlinks requerem privilégios no Windows")
    def test_symlink_dir_is_ignored_by_default(self, tmp_path: Path) -> None:
        """Diretório symlink não deve ser seguido quando follow_symlinks=False."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "main.py").write_text("def main(): pass\n")

        # Cria um diretório real com arquivo e um symlink apontando para ele
        real_dir = tmp_path / "real_lib"
        real_dir.mkdir()
        (real_dir / "lib.py").write_text("def lib(): pass\n")
        link_dir = root / "linked_lib"
        link_dir.symlink_to(real_dir)

        scanner = RepositoryScanner(follow_symlinks=False)
        result = scanner.scan(root)
        names = {f.relative_path.name for f in result.files}

        # lib.py não deve aparecer — o symlink foi ignorado
        assert "lib.py" not in names
        assert "main.py" in names

    @pytest.mark.skipif(sys.platform == "win32", reason="Symlinks requerem privilégios no Windows")
    def test_symlink_dir_is_followed_when_enabled(self, tmp_path: Path) -> None:
        """Diretório symlink deve ser seguido quando follow_symlinks=True."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "main.py").write_text("def main(): pass\n")

        real_dir = tmp_path / "real_lib"
        real_dir.mkdir()
        (real_dir / "lib.py").write_text("def lib(): pass\n")
        link_dir = root / "linked_lib"
        link_dir.symlink_to(real_dir)

        scanner = RepositoryScanner(follow_symlinks=True)
        result = scanner.scan(root)
        names = {f.relative_path.name for f in result.files}

        assert "lib.py" in names
        assert "main.py" in names


# ---------------------------------------------------------------------------
# Testes de iter_files() — lazy/streaming
# ---------------------------------------------------------------------------


class TestIterFiles:
    """Testes do método iter_files() para avaliação preguiçosa."""

    def test_iter_files_yields_file_metadata(self, scanner: RepositoryScanner, repo: Path) -> None:
        """iter_files() deve gerar instâncias de FileMetadata."""
        for metadata in scanner.iter_files(repo):
            assert isinstance(metadata, FileMetadata)

    def test_iter_files_same_files_as_scan(self, scanner: RepositoryScanner, repo: Path) -> None:
        """iter_files() deve retornar os mesmos arquivos que scan()."""
        scan_names = {f.relative_path.name for f in scanner.scan(repo).files}
        iter_names = {f.relative_path.name for f in scanner.iter_files(repo)}
        assert scan_names == iter_names

    def test_iter_files_invalid_directory_raises(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        """iter_files() deve levantar NotADirectoryError para caminho inválido."""
        with pytest.raises(NotADirectoryError):
            list(scanner.iter_files(tmp_path / "nao_existe"))

    def test_iter_files_is_generator(self, scanner: RepositoryScanner, repo: Path) -> None:
        """iter_files() deve retornar um generator (avaliação lazy)."""
        import types
        result = scanner.iter_files(repo)
        assert isinstance(result, types.GeneratorType)

    def test_iter_files_respects_ignore_dirs(self, repo: Path) -> None:
        """iter_files() deve respeitar a lista de diretórios ignorados."""
        scanner = RepositoryScanner()
        paths = [str(f.relative_path) for f in scanner.iter_files(repo)]
        assert not any(".git" in p for p in paths)
        assert not any("node_modules" in p for p in paths)


# ---------------------------------------------------------------------------
# Testes de propriedades do scanner
# ---------------------------------------------------------------------------


class TestScannerProperties:
    """Testes das propriedades públicas do scanner."""

    @pytest.mark.parametrize("expected_dir", [".git", "node_modules", "dist", "build", ".cache", "__pycache__"])
    def test_ignore_dirs_contains_defaults(self, expected_dir: str) -> None:
        """ignore_dirs deve conter todos os diretórios padrão."""
        assert expected_dir in RepositoryScanner().ignore_dirs

    @pytest.mark.parametrize("expected_ext", [".py", ".java", ".js", ".ts"])
    def test_supported_extensions_contains_defaults(self, expected_ext: str) -> None:
        """supported_extensions deve conter as extensões padrão."""
        assert expected_ext in RepositoryScanner().supported_extensions

    def test_ignore_dirs_is_frozenset(self) -> None:
        """ignore_dirs deve ser imutável (frozenset)."""
        assert isinstance(RepositoryScanner().ignore_dirs, frozenset)

    def test_supported_extensions_is_frozenset(self) -> None:
        """supported_extensions deve ser imutável (frozenset)."""
        assert isinstance(RepositoryScanner().supported_extensions, frozenset)


# ---------------------------------------------------------------------------
# Testes de diretório vazio
# ---------------------------------------------------------------------------


class TestEmptyDirectory:
    """Testes com diretório vazio ou sem arquivos suportados."""

    def test_empty_directory_returns_empty_result(self, tmp_path: Path) -> None:
        """Diretório vazio deve retornar ScanResult com zero arquivos."""
        root = tmp_path / "empty"
        root.mkdir()
        result = RepositoryScanner().scan(root)
        assert result.total_files == 0
        assert result.files == []

    def test_directory_with_only_ignored_files(self, tmp_path: Path) -> None:
        """Diretório com apenas arquivos não suportados deve retornar zero arquivos válidos."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "README.md").write_text("# Docs\n")
        (root / "config.yaml").write_text("key: value\n")
        result = RepositoryScanner().scan(root)
        assert result.total_files == 0
