from __future__ import annotations

import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "python-docstring-mismatch-finder.py"


def load_mismatch_module():
    spec = importlib.util.spec_from_file_location(
        "python_docstring_mismatch_finder",
        SCRIPT_PATH,
    )
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
            def supported_layouts(alpha: str, beta: int, *args: str, gamma: bool = False, **kwargs: str) -> str:
                """Exercise supported Args layouts.

                Args:
                    alpha:
                        Multi-line description for alpha.
                        Continues on another line.
                    beta (int): Inline description for beta.
                    *args:
                        Extra positional values.
                    gamma: Keyword-only flag.
                    **kwargs (dict[str, str]):
                        Extra keyword values.

                Returns:
                    str: Echoed value.
                """
                return alpha


            def missing_doc_entry(required: str, *args: str, **kwargs: str) -> str:
                """Exercise a missing documented parameter.

                Args:
                    required: Present.
                    **kwargs: Extra keyword values.

                Returns:
                    str: Echoed value.
                """
                return required
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_return_mismatch_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "return_mismatch_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            from collections.abc import Generator


            def outer() -> str:
                """Return the outer value.

                Returns:
                    The outer value.
                """

                def inner() -> Generator[str, None, None]:
                    """Yield a nested marker.

                    Yields:
                        Nested marker.
                    """
                    yield "nested"

                next(inner())
                return "outer"


            def missing_returns(value: int) -> int:
                """Echo the provided value.

                Args:
                    value: Value to return.
                """
                return value


            def generator_with_both() -> Generator[str, None, None]:
                """Yield each generated value.

                Returns:
                    The generated values.

                Yields:
                    Individual generated values.
                """
                yield "item"
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_property_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "property_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            from functools import cached_property


            class Example:
                def __init__(self) -> None:
                    self._display_name = "copilot"

                @property
                def display_name(self) -> str:
                    """Configured display name."""
                    return self._display_name

                @display_name.setter
                def display_name(self, value: str) -> None:
                    """Update the display name.

                    Yields:
                        Nothing.
                    """
                    self._display_name = value

                @display_name.deleter
                def display_name(self) -> None:
                    """Clear the display name.

                    Yields:
                        Nothing.
                    """
                    self._display_name = ""

                @cached_property
                def slug(self) -> str:
                    """Cached slug."""
                    return "copilot"
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_args_parity_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "args_parity_module.py"
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


def write_duplicate_method_names_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "duplicate_method_names.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            class Alpha:
                def run(self, value: int) -> int:
                    """Run the configured operation."""
                    return value


            class Beta:
                def run(self, value: int) -> int:
                    """Run the configured operation."""
                    return value
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


def test_parse_args_section_supports_common_google_layouts() -> None:
    module = load_mismatch_module()

    doc = textwrap.dedent(
        '''
        Summary.

        Args:
            alpha:
                Multi-line description.
            beta (int): Inline description.
            *args:
                Additional positional values.
            **kwargs (dict[str, str]):
                Additional keyword values.

        Returns:
            str: Example return value.
        '''
    )

    assert module.parse_args_section(doc) == ["alpha", "beta", "*args", "**kwargs"]


def test_check_file_matches_supported_args_semantically(tmp_path: Path) -> None:
    module = load_mismatch_module()
    sample_path = write_sample_module(tmp_path)

    issues = module.check_file(str(sample_path))
    issues_by_name = {issue["name"]: issue for issue in issues}

    assert "supported_layouts" not in issues_by_name
    assert issues_by_name["missing_doc_entry"]["missing_params"] == ["*args"]
    assert issues_by_name["missing_doc_entry"]["extra_params"] == []


def test_check_file_flags_missing_returns_and_ignores_nested_generator_yields(
    tmp_path: Path,
) -> None:
    module = load_mismatch_module()
    sample_path = write_return_mismatch_module(tmp_path)

    issues = module.check_file(str(sample_path))
    issues_by_name = {issue["name"]: issue for issue in issues}

    assert "outer" not in issues_by_name
    assert issues_by_name["missing_returns"]["missing_params"] == []
    assert issues_by_name["missing_returns"]["extra_params"] == []
    assert issues_by_name["missing_returns"]["generator"] is False
    assert issues_by_name["missing_returns"]["has_returns"] is False
    assert issues_by_name["missing_returns"]["has_yields"] is False

    assert issues_by_name["generator_with_both"]["missing_params"] == []
    assert issues_by_name["generator_with_both"]["extra_params"] == []
    assert issues_by_name["generator_with_both"]["generator"] is True
    assert issues_by_name["generator_with_both"]["has_returns"] is True
    assert issues_by_name["generator_with_both"]["has_yields"] is True


def test_check_file_skips_overload_stubs_and_property_getters(tmp_path: Path) -> None:
    module = load_mismatch_module()

    overload_issues = module.check_file(str(write_overload_module(tmp_path)))
    property_issues = module.check_file(str(write_property_module(tmp_path)))

    assert overload_issues == []
    assert property_issues == []


def test_check_file_flags_args_order_duplicates_and_keyword_only_markers(
    tmp_path: Path,
) -> None:
    module = load_mismatch_module()
    sample_path = write_args_parity_module(tmp_path)

    issues = module.check_file(str(sample_path))
    issues_by_name = {issue["name"]: issue for issue in issues}

    assert issues_by_name["out_of_order"]["missing_params"] == []
    assert issues_by_name["out_of_order"]["extra_params"] == []
    assert issues_by_name["out_of_order"]["arg_issues"] == ["parameters out of signature order"]

    assert issues_by_name["kw_only_and_varargs"]["missing_params"] == ["*args"]
    assert issues_by_name["kw_only_and_varargs"]["extra_params"] == ["args"]
    assert issues_by_name["kw_only_and_varargs"]["arg_issues"] == []

    assert issues_by_name["duplicated"]["missing_params"] == []
    assert issues_by_name["duplicated"]["extra_params"] == []
    assert issues_by_name["duplicated"]["arg_issues"] == ["duplicate entries for alpha"]


def test_check_file_accepts_summary_line_returns_and_skips_docless_overrides(
    tmp_path: Path,
) -> None:
    module = load_mismatch_module()

    assert module.check_file(str(write_summary_line_module(tmp_path))) == []
    assert module.check_file(str(write_override_module(tmp_path))) == []


def test_check_file_emits_qualified_names_for_repeated_methods(tmp_path: Path) -> None:
    module = load_mismatch_module()
    sample_path = write_duplicate_method_names_module(tmp_path)

    issues = module.check_file(str(sample_path))

    assert {issue["name"] for issue in issues} == {"Alpha.run", "Beta.run"}
    assert {issue["kind"] for issue in issues} == {"method"}


def test_check_file_flags_property_args_and_allows_special_self_docs(tmp_path: Path) -> None:
    module = load_mismatch_module()

    property_issues = module.check_file(str(write_property_args_module(tmp_path)))
    self_issues = module.check_file(str(write_self_semantics_module(tmp_path)))

    assert property_issues == [
        {
            "name": "Example.display_name",
            "kind": "method",
            "lineno": 3,
            "missing_params": [],
            "extra_params": [],
            "arg_issues": ["property docstring should not include an Args section"],
            "generator": False,
            "has_returns": False,
            "has_yields": False,
        }
    ]
    assert self_issues == []


def test_check_file_flags_stray_returns_for_none_returning_callables(tmp_path: Path) -> None:
    module = load_mismatch_module()
    sample_path = tmp_path / "none_return_module.py"
    sample_path.write_text(
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

    issues = module.check_file(str(sample_path))

    assert len(issues) == 1
    assert issues[0]["name"] == "noop"
    assert issues[0]["lineno"] == 1
    assert issues[0]["missing_params"] == []
    assert issues[0]["extra_params"] == []
    assert issues[0]["arg_issues"] == []
    assert issues[0]["generator"] is False
    assert issues[0]["has_returns"] is True
    assert issues[0]["has_yields"] is False


def test_check_file_treats_noreturn_as_non_returning(tmp_path: Path) -> None:
    module = load_mismatch_module()
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

    assert module.check_file(str(sample_path)) == []




@pytest.mark.parametrize(
    ("argv", "expected_returncode", "expected_stream"),
    [
        ([], 1, "stderr"),
        (["sample.py", "extra.py"], 1, "stderr"),
        (["--help"], 0, "stdout"),
    ],
)
def test_cli_handles_usage_requests_consistently(
    argv: list[str],
    expected_returncode: int,
    expected_stream: str,
) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *argv],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == expected_returncode

    output = result.stdout if expected_stream == "stdout" else result.stderr
    other_output = result.stderr if expected_stream == "stdout" else result.stdout
    assert "python-docstring-mismatch-finder.py" in output
    assert output.startswith("Usage: python ")
    assert other_output == ""