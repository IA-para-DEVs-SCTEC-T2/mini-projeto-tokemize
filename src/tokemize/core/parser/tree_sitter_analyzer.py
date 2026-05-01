"""Analisador sintático baseado em Tree-sitter para o Tokemize.

Extrai artefatos estruturais (classes, funções, métodos, imports) de arquivos
de código-fonte usando grammars Tree-sitter para Python, Java, JavaScript e
TypeScript.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

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
# Inicialização lazy dos parsers (um por linguagem)
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
# Extratores por linguagem
# ---------------------------------------------------------------------------

# Tipo de função extratora: recebe (node, source_bytes, file_path) → list[Artifact]
_ExtractorFn = Callable[[Node, bytes, str], list[Artifact]]


def _node_text(node: Node, source: bytes) -> str:
    """Extrai o texto original de um nó da AST.

    Args:
        node: Nó da AST.
        source: Bytes do arquivo fonte.

    Returns:
        Texto do nó como string UTF-8.
    """
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _child_text(node: Node, *types: str) -> str:
    """Retorna o texto do primeiro filho com um dos tipos especificados.

    Args:
        node: Nó pai.
        *types: Tipos de nó a procurar.

    Returns:
        Texto do filho encontrado ou string vazia.
    """
    for child in node.children:
        if child.type in types:
            return child.text.decode("utf-8", errors="replace") if child.text else ""
    return ""


# ---- Python ----------------------------------------------------------------

def _extract_python(node: Node, source: bytes, file_path: str) -> list[Artifact]:
    """Extrai artefatos de um arquivo Python.

    Percorre a AST recursivamente extraindo:
    - import_statement → type "import"
    - import_from_statement → type "import"
    - function_definition (top-level) → type "function"
    - class_definition → type "class"
    - function_definition dentro de class → type "method"
    - decorated_definition → delega ao nó interno

    Args:
        node: Nó raiz da AST.
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo (para metadados).

    Returns:
        Lista de Artifact extraídos.
    """
    artifacts: list[Artifact] = []
    _walk_python(node, source, file_path, artifacts, inside_class=False)
    return artifacts


def _walk_python(
    node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    inside_class: bool,
) -> None:
    """Percorre recursivamente a AST Python extraindo artefatos.

    Args:
        node: Nó atual da AST.
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.
        artifacts: Lista acumuladora de artefatos.
        inside_class: True se o nó atual está dentro de uma classe.
    """
    for child in node.children:
        if child.type in ("import_statement", "import_from_statement"):
            name = _python_import_name(child, source)
            artifacts.append(
                Artifact(
                    name=name,
                    type="import",
                    start_line=child.start_point.row + 1,
                    end_line=child.end_point.row + 1,
                    language="python",
                    content=_node_text(child, source),
                    file_path=file_path,
                )
            )

        elif child.type == "decorated_definition":
            # Delega ao nó interno (function_definition ou class_definition)
            # O range do decorated_definition inclui os decorators
            inner = next(
                (
                    c
                    for c in child.children
                    if c.type in ("function_definition", "class_definition")
                ),
                None,
            )
            if inner:
                _extract_python_def(
                    inner, child, source, file_path, artifacts, inside_class
                )

        elif child.type in ("function_definition", "class_definition"):
            _extract_python_def(
                child, child, source, file_path, artifacts, inside_class
            )


def _extract_python_def(
    node: Node,
    range_node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    inside_class: bool,
) -> None:
    """Extrai um artefato de definição Python (função ou classe).

    Args:
        node: Nó da definição (function_definition ou class_definition).
        range_node: Nó usado para calcular start/end line (pode incluir decorators).
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.
        artifacts: Lista acumuladora.
        inside_class: True se está dentro de uma classe.
    """
    name = _child_text(node, "identifier")
    if not name:
        return

    if node.type == "function_definition":
        artifact_type = "method" if inside_class else "function"
        artifacts.append(
            Artifact(
                name=name,
                type=artifact_type,
                start_line=range_node.start_point.row + 1,
                end_line=range_node.end_point.row + 1,
                language="python",
                content=_node_text(range_node, source),
                file_path=file_path,
            )
        )

    elif node.type == "class_definition":
        artifacts.append(
            Artifact(
                name=name,
                type="class",
                start_line=range_node.start_point.row + 1,
                end_line=range_node.end_point.row + 1,
                language="python",
                content=_node_text(range_node, source),
                file_path=file_path,
            )
        )
        # Percorre o corpo da classe para extrair métodos
        body = next(
            (c for c in node.children if c.type == "block"), None
        )
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
        # import X, Y → pega o primeiro nome
        for child in node.children:
            if child.type in ("dotted_name", "aliased_import"):
                return child.text.decode("utf-8", errors="replace") if child.text else ""
        return _node_text(node, source).strip()

    # import_from_statement: from X import Y
    module = ""
    imported = ""
    for child in node.children:
        if child.type == "dotted_name" and not module:
            module = child.text.decode("utf-8", errors="replace") if child.text else ""
        elif child.type in ("dotted_name", "identifier") and module:
            imported = child.text.decode("utf-8", errors="replace") if child.text else ""
            break
        elif child.type == "import":
            continue
    if module and imported:
        return f"{module}.{imported}"
    return module or _node_text(node, source).strip()


# ---- Java ------------------------------------------------------------------

def _extract_java(node: Node, source: bytes, file_path: str) -> list[Artifact]:
    """Extrai artefatos de um arquivo Java.

    Extrai:
    - import_declaration → type "import"
    - class_declaration / interface_declaration → type "class"
    - method_declaration / constructor_declaration → type "method"

    Args:
        node: Nó raiz da AST.
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.

    Returns:
        Lista de Artifact extraídos.
    """
    artifacts: list[Artifact] = []
    _walk_java(node, source, file_path, artifacts, inside_class=False)
    return artifacts


def _walk_java(
    node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    inside_class: bool,
) -> None:
    """Percorre recursivamente a AST Java.

    Args:
        node: Nó atual.
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.
        artifacts: Lista acumuladora.
        inside_class: True se dentro de uma classe.
    """
    for child in node.children:
        if child.type == "import_declaration":
            # Pega o scoped_identifier ou dotted_name
            name = ""
            for c in child.children:
                if c.type in ("scoped_identifier", "identifier"):
                    name = c.text.decode("utf-8", errors="replace") if c.text else ""
                    break
            artifacts.append(
                Artifact(
                    name=name or _node_text(child, source).strip(),
                    type="import",
                    start_line=child.start_point.row + 1,
                    end_line=child.end_point.row + 1,
                    language="java",
                    content=_node_text(child, source),
                    file_path=file_path,
                )
            )

        elif child.type in ("class_declaration", "interface_declaration", "enum_declaration"):
            name = _child_text(child, "identifier")
            if name:
                artifacts.append(
                    Artifact(
                        name=name,
                        type="class",
                        start_line=child.start_point.row + 1,
                        end_line=child.end_point.row + 1,
                        language="java",
                        content=_node_text(child, source),
                        file_path=file_path,
                    )
                )
            # Percorre o corpo para métodos
            _walk_java(child, source, file_path, artifacts, inside_class=True)

        elif child.type in ("method_declaration", "constructor_declaration") and inside_class:
            name = _child_text(child, "identifier")
            if name:
                artifacts.append(
                    Artifact(
                        name=name,
                        type="method",
                        start_line=child.start_point.row + 1,
                        end_line=child.end_point.row + 1,
                        language="java",
                        content=_node_text(child, source),
                        file_path=file_path,
                    )
                )

        else:
            _walk_java(child, source, file_path, artifacts, inside_class)


# ---- JavaScript ------------------------------------------------------------

def _extract_javascript(node: Node, source: bytes, file_path: str) -> list[Artifact]:
    """Extrai artefatos de um arquivo JavaScript.

    Extrai:
    - import_statement → type "import"
    - class_declaration → type "class"
    - method_definition → type "method"
    - function_declaration → type "function"
    - lexical_declaration / variable_declaration com arrow function → type "function"

    Args:
        node: Nó raiz da AST.
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.

    Returns:
        Lista de Artifact extraídos.
    """
    artifacts: list[Artifact] = []
    _walk_js(node, source, file_path, artifacts, language="javascript", inside_class=False)
    return artifacts


def _walk_js(
    node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    language: str,
    inside_class: bool,
) -> None:
    """Percorre recursivamente a AST JavaScript/TypeScript.

    Args:
        node: Nó atual.
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.
        artifacts: Lista acumuladora.
        language: "javascript" ou "typescript".
        inside_class: True se dentro de uma classe.
    """
    for child in node.children:
        if child.type == "import_statement":
            name = _js_import_name(child, source)
            artifacts.append(
                Artifact(
                    name=name,
                    type="import",
                    start_line=child.start_point.row + 1,
                    end_line=child.end_point.row + 1,
                    language=language,
                    content=_node_text(child, source),
                    file_path=file_path,
                )
            )

        elif child.type == "class_declaration":
            # JS usa "identifier", TS usa "type_identifier"
            name = _child_text(child, "identifier", "type_identifier")
            if name:
                artifacts.append(
                    Artifact(
                        name=name,
                        type="class",
                        start_line=child.start_point.row + 1,
                        end_line=child.end_point.row + 1,
                        language=language,
                        content=_node_text(child, source),
                        file_path=file_path,
                    )
                )
            # Percorre o corpo da classe
            body = next(
                (c for c in child.children if c.type == "class_body"), None
            )
            if body:
                _walk_js(body, source, file_path, artifacts, language, inside_class=True)

        elif child.type == "method_definition" and inside_class:
            name = _child_text(child, "property_identifier", "identifier")
            if name:
                artifacts.append(
                    Artifact(
                        name=name,
                        type="method",
                        start_line=child.start_point.row + 1,
                        end_line=child.end_point.row + 1,
                        language=language,
                        content=_node_text(child, source),
                        file_path=file_path,
                    )
                )

        elif child.type == "function_declaration":
            name = _child_text(child, "identifier")
            if name:
                artifacts.append(
                    Artifact(
                        name=name,
                        type="function",
                        start_line=child.start_point.row + 1,
                        end_line=child.end_point.row + 1,
                        language=language,
                        content=_node_text(child, source),
                        file_path=file_path,
                    )
                )

        elif child.type in ("lexical_declaration", "variable_declaration"):
            # Detecta: const foo = () => ... ou const foo = function() ...
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
        name = _child_text(declarator, "identifier")
        if not name:
            continue
        # Verifica se o valor é arrow_function ou function_expression
        value = next(
            (
                c
                for c in declarator.children
                if c.type in ("arrow_function", "function_expression", "function")
            ),
            None,
        )
        if value:
            artifacts.append(
                Artifact(
                    name=name,
                    type="function",
                    start_line=node.start_point.row + 1,
                    end_line=node.end_point.row + 1,
                    language=language,
                    content=_node_text(node, source),
                    file_path=file_path,
                )
            )


def _js_import_name(node: Node, source: bytes) -> str:
    """Extrai o nome representativo de um import JavaScript/TypeScript.

    Args:
        node: Nó import_statement.
        source: Bytes do arquivo fonte.

    Returns:
        Caminho do módulo importado (ex: "react", "./utils").
    """
    # Procura string literal com o caminho do módulo
    for child in node.children:
        if child.type == "string":
            text = child.text.decode("utf-8", errors="replace") if child.text else ""
            return text.strip("'\"")
    return _node_text(node, source).strip()


# ---- TypeScript ------------------------------------------------------------

def _extract_typescript(node: Node, source: bytes, file_path: str) -> list[Artifact]:
    """Extrai artefatos de um arquivo TypeScript.

    Reutiliza o walker JavaScript com linguagem "typescript".
    Adiciona suporte a interface_declaration e type_alias_declaration.

    Args:
        node: Nó raiz da AST.
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.

    Returns:
        Lista de Artifact extraídos.
    """
    artifacts: list[Artifact] = []
    _walk_ts(node, source, file_path, artifacts, inside_class=False)
    return artifacts


def _walk_ts(
    node: Node,
    source: bytes,
    file_path: str,
    artifacts: list[Artifact],
    inside_class: bool,
) -> None:
    """Percorre recursivamente a AST TypeScript.

    Estende o walker JS com suporte a interface_declaration.
    Para os demais tipos de nó, delega ao walker JS.

    Args:
        node: Nó atual.
        source: Bytes do arquivo fonte.
        file_path: Caminho do arquivo.
        artifacts: Lista acumuladora.
        inside_class: True se dentro de uma classe.
    """
    for child in node.children:
        if child.type == "interface_declaration":
            name = _child_text(child, "type_identifier", "identifier")
            if name:
                artifacts.append(
                    Artifact(
                        name=name,
                        type="class",  # interfaces mapeiam para "class" no modelo
                        start_line=child.start_point.row + 1,
                        end_line=child.end_point.row + 1,
                        language="typescript",
                        content=_node_text(child, source),
                        file_path=file_path,
                    )
                )
            # Percorre o corpo da interface para métodos
            body = next(
                (c for c in child.children if c.type == "object_type"), None
            )
            if body:
                _walk_ts(body, source, file_path, artifacts, inside_class=True)

        elif child.type == "class_declaration":
            name = _child_text(child, "type_identifier", "identifier")
            if name:
                artifacts.append(
                    Artifact(
                        name=name,
                        type="class",
                        start_line=child.start_point.row + 1,
                        end_line=child.end_point.row + 1,
                        language="typescript",
                        content=_node_text(child, source),
                        file_path=file_path,
                    )
                )
            body = next(
                (c for c in child.children if c.type == "class_body"), None
            )
            if body:
                _walk_ts(body, source, file_path, artifacts, inside_class=True)

        elif child.type == "method_definition" and inside_class:
            name = _child_text(child, "property_identifier", "identifier")
            if name:
                artifacts.append(
                    Artifact(
                        name=name,
                        type="method",
                        start_line=child.start_point.row + 1,
                        end_line=child.end_point.row + 1,
                        language="typescript",
                        content=_node_text(child, source),
                        file_path=file_path,
                    )
                )

        elif child.type == "function_declaration":
            name = _child_text(child, "identifier")
            if name:
                artifacts.append(
                    Artifact(
                        name=name,
                        type="function",
                        start_line=child.start_point.row + 1,
                        end_line=child.end_point.row + 1,
                        language="typescript",
                        content=_node_text(child, source),
                        file_path=file_path,
                    )
                )

        elif child.type == "import_statement":
            name = _js_import_name(child, source)
            artifacts.append(
                Artifact(
                    name=name,
                    type="import",
                    start_line=child.start_point.row + 1,
                    end_line=child.end_point.row + 1,
                    language="typescript",
                    content=_node_text(child, source),
                    file_path=file_path,
                )
            )

        elif child.type in ("lexical_declaration", "variable_declaration"):
            _extract_js_variable_fn(child, source, file_path, artifacts, "typescript")

        else:
            _walk_ts(child, source, file_path, artifacts, inside_class)


# ---------------------------------------------------------------------------
# Mapeamento de linguagem → extrator
# ---------------------------------------------------------------------------

_EXTRACTORS: dict[str, _ExtractorFn] = {
    "python": _extract_python,
    "java": _extract_java,
    "javascript": _extract_javascript,
    "typescript": _extract_typescript,
}

# _walk_js_single foi removido — TypeScript tem walker próprio (_walk_ts)


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class TreeSitterAnalyzer:
    """Analisa arquivos de código-fonte com Tree-sitter e extrai artefatos.

    Suporta Python, Java, JavaScript e TypeScript. Retorna artefatos parciais
    em caso de erros de sintaxe, registrando warnings com a localização.

    Args:
        language_map: Mapeamento de extensão → linguagem.
            Usa SUPPORTED_LANGUAGES por padrão.

    Example:
        >>> analyzer = TreeSitterAnalyzer()
        >>> artifacts = analyzer.analyze(Path("meu_arquivo.py"))
        >>> for a in artifacts:
        ...     print(a.type, a.name, a.start_line)
    """

    def __init__(
        self, language_map: dict[str, str] | None = None
    ) -> None:
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

        # Detecta erros de sintaxe na AST
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
                artifacts = self.analyze(path)
                all_artifacts.extend(artifacts)
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
