"""Analisador sintático baseado em Tree-sitter para o Tokemize.

Extrai artefatos estruturais (classes, funções, métodos, imports) de arquivos
de código-fonte usando grammars Tree-sitter para Python, Java, JavaScript e
TypeScript.

Abordagem de extração:
    Usa child_by_field_name() — a API declarativa recomendada pelo Tree-sitter
    para acessar nós nomeados na gramática (ex: name:, body:, parameters:).
    Isso substitui a navegação manual por tipo de nó, tornando o código mais
    conciso, preciso e resiliente a mudanças de gramática.

Thread-safety:
    O dicionário _PARSERS é compartilhado entre instâncias. Parsers do
    Tree-sitter não são thread-safe. Para uso concorrente, instancie um
    TreeSitterAnalyzer por thread ou use threading.local().
"""

from __future__ import annotations

import logging
from pathlib import Path

import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjs
import tree_sitter_python as tspython
import tree_sitter_typescript as tsts
from tree_sitter import Language, Node, Parser

from tokemize.models.artifact import Artifact

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Linguagens suportadas
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES: dict[str, str] = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
}


class UnsupportedLanguageError(ValueError):
    """Lançada quando a extensão do arquivo não tem grammar Tree-sitter mapeado.

    Args:
        extension: Extensão do arquivo não suportada.
    """

    def __init__(self, extension: str) -> None:
        super().__init__(
            f"Extensão '{extension}' não é suportada. "
            f"Extensões suportadas: {sorted(SUPPORTED_LANGUAGES.keys())}"
        )
        self.extension = extension


class ParseError(RuntimeError):
    """Lançada quando o Tree-sitter falha ao processar o arquivo.

    Args:
        file_path: Caminho do arquivo que causou o erro.
        message: Descrição do erro.
    """

    def __init__(self, file_path: Path, message: str) -> None:
        super().__init__(f"Erro ao analisar '{file_path}': {message}")
        self.file_path = file_path


# ---------------------------------------------------------------------------
# Parsers lazy — um por linguagem, criados na primeira chamada
#
# AVISO DE THREAD-SAFETY: este dicionário é compartilhado. Para uso
# concorrente, use threading.local() ou instancie parsers por thread.
# ---------------------------------------------------------------------------

_PARSERS: dict[str, Parser] = {}


def _get_parser(language: str) -> Parser:
    """Retorna (ou cria) o parser Tree-sitter para a linguagem.

    Args:
        language: Nome da linguagem ("python", "java", "javascript", "typescript").

    Returns:
        Instância de Parser configurada para a linguagem.

    Raises:
        UnsupportedLanguageError: Se a linguagem não for suportada.
    """
    if language in _PARSERS:
        return _PARSERS[language]

    lang_obj: Language
    if language == "python":
        lang_obj = Language(tspython.language())
    elif language == "java":
        lang_obj = Language(tsjava.language())
    elif language == "javascript":
        lang_obj = Language(tsjs.language())
    elif language == "typescript":
        lang_obj = Language(tsts.language_typescript())
    else:
        raise UnsupportedLanguageError(language)

    parser = Parser(lang_obj)
    _PARSERS[language] = parser
    return parser


# ---------------------------------------------------------------------------
# Utilitários de extração de texto
# ---------------------------------------------------------------------------

def _text(node: Node | None, source: bytes) -> str:
    """Extrai o texto original de um nó da AST.

    Args:
        node: Nó da AST ou None.
        source: Bytes do arquivo fonte.

    Returns:
        Texto do nó como string UTF-8, ou string vazia se node for None.
    """
    if node is None:
        return ""
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _field_text(node: Node, field: str) -> str:
    """Retorna o texto do filho acessado por nome de campo (field name).

    Usa child_by_field_name() — a API declarativa do Tree-sitter que acessa
    nós nomeados na gramática (ex: name:, body:, parameters:).

    Args:
        node: Nó pai.
        field: Nome do campo na gramática (ex: "name", "body").

    Returns:
        Texto do campo ou string vazia se o campo não existir.
    """
    child = node.child_by_field_name(field)
    if child is None:
        return ""
    return child.text.decode("utf-8", errors="replace") if child.text else ""


def _make_artifact(
    name: str,
    artifact_type: str,
    node: Node,
    source: bytes,
    language: str,
    file_path: str,
) -> Artifact:
    """Cria um Artifact a partir de um nó da AST.

    Args:
        name: Nome do artefato.
        artifact_type: Tipo: "function", "class", "method" ou "import".
        node: Nó da AST que representa o artefato completo.
        source: Bytes do arquivo fonte.
        language: Linguagem de programação.
        file_path: Caminho do arquivo de origem.

    Returns:
        Instância de Artifact com todos os metadados preenchidos.
    """
    return Artifact(
        name=name,
        type=artifact_type,
        start_line=node.start_point.row + 1,
        end_line=node.end_point.row + 1,
        language=language,
        content=_text(node, source),
        file_path=file_path,
    )


# ---------------------------------------------------------------------------
# Extrator Python
# ---------------------------------------------------------------------------

def _extract_python(root: Node, source: bytes, file_path: str) -> list[Artifact]:
    """Extrai artefatos de um arquivo Python usando field names da gramática.

    Extrai:
    - import_statement / import_from_statement → "import"
    - function_definition (top-level) → "function"
    - class_definition → "class"
    - function_definition dentro de class → "method"
    - decorated_definition → delega ao nó interno preservando o range completo

    Args:
        root: Nó raiz da AST (module).
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.

    Returns:
        Lista de Artifact extraídos.
    """
    artifacts: list[Artifact] = []
    _walk_python(root, source, file_path, artifacts, inside_class=False)
    return artifacts


def _walk_python(
    node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    inside_class: bool,
) -> None:
    for child in node.children:
        if child.type == "import_statement":
            # import X  →  name via primeiro dotted_name ou aliased_import
            name = _python_import_name(child, source)
            artifacts.append(_make_artifact(name, "import", child, source, "python", file_path))

        elif child.type == "import_from_statement":
            name = _python_import_name(child, source)
            artifacts.append(_make_artifact(name, "import", child, source, "python", file_path))

        elif child.type == "decorated_definition":
            # O range do decorated_definition inclui os decorators
            inner = next(
                (c for c in child.children if c.type in ("function_definition", "class_definition")),
                None,
            )
            if inner:
                _process_python_def(inner, child, source, file_path, artifacts, inside_class)

        elif child.type == "function_definition":
            _process_python_def(child, child, source, file_path, artifacts, inside_class)

        elif child.type == "class_definition":
            _process_python_def(child, child, source, file_path, artifacts, inside_class)


def _process_python_def(
    node: Node,
    range_node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    inside_class: bool,
) -> None:
    """Processa uma definição Python (função ou classe) e extrai o artefato.

    Args:
        node: Nó da definição (function_definition ou class_definition).
        range_node: Nó cujo range define start/end line (inclui decorators se houver).
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.
        artifacts: Lista acumuladora.
        inside_class: True se está dentro de uma classe.
    """
    # child_by_field_name("name") acessa o campo `name:` da gramática Python
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return
    name = name_node.text.decode("utf-8", errors="replace") if name_node.text else ""
    if not name:
        return

    if node.type == "function_definition":
        artifact_type = "method" if inside_class else "function"
        artifacts.append(_make_artifact(name, artifact_type, range_node, source, "python", file_path))

    elif node.type == "class_definition":
        artifacts.append(_make_artifact(name, "class", range_node, source, "python", file_path))
        # Percorre o corpo da classe para extrair métodos
        body = node.child_by_field_name("body")
        if body:
            _walk_python(body, source, file_path, artifacts, inside_class=True)


def _python_import_name(node: Node, source: bytes) -> str:
    """Extrai o nome representativo de um import Python.

    Para `import os` → "os"
    Para `from pathlib import Path` → "pathlib.Path"

    Args:
        node: Nó import_statement ou import_from_statement.
        source: Bytes do arquivo fonte.

    Returns:
        Nome do import como string.
    """
    if node.type == "import_statement":
        for child in node.children:
            if child.type in ("dotted_name", "aliased_import"):
                return child.text.decode("utf-8", errors="replace") if child.text else ""
        return _text(node, source).strip()

    # import_from_statement: from <module> import <name>
    module = ""
    imported = ""
    for child in node.children:
        if child.type == "dotted_name" and not module:
            module = child.text.decode("utf-8", errors="replace") if child.text else ""
        elif child.type in ("dotted_name", "identifier") and module:
            imported = child.text.decode("utf-8", errors="replace") if child.text else ""
            break
    if module and imported:
        return f"{module}.{imported}"
    return module or _text(node, source).strip()


# ---------------------------------------------------------------------------
# Extrator Java
# ---------------------------------------------------------------------------

def _extract_java(root: Node, source: bytes, file_path: str) -> list[Artifact]:
    """Extrai artefatos de um arquivo Java usando field names da gramática.

    Extrai:
    - import_declaration → "import"
    - class_declaration / interface_declaration / enum_declaration → "class"
    - method_declaration / constructor_declaration → "method"

    Args:
        root: Nó raiz da AST (program).
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.

    Returns:
        Lista de Artifact extraídos.
    """
    artifacts: list[Artifact] = []
    _walk_java(root, source, file_path, artifacts, inside_class=False)
    return artifacts


def _walk_java(
    node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    inside_class: bool,
) -> None:
    for child in node.children:
        if child.type == "import_declaration":
            # Java: import java.util.List; → scoped_identifier ou identifier
            name = ""
            for c in child.children:
                if c.type in ("scoped_identifier", "identifier"):
                    name = c.text.decode("utf-8", errors="replace") if c.text else ""
                    break
            artifacts.append(
                _make_artifact(name or _text(child, source).strip(), "import", child, source, "java", file_path)
            )

        elif child.type in ("class_declaration", "interface_declaration", "enum_declaration"):
            # child_by_field_name("name") acessa o campo `name:` da gramática Java
            name = _field_text(child, "name")
            if name:
                artifacts.append(_make_artifact(name, "class", child, source, "java", file_path))
            # Percorre o corpo para métodos
            body = child.child_by_field_name("body")
            if body:
                _walk_java(body, source, file_path, artifacts, inside_class=True)

        elif child.type in ("method_declaration", "constructor_declaration") and inside_class:
            name = _field_text(child, "name")
            if name:
                artifacts.append(_make_artifact(name, "method", child, source, "java", file_path))

        else:
            _walk_java(child, source, file_path, artifacts, inside_class)


# ---------------------------------------------------------------------------
# Extrator JavaScript
# ---------------------------------------------------------------------------

def _extract_javascript(root: Node, source: bytes, file_path: str) -> list[Artifact]:
    """Extrai artefatos de um arquivo JavaScript usando field names da gramática.

    Extrai:
    - import_statement → "import"
    - class_declaration → "class"
    - method_definition → "method"
    - function_declaration → "function"
    - lexical_declaration / variable_declaration com arrow/function → "function"

    Args:
        root: Nó raiz da AST (program).
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.

    Returns:
        Lista de Artifact extraídos.
    """
    artifacts: list[Artifact] = []
    _walk_js(root, source, file_path, artifacts, language="javascript", inside_class=False)
    return artifacts


def _walk_js(
    node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    language: str,
    inside_class: bool,
) -> None:
    for child in node.children:
        if child.type == "import_statement":
            name = _js_import_name(child, source)
            artifacts.append(_make_artifact(name, "import", child, source, language, file_path))

        elif child.type == "class_declaration":
            # child_by_field_name("name") acessa o campo `name:` da gramática JS/TS
            name = _field_text(child, "name")
            if name:
                artifacts.append(_make_artifact(name, "class", child, source, language, file_path))
            body = child.child_by_field_name("body")
            if body:
                _walk_js(body, source, file_path, artifacts, language, inside_class=True)

        elif child.type == "method_definition" and inside_class:
            # child_by_field_name("name") acessa o campo `name:` da gramática JS/TS
            name = _field_text(child, "name")
            if name:
                artifacts.append(_make_artifact(name, "method", child, source, language, file_path))

        elif child.type == "function_declaration":
            # child_by_field_name("name") acessa o campo `name:` da gramática JS/TS
            name = _field_text(child, "name")
            if name:
                artifacts.append(_make_artifact(name, "function", child, source, language, file_path))

        elif child.type in ("lexical_declaration", "variable_declaration"):
            _extract_js_variable_fn(child, source, file_path, artifacts, language)

        else:
            _walk_js(child, source, file_path, artifacts, language, inside_class)


def _extract_js_variable_fn(
    node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    language: str,
) -> None:
    """Extrai funções declaradas como variáveis (arrow functions, function expressions).

    Detecta padrões como:
    - const foo = (x) => x + 1
    - const foo = function(x) { return x; }

    Args:
        node: Nó lexical_declaration ou variable_declaration.
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.
        artifacts: Lista acumuladora.
        language: "javascript" ou "typescript".
    """
    for declarator in node.children:
        if declarator.type != "variable_declarator":
            continue
        # child_by_field_name("name") acessa o campo `name:` do variable_declarator
        name_node = declarator.child_by_field_name("name")
        if name_node is None:
            continue
        name = name_node.text.decode("utf-8", errors="replace") if name_node.text else ""
        if not name:
            continue
        # child_by_field_name("value") acessa o campo `value:` do variable_declarator
        value = declarator.child_by_field_name("value")
        if value and value.type in ("arrow_function", "function_expression", "function"):
            artifacts.append(_make_artifact(name, "function", node, source, language, file_path))


def _js_import_name(node: Node, source: bytes) -> str:
    """Extrai o caminho do módulo de um import JavaScript/TypeScript.

    Args:
        node: Nó import_statement.
        source: Bytes do arquivo fonte.

    Returns:
        Caminho do módulo importado (ex: "react", "./utils").
    """
    # child_by_field_name("source") acessa o campo `source:` do import_statement
    source_node = node.child_by_field_name("source")
    if source_node and source_node.text:
        return source_node.text.decode("utf-8", errors="replace").strip("'\"")
    # Fallback: procura string literal
    for child in node.children:
        if child.type == "string" and child.text:
            return child.text.decode("utf-8", errors="replace").strip("'\"")
    return _text(node, source).strip()


# ---------------------------------------------------------------------------
# Extrator TypeScript
# ---------------------------------------------------------------------------

def _extract_typescript(root: Node, source: bytes, file_path: str) -> list[Artifact]:
    """Extrai artefatos de um arquivo TypeScript usando field names da gramática.

    Estende o extrator JavaScript com suporte a:
    - interface_declaration → "class" (interfaces mapeiam para "class" no modelo)

    Args:
        root: Nó raiz da AST (program).
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.

    Returns:
        Lista de Artifact extraídos.
    """
    artifacts: list[Artifact] = []
    _walk_ts(root, source, file_path, artifacts, inside_class=False)
    return artifacts


def _walk_ts(
    node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    inside_class: bool,
) -> None:
    for child in node.children:
        if child.type == "interface_declaration":
            # child_by_field_name("name") acessa o campo `name:` da gramática TS
            name = _field_text(child, "name")
            if name:
                artifacts.append(_make_artifact(name, "class", child, source, "typescript", file_path))
            body = child.child_by_field_name("body")
            if body:
                _walk_ts(body, source, file_path, artifacts, inside_class=True)

        elif child.type == "class_declaration":
            name = _field_text(child, "name")
            if name:
                artifacts.append(_make_artifact(name, "class", child, source, "typescript", file_path))
            body = child.child_by_field_name("body")
            if body:
                _walk_ts(body, source, file_path, artifacts, inside_class=True)

        elif child.type == "method_definition" and inside_class:
            name = _field_text(child, "name")
            if name:
                artifacts.append(_make_artifact(name, "method", child, source, "typescript", file_path))

        elif child.type == "function_declaration":
            name = _field_text(child, "name")
            if name:
                artifacts.append(_make_artifact(name, "function", child, source, "typescript", file_path))

        elif child.type == "import_statement":
            name = _js_import_name(child, source)
            artifacts.append(_make_artifact(name, "import", child, source, "typescript", file_path))

        elif child.type in ("lexical_declaration", "variable_declaration"):
            _extract_js_variable_fn(child, source, file_path, artifacts, "typescript")

        else:
            _walk_ts(child, source, file_path, artifacts, inside_class)


# ---------------------------------------------------------------------------
# Mapeamento de linguagem → extrator
# ---------------------------------------------------------------------------

_EXTRACTORS = {
    "python": _extract_python,
    "java": _extract_java,
    "javascript": _extract_javascript,
    "typescript": _extract_typescript,
}


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class TreeSitterAnalyzer:
    """Analisa arquivos de código-fonte com Tree-sitter e extrai artefatos.

    Suporta Python, Java, JavaScript e TypeScript. Retorna artefatos parciais
    em caso de erros de sintaxe, registrando warnings com a localização.

    A extração usa child_by_field_name() — a API declarativa do Tree-sitter
    que acessa campos nomeados na gramática, tornando o código conciso e
    resiliente a mudanças de gramática.

    Thread-safety: não é thread-safe por padrão devido ao cache _PARSERS
    compartilhado. Para uso concorrente, instancie um TreeSitterAnalyzer
    por thread.

    Args:
        language_map: Mapeamento de extensão → linguagem.
            Usa SUPPORTED_LANGUAGES por padrão.

    Example:
        >>> analyzer = TreeSitterAnalyzer()
        >>> artifacts = analyzer.analyze(Path("meu_arquivo.py"))
        >>> for a in artifacts:
        ...     print(a.type, a.name, a.start_line)
    """

    def __init__(self, language_map: dict[str, str] | None = None) -> None:
        self._language_map = language_map or SUPPORTED_LANGUAGES

    def analyze(self, file_path: Path) -> list[Artifact]:
        """Extrai artefatos sintáticos de um arquivo de código-fonte.

        Args:
            file_path: Caminho para o arquivo a ser analisado.

        Returns:
            Lista de Artifact extraídos. Pode ser parcial se houver erros
            de sintaxe — os artefatos válidos são retornados mesmo assim.

        Raises:
            UnsupportedLanguageError: Se a extensão não for suportada.
            FileNotFoundError: Se o arquivo não existir.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        ext = file_path.suffix.lower()
        language = self._language_map.get(ext)
        if language is None:
            raise UnsupportedLanguageError(ext)

        source = self._read_source(file_path)
        parser = _get_parser(language)
        tree = parser.parse(source)

        if tree.root_node.has_error:
            logger.warning(
                "Erros de sintaxe detectados em '%s'. "
                "Artefatos válidos serão retornados parcialmente.",
                file_path,
            )
            self._log_syntax_errors(tree.root_node, file_path)

        extractor = _EXTRACTORS[language]
        artifacts = extractor(tree.root_node, source, str(file_path))

        logger.debug(
            "Arquivo '%s' analisado: %d artefatos extraídos",
            file_path,
            len(artifacts),
        )
        return artifacts

    def analyze_many(self, file_paths: list[Path]) -> list[Artifact]:
        """Extrai artefatos de múltiplos arquivos.

        Arquivos que falham são logados e ignorados (não interrompem o processo).

        Args:
            file_paths: Lista de caminhos de arquivos a serem analisados.

        Returns:
            Lista concatenada de todos os artefatos extraídos.
        """
        all_artifacts: list[Artifact] = []
        for path in file_paths:
            try:
                all_artifacts.extend(self.analyze(path))
            except (UnsupportedLanguageError, FileNotFoundError) as exc:
                logger.warning("Ignorando arquivo '%s': %s", path, exc)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Erro inesperado ao analisar '%s': %s", path, exc, exc_info=True
                )
        return all_artifacts

    def detect_language(self, file_path: Path) -> str:
        """Detecta a linguagem de um arquivo pela extensão.

        Args:
            file_path: Caminho do arquivo.

        Returns:
            Nome da linguagem (ex: "python").

        Raises:
            UnsupportedLanguageError: Se a extensão não for suportada.
        """
        ext = Path(file_path).suffix.lower()
        language = self._language_map.get(ext)
        if language is None:
            raise UnsupportedLanguageError(ext)
        return language

    def _read_source(self, file_path: Path) -> bytes:
        """Lê o conteúdo de um arquivo como bytes.

        Args:
            file_path: Caminho do arquivo.

        Returns:
            Conteúdo do arquivo em bytes.

        Raises:
            ParseError: Se o arquivo não puder ser lido.
        """
        try:
            return file_path.read_bytes()
        except (OSError, PermissionError) as exc:
            raise ParseError(file_path, str(exc)) from exc

    def _log_syntax_errors(self, node: Node, file_path: Path) -> None:
        """Percorre a AST e loga os nós com erro de sintaxe.

        Args:
            node: Nó raiz da AST.
            file_path: Caminho do arquivo (para contexto no log).
        """
        if node.type == "ERROR" or node.is_missing:
            logger.warning(
                "Erro de sintaxe em '%s' na linha %d, coluna %d",
                file_path,
                node.start_point.row + 1,
                node.start_point.column + 1,
            )
        for child in node.children:
            if child.has_error:
                self._log_syntax_errors(child, file_path)
