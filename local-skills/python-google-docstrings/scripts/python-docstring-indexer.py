#!/usr/bin/env python3
"""python-docstring-indexer.py — Build a YAML-style inventory of docstrings.

Small utility that parses a Python source file and enumerates module,
class, function (including nested) definitions together with a
boolean indicating whether each definition has a docstring. The
output shape is suitable for emitting YAML for auditing or CI checks.

Usage:
    python .github/skills/python-google-docstrings/scripts/python-docstring-indexer.py \
        path/to/your_file.py

Examples:
    >>> build_index('example.py')
    {'docstring_index': {'total': 5, 'items': [...]}}
"""

import ast
import json
import sys
import pathlib


CALLABLE_NODE_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
OVERLOAD_DECORATOR_NAMES = {"overload"}
PROPERTY_ACCESSOR_DECORATOR_NAMES = {"setter", "deleter"}


def _is_fixture_decorator(node):
    """Return True when a decorator expression targets a fixture factory.

    The detector accepts the common pytest spellings ``@fixture``,
    ``@fixture(...)``, ``@pytest.fixture``, and ``@pytest.fixture(...)``.
    Attribute aliases such as ``@pytest_asyncio.fixture`` are also
    supported because the terminal attribute name remains ``fixture``.

    Args:
        node (ast.AST): Decorator expression to inspect.

    Returns:
        bool: True when the expression resolves to a fixture decorator.
    """
    if isinstance(node, ast.Call):
        return _is_fixture_decorator(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr == "fixture"
    if isinstance(node, ast.Name):
        return node.id == "fixture"
    return False


def _is_overload_decorator(node):
    """Return True when a decorator expression targets typing.overload."""

    if isinstance(node, ast.Call):
        return _is_overload_decorator(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr in OVERLOAD_DECORATOR_NAMES
    if isinstance(node, ast.Name):
        return node.id in OVERLOAD_DECORATOR_NAMES
    return False


def _is_property_accessor_decorator(node):
    """Return True when a decorator expression targets a property accessor."""

    if isinstance(node, ast.Call):
        return _is_property_accessor_decorator(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr in PROPERTY_ACCESSOR_DECORATOR_NAMES
    if isinstance(node, ast.Name):
        return node.id in PROPERTY_ACCESSOR_DECORATOR_NAMES
    return False


def is_fixture(node):
    """Detect if a function node is decorated as a pytest fixture.

    Args:
        node (ast.AST): An AST node that may be a function definition. The
            function examines ``node.decorator_list`` to find a decorator
            matching a bare ``fixture`` name or any ``*.fixture`` attribute,
            with or without call syntax.

    Returns:
        bool: True if the node appears to be a pytest fixture, False
            otherwise.

    Examples:
        >>> import ast
        >>> src = '@fixture(name="fx")\ndef fx():\n    pass\n'
        >>> tree = ast.parse(src)
        >>> is_fixture(tree.body[0])
        True
    """
    for dec in getattr(node, "decorator_list", []):
        if _is_fixture_decorator(dec):
            return True
    return False


def is_overload(node):
    """Detect whether a function node is an overload stub."""

    for dec in getattr(node, "decorator_list", []):
        if _is_overload_decorator(dec):
            return True
    return False


def is_property_accessor(node):
    """Detect whether a function node is a property setter or deleter."""

    for dec in getattr(node, "decorator_list", []):
        if _is_property_accessor_decorator(dec):
            return True
    return False


def walk_definitions(tree, parent_name=None, parent_node=None):
    """Yield definition metadata for module/class/function nodes.

    This generator walks the AST subtree rooted at ``tree`` and yields a
    dictionary for each class, function (including async functions), and
    nested function, including definitions nested under control-flow nodes.
    The returned dictionaries match the lightweight audit shape used by
    this tool.

    Args:
        tree (ast.AST): Root AST node to inspect (typically the module
            AST returned by :func:`ast.parse`).
        parent_name (str | None): Optional dotted parent name used to
            construct fully-qualified names for nested definitions.

    Yields:
        dict: Mapping with the keys:
            - name (str): Fully-qualified name (e.g. "MyClass.method").
            - kind (str): One of "module", "class", "function",
              "method", "nested_function", "fixture", or "test".
            - lineno (int): The node's starting line number.
            - has_docstring (bool): True if the node has a docstring.

    Examples:
        >>> import ast
        >>> tree = ast.parse('def a():\n    def b():\n        pass')
        >>> list(walk_definitions(tree))
        [{'name': 'a', 'kind': 'function', 'lineno': 1, 'has_docstring': False},
         {'name': 'a.b', 'kind': 'nested_function', 'lineno': 2, 'has_docstring': False}]
    """
    current_parent = tree if parent_node is None else parent_node

    for node in ast.iter_child_nodes(tree):
        name = getattr(node, "name", None)
        if isinstance(node, CALLABLE_NODE_TYPES):
            if is_overload(node):
                continue
            if is_property_accessor(node):
                continue
            full_name = f"{parent_name}.{name}" if parent_name else name
            kind = "function"
            if is_fixture(node):
                kind = "fixture"
            elif name and name.startswith("test_"):
                kind = "test"
            elif parent_name and isinstance(current_parent, ast.ClassDef):
                kind = "method"
            elif parent_name and isinstance(current_parent, CALLABLE_NODE_TYPES):
                kind = "nested_function"
            yield {
                "name": full_name,
                "kind": kind,
                "lineno": node.lineno,
                "has_docstring": bool(ast.get_docstring(node)),
            }
            yield from walk_definitions(node, parent_name=full_name, parent_node=node)
            continue

        elif isinstance(node, ast.ClassDef):
            full_name = f"{parent_name}.{name}" if parent_name else name
            yield {
                "name": full_name,
                "kind": "class",
                "lineno": node.lineno,
                "has_docstring": bool(ast.get_docstring(node)),
            }
            yield from walk_definitions(node, parent_name=full_name, parent_node=node)
            continue

        yield from walk_definitions(node, parent_name=parent_name, parent_node=current_parent)


def build_index(filepath):
    """Build a docstring inventory for a Python source file.

    Parses ``filepath`` and returns a dictionary containing a count and
    the list of discovered definitions. This shape is convenient for
    serializing to YAML for reporting or CI checks.

    Args:
        filepath (str | pathlib.Path): Path to the Python source file to
            inspect.

    Returns:
        dict: Structure with a single key ``docstring_index`` mapping to a
        dictionary with::

            {
                'total': int,
                'items': [
                    {
                        'name': str,
                        'kind': str,
                        'lineno': int,
                        'has_docstring': bool
                    },
                    ...
                ]
            }

    Raises:
        SystemExit: If the provided ``filepath`` does not exist. The
            function calls :func:`sys.exit` to mirror the original CLI
            behaviour.

    Examples:
        >>> build_index('some_module.py')
        {'docstring_index': {'total': 3, 'items': [...]}}
    """
    path = pathlib.Path(filepath)
    if not path.exists():
        sys.exit(f"Error: file not found: {filepath}")

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    items = list(walk_definitions(tree))
    # Include module docstring
    items.insert(0, {"name": "module", "kind": "module", "lineno": 1, "has_docstring": bool(ast.get_docstring(tree))})

    return {"docstring_index": {"total": len(items), "items": items}}


def yaml_scalar(value):
    """Render a scalar value as YAML-safe text."""

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def dump_yaml(value, indent=0):
    """Render a limited subset of YAML for the index output."""

    padding = " " * indent
    if isinstance(value, dict):
        if not value:
            return f"{padding}{{}}"

        lines = []
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

            if isinstance(item, list):
                lines.append(f"{padding}-")
                lines.append(dump_yaml(item, indent + 2))
                continue

            lines.append(f"{padding}- {yaml_scalar(item)}")

        return "\n".join(lines)

    return f"{padding}{yaml_scalar(value)}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python .github/skills/python-google-docstrings/scripts/"
            "python-docstring-indexer.py path/to/file.py",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = sys.argv[1]
    index = build_index(input_path)

    # Print in clean YAML for readability
    print(dump_yaml(index))
