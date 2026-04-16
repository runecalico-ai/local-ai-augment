from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "python-docstring-sync-audit.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("python_docstring_sync_audit", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load script module from {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_sample_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "sample_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            """Sample module for sync-audit coverage."""

            import pytest


            class Example:
                async def method(self, value: int) -> str:
                    """Run method."""
                    if value < 0:
                        raise ValueError("negative")
                    return str(value)


            async def async_function(value: int) -> str:
                """Run function."""
                if value < 0:
                    raise ValueError("negative")
                return str(value)


            def outer(flag: bool) -> None:
                """Wrap nested function."""

                def inner(name: str) -> str:
                    """Normalize the provided name."""
                    if not name:
                        raise ValueError("missing")
                    return name

                if flag:
                    inner("")


            @pytest.fixture
            async def configured_client():
                """Provide configured client."""
                yield "client"


            async def test_async_case(configured_client):
                """Exercise async case."""
                assert configured_client == "client"
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_property_control_flow_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "property_control_flow.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            class Example:
                @property
                def display_name(self) -> str:
                    """Configured display name."""
                    return "copilot"


            def outer(flag: bool) -> None:
                """Run a nested helper when enabled.

                Args:
                    flag: Whether to call the nested helper.
                """
                if flag:
                    def inner(value: int) -> int:
                        """Compute the nested value."""
                        return value

                    inner(1)
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_overload_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "overload_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            import typing
            from typing import overload


            @overload
            def parse_value(value: str) -> int:
                ...


            @typing.overload
            def parse_value(value: bytes) -> int:
                ...


            def parse_value(value: str | bytes) -> int:
                """Parse a supported raw value.

                Args:
                    value: Raw value to parse.

                Returns:
                    Parsed integer length.
                """
                return len(value)
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_args_and_raises_parity_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "args_and_raises_parity.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            def out_of_order(alpha: str, beta: int) -> str:
                """Return the primary value.

                Args:
                    beta: Beta value.
                    alpha: Alpha value.

                Returns:
                    Primary value.
                """
                return alpha


            def kw_only_and_varargs(alpha: str, *args: str, beta: int, **kwargs: str) -> str:
                """Return the primary value.

                Args:
                    alpha: Alpha value.
                    args: Extra positional values.
                    beta: Beta value.
                    **kwargs: Extra keyword values.

                Returns:
                    Primary value.
                """
                return alpha


            def duplicated(alpha: str) -> str:
                """Return the primary value.

                Args:
                    alpha: First description.
                    alpha: Duplicate description.

                Returns:
                    Primary value.
                """
                return alpha


            def stale_raises(alpha: str) -> str:
                """Return the primary value.

                Args:
                    alpha: Primary value.

                Returns:
                    Primary value.

                Raises:
                    ValueError: No longer raised.
                """
                return alpha
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_property_accessor_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "property_accessor_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            class Example:
                def __init__(self) -> None:
                    self._display_name = "copilot"

                @property
                def display_name(self) -> str:
                    """Configured display name."""
                    return self._display_name

                @display_name.setter
                def display_name(self, value: str) -> None:
                    """Update the display name."""
                    if not value:
                        raise ValueError("missing")
                    self._display_name = value

                @display_name.deleter
                def display_name(self) -> None:
                    """Clear the display name."""
                    self._display_name = ""
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_override_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "override_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            from typing_extensions import override


            class Base:
                def render(self) -> str:
                    """Return the rendered payload."""
                    return "base"


            class Child(Base):
                @override
                def render(self) -> str:
                    return "child"
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_summary_line_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "summary_line_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            from collections.abc import Generator


            def render_name() -> str:
                """Returns the rendered display name."""
                return "copilot"


            def iter_names() -> Generator[str, None, None]:
                """Yields configured display names."""
                yield "copilot"
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_property_args_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "property_args_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            class Example:
                @property
                def display_name(self) -> str:
                    """Configured display name.

                    Args:
                        value: Should not appear on a property getter.
                    """
                    return "copilot"
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_self_semantics_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "self_semantics_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            class Repository:
                def fetch(self, key: str) -> str:
                    """Return the stored value for a key.

                    Args:
                        self: Repository bound to the current tenant shard.
                        key: Cache key to look up.
                    """
                    return key
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def filter_prompt_scoped_details(
    details: list[dict[str, object]],
    *,
    required_names: set[str],
    ignored_raise_names: set[str],
) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    for detail in details:
        name = detail["name"]
        issue_type = detail["type"]
        if name not in required_names:
            continue
        if issue_type == "raises" and name in ignored_raise_names:
            continue
        filtered.append(detail)
    return filtered


def test_build_sync_audit_reports_structured_details_for_supported_kinds(tmp_path: Path):
    module = load_audit_module()
    sample_path = write_sample_module(tmp_path)

    report = module.build_sync_audit(sample_path)
    audit = report["docstring_sync_audit"]
    tree = ast.parse(sample_path.read_text(encoding="utf-8"), filename=str(sample_path))
    definitions_by_name = {
        definition.name: definition.kind
        for definition in module.iter_callable_definitions(tree)
    }

    assert audit["checked_items"] == 6
    assert audit["remaining_issues"] == len(audit["details"])
    assert audit["remaining_issues"] > 0
    assert definitions_by_name == {
        "Example.method": "method",
        "async_function": "function",
        "outer": "function",
        "outer.inner": "nested_function",
        "configured_client": "fixture",
        "test_async_case": "test",
    }

    expected_entries = {
        ("Example.method", "method", "returns"),
        ("async_function", "function", "returns"),
        ("outer.inner", "nested_function", "returns"),
        ("configured_client", "fixture", "returns"),
    }

    actual_entries = {
        (detail["name"], detail["kind"], detail["type"])
        for detail in audit["details"]
    }

    assert expected_entries.issubset(actual_entries)

    for detail in audit["details"]:
        assert set(detail) == {"name", "kind", "line", "type", "issue"}
        assert isinstance(detail["line"], int)
        assert detail["kind"] in {"method", "function", "nested_function", "fixture", "test"}
        assert detail["type"] in {"args", "returns", "raises"}
        assert isinstance(detail["issue"], str)
        assert detail["issue"]


def test_build_sync_audit_discovers_control_flow_nested_functions_and_skips_property_returns(
    tmp_path: Path,
) -> None:
    module = load_audit_module()
    sample_path = write_property_control_flow_module(tmp_path)

    audit = module.build_sync_audit(sample_path)["docstring_sync_audit"]
    actual_entries = {
        (detail["name"], detail["kind"], detail["type"])
        for detail in audit["details"]
    }

    assert audit["checked_items"] == 3
    assert ("outer.inner", "nested_function", "returns") in actual_entries
    assert ("Example.display_name", "method", "returns") not in actual_entries


def test_build_sync_audit_skips_property_accessors_and_flags_args_order_and_stale_raises(
    tmp_path: Path,
) -> None:
    module = load_audit_module()

    property_audit = module.build_sync_audit(write_property_accessor_module(tmp_path))["docstring_sync_audit"]
    assert property_audit["remaining_issues"] == 0

    parity_audit = module.build_sync_audit(write_args_and_raises_parity_module(tmp_path))["docstring_sync_audit"]
    issue_by_key = {
        (detail["name"], detail["type"]): detail["issue"]
        for detail in parity_audit["details"]
    }

    assert "parameters out of signature order" in issue_by_key[("out_of_order", "args")]
    assert "missing *args" in issue_by_key[("kw_only_and_varargs", "args")]
    assert "extra args" in issue_by_key[("kw_only_and_varargs", "args")]
    assert "duplicate alpha" in issue_by_key[("duplicated", "args")]
    assert ("stale_raises", "raises") not in issue_by_key


def test_build_sync_audit_accepts_summary_line_return_and_override_exceptions(
    tmp_path: Path,
) -> None:
    module = load_audit_module()

    summary_audit = module.build_sync_audit(write_summary_line_module(tmp_path))["docstring_sync_audit"]
    override_audit = module.build_sync_audit(write_override_module(tmp_path))["docstring_sync_audit"]

    assert summary_audit["remaining_issues"] == 0
    assert override_audit["remaining_issues"] == 0


def test_build_sync_audit_flags_property_args_and_allows_special_self_docs(
    tmp_path: Path,
) -> None:
    module = load_audit_module()

    property_audit = module.build_sync_audit(write_property_args_module(tmp_path))["docstring_sync_audit"]
    self_audit = module.build_sync_audit(write_self_semantics_module(tmp_path))["docstring_sync_audit"]

    assert property_audit["details"] == [
        {
            "name": "Example.display_name",
            "kind": "method",
            "line": 3,
            "type": "args",
            "issue": "Property docstring should not include an Args section.",
        }
    ]
    assert self_audit["remaining_issues"] == 0


def test_prompt_scope_filter_removes_out_of_scope_tests_and_precondition_raises(
    tmp_path: Path,
) -> None:
    module = load_audit_module()
    sample_path = write_sample_module(tmp_path)

    details = module.build_sync_audit(sample_path)["docstring_sync_audit"]["details"]
    filtered = filter_prompt_scoped_details(
        details,
        required_names={
            "Example.method",
            "async_function",
            "outer.inner",
            "configured_client",
        },
        ignored_raise_names={"Example.method", "async_function", "outer.inner"},
    )

    assert {(detail["name"], detail["type"]) for detail in filtered} == {
        ("Example.method", "returns"),
        ("async_function", "returns"),
        ("outer.inner", "returns"),
        ("configured_client", "returns"),
    }


def test_build_sync_audit_skips_overload_stubs_and_flags_stray_returns_for_none(
    tmp_path: Path,
) -> None:
    module = load_audit_module()
    overload_path = write_overload_module(tmp_path)

    overload_audit = module.build_sync_audit(overload_path)["docstring_sync_audit"]

    assert overload_audit == {
        "checked_items": 1,
        "remaining_issues": 0,
        "details": [],
    }

    none_return_path = tmp_path / "none_return_module.py"
    none_return_path.write_text(
        textwrap.dedent(
            '''
            def noop() -> None:
                """Do nothing.

                Returns:
                    Nothing useful.
                """
                return None
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    none_return_audit = module.build_sync_audit(none_return_path)["docstring_sync_audit"]

    assert none_return_audit["remaining_issues"] == 1
    assert none_return_audit["details"] == [
        {
            "name": "noop",
            "kind": "function",
            "line": 1,
            "type": "returns",
            "issue": "Docstring should omit Returns for a None-returning callable.",
        }
    ]


def test_build_sync_audit_treats_noreturn_as_non_returning(tmp_path: Path) -> None:
    module = load_audit_module()
    sample_path = tmp_path / "noreturn_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            from typing import NoReturn


            def abort(message: str) -> NoReturn:
                """Abort the current operation.

                Raises:
                    RuntimeError: Always raised to abort the operation.
                """
                raise RuntimeError(message)
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    audit = module.build_sync_audit(sample_path)["docstring_sync_audit"]

    assert audit["details"] == []


def test_cli_emits_fenced_yaml_block(tmp_path: Path):
    sample_path = write_sample_module(tmp_path)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(sample_path)],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.startswith("```yaml docstring_sync_audit\n")
    assert "docstring_sync_audit:\n" in result.stdout
    assert result.stdout.rstrip().endswith("```")


def test_cli_usage_references_current_script_name():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 1
    assert "python-docstring-sync-audit.py" in result.stderr