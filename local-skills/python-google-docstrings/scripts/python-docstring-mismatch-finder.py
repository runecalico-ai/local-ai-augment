#!/usr/bin/env python3
"""Command-line checker for Google-style docstring signature mismatches.

This small utility examines a Python source file and reports functions
whose docstring `Args:` section does not match the function signature and
whether `Returns:`/`Yields:` sections are consistent with the function body.

It is intentionally lightweight and conservative: signatures are taken from
the AST (the source of truth), and the `Args:` section parser accepts the
common Google-style layouts `name: description`, `name (type): description`,
continuation lines after `name:`, and starred `*args`/`**kwargs` entries.

Usage:
    python .github/skills/python-google-docstrings/scripts/python-docstring-mismatch-finder.py \
        <path-to-python-file>

Notes:
    - This bundled script is the authoritative mismatch checker for the
      python-google-docstrings skill.
    - Use tools/python-docstring-mismatch-finder.py only as a fallback when
      this bundled script is unavailable in the current checkout.
    - The checker ignores `self` and `cls` parameters when comparing docs.
    - Generators are detected by scanning for ast.Yield / ast.YieldFrom nodes.
    - This module only reports mismatches; it does not modify source files.
"""

import ast
import json
import pathlib
import re
import sys
from collections import Counter
from dataclasses import dataclass


CALLABLE_NODE_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
SKIPPED_BODY_NODE_TYPES = CALLABLE_NODE_TYPES + (ast.ClassDef, ast.Lambda)
OVERRIDE_DECORATOR_NAMES = {"override"}
PROPERTY_GETTER_DECORATOR_NAMES = {"property", "cached_property", "getter"}
PROPERTY_ACCESSOR_DECORATOR_NAMES = {"setter", "deleter"}
PROPERTY_DECORATOR_NAMES = PROPERTY_GETTER_DECORATOR_NAMES | PROPERTY_ACCESSOR_DECORATOR_NAMES
OVERLOAD_DECORATOR_NAMES = {"overload"}
ARGS_HEADER_RE = re.compile(r"^\s*Args:\s*$")
PARAM_LINE_RE = re.compile(
    r"^(?P<indent>\s+)(?P<name>\*{0,2}[a-zA-Z_][\w]*)(?:\s*\([^)]*\))?\s*:(?P<description>\s*.*)?$"
)


@dataclass(frozen=True)
class CallableDefinition:
    """Describe a callable definition emitted by the mismatch checker."""

    name: str
    kind: str
    node: ast.FunctionDef | ast.AsyncFunctionDef
    is_property: bool = False
    is_property_accessor: bool = False
    is_override: bool = False


def decorator_matches_names(node: ast.AST, names: set[str]) -> bool:
    """Return True when a decorator expression resolves to any named decorator."""

    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Attribute):
        return target.attr in names
    if isinstance(target, ast.Name):
        return target.id in names
    return False


def is_property(node: ast.AST) -> bool:
    """Return True when a callable is decorated as a property getter."""

    return property_kind(node) is not None


def property_kind(node: ast.AST) -> str | None:
    """Return the property classification for a decorated callable."""

    for decorator in getattr(node, "decorator_list", []):
        if decorator_matches_names(decorator, PROPERTY_ACCESSOR_DECORATOR_NAMES):
            return "accessor"
        if decorator_matches_names(decorator, PROPERTY_GETTER_DECORATOR_NAMES):
            return "getter"
    return None


def is_property_accessor(node: ast.AST) -> bool:
    """Return True when a callable is a property setter or deleter."""

    return property_kind(node) == "accessor"


def is_overload(node: ast.AST) -> bool:
    """Return True when a callable is an overload stub."""

    return any(
        decorator_matches_names(decorator, OVERLOAD_DECORATOR_NAMES)
        for decorator in getattr(node, "decorator_list", [])
    )


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


def is_fixture(node: ast.AST) -> bool:
    """Return True when a callable is decorated as a pytest fixture."""

    return any(
        decorator_matches_names(decorator, {"fixture"})
        for decorator in getattr(node, "decorator_list", [])
    )


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


def classify_definition(node: ast.FunctionDef | ast.AsyncFunctionDef, parent: ast.AST) -> str:
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
):
    """Yield callable definitions with stable qualified names."""

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


def parse_args_entries(doc: str) -> list[tuple[str, str]]:
    """Extract parameter entries from the "Args:" section of a docstring.

    The parser looks for a top-level "Args:" heading and then collects
    parameter entries written using common Google-style layouts.

    Args:
        doc (str): Full docstring text to scan for an "Args:" section.

    Returns:
        list[tuple[str, str]]: Ordered parameter names and their leading descriptions.

    Examples:
        >>> parse_args_entries('''Args:\n    x:\n        value\n    *args (str): extras''')
        [('x', 'value'), ('*args', 'extras')]
    """
    entries: list[tuple[str, str]] = []
    in_args = False
    param_indent = None
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
        if ARGS_HEADER_RE.match(line):
            flush_current()
            in_args = True
            param_indent = None
            continue
        if not in_args:
            continue

        stripped_line = line.strip()
        if not stripped_line:
            continue
        if not line.startswith((" ", "\t")):
            flush_current()
            break
        if re.match(r"^\s*(Returns|Yields|Raises):\s*$", line):
            flush_current()
            break

        match = PARAM_LINE_RE.match(line)
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
    """Extract parameter names from the "Args:" section of a docstring.

    The parser looks for a top-level "Args:" heading and then collects
    parameter entries written using common Google-style layouts. Only the
    documented parameter name is returned.

    Args:
        doc (str): Full docstring text to scan for an "Args:" section.

    Returns:
        list[str]: Ordered list of parameter names found under the "Args:" section.

    Examples:
        >>> parse_args_section('''Args:\n    x:\n        value\n    *args (str): extras''')
        ['x', '*args']
    """
    return [name for name, _ in parse_args_entries(doc)]


def signature_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, bool]]:
    """Return ordered signature parameters and whether they are keyword-only."""

    params: list[tuple[str, bool]] = []
    posonly = getattr(node.args, "posonlyargs", [])
    for arg in posonly + node.args.args:
        if arg.arg not in {"self", "cls"}:
            params.append((arg.arg, False))
    if node.args.vararg:
        params.append((f"*{node.args.vararg.arg}", False))
    for arg in node.args.kwonlyargs:
        params.append((arg.arg, True))
    if node.args.kwarg:
        params.append((f"**{node.args.kwarg.arg}", False))
    return params


def has_args_section(doc: str) -> bool:
    """Return True when a Google-style Args section header is present."""

    return bool(re.search(r"^\s*Args:\s*$", doc, re.M))


def has_yield(node: ast.AST) -> bool:
    """Detect whether an AST node contains a yield or yield-from expression.

    Args:
        node (ast.AST): AST node to inspect (typically a FunctionDef/AsyncFunctionDef).

    Returns:
        bool: True if the node contains any ast.Yield or ast.YieldFrom nodes.

    Examples:
        >>> has_yield(node)
        True
    """
    return any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in iter_body_nodes(node))


def iter_body_nodes(node: ast.AST):
    """Yield descendant body nodes while skipping nested defs and classes."""

    for child in getattr(node, "body", []):
        yield from iter_non_nested_body_nodes(child)


def iter_non_nested_body_nodes(node: ast.AST):
    """Yield descendants unless they belong to a nested scope."""

    if isinstance(node, SKIPPED_BODY_NODE_TYPES):
        return

    yield node
    for child in ast.iter_child_nodes(node):
        yield from iter_non_nested_body_nodes(child)


def has_return_with_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when the callable has an explicit non-None return value."""

    return any(
        isinstance(child, ast.Return) and child.value is not None and not is_none_literal(child.value)
        for child in iter_body_nodes(node)
    )


def is_none_literal(node: ast.AST) -> bool:
    """Return True when an AST node represents the literal None value."""

    return isinstance(node, ast.Constant) and node.value is None


def has_non_none_return_annotation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when the callable is annotated with a non-None return."""

    if node.returns is None:
        return False
    terminal_name = ast.unparse(node.returns).split(".")[-1]
    return terminal_name not in {"None", "NoReturn", "Never"}


def summary_starts_with(doc: str, prefixes: tuple[str, ...]) -> bool:
    """Return True when the first non-empty docstring line starts with a prefix."""

    for line in doc.splitlines():
        stripped = line.strip().lower()
        if stripped:
            return stripped.startswith(tuple(prefix.lower() for prefix in prefixes))
    return False


def normalize_param_name(name: str) -> str:
    """Return a canonical parameter name for semantic comparison.

    Args:
        name (str): Documented or signature parameter name.

    Returns:
        str: Parameter name without leading star markers.
    """
    return name.lstrip("*")


def check_file(path: str) -> list[dict[str, object]]:
    """Check a Python source file for docstring/signature mismatches.

    The function parses the file using the AST, walks function and async
    function definitions, and compares the function signature parameters
    to the names documented under an "Args:" section. It also verifies
    whether generator functions (containing `yield`) are documented with
    a "Yields:" section and that non-generator functions do not claim
    to "Yields:".

    Args:
        path (str): Filesystem path to the Python source file to check.

    Returns:
        list[dict]: A list of issue dictionaries. Each dictionary contains:
            name (str): Stable qualified function or method name.
            kind (str): Callable kind such as function, method, fixture, or test.
            lineno (int): Line number of the function definition.
            missing_params (list[str]): Parameters present in the signature but
                not documented in the docstring's Args: section.
            extra_params (list[str]): Parameters documented in Args: but not
                present in the signature.
            arg_issues (list[str]): Additional Args parity problems such as
                reordering or duplicates.
            generator (bool): True if the function contains yield/yield from.
            has_returns (bool): True if a "Returns:" section is present.
            has_yields (bool): True if a "Yields:" section is present.

    Raises:
        FileNotFoundError: If the file at `path` cannot be read.
        SyntaxError: If the source cannot be parsed by the AST.

    Examples:
        >>> check_file('example.py')
        [{'name': 'foo', 'lineno': 10, 'missing_params': ['x'], ...}]
    """
    src = pathlib.Path(path).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=path)
    override_names, override_modules = collect_override_imports(tree)
    issues = []

    for definition in iter_callable_definitions(
        tree,
        override_names=override_names,
        override_modules=override_modules,
    ):
        if definition.is_property_accessor:
            continue

        node = definition.node
        name = definition.name
        signature_params = signature_parameters(node)
        sig_params = [param for param, _ in signature_params]

        doc = ast.get_docstring(node) or ""
        if definition.is_override and not doc:
            continue

        is_gen = has_yield(node)
        summary_returns = summary_starts_with(doc, ("return ", "returns "))
        summary_yields = summary_starts_with(doc, ("yield ", "yields "))
        if definition.is_property:
            missing = []
            extras = []
            arg_issues = ["property docstring should not include an Args section"] if has_args_section(doc) else []
        elif not has_args_section(doc):
            missing = []
            extras = []
            arg_issues = []
        else:
            doc_entries = [
                (param_name, description)
                for param_name, description in (parse_args_entries(doc) if doc else [])
                if param_name not in {"self", "cls"}
            ]
            doc_params = [name for name, _ in doc_entries]
            missing = [param for param in sig_params if param not in doc_params]
            extras = [param for param in doc_params if param not in sig_params]
            duplicates = [param for param, count in Counter(doc_params).items() if count > 1]
            arg_issues = []
            if duplicates:
                arg_issues.append(f"duplicate entries for {', '.join(duplicates)}")
            if not missing and not extras and not duplicates and doc_params != sig_params:
                arg_issues.append("parameters out of signature order")

        # returns/yields presence
        has_returns = bool(re.search(r"^\s*Returns:\s*$", doc, re.M))
        has_yields = bool(re.search(r"^\s*Yields:\s*$", doc, re.M))
        expects_returns = has_non_none_return_annotation(node) or has_return_with_value(node)

        if definition.is_property:
            ret_issue = has_yields
        elif is_gen:
            ret_issue = (not has_yields and not summary_yields) or has_returns
        else:
            ret_issue = has_yields or (
                expects_returns and not has_returns and not summary_returns
            ) or ((not expects_returns) and has_returns)

        if missing or extras or arg_issues or ret_issue:
            issues.append(
                {
                    "name": name,
                    "kind": definition.kind,
                    "lineno": node.lineno,
                    "missing_params": missing,
                    "extra_params": extras,
                    "arg_issues": arg_issues,
                    "generator": is_gen,
                    "has_returns": has_returns,
                    "has_yields": has_yields,
                }
            )
    return issues


def usage(program_name: str) -> str:
    """Return the CLI usage string for this script.

    Args:
        program_name (str): Program name shown in the usage output.

    Returns:
        str: Human-readable CLI usage text.
    """
    return f"Usage: python {program_name} <path-to-python-file>"


def main(argv: list[str] | None = None) -> int:
    """Run the mismatch checker CLI.

    Args:
        argv (list[str] | None): Optional CLI arguments without the program name.

    Returns:
        int: Process exit status.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    program_name = pathlib.Path(sys.argv[0]).name if argv is None else "python-docstring-mismatch-finder.py"

    if args == ["-h"] or args == ["--help"]:
        print(usage(program_name))
        return 0
    if len(args) != 1:
        print(usage(program_name), file=sys.stderr)
        return 1

    path = args[0]
    problems = check_file(path)
    print(json.dumps({"file": path, "issues": problems, "count": len(problems)}, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
