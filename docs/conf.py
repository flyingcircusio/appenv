"""Sphinx configuration for appenv documentation."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Project information
project = "appenv"
copyright = "2026, Flying Circus"
author = "Christian Theune"

# Read version from source
version_path = Path(__file__).parent.parent / "src" / "appenv.py"
for line in version_path.read_text().splitlines():
    if line.startswith("__version__"):
        release = version = line.split('"')[1]
        break
else:
    release = version = "dev"

# Extensions
extensions = [
    # Markdown support
    "myst_parser",
    # Automatic API documentation
    "autoapi.extension",
    # Source code viewing
    "sphinx.ext.viewcode",
    # Type hints in documentation
    "sphinx_autodoc_typehints",
    # AI-friendly output (llms.txt)
    "sphinx_llm.txt",
    # UX enhancements
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_togglebutton",
    # Diagrams
    "sphinx.ext.graphviz",
    # Planned features / TODOs
    "sphinx.ext.todo",
    # Social sharing metadata
    "sphinxext.opengraph",
]

# source_suffix: autoapi generates .rst internally, so register both
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}

# autoapi configuration
autoapi_type = "python"
autoapi_dirs = ["../src"]
autoapi_file_patterns = ["*.py"]
autoapi_generate_api_docs = True
autoapi_add_toctree_entry = True
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]
autoapi_keep_files = True
autoapi_python_use_implicit_namespaces = True


# Skip private members (underscore prefix except dunder)
def autoapi_skip_member(
    _app, _what: str, name: str, _obj, skip: bool, _options
) -> bool:
    if name.startswith("_") and not name.startswith("__"):
        return True
    return skip


def _suppress_autoapi_orphan_warnings(app, env, docnames):
    """Post-build hook: fix autoapi toctree for single-file modules.

    autoapi generates an empty toctree in autoapi/index.rst when the source
    is a single .py file (not a package). Add the generated module page so
    it is not reported as orphan.
    """
    autoapi_index = Path(app.srcdir) / "autoapi" / "index.rst"
    if not autoapi_index.exists():
        return
    content = autoapi_index.read_text()
    if "src/appenv/index" in content:
        return
    content = content.replace(
        ".. toctree::\n   :titlesonly:\n\n\n",
        ".. toctree::\n   :titlesonly:\n\n   src/appenv/index\n\n",
    )
    autoapi_index.write_text(content)


# --- Stub type injection for autoapi ---

_STUB_PATH = Path(__file__).parent.parent / "src" / "appenv.pyi"


def _parse_stub_types(stub_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Parse .pyi stub to extract typed signatures and attribute types.

    Returns (func_sigs, attr_types) where:
    - func_sigs: qualified_name -> "(param: type, ...) -> RetType"
    - attr_types: qualified_name -> "TypeAnnotation"
    """
    if not stub_path.exists():
        return {}, {}

    tree = ast.parse(stub_path.read_text())
    func_sigs: dict[str, str] = {}
    attr_types: dict[str, str] = {}

    def _ann(node: ast.expr) -> str:
        return ast.unparse(node)

    def _is_ellipsis(node: ast.expr | None) -> bool:
        return isinstance(node, ast.Constant) and node.value is ...

    def _build_params(args: ast.arguments, strip_self: bool = False) -> str:
        parts: list[str] = []
        pos_args = list(args.args)
        if strip_self and pos_args and pos_args[0].arg == "self":
            pos_args = pos_args[1:]

        defaults_offset = len(args.args) - len(args.defaults)

        for i, arg in enumerate(pos_args):
            orig_i = i + (len(args.args) - len(pos_args))
            p = arg.arg
            if arg.annotation:
                p += f": {_ann(arg.annotation)}"
            di = orig_i - defaults_offset
            if 0 <= di < len(args.defaults) and not _is_ellipsis(args.defaults[di]):
                p += f" = {ast.unparse(args.defaults[di])}"
            parts.append(p)

        if args.vararg:
            p = f"*{args.vararg.arg}"
            if args.vararg.annotation:
                p += f": {_ann(args.vararg.annotation)}"
            parts.append(p)
        elif args.kwonlyargs:
            parts.append("*")

        for i, arg in enumerate(args.kwonlyargs):
            p = arg.arg
            if arg.annotation:
                p += f": {_ann(arg.annotation)}"
            kw_default = args.kw_defaults[i]
            if kw_default is not None and not _is_ellipsis(kw_default):
                p += f" = {ast.unparse(kw_default)}"
            parts.append(p)

        if args.kwarg:
            p = f"**{args.kwarg.arg}"
            if args.kwarg.annotation:
                p += f": {_ann(args.kwarg.annotation)}"
            parts.append(p)

        return ", ".join(parts)

    def _build_sig(func: ast.FunctionDef, strip_self: bool = False) -> str:
        params = _build_params(func.args, strip_self)
        sig = f"({params})"
        if func.returns:
            sig += f" -> {_ann(func.returns)}"
        return sig

    def _is_property(func: ast.FunctionDef) -> bool:
        return any(
            isinstance(d, ast.Name) and d.id == "property" for d in func.decorator_list
        )

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            func_sigs[node.name] = _build_sig(node)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            attr_types[node.target.id] = _ann(node.annotation)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and _is_property(item):
                    if item.returns:
                        attr_types[f"{node.name}.{item.name}"] = _ann(item.returns)
                elif isinstance(item, ast.FunctionDef):
                    func_sigs[f"{node.name}.{item.name}"] = _build_sig(
                        item, strip_self=True
                    )
                elif isinstance(item, ast.AnnAssign) and isinstance(
                    item.target, ast.Name
                ):
                    attr_types[f"{node.name}.{item.target.id}"] = _ann(item.annotation)

    return func_sigs, attr_types


def _inject_stub_types(app, env, docnames):
    """Post-autoapi hook: inject type information from .pyi stubs."""
    try:
        func_sigs, attr_types = _parse_stub_types(_STUB_PATH)
    except SyntaxError:
        return
    if not func_sigs and not attr_types:
        return

    autoapi_dir = Path(app.srcdir) / "autoapi"
    if not autoapi_dir.exists():
        return

    for rst_file in autoapi_dir.rglob("*.rst"):
        content = rst_file.read_text()
        patched = _patch_rst_with_stub_types(content, func_sigs, attr_types)
        if patched != content:
            rst_file.write_text(patched)


def _patch_rst_with_stub_types(
    content: str, func_sigs: dict[str, str], attr_types: dict[str, str]
) -> str:
    """Patch autoapi-generated RST with type information from stubs."""
    lines = content.split("\n")
    result: list[str] = []
    current_class: str | None = None

    for i, line in enumerate(lines):
        patched = line
        next_line = lines[i + 1] if i + 1 < len(lines) else ""

        # Track class/exception context and patch constructor params
        m = re.match(r"^\.\. py:(class|exception):: (\w+)", line)
        if m:
            current_class = m.group(2)
            init_key = f"{current_class}.__init__"
            if init_key in func_sigs:
                # Extract params only (drop return type from __init__)
                params = func_sigs[init_key].split(" -> ", 1)[0]
                patched = re.sub(r"\(.*\)$", params, line, count=1)

        # Module-level functions
        m = re.match(r"^(\.\. py:function:: )(\w+)\(.*\)$", line)
        if m:
            name = m.group(2)
            if name in func_sigs:
                patched = f"{m.group(1)}{name}{func_sigs[name]}"

        # Module-level data/variables
        m = re.match(r"^(\.\. py:data:: )(\w+)$", line)
        if m:
            name = m.group(2)
            if name in attr_types and ":type:" not in next_line:
                patched += f"\n   :type: {attr_types[name]}"

        # Class methods (indented under class)
        m = re.match(r"^(\s+)(\.\. py:method:: )(\w+)\(.*\)$", line)
        if m and current_class:
            indent, prefix, name = m.group(1), m.group(2), m.group(3)
            key = f"{current_class}.{name}"
            if key in func_sigs:
                patched = f"{indent}{prefix}{name}{func_sigs[key]}"

        # Class properties
        m = re.match(r"^(\s+)(\.\. py:property:: )(\w+)$", line)
        if m and current_class:
            indent, prefix, name = m.group(1), m.group(2), m.group(3)
            key = f"{current_class}.{name}"
            if key in attr_types and ":type:" not in next_line:
                patched += f"\n{indent}   :type: {attr_types[key]}"

        # Class attributes
        m = re.match(r"^(\s+)(\.\. py:attribute:: )(\w+)$", line)
        if m and current_class:
            indent, prefix, name = m.group(1), m.group(2), m.group(3)
            key = f"{current_class}.{name}"
            if key in attr_types and ":type:" not in next_line:
                patched += f"\n{indent}   :type: {attr_types[key]}"

        result.append(patched)

    return "\n".join(result)


def setup(app):
    app.connect("autoapi-skip-member", autoapi_skip_member)
    app.connect("env-before-read-docs", _suppress_autoapi_orphan_warnings)
    app.connect("env-before-read-docs", _inject_stub_types)


# MyST configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
    "dollarmath",
]
myst_heading_anchors = 3
myst_all_links_external = False

# sphinx-copybutton configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | "
copybutton_prompt_is_regexp = True

# Type hints presentation
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# sphinx-llm configuration
llms_txt_build_parallel = True
llms_txt_full_build = True
llms_txt_suffix_mode = "auto"
llms_txt_description = (
    "appenv - Self-contained bootstrapping and updating of Python CLI applications"
)

# sphinx.ext.todo configuration
todo_include_todos = True

# sphinx.ext.graphviz configuration
graphviz_output_format = "svg"

# Theme configuration
html_theme = "furo"
html_title = f"appenv {release}"
html_theme_options = {
    "source_repository": "https://github.com/flyingcircusio/appenv/",
    "source_branch": "main",
    "source_directory": "docs/",
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "light_css_variables": {
        "font-stack": "Inter, sans-serif",
    },
}

# Templates path
templates_path = ["_templates"]

# Exclude patterns
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Suppress specific warnings that are known and harmless
suppress_warnings = [
    "myst.header",
]
