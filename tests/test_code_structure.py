from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src" / "green_v2"

MAX_MODULE_LINES = 600
MAX_CLASS_LINES = 300
MAX_FUNCTION_LINES = 80

FORBIDDEN_GENERIC_MODULES = {"db.py", "helpers.py", "misc.py", "utils.py"}
DOMAIN_FORBIDDEN_IMPORTS = {
    "fastapi",
    "pika",
    "psycopg",
    "uvicorn",
    "green_v2.api",
    "green_v2.application",
    "green_v2.data_access",
    "green_v2.ingestion",
    "green_v2.messaging",
    "green_v2.station_agent",
    "green_v2.workers",
}
INTERFACE_FORBIDDEN_IMPORTS = {
    "pika",
    "psycopg",
    "green_v2.data_access",
    "green_v2.messaging",
}


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _line_span(node: ast.AST) -> int:
    start = getattr(node, "lineno", 0)
    end = getattr(node, "end_lineno", start)
    return max(0, end - start + 1)


def _import_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _matches_prefix(name: str, prefixes: set[str]) -> bool:
    return any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes)


def test_python_modules_remain_readable() -> None:
    violations: list[str] = []
    for path in _python_files(SOURCE_ROOT):
        relative = path.relative_to(ROOT)
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_MODULE_LINES:
            violations.append(f"{relative}: module has {line_count} lines")
    assert not violations, "\n".join(violations)


def test_functions_and_classes_remain_focused() -> None:
    violations: list[str] = []
    for path in _python_files(SOURCE_ROOT):
        relative = path.relative_to(ROOT)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                span = _line_span(node)
                if span > MAX_FUNCTION_LINES:
                    violations.append(f"{relative}:{node.lineno} {node.name} has {span} lines")
            elif isinstance(node, ast.ClassDef):
                span = _line_span(node)
                if span > MAX_CLASS_LINES:
                    violations.append(f"{relative}:{node.lineno} {node.name} has {span} lines")
    assert not violations, "\n".join(violations)


def test_generic_catch_all_modules_are_not_created() -> None:
    violations = [
        str(path.relative_to(ROOT))
        for path in _python_files(SOURCE_ROOT)
        if path.name in FORBIDDEN_GENERIC_MODULES
    ]
    assert not violations, "禁止建立通用集中模組：\n" + "\n".join(violations)


def test_domain_has_no_framework_or_io_dependencies() -> None:
    violations: list[str] = []
    for path in _python_files(SOURCE_ROOT / "domain"):
        relative = path.relative_to(ROOT)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
        for name in sorted(_import_names(tree)):
            if _matches_prefix(name, DOMAIN_FORBIDDEN_IMPORTS):
                violations.append(f"{relative} imports {name}")
    assert not violations, "\n".join(violations)


def test_entrypoints_do_not_bypass_application_layer() -> None:
    violations: list[str] = []
    interface_roots = ("api", "ingestion", "station_agent", "workers")
    for interface_root in interface_roots:
        for path in _python_files(SOURCE_ROOT / interface_root):
            relative = path.relative_to(ROOT)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
            for name in sorted(_import_names(tree)):
                if _matches_prefix(name, INTERFACE_FORBIDDEN_IMPORTS):
                    violations.append(f"{relative} imports {name}")
    assert not violations, "\n".join(violations)
