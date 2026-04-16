from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "python-docstring-indexer.py"


def load_indexer_module():
    spec = importlib.util.spec_from_file_location("python_docstring_indexer", SCRIPT_PATH)
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
            """Sample module for docstring-indexer coverage."""

            @fixture
            def bare_name_fixture():
                return "bare-name"


            @fixture(name="configured")
            def bare_name_call_fixture():
                return "bare-name-call"


            @pytest.fixture
            def attribute_fixture():
                return "attribute"


            @pytest.fixture(scope="session")
            def attribute_call_fixture():
                return "attribute-call"


            def plain_function():
                return "plain"
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_control_flow_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "control_flow_module.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            """Sample module for control-flow discovery coverage."""

            def outer(flag: bool) -> int:
                """Run nested definitions based on control flow."""
                if flag:
                    def inner() -> int:
                        """Return from the nested helper."""
                        return 1

                    return inner()

                try:
                    class Local:
                        def method(self) -> int:
                            """Return from the local class."""
                            return 2
                except RuntimeError:
                    return 0

                return Local().method()
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
                """Parse a supported raw value."""
                return len(value)
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def write_fixture_named_like_test_module(tmp_path: Path) -> Path:
    sample_path = tmp_path / "fixture_named_like_test.py"
    sample_path.write_text(
        textwrap.dedent(
            '''
            import pytest


            @pytest.fixture
            def test_configured_client():
                return "fixture"
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
                @property
                def display_name(self) -> str:
                    """Configured display name."""
                    return "copilot"

                @display_name.setter
                def display_name(self, value: str) -> None:
                    self._display_name = value

                @display_name.deleter
                def display_name(self) -> None:
                    self._display_name = ""
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return sample_path


def test_build_index_classifies_fixture_decorator_variants(tmp_path: Path) -> None:
    module = load_indexer_module()
    sample_path = write_sample_module(tmp_path)

    report = module.build_index(sample_path)
    index = report["docstring_index"]
    items_by_name = {item["name"]: item for item in index["items"]}

    assert set(index) == {"total", "items"}
    assert index["total"] == 6

    assert items_by_name["bare_name_fixture"]["kind"] == "fixture"
    assert items_by_name["bare_name_call_fixture"]["kind"] == "fixture"
    assert items_by_name["attribute_fixture"]["kind"] == "fixture"
    assert items_by_name["attribute_call_fixture"]["kind"] == "fixture"
    assert items_by_name["plain_function"]["kind"] == "function"


def test_build_index_discovers_nested_definitions_inside_control_flow(tmp_path: Path) -> None:
    module = load_indexer_module()
    sample_path = write_control_flow_module(tmp_path)

    report = module.build_index(sample_path)
    index = report["docstring_index"]
    items_by_name = {item["name"]: item for item in index["items"]}

    assert index["total"] == 5
    assert items_by_name["outer"]["kind"] == "function"
    assert items_by_name["outer.inner"]["kind"] == "nested_function"
    assert items_by_name["outer.Local"]["kind"] == "class"
    assert items_by_name["outer.Local.method"]["kind"] == "method"


def test_build_index_skips_overload_stubs(tmp_path: Path) -> None:
    module = load_indexer_module()
    sample_path = write_overload_module(tmp_path)

    report = module.build_index(sample_path)
    index = report["docstring_index"]
    items = index["items"]

    assert index["total"] == 2
    assert items[0] == {"name": "module", "kind": "module", "lineno": 1, "has_docstring": False}
    assert items[1]["name"] == "parse_value"
    assert items[1]["kind"] == "function"
    assert items[1]["has_docstring"] is True
    assert items[1]["lineno"] > 1


def test_build_index_prefers_fixture_classification_over_test_name(tmp_path: Path) -> None:
    module = load_indexer_module()
    sample_path = write_fixture_named_like_test_module(tmp_path)

    report = module.build_index(sample_path)
    items_by_name = {item["name"]: item for item in report["docstring_index"]["items"]}

    assert items_by_name["test_configured_client"]["kind"] == "fixture"


def test_build_index_skips_property_accessors(tmp_path: Path) -> None:
    module = load_indexer_module()
    sample_path = write_property_accessor_module(tmp_path)

    report = module.build_index(sample_path)
    items_by_name = {item["name"]: item for item in report["docstring_index"]["items"]}

    assert report["docstring_index"]["total"] == 3
    assert set(items_by_name) == {"module", "Example", "Example.display_name"}