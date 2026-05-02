"""Testes de integração: Scanner + TreeSitterAnalyzer via RepositoryParser.

Valida o fluxo completo:
    RepositoryScanner → [FileMetadata] → TreeSitterAnalyzer → [Artifact]

Cobre:
- parse() retorna RepositoryParseResult com arquivos e artefatos
- Artefatos têm file_path rastreável ao FileMetadata do scanner
- Diretórios ignorados pelo scanner não geram artefatos
- Múltiplas linguagens no mesmo repositório
- Repositório vazio ou sem arquivos suportados
- Arquivos com erro de sintaxe não interrompem o pipeline
- parse_streaming() gera os mesmos artefatos que parse()
- parse_repository() (função de conveniência) funciona corretamente
- Métricas de execução (elapsed_seconds, total_artifacts, etc.)
- Agrupamentos: by_file, by_type, by_language
- summary() retorna string legível
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tokemize.core.parser.repository_parser import (
    RepositoryParseResult,
    RepositoryParser,
    parse_repository,
)
from tokemize.core.parser.scanner import RepositoryScanner
from tokemize.core.parser.tree_sitter_analyzer import TreeSitterAnalyzer
from tokemize.models.artifact import Artifact


# ---------------------------------------------------------------------------
# Fixtures — repositório fake multi-linguagem
# ---------------------------------------------------------------------------

@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """Repositório fake com arquivos Python, Java, JS, TS e dirs ignorados.

    Estrutura:
        repo/
        ├── main.py           → function: main, import: os
        ├── utils.py          → function: helper, class: Config
        ├── Service.java      → class: Service, method: execute, import: java.util.List
        ├── app.js            → function: init, class: App, method: run
        ├── types.ts          → interface: IUser (→ class), function: createUser
        ├── README.md         → ignorado (extensão)
        ├── .git/
        │   └── config        → ignorado (dir)
        ├── node_modules/
        │   └── lib.js        → ignorado (dir)
        └── src/
            └── parser.py     → function: parse, class: Parser, method: run
    """
    root = tmp_path / "repo"
    root.mkdir()

    (root / "main.py").write_text(
        "import os\n\ndef main():\n    pass\n",
        encoding="utf-8",
    )
    (root / "utils.py").write_text(
        "class Config:\n    def load(self):\n        pass\n\ndef helper():\n    return 42\n",
        encoding="utf-8",
    )
    (root / "Service.java").write_text(
        "import java.util.List;\npublic class Service {\n    public void execute() {}\n}\n",
        encoding="utf-8",
    )
    (root / "app.js").write_text(
        "class App {\n    run() {}\n}\nfunction init() {}\n",
        encoding="utf-8",
    )
    (root / "types.ts").write_text(
        "interface IUser { name: string; }\nfunction createUser(name: string): IUser { return { name }; }\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Docs\n", encoding="utf-8")

    # Dirs ignorados
    git_dir = root / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("[core]\n")

    nm_dir = root / "node_modules"
    nm_dir.mkdir()
    (nm_dir / "lib.js").write_text("module.exports = {};\n")

    # Subdiretório válido
    src_dir = root / "src"
    src_dir.mkdir()
    (src_dir / "parser.py").write_text(
        "class Parser:\n    def run(self):\n        pass\n\ndef parse():\n    pass\n",
        encoding="utf-8",
    )

    return root


@pytest.fixture()
def parser() -> RepositoryParser:
    """RepositoryParser com configuração padrão."""
    return RepositoryParser()


# ---------------------------------------------------------------------------
# Testes do resultado básico
# ---------------------------------------------------------------------------

class TestRepositoryParserBasic:
    """Testes do fluxo básico de parse."""

    def test_parse_returns_repository_parse_result(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """parse() deve retornar uma instância de RepositoryParseResult."""
        result = parser.parse(repo)
        assert isinstance(result, RepositoryParseResult)

    def test_parse_root_is_set(self, parser: RepositoryParser, repo: Path) -> None:
        """RepositoryParseResult.root deve ser o diretório analisado."""
        result = parser.parse(repo)
        assert result.root == repo.resolve()

    def test_parse_finds_all_valid_files(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """parse() deve encontrar todos os arquivos com extensão suportada."""
        result = parser.parse(repo)
        names = {f.relative_path.name for f in result.files}
        assert names == {
            "main.py", "utils.py", "Service.java",
            "app.js", "types.ts", "parser.py",
        }

    def test_parse_total_files_matches_files_list(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """total_files deve ser igual ao tamanho da lista files."""
        result = parser.parse(repo)
        assert result.total_files == len(result.files)

    def test_parse_extracts_artifacts(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """parse() deve extrair pelo menos um artefato por arquivo válido."""
        result = parser.parse(repo)
        assert result.total_artifacts > 0
        assert result.total_artifacts == len(result.artifacts)

    def test_parse_elapsed_seconds_positive(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """elapsed_seconds deve ser maior que zero."""
        result = parser.parse(repo)
        assert result.elapsed_seconds > 0

    def test_parse_invalid_directory_raises(
        self, parser: RepositoryParser, tmp_path: Path
    ) -> None:
        """parse() deve levantar NotADirectoryError para caminho inválido."""
        with pytest.raises(NotADirectoryError):
            parser.parse(tmp_path / "nao_existe")


# ---------------------------------------------------------------------------
# Testes de rastreabilidade Scanner → Analyzer
# ---------------------------------------------------------------------------

class TestTracability:
    """Testa que artefatos são rastreáveis aos arquivos do scanner."""

    def test_artifact_file_path_matches_scanner_file(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """file_path de cada artefato deve corresponder a um arquivo do scanner."""
        result = parser.parse(repo)
        scanner_paths = {str(f.path) for f in result.files}
        for artifact in result.artifacts:
            assert artifact.file_path in scanner_paths, (
                f"Artefato '{artifact.name}' tem file_path '{artifact.file_path}' "
                f"que não está na lista do scanner"
            )

    def test_every_file_has_at_least_one_artifact(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Cada arquivo encontrado pelo scanner deve ter pelo menos 1 artefato."""
        result = parser.parse(repo)
        files_with_artifacts = {a.file_path for a in result.artifacts}
        for file_meta in result.files:
            assert str(file_meta.path) in files_with_artifacts, (
                f"Arquivo '{file_meta.relative_path}' não gerou nenhum artefato"
            )

    def test_ignored_dirs_produce_no_artifacts(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Arquivos em diretórios ignorados não devem gerar artefatos."""
        result = parser.parse(repo)
        for artifact in result.artifacts:
            assert "node_modules" not in artifact.file_path
            assert ".git" not in artifact.file_path

    def test_artifact_language_matches_file_extension(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Linguagem do artefato deve corresponder à extensão do arquivo."""
        ext_to_lang = {".py": "python", ".java": "java", ".js": "javascript", ".ts": "typescript"}
        result = parser.parse(repo)
        for artifact in result.artifacts:
            ext = Path(artifact.file_path).suffix.lower()
            expected_lang = ext_to_lang.get(ext)
            if expected_lang:
                assert artifact.language == expected_lang, (
                    f"Artefato '{artifact.name}' tem language='{artifact.language}' "
                    f"mas extensão '{ext}' esperava '{expected_lang}'"
                )


# ---------------------------------------------------------------------------
# Testes de extração por linguagem
# ---------------------------------------------------------------------------

class TestMultiLanguageExtraction:
    """Testa extração de artefatos em múltiplas linguagens no mesmo repositório."""

    def test_extracts_python_artifacts(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Deve extrair artefatos Python do repositório."""
        result = parser.parse(repo)
        py_artifacts = [a for a in result.artifacts if a.language == "python"]
        names = {a.name for a in py_artifacts}
        assert "main" in names
        assert "helper" in names
        assert "Config" in names
        assert "Parser" in names

    def test_extracts_java_artifacts(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Deve extrair artefatos Java do repositório."""
        result = parser.parse(repo)
        java_artifacts = [a for a in result.artifacts if a.language == "java"]
        names = {a.name for a in java_artifacts}
        assert "Service" in names
        assert "execute" in names

    def test_extracts_javascript_artifacts(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Deve extrair artefatos JavaScript do repositório."""
        result = parser.parse(repo)
        js_artifacts = [a for a in result.artifacts if a.language == "javascript"]
        names = {a.name for a in js_artifacts}
        assert "App" in names
        assert "init" in names

    def test_extracts_typescript_artifacts(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Deve extrair artefatos TypeScript do repositório."""
        result = parser.parse(repo)
        ts_artifacts = [a for a in result.artifacts if a.language == "typescript"]
        names = {a.name for a in ts_artifacts}
        assert "IUser" in names
        assert "createUser" in names

    def test_all_four_languages_represented(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Todas as quatro linguagens devem estar representadas nos artefatos."""
        result = parser.parse(repo)
        languages = {a.language for a in result.artifacts}
        assert languages == {"python", "java", "javascript", "typescript"}


# ---------------------------------------------------------------------------
# Testes de agrupamento
# ---------------------------------------------------------------------------

class TestGrouping:
    """Testa os métodos de agrupamento do RepositoryParseResult."""

    def test_artifacts_by_file_keys_are_file_paths(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """artifacts_by_file() deve ter como chaves os caminhos dos arquivos."""
        result = parser.parse(repo)
        by_file = result.artifacts_by_file()
        scanner_paths = {str(f.path) for f in result.files}
        for key in by_file:
            assert key in scanner_paths

    def test_artifacts_by_file_all_artifacts_present(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """artifacts_by_file() deve conter todos os artefatos sem perda."""
        result = parser.parse(repo)
        by_file = result.artifacts_by_file()
        total = sum(len(v) for v in by_file.values())
        assert total == result.total_artifacts

    def test_artifacts_by_type_valid_keys(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """artifacts_by_type() deve ter apenas tipos válidos como chaves."""
        result = parser.parse(repo)
        valid_types = {"function", "class", "method", "import"}
        for key in result.artifacts_by_type():
            assert key in valid_types

    def test_artifacts_by_type_all_artifacts_present(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """artifacts_by_type() deve conter todos os artefatos sem perda."""
        result = parser.parse(repo)
        total = sum(len(v) for v in result.artifacts_by_type().values())
        assert total == result.total_artifacts

    def test_artifacts_by_language_all_artifacts_present(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """artifacts_by_language() deve conter todos os artefatos sem perda."""
        result = parser.parse(repo)
        total = sum(len(v) for v in result.artifacts_by_language().values())
        assert total == result.total_artifacts

    def test_summary_contains_key_metrics(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """summary() deve conter as métricas principais."""
        result = parser.parse(repo)
        summary = result.summary()
        assert str(result.total_files) in summary
        assert str(result.total_artifacts) in summary
        assert "python" in summary.lower()


# ---------------------------------------------------------------------------
# Testes de resiliência
# ---------------------------------------------------------------------------

class TestResilience:
    """Testa comportamento do pipeline em situações adversas."""

    def test_syntax_error_file_does_not_stop_pipeline(
        self, tmp_path: Path
    ) -> None:
        """Arquivo com erro de sintaxe não deve interromper a análise dos demais."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "valid.py").write_text("def ok(): pass\n", encoding="utf-8")
        (root / "broken.py").write_text("def broken(\n", encoding="utf-8")

        result = RepositoryParser().parse(root)
        names = {a.name for a in result.artifacts}
        assert "ok" in names
        # broken.py pode gerar 0 artefatos mas não deve quebrar
        assert result.failed_files == 0  # erro de sintaxe parcial não é falha

    def test_empty_repository_returns_empty_result(self, tmp_path: Path) -> None:
        """Repositório sem arquivos suportados deve retornar resultado vazio."""
        root = tmp_path / "empty"
        root.mkdir()
        (root / "README.md").write_text("# Docs\n")

        result = RepositoryParser().parse(root)
        assert result.total_files == 0
        assert result.total_artifacts == 0
        assert result.artifacts == []

    def test_repository_with_only_ignored_dirs(self, tmp_path: Path) -> None:
        """Repositório com apenas dirs ignorados deve retornar resultado vazio."""
        root = tmp_path / "proj"
        root.mkdir()
        nm = root / "node_modules"
        nm.mkdir()
        (nm / "lib.js").write_text("module.exports = {};\n")

        result = RepositoryParser().parse(root)
        assert result.total_files == 0
        assert result.total_artifacts == 0

    def test_custom_ignore_dirs_respected(self, tmp_path: Path) -> None:
        """Diretórios customizados ignorados não devem gerar artefatos."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "main.py").write_text("def main(): pass\n")
        vendor = root / "vendor"
        vendor.mkdir()
        (vendor / "lib.py").write_text("def vendor_func(): pass\n")

        scanner = RepositoryScanner(ignore_dirs={"vendor"})
        result = RepositoryParser(scanner=scanner).parse(root)
        names = {a.name for a in result.artifacts}
        assert "main" in names
        assert "vendor_func" not in names


# ---------------------------------------------------------------------------
# Testes do parse_streaming()
# ---------------------------------------------------------------------------

class TestStreaming:
    """Testa o modo streaming do RepositoryParser."""

    def test_streaming_yields_artifacts(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """parse_streaming() deve gerar instâncias de Artifact."""
        artifacts = list(parser.parse_streaming(repo))
        assert len(artifacts) > 0
        assert all(isinstance(a, Artifact) for a in artifacts)

    def test_streaming_same_artifacts_as_parse(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """parse_streaming() deve gerar os mesmos artefatos que parse()."""
        batch_names = {a.name for a in parser.parse(repo).artifacts}
        stream_names = {a.name for a in parser.parse_streaming(repo)}
        assert batch_names == stream_names

    def test_streaming_respects_ignore_dirs(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """parse_streaming() não deve gerar artefatos de dirs ignorados."""
        for artifact in parser.parse_streaming(repo):
            assert "node_modules" not in artifact.file_path
            assert ".git" not in artifact.file_path

    def test_streaming_invalid_directory_raises(
        self, parser: RepositoryParser, tmp_path: Path
    ) -> None:
        """parse_streaming() deve levantar NotADirectoryError para caminho inválido."""
        with pytest.raises(NotADirectoryError):
            list(parser.parse_streaming(tmp_path / "nao_existe"))


# ---------------------------------------------------------------------------
# Testes da função de conveniência parse_repository()
# ---------------------------------------------------------------------------

class TestParseRepositoryFunction:
    """Testa a função de conveniência parse_repository()."""

    def test_parse_repository_returns_result(self, repo: Path) -> None:
        """parse_repository() deve retornar RepositoryParseResult."""
        result = parse_repository(repo)
        assert isinstance(result, RepositoryParseResult)

    def test_parse_repository_extracts_artifacts(self, repo: Path) -> None:
        """parse_repository() deve extrair artefatos do repositório."""
        result = parse_repository(repo)
        assert result.total_artifacts > 0

    def test_parse_repository_custom_ignore_dirs(self, tmp_path: Path) -> None:
        """parse_repository() deve respeitar ignore_dirs customizados."""
        root = tmp_path / "proj"
        root.mkdir()
        (root / "main.py").write_text("def main(): pass\n")
        custom = root / "custom_ignore"
        custom.mkdir()
        (custom / "hidden.py").write_text("def hidden(): pass\n")

        result = parse_repository(root, ignore_dirs={"custom_ignore"})
        names = {a.name for a in result.artifacts}
        assert "main" in names
        assert "hidden" not in names

    def test_parse_repository_public_import(self, repo: Path) -> None:
        """parse_repository deve ser importável via tokemize.repository_parser."""
        from tokemize.repository_parser import parse_repository as pr  # noqa: PLC0415
        result = pr(repo)
        assert result.total_artifacts > 0


# ---------------------------------------------------------------------------
# Testes de invariantes dos artefatos no pipeline completo
# ---------------------------------------------------------------------------

class TestArtifactInvariantsIntegration:
    """Valida invariantes dos artefatos produzidos pelo pipeline completo."""

    def test_all_artifacts_have_valid_type(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Todos os artefatos do pipeline devem ter type válido."""
        valid_types = {"function", "class", "method", "import"}
        result = parser.parse(repo)
        for a in result.artifacts:
            assert a.type in valid_types, f"type inválido: {a.type} em {a.name}"

    def test_all_artifacts_have_non_empty_name(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Todos os artefatos devem ter name não vazio."""
        result = parser.parse(repo)
        for a in result.artifacts:
            assert a.name.strip() != "", f"name vazio em {a}"

    def test_all_artifacts_have_valid_line_range(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Todos os artefatos devem ter start_line <= end_line."""
        result = parser.parse(repo)
        for a in result.artifacts:
            assert a.start_line <= a.end_line, (
                f"Invariante violada: start={a.start_line} > end={a.end_line} em {a.name}"
            )

    def test_all_artifacts_have_non_empty_content(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Todos os artefatos devem ter content não vazio."""
        result = parser.parse(repo)
        for a in result.artifacts:
            assert a.content.strip() != "", f"content vazio em {a.name}"

    def test_all_artifacts_are_json_serializable(
        self, parser: RepositoryParser, repo: Path
    ) -> None:
        """Todos os artefatos do pipeline devem ser serializáveis em JSON."""
        import json  # noqa: PLC0415
        result = parser.parse(repo)
        for a in result.artifacts:
            d = a.to_dict()
            json_str = json.dumps(d)
            assert isinstance(json_str, str)
