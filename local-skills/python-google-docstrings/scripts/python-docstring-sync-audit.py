"""Audit Google-style docstring synchronization for callable definitions.

The audit covers methods, functions, nested functions, fixtures, and tests,
including async definitions. It emits a fenced YAML block named
``docstring_sync_audit`` for use by the bundled prompt.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CALLABLE_NODE_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
SKIPPED_BODY_NODE_TYPES = CALLABLE_NODE_TYPES + (ast.ClassDef, ast.Lambda)
OVERLOAD_DECORATOR_NAMES = {"overload"}
OVERRIDE_DECORATOR_NAMES = {"override"}
PROPERTY_GETTER_DECORATOR_NAMES = {"property", "cached_property", "getter"}
PROPERTY_ACCESSOR_DECORATOR_NAMES = {"setter", "deleter"}
PROPERTY_DECORATOR_NAMES = PROPERTY_GETTER_DECORATOR_NAMES | PROPERTY_ACCESSOR_DECORATOR_NAMES
SECTION_RE = re.compile(r"^\s*(Args|Returns|Yields|Raises):\s*$")
PARAM_RE = re.compile(
    r"^(?P<indent>\s+)(?P<name>\*{0,2}[a-zA-Z_][\w]*)"
    r"(?:\s*\([^)]*\))?\s*:(?P<description>\s*.*)?$"
)


@dataclass(frozen=True)
class CallableDefinition:
    """Describe a callable definition audited by the sync checker."""

    name: str
    kind: str
    line: int
    node: ast.FunctionDef | ast.AsyncFunctionDef
    is_property: bool = False
    is_property_accessor: bool = False
    is_override: bool = False


def get_doc(node: ast.AST) -> str:
    """Return an AST node docstring or an empty string."""

    return ast.get_docstring(node) or ""


def is_fixture(node: ast.AST) -> bool:
    """Return True when a callable is decorated as a pytest fixture."""

    for decorator in getattr(node, "decorator_list", []):
        if decorator_matches_names(decorator, {"fixture"}):
            return True
    return False


def collect_override_imports(tree: ast.AST) -> tuple[set[str], set[str]]:
    """Return imported override names and module aliases from typing modules."""

    override_names: set[str] = set()
    override_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in {"typing", "typing_extensions"}:
            for alias in node.names:
                if alias.name == "override":
                    override_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {"typing", "typing_extensions"}:
                    override_modules.add(alias.asname or alias.name)
    return override_names, override_modules


def decorator_matches_names(node: ast.AST, names: set[str]) -> bool:
    """Return True when a decorator expression resolves to any named decorator."""

    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Attribute):
        return target.attr in names
    if isinstance(target, ast.Name):
        return target.id in names
    return False


def property_kind(node: ast.AST) -> str | None:
    """Return the property classification for a decorated callable."""

    for decorator in getattr(node, "decorator_list", []):
        if decorator_matches_names(decorator, PROPERTY_ACCESSOR_DECORATOR_NAMES):
            return "accessor"
        if decorator_matches_names(decorator, PROPERTY_GETTER_DECORATOR_NAMES):
            return "getter"
    return None


def is_property(node: ast.AST) -> bool:
    """Return True when a callable is decorated as a property-like member."""

    return property_kind(node) is not None


def is_property_accessor(node: ast.AST) -> bool:
    """Return True when a callable is a property setter or deleter."""

    return property_kind(node) == "accessor"


def is_override(node: ast.AST, override_names: set[str], override_modules: set[str]) -> bool:
    """Return True when a callable is decorated with @override."""

    for decorator in getattr(node, "decorator_list", []):
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Name) and target.id in override_names:
            return True
        if (
            isinstance(target, ast.Attribute)
            and target.attr in OVERRIDE_DECORATOR_NAMES
            and isinstance(target.value, ast.Name)
            and target.value.id in override_modules
        ):
            return True
    return False


def is_overload(node: ast.AST) -> bool:
    """Return True when a callable is an overload stub."""

    for decorator in getattr(node, "decorator_list", []):
        if decorator_matches_names(decorator, OVERLOAD_DECORATOR_NAMES):
            return True
    return False


def classify_definition(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    parent: ast.AST,
) -> str:
    """Classify a callable using the bundle's docstring-indexing rules."""

    if is_fixture(node):
        return "fixture"
    if node.name.startswith("test_"):
        return "test"
    if isinstance(parent, ast.ClassDef):
        return "method"
    if isinstance(parent, CALLABLE_NODE_TYPES):
        return "nested_function"
    return "function"


def iter_callable_definitions(
    tree: ast.AST,
    *,
    parent: ast.AST | None = None,
    parent_name: str | None = None,
    override_names: set[str] | None = None,
    override_modules: set[str] | None = None,
) -> Iterator[CallableDefinition]:
    """Yield callable definitions with fully qualified names and kinds."""

    current_parent = tree if parent is None else parent
    active_override_names = set() if override_names is None else override_names
    active_override_modules = set() if override_modules is None else override_modules
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, CALLABLE_NODE_TYPES):
            if is_overload(child):
                continue
            full_name = f"{parent_name}.{child.name}" if parent_name else child.name
            yield CallableDefinition(
                name=full_name,
                kind=classify_definition(child, current_parent),
                line=child.lineno,
                node=child,
                is_property=is_property(child),
                is_property_accessor=is_property_accessor(child),
                is_override=is_override(child, active_override_names, active_override_modules),
            )
            yield from iter_callable_definitions(
                child,
                parent=child,
                parent_name=full_name,
                override_names=active_override_names,
                override_modules=active_override_modules,
            )
            continue

        if isinstance(child, ast.ClassDef):
            full_name = f"{parent_name}.{child.name}" if parent_name else child.name
            yield from iter_callable_definitions(
                child,
                parent=child,
                parent_name=full_name,
                override_names=active_override_names,
                override_modules=active_override_modules,
            )
            continue

        yield from iter_callable_definitions(
            child,
            parent=current_parent,
            parent_name=parent_name,
            override_names=active_override_names,
            override_modules=active_override_modules,
        )


def signature_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, bool]]:
    """Return ordered signature parameters and whether they are keyword-only."""

    params: list[tuple[str, bool]] = []
    for arg in node.args.posonlyargs + node.args.args:
        if arg.arg not in {"self", "cls"}:
            params.append((arg.arg, False))
    if node.args.vararg:
        params.append((f"*{node.args.vararg.arg}", False))
    for arg in node.args.kwonlyargs:
        params.append((arg.arg, True))
    if node.args.kwarg:
        params.append((f"**{node.args.kwarg.arg}", False))
    return params


def has_section(doc: str, section: str) -> bool:
    """Return True when a Google-style section header is present."""

    return bool(re.search(rf"^\s*{re.escape(section)}:\s*$", doc, re.MULTILINE))


def parse_args_entries(doc: str) -> list[tuple[str, str]]:
    """Extract documented Args entries with their leading descriptions."""

    entries: list[tuple[str, str]] = []
    in_args = False
    param_indent: int | None = None
    current_name: str | None = None
    current_description: list[str] = []

    def flush_current() -> None:
        nonlocal current_name, current_description
        if current_name is None:
            return
        description = " ".join(part for part in current_description if part).strip()
        entries.append((current_name, description))
        current_name = None
        current_description = []

    for line in doc.splitlines():
        if re.match(r"^\s*Args:\s*$", line):
            flush_current()
            in_args = True
            param_indent = None
            continue
        if not in_args:
            continue
        if SECTION_RE.match(line):
            flush_current()
            break
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")):
            flush_current()
            break
        match = PARAM_RE.match(line)
        if match:
            line_indent = len(match.group("indent"))
            if param_indent is None:
                param_indent = line_indent
            if line_indent == param_indent:
                flush_current()
                current_name = match.group("name")
                description = (match.group("description") or "").strip()
                current_description = [description] if description else []
                continue

        if current_name is None:
            continue
        current_description.append(line.strip())

    flush_current()
    return entries


def parse_args_section(doc: str) -> list[str]:
    """Extract documented argument names from a Google-style Args section."""

    return [name for name, _ in parse_args_entries(doc)]


def iter_body_nodes(node: ast.AST) -> Iterator[ast.AST]:
    """Yield statement-body nodes while skipping nested functions and classes."""

    for child in getattr(node, "body", []):
        yield from iter_non_nested_body_nodes(child)


def iter_non_nested_body_nodes(node: ast.AST) -> Iterator[ast.AST]:
    """Yield descendant nodes, excluding nested callables, classes, and lambdas."""

    if isinstance(node, SKIPPED_BODY_NODE_TYPES):
        return

    yield node
    for child in ast.iter_child_nodes(node):
        yield from iter_non_nested_body_nodes(child)


def has_yield(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when the callable body yields values."""

    return any(isinstance(child, (ast.Yield, ast.YieldFrom)) for child in iter_body_nodes(node))


def has_return_with_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when the callable has an explicit non-None return value."""

    return any(
        isinstance(child, ast.Return) and child.value is not None and not is_none_literal(child.value)
        for child in iter_body_nodes(node)
    )


def is_none_literal(node: ast.AST) -> bool:
    """Return True when an AST node represents the literal None value."""

    return isinstance(node, ast.Constant) and node.value is None


def has_explicit_raise(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when the callable body contains an explicit raise."""

    return any(isinstance(child, ast.Raise) for child in iter_body_nodes(node))


def has_non_none_return_annotation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when the callable annotation is present and not None."""

    if node.returns is None:
        return False
    terminal_name = ast.unparse(node.returns).split(".")[-1]
    return terminal_name not in {"None", "NoReturn", "Never"}


def summary_starts_with(doc: str, prefixes: Sequence[str]) -> bool:
    """Return True when the first docstring line starts with any prefix."""

    for line in doc.splitlines():
        stripped = line.strip().lower()
        if stripped:
            return stripped.startswith(tuple(prefix.lower() for prefix in prefixes))
    return False


def build_issue(
    definition: CallableDefinition,
    issue_type: str,
    message: str,
) -> dict[str, Any]:
    """Return a structured audit issue entry."""

    return {
        "name": definition.name,
        "kind": definition.kind,
        "line": definition.line,
        "type": issue_type,
        "issue": message,
    }


def audit_args(definition: CallableDefinition, doc: str) -> dict[str, Any] | None:
    """Return an args issue when docstring arguments do not match the signature."""

    if definition.is_property:
        if has_section(doc, "Args"):
            return build_issue(
                definition,
                "args",
                "Property docstring should not include an Args section.",
            )
        return None

    signature_params = signature_parameters(definition.node)
    documented_entries = [
        (name, description)
        for name, description in parse_args_entries(doc)
        if name not in {"self", "cls"}
    ]
    expected_names = [name for name, _ in signature_params]
    documented_names = [name for name, _ in documented_entries]

    if not signature_params:
        if documented_names:
            extras = ", ".join(documented_names)
            return build_issue(
                definition,
                "args",
                f"Args section documents parameters not present in the signature: {extras}.",
            )
        return None

    if not has_section(doc, "Args"):
        return None

    missing = [name for name in expected_names if name not in documented_names]
    extras = [name for name in documented_names if name not in expected_names]
    duplicates = [name for name, count in Counter(documented_names).items() if count > 1]
    order_mismatch = not missing and not extras and not duplicates and documented_names != expected_names

    if not missing and not extras and not duplicates and not order_mismatch:
        return None

    problems: list[str] = []
    if missing:
        problems.append(f"missing {', '.join(missing)}")
    if extras:
        problems.append(f"extra {', '.join(extras)}")
    if duplicates:
        problems.append(f"duplicate {', '.join(duplicates)}")
    if order_mismatch:
        problems.append("parameters out of signature order")
    problem_text = "; ".join(problems)
    return build_issue(definition, "args", f"Args section does not match the signature: {problem_text}.")


def audit_returns(definition: CallableDefinition, doc: str) -> dict[str, Any] | None:
    """Return a returns issue when Returns or Yields sections are out of sync."""

    if definition.is_property_accessor:
        return None

    if definition.is_property:
        if has_section(doc, "Yields"):
            return build_issue(
                definition,
                "returns",
                "Property docstring should not include a Yields section.",
            )
        return None

    is_generator = has_yield(definition.node)
    expects_returns = has_non_none_return_annotation(definition.node) or has_return_with_value(definition.node)
    summary_returns = summary_starts_with(doc, ("return ", "returns "))
    summary_yields = summary_starts_with(doc, ("yield ", "yields "))

    if is_generator:
        if not has_section(doc, "Yields") and not summary_yields:
            return build_issue(definition, "returns", "Missing Yields section for yielded values.")
        if has_section(doc, "Returns"):
            return build_issue(definition, "returns", "Generator docstring should use Yields instead of Returns.")
        return None

    if has_section(doc, "Yields"):
        return build_issue(definition, "returns", "Non-generator docstring should not include a Yields section.")

    if expects_returns and not has_section(doc, "Returns") and not summary_returns:
        return build_issue(definition, "returns", "Missing Returns section for a non-None return value.")

    if not expects_returns and has_section(doc, "Returns"):
        return build_issue(definition, "returns", "Docstring should omit Returns for a None-returning callable.")

    return None


def audit_raises(definition: CallableDefinition, doc: str) -> dict[str, Any] | None:
    """Return a raises issue when explicit raises lack a Raises section."""

    if definition.is_property_accessor:
        return None

    has_explicit = has_explicit_raise(definition.node)
    has_raises_section = has_section(doc, "Raises")

    if has_explicit and not has_raises_section:
        return build_issue(definition, "raises", "Missing Raises section for explicit raise statements.")
    return None


def audit_callable(definition: CallableDefinition) -> list[dict[str, Any]]:
    """Return all structured issues for a callable definition."""

    doc = get_doc(definition.node)
    if definition.is_override and not doc:
        return []

    issues = [
        audit_args(definition, doc),
        audit_returns(definition, doc),
        audit_raises(definition, doc),
    ]
    return [issue for issue in issues if issue is not None]


def build_sync_audit(path: str | Path) -> dict[str, dict[str, Any]]:
    """Build the structured docstring sync audit for a Python file."""

    source_path = Path(path)
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    override_names, override_modules = collect_override_imports(tree)
    definitions = [
        definition
        for definition in iter_callable_definitions(
            tree,
            override_names=override_names,
            override_modules=override_modules,
        )
        if not definition.is_property_accessor
    ]
    details: list[dict[str, Any]] = []
    for definition in definitions:
        details.extend(audit_callable(definition))

    return {
        "docstring_sync_audit": {
            "checked_items": len(definitions),
            "remaining_issues": len(details),
            "details": details,
        }
    }


def yaml_scalar(value: Any) -> str:
    """Render a scalar value as YAML-safe text."""

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def dump_yaml(value: Any, indent: int = 0) -> str:
    """Render a limited subset of YAML for the audit report."""

    padding = " " * indent
    if isinstance(value, dict):
        if not value:
            return f"{padding}{{}}"

        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                if isinstance(item, list) and not item:
                    lines.append(f"{padding}{key}: []")
                elif isinstance(item, dict) and not item:
                    lines.append(f"{padding}{key}: {{}}")
                else:
                    lines.append(f"{padding}{key}:")
                    lines.append(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{padding}{key}: {yaml_scalar(item)}")
        return "\n".join(lines)

    if isinstance(value, list):
        if not value:
            return f"{padding}[]"

        lines = []
        for item in value:
            if isinstance(item, dict):
                first = True
                for key, nested in item.items():
                    prefix = "- " if first else "  "
                    if isinstance(nested, (dict, list)):
                        if isinstance(nested, list) and not nested:
                            lines.append(f"{padding}{prefix}{key}: []")
                        elif isinstance(nested, dict) and not nested:
                            lines.append(f"{padding}{prefix}{key}: {{}}")
                        else:
                            lines.append(f"{padding}{prefix}{key}:")
                            lines.append(dump_yaml(nested, indent + 4))
                    else:
                        lines.append(f"{padding}{prefix}{key}: {yaml_scalar(nested)}")
                    first = False
                continue

            lines.append(f"{padding}- {yaml_scalar(item)}")
        return "\n".join(lines)

    return f"{padding}{yaml_scalar(value)}"


def render_fenced_yaml(report: dict[str, dict[str, Any]]) -> str:
    """Render the audit report as a fenced YAML block."""

    return "```yaml docstring_sync_audit\n" + dump_yaml(report) + "\n```"


def usage(program_name: str) -> str:
    """Return the CLI usage string for this script."""

    return f"Usage: python {program_name} path/to/file.py"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the sync audit CLI."""

    args = list(sys.argv[1:] if argv is None else argv)
    program_name = Path(sys.argv[0]).name if argv is None else "python-docstring-sync-audit.py"
    if len(args) != 1:
        print(usage(program_name), file=sys.stderr)
        return 1

    report = build_sync_audit(args[0])
    print(render_fenced_yaml(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
