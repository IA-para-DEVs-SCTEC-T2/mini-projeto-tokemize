"""Testes unitários para o TreeSitterAnalyzer.

Cobre:
- Extração de artefatos Python (imports, funções, classes, métodos)
- Extração de artefatos Java (imports, classes, métodos)
- Extração de artefatos JavaScript (imports, funções, classes, métodos, arrow fns)
- Extração de artefatos TypeScript (imports, funções, classes, interfaces, métodos)
- Metadados obrigatórios em todos os artefatos
- Preservação do conteúdo textual original
- UnsupportedLanguageError para extensões não suportadas
- FileNotFoundError para arquivos inexistentes
- analyze_many() ignora erros e continua
- detect_language() detecta corretamente
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tokemize.core.parser.tree_sitter_analyzer import (
    SUPPORTED_LANGUAGES,
    TreeSitterAnalyzer,
    UnsupportedLanguageError,
)
from tokemize.models.artifact import Artifact

VALID_ARTIFACT_TYPES = {"function", "class", "method", "import"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def analyzer() -> TreeSitterAnalyzer:
    """Instância padrão do TreeSitterAnalyzer."""
    return TreeSitterAnalyzer()


def _write(tmp_path: Path, filename: str, content: str) -> Path:
    """Escreve um arquivo temporário e retorna seu Path."""
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Helpers de asserção
# ---------------------------------------------------------------------------


def _assert_artifact_valid(artifact: Artifact, language: str) -> None:
    """Verifica que um artefato possui todos os metadados obrigatórios."""
    assert artifact.name, f"name vazio em {artifact}"
    assert artifact.type in VALID_ARTIFACT_TYPES, f"type inválido: {artifact.type}"
    assert artifact.start_line >= 1, f"start_line < 1: {artifact}"
    assert artifact.end_line >= artifact.start_line, f"end_line < start_line: {artifact}"
    assert artifact.language == language, f"language errada: {artifact.language}"
    assert artifact.content, f"content vazio em {artifact}"


def _find(artifacts: list[Artifact], name: str, type_: str) -> Artifact | None:
    """Encontra um artefato pelo nome e tipo."""
    return next(
        (a for a in artifacts if a.name == name and a.type == type_), None
    )


# ---------------------------------------------------------------------------
# Testes Python
# ---------------------------------------------------------------------------


class TestPythonExtraction:
    """Testes de extração de artefatos Python."""

    PYTHON_CODE = """\
import os
from pathlib import Path

class MyClass:
    def my_method(self, x: int) -> str:
        return str(x)

    def another_method(self):
        pass

def standalone_func(a, b):
    return a + b

def another_func():
    pass
"""

    def test_extracts_import_statement(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair import_statement como artefato do tipo 'import'."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        imp = _find(artifacts, "os", "import")
        assert imp is not None

    def test_extracts_from_import(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair import_from_statement como artefato do tipo 'import'."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        imp = next((a for a in artifacts if a.type == "import" and "pathlib" in a.name), None)
        assert imp is not None

    def test_extracts_class(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair class_definition como artefato do tipo 'class'."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        cls = _find(artifacts, "MyClass", "class")
        assert cls is not None

    def test_extracts_methods_inside_class(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair funções dentro de classe como tipo 'method'."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        method = _find(artifacts, "my_method", "method")
        assert method is not None
        another = _find(artifacts, "another_method", "method")
        assert another is not None

    def test_extracts_top_level_function(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair funções top-level como tipo 'function'."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        func = _find(artifacts, "standalone_func", "function")
        assert func is not None

    def test_does_not_extract_method_as_function(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Métodos dentro de classe não devem aparecer como 'function'."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        wrong = _find(artifacts, "my_method", "function")
        assert wrong is None

    def test_all_artifacts_have_valid_metadata(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Todos os artefatos Python devem ter metadados válidos."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        assert len(artifacts) > 0
        for a in artifacts:
            _assert_artifact_valid(a, "python")

    def test_content_preserves_original_text(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """O campo content deve preservar o texto original do artefato."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        func = _find(artifacts, "standalone_func", "function")
        assert func is not None
        assert "def standalone_func" in func.content
        assert "return a + b" in func.content

    def test_start_end_line_accuracy(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """start_line e end_line devem corresponder às linhas reais no arquivo."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        imp_os = _find(artifacts, "os", "import")
        assert imp_os is not None
        assert imp_os.start_line == 1
        assert imp_os.end_line == 1

    def test_file_path_in_artifact(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """file_path no artefato deve corresponder ao arquivo analisado."""
        f = _write(tmp_path, "code.py", self.PYTHON_CODE)
        artifacts = analyzer.analyze(f)
        assert all(a.file_path == str(f) for a in artifacts)

    def test_empty_file_returns_empty_list(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Arquivo Python vazio deve retornar lista vazia."""
        f = _write(tmp_path, "empty.py", "")
        artifacts = analyzer.analyze(f)
        assert artifacts == []

    def test_only_comments_returns_empty_list(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Arquivo com apenas comentários não deve gerar artefatos."""
        f = _write(tmp_path, "comments.py", "# apenas um comentário\n# outro\n")
        artifacts = analyzer.analyze(f)
        assert artifacts == []

    def test_decorated_function_extracted(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Função decorada deve ser extraída corretamente."""
        code = "@staticmethod\ndef decorated(): pass\n"
        f = _write(tmp_path, "deco.py", code)
        artifacts = analyzer.analyze(f)
        func = _find(artifacts, "decorated", "function")
        assert func is not None


# ---------------------------------------------------------------------------
# Testes Java
# ---------------------------------------------------------------------------


class TestJavaExtraction:
    """Testes de extração de artefatos Java."""

    JAVA_CODE = """\
import java.util.List;
import java.io.IOException;

public class MyService {
    public void processItems(List<String> items) {
        // process
    }

    private int calculate(int x) {
        return x * 2;
    }
}
"""

    def test_extracts_import(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair import_declaration como tipo 'import'."""
        f = _write(tmp_path, "MyService.java", self.JAVA_CODE)
        artifacts = analyzer.analyze(f)
        imports = [a for a in artifacts if a.type == "import"]
        assert len(imports) == 2

    def test_extracts_class(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair class_declaration como tipo 'class'."""
        f = _write(tmp_path, "MyService.java", self.JAVA_CODE)
        artifacts = analyzer.analyze(f)
        cls = _find(artifacts, "MyService", "class")
        assert cls is not None

    def test_extracts_methods(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair method_declaration como tipo 'method'."""
        f = _write(tmp_path, "MyService.java", self.JAVA_CODE)
        artifacts = analyzer.analyze(f)
        m1 = _find(artifacts, "processItems", "method")
        m2 = _find(artifacts, "calculate", "method")
        assert m1 is not None
        assert m2 is not None

    def test_all_artifacts_have_valid_metadata(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Todos os artefatos Java devem ter metadados válidos."""
        f = _write(tmp_path, "MyService.java", self.JAVA_CODE)
        artifacts = analyzer.analyze(f)
        assert len(artifacts) > 0
        for a in artifacts:
            _assert_artifact_valid(a, "java")

    def test_content_preserves_original_text(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """O campo content deve preservar o texto original do método Java."""
        f = _write(tmp_path, "MyService.java", self.JAVA_CODE)
        artifacts = analyzer.analyze(f)
        method = _find(artifacts, "calculate", "method")
        assert method is not None
        assert "calculate" in method.content
        assert "return x * 2" in method.content


# ---------------------------------------------------------------------------
# Testes JavaScript
# ---------------------------------------------------------------------------


class TestJavaScriptExtraction:
    """Testes de extração de artefatos JavaScript."""

    JS_CODE = (
        "class Calculator {\n"
        "    add(a, b) { return a + b; }\n"
        "    subtract(a, b) { return a - b; }\n"
        "}\n"
        "\n"
        "function greet(name) {\n"
        "    return 'Hello ' + name;\n"
        "}\n"
        "\n"
        "const multiply = (a, b) => a * b;\n"
        "const divide = function(a, b) { return a / b; };\n"
    )

    def test_extracts_class(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair class_declaration como tipo 'class'."""
        f = _write(tmp_path, "calc.js", self.JS_CODE)
        artifacts = analyzer.analyze(f)
        cls = _find(artifacts, "Calculator", "class")
        assert cls is not None

    def test_extracts_methods_inside_class(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair method_definition dentro de classe como tipo 'method'."""
        f = _write(tmp_path, "calc.js", self.JS_CODE)
        artifacts = analyzer.analyze(f)
        add = _find(artifacts, "add", "method")
        sub = _find(artifacts, "subtract", "method")
        assert add is not None
        assert sub is not None

    def test_extracts_function_declaration(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair function_declaration como tipo 'function'."""
        f = _write(tmp_path, "calc.js", self.JS_CODE)
        artifacts = analyzer.analyze(f)
        func = _find(artifacts, "greet", "function")
        assert func is not None

    def test_extracts_arrow_function(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair arrow function como tipo 'function'."""
        f = _write(tmp_path, "calc.js", self.JS_CODE)
        artifacts = analyzer.analyze(f)
        arrow = _find(artifacts, "multiply", "function")
        assert arrow is not None

    def test_extracts_function_expression(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair function expression como tipo 'function'."""
        f = _write(tmp_path, "calc.js", self.JS_CODE)
        artifacts = analyzer.analyze(f)
        fn_expr = _find(artifacts, "divide", "function")
        assert fn_expr is not None

    def test_all_artifacts_have_valid_metadata(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Todos os artefatos JavaScript devem ter metadados válidos."""
        f = _write(tmp_path, "calc.js", self.JS_CODE)
        artifacts = analyzer.analyze(f)
        assert len(artifacts) > 0
        for a in artifacts:
            _assert_artifact_valid(a, "javascript")


# ---------------------------------------------------------------------------
# Testes TypeScript
# ---------------------------------------------------------------------------


class TestTypeScriptExtraction:
    """Testes de extração de artefatos TypeScript."""

    TS_CODE = (
        "interface IShape {\n"
        "    area(): number;\n"
        "}\n"
        "\n"
        "class Circle implements IShape {\n"
        "    constructor(private radius: number) {}\n"
        "    area(): number { return Math.PI * this.radius ** 2; }\n"
        "}\n"
        "\n"
        "function createCircle(r: number): Circle {\n"
        "    return new Circle(r);\n"
        "}\n"
    )

    def test_extracts_interface_as_class(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair interface_declaration como tipo 'class'."""
        f = _write(tmp_path, "shapes.ts", self.TS_CODE)
        artifacts = analyzer.analyze(f)
        iface = _find(artifacts, "IShape", "class")
        assert iface is not None

    def test_extracts_class(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair class_declaration como tipo 'class'."""
        f = _write(tmp_path, "shapes.ts", self.TS_CODE)
        artifacts = analyzer.analyze(f)
        cls = _find(artifacts, "Circle", "class")
        assert cls is not None

    def test_extracts_methods_inside_class(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair métodos dentro de classe TypeScript como tipo 'method'."""
        f = _write(tmp_path, "shapes.ts", self.TS_CODE)
        artifacts = analyzer.analyze(f)
        method = _find(artifacts, "area", "method")
        assert method is not None

    def test_extracts_function(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Deve extrair function_declaration TypeScript como tipo 'function'."""
        f = _write(tmp_path, "shapes.ts", self.TS_CODE)
        artifacts = analyzer.analyze(f)
        func = _find(artifacts, "createCircle", "function")
        assert func is not None

    def test_all_artifacts_have_valid_metadata(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Todos os artefatos TypeScript devem ter metadados válidos."""
        f = _write(tmp_path, "shapes.ts", self.TS_CODE)
        artifacts = analyzer.analyze(f)
        assert len(artifacts) > 0
        for a in artifacts:
            _assert_artifact_valid(a, "typescript")


# ---------------------------------------------------------------------------
# Testes de erros e edge cases
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Testes de tratamento de erros e casos extremos."""

    def test_unsupported_extension_raises(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Extensão não suportada deve levantar UnsupportedLanguageError."""
        f = _write(tmp_path, "script.rb", "puts 'hello'\n")
        with pytest.raises(UnsupportedLanguageError) as exc_info:
            analyzer.analyze(f)
        assert ".rb" in str(exc_info.value)

    def test_unsupported_extension_error_message(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Mensagem de erro deve indicar a extensão não suportada."""
        f = _write(tmp_path, "data.csv", "a,b,c\n")
        with pytest.raises(UnsupportedLanguageError) as exc_info:
            analyzer.analyze(f)
        assert ".csv" in str(exc_info.value)

    def test_file_not_found_raises(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Arquivo inexistente deve levantar FileNotFoundError."""
        fake = tmp_path / "nao_existe.py"
        with pytest.raises(FileNotFoundError):
            analyzer.analyze(fake)

    def test_syntax_error_returns_partial_artifacts(
        self, analyzer: TreeSitterAnalyzer, tmp_path: Path
    ) -> None:
        """Arquivo com erro de sintaxe deve retornar artefatos válidos parcialmente."""
        code = "def valid_func():\n    pass\n\ndef broken(\n"
        f = _write(tmp_path, "broken.py", code)
        # Não deve levantar exceção
        artifacts = analyzer.analyze(f)
        # A função válida deve ser extraída
        func = _find(artifacts, "valid_func", "function")
        assert func is not None

    def test_analyze_many_skips_unsupported(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """analyze_many() deve ignorar arquivos não suportados e continuar."""
        py_file = _write(tmp_path, "code.py", "def foo(): pass\n")
        rb_file = _write(tmp_path, "script.rb", "puts 'hi'\n")

        artifacts = analyzer.analyze_many([py_file, rb_file])
        names = [a.name for a in artifacts]
        assert "foo" in names

    def test_analyze_many_skips_missing_files(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """analyze_many() deve ignorar arquivos inexistentes e continuar."""
        py_file = _write(tmp_path, "code.py", "def bar(): pass\n")
        missing = tmp_path / "ghost.py"

        artifacts = analyzer.analyze_many([py_file, missing])
        names = [a.name for a in artifacts]
        assert "bar" in names

    def test_analyze_many_concatenates_results(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """analyze_many() deve concatenar artefatos de todos os arquivos."""
        f1 = _write(tmp_path, "a.py", "def func_a(): pass\n")
        f2 = _write(tmp_path, "b.py", "def func_b(): pass\n")

        artifacts = analyzer.analyze_many([f1, f2])
        names = [a.name for a in artifacts]
        assert "func_a" in names
        assert "func_b" in names


# ---------------------------------------------------------------------------
# Testes de detect_language
# ---------------------------------------------------------------------------


class TestDetectLanguage:
    """Testes do método detect_language."""

    @pytest.mark.parametrize(
        "filename, expected_language",
        [
            ("script.py", "python"),
            ("App.java", "java"),
            ("index.js", "javascript"),
            ("types.ts", "typescript"),
        ],
    )
    def test_detect_language_by_extension(
        self,
        analyzer: TreeSitterAnalyzer,
        tmp_path: Path,
        filename: str,
        expected_language: str,
    ) -> None:
        """detect_language() deve retornar a linguagem correta para cada extensão."""
        f = tmp_path / filename
        assert analyzer.detect_language(f) == expected_language

    def test_detect_language_unsupported_raises(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """detect_language() deve levantar UnsupportedLanguageError para extensão desconhecida."""
        f = tmp_path / "file.xyz"
        with pytest.raises(UnsupportedLanguageError):
            analyzer.detect_language(f)

    def test_detect_language_case_insensitive(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """detect_language() deve ser case-insensitive para extensões."""
        f = tmp_path / "Script.PY"
        # A extensão é normalizada para lowercase no analyzer
        assert analyzer.detect_language(f) == "python"


# ---------------------------------------------------------------------------
# Testes de invariantes do modelo Artifact
# ---------------------------------------------------------------------------


class TestArtifactInvariants:
    """Testes das invariantes do dataclass Artifact."""

    def test_artifact_start_line_lte_end_line(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Todos os artefatos devem ter start_line <= end_line."""
        code = "import os\nclass Foo:\n    def bar(self): pass\ndef baz(): pass\n"
        f = _write(tmp_path, "inv.py", code)
        artifacts = analyzer.analyze(f)
        for a in artifacts:
            assert a.start_line <= a.end_line, f"Invariante violada: {a}"

    def test_artifact_type_is_valid(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Todos os artefatos devem ter type em {'function','class','method','import'}."""
        code = "import os\nclass Foo:\n    def bar(self): pass\ndef baz(): pass\n"
        f = _write(tmp_path, "types.py", code)
        artifacts = analyzer.analyze(f)
        for a in artifacts:
            assert a.type in VALID_ARTIFACT_TYPES

    def test_artifact_name_not_empty(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Todos os artefatos devem ter name não vazio."""
        code = "import os\nclass Foo:\n    def bar(self): pass\ndef baz(): pass\n"
        f = _write(tmp_path, "names.py", code)
        artifacts = analyzer.analyze(f)
        for a in artifacts:
            assert a.name.strip() != ""

    def test_artifact_content_not_empty(self, analyzer: TreeSitterAnalyzer, tmp_path: Path) -> None:
        """Todos os artefatos devem ter content não vazio."""
        code = "import os\nclass Foo:\n    def bar(self): pass\ndef baz(): pass\n"
        f = _write(tmp_path, "content.py", code)
        artifacts = analyzer.analyze(f)
        for a in artifacts:
            assert a.content.strip() != ""


# ---------------------------------------------------------------------------
# Testes diretos do modelo Artifact (__post_init__)
# ---------------------------------------------------------------------------


class TestArtifactModel:
    """Testes das validações do dataclass Artifact."""

    def test_artifact_invalid_start_end_line_raises(self) -> None:
        """Artifact com start_line > end_line deve levantar ValueError."""
        with pytest.raises(ValueError, match="start_line"):
            Artifact(
                name="foo",
                type="function",
                start_line=10,
                end_line=5,  # inválido
                language="python",
                content="def foo(): pass",
            )

    def test_artifact_invalid_type_raises(self) -> None:
        """Artifact com type inválido deve levantar ValueError."""
        with pytest.raises(ValueError, match="Tipo inválido"):
            Artifact(
                name="foo",
                type="variable",  # inválido
                start_line=1,
                end_line=1,
                language="python",
                content="x = 1",
            )

    def test_artifact_valid_construction(self) -> None:
        """Artifact com dados válidos deve ser criado sem exceção."""
        a = Artifact(
            name="my_func",
            type="function",
            start_line=1,
            end_line=3,
            language="python",
            content="def my_func(): pass",
        )
        assert a.name == "my_func"
        assert a.type == "function"
        assert a.file_path == ""  # default
