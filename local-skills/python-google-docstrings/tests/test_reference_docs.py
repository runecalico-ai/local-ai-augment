from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / "SKILL.md"
PROMPT_PATH = ROOT / "references" / "python-docstrings-google.prompt.md"
EXAMPLES_PATH = ROOT / "references" / "examples.md"


def test_skill_metadata_surfaces_specialized_use_cases() -> None:
    skill_text = SKILL_PATH.read_text(encoding="utf-8")

    assert "pytest fixtures and tests" in skill_text
    assert "synchronization audits" in skill_text
    assert "property" in skill_text
    assert "dataclass" in skill_text
    assert "overload" in skill_text
    assert "override" in skill_text
    assert "@overload" in skill_text
    assert "Bundled scripts are authoritative" in skill_text
    assert "stale exception notes" in skill_text
    assert "keyword-only" in skill_text
    assert "docstring-less overrides as manual" in skill_text


def test_prompt_metadata_and_reference_example_use_non_redundant_type_text() -> None:
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")

    assert "pytest fixtures/tests" in prompt_text
    assert "property" in prompt_text
    assert "overload" in prompt_text
    assert "overridden methods" in prompt_text
    assert "user_id (int):" not in prompt_text
    assert "dict: Dictionary with keys:" not in prompt_text
    assert "Args:\n        user_id:" in prompt_text
    assert "Returns:\n        Dictionary with keys:" in prompt_text
    assert "helper scripts are intentionally conservative" in prompt_text
    assert "callable-only sync audit does not validate class Args blocks" in prompt_text
    assert "pure-test modules" in prompt_text
    assert "either include\n  an explicit Returns: or Yields: section" in prompt_text
    assert "stale exception notes manually before" in prompt_text
    assert "do not provide every aggregate field directly" in prompt_text
    assert "not a standalone completeness\noracle" in prompt_text
    assert "has_docstring. Derive required_docstring, reason, and required_total at the\n  prompt layer" in prompt_text
    assert "prompt-level aggregates" in prompt_text
    assert "absence of a literal keyword-only marker" in prompt_text
    assert "docstring-less overrides are treated as manual\n  exceptions" in prompt_text


def test_examples_avoid_repeating_signature_types_in_annotated_functions() -> None:
    examples_text = EXAMPLES_PATH.read_text(encoding="utf-8")

    assert "transactions (pd.DataFrame):" not in examples_text
    assert "items (list[dict]):" not in examples_text
    assert "endpoint (str):" not in examples_text
    assert "urls (list[str]):" not in examples_text
    assert "max_attempts (int, optional):" not in examples_text
    assert "data (dict[str, Any]):" not in examples_text
    assert "capacity (int):" not in examples_text
    assert "message (str):" not in examples_text

    assert "transactions: Transaction records" in examples_text
    assert "items: Items to process" in examples_text
    assert "endpoint: Full URL of the API endpoint." in examples_text
    assert "urls: List of URLs to fetch." in examples_text
    assert "max_attempts: Maximum retry attempts." in examples_text
    assert "data: User input data to validate." in examples_text
    assert "@overload" in examples_text
    assert "@staticmethod" in examples_text
    assert "@classmethod" in examples_text
    assert "@dataclass" in examples_text
    assert "def log_event(event: str) -> None:" in examples_text
    assert "async def fetch_status" in examples_text
    assert "async def stream_results" in examples_text
    assert "@pytest.fixture" in examples_text
    assert "def test_refresh_token_retries_once" in examples_text
    assert "Keyword-only flag" in examples_text