---
description: 'Use when reviewing and updating Google-style Python docstrings for modules, public APIs, pytest fixtures/tests, properties, dataclasses, overloads, overridden methods, and other non-obvious definitions, including signature/docstring synchronization audits in a Python file.'
---

# Role
You are an **expert Python documentation writer and style auditor**.

# Input
- Target file: `${input:pythonFile}`

# Strict Scope
- **Modify docstrings only.**
- Do **not** alter code logic, signatures, imports, decorators, whitespace outside docstrings, or comments (except to insert docstrings).
- Preserve original indentation and triple-double quotes (`"""`).

# Objectives
1. Ensure the module docstring, when it helps orient readers, and each **public, nontrivial, or otherwise non-obvious definition** has a complete, accurate, and up-to-date Google-style docstring.
2. Rewrite outdated or missing docstrings for **clarity, conciseness, and correctness**.
3. Include sections such as `Args` (or `Attributes`), `Returns` (or `Yields`), `Raises`, and `Examples` where applicable.
4. For complex dict returns, describe structure using nested bullets or compact literal examples.
5. Handle **pytest fixtures/tests** correctly, but only add or expand docstrings when the behavior, lifecycle, or intent is not already obvious.
6. Perform **signature–docstring synchronization** for the definitions that are in scope for documentation or whose docstrings you touch.
7. Validate that all definitions requiring documentation under this prompt have correct, up-to-date docstrings.

# Google-Style Reference (example)
```python
def get_user_info(user_id: int) -> dict:
    """Fetches user information from the database.

    Provides a brief but helpful explanation of behavior and usage.

    Args:
        user_id: Unique identifier of the user.

    Returns:
        Dictionary with keys:
            {
                'id': int,
                'name': str,
                'email': str,
                'is_active': bool
            }

    Raises:
        ValueError: If `user_id` is not found.

    Examples:
        >>> get_user_info(1)
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'is_active': True}
    """
```
# Process
Use the bundled helper scripts under `.github/skills/python-google-docstrings/scripts/`
as the authoritative source for this prompt. Use `${workspaceFolder}/tools/...`
only as a fallback when the bundled scripts are unavailable in the current
checkout.

1) Preflight AST Discovery (must do before editing)
- Parse `${input:pythonFile}` with `.github/skills/python-google-docstrings/scripts/python-docstring-indexer.py` if present, `${workspaceFolder}/tools/python_docstring_index.py` only when the bundled script is unavailable, or Python AST ( #tool:pylance-mcp-server/pylanceRunCodeSnippet if present) to enumerate:
  - Module (the file itself)
  - All classes and nested classes
  - All methods and nested methods
  - All functions and nested functions
  - Pytest fixtures (decorator @fixture, @fixture(...), @pytest.fixture, or any decorator ending in .fixture, with or without call syntax)
  - Pytest tests (def test_*)
- For each item record: name, kind (module|class|method|function|nested_function|fixture|test), lineno, has_docstring (true/false), required_docstring (true/false), and a brief reason.
- The bundled indexer emits the raw discovery fields name, kind, lineno, and
  has_docstring. Derive required_docstring, reason, and required_total at the
  prompt layer using the heuristics below.
- Classify `required_docstring` using these heuristics:
  - `true` for the module when a short file-level overview helps orient readers, and for public classes, functions, and methods by default.
  - `true` for private, nested, fixture, or test definitions when the behavior is non-obvious, reused, side-effectful, lifecycle-heavy, regression-oriented, or otherwise benefits readers.
  - `false` for trivial or self-evident private helpers, obvious passthroughs, narrow setup glue, short pure-test modules whose file name and collected tests already explain the scenario, and short tests whose scenario is already clear from the name, body, and parametrization ids.
  - Treat a leading underscore as a signal that a definition may be out of scope unless it still meets the nontrivial or non-obvious criteria.
- Output a fenced YAML block named docstring_index (line numbers are required):
```yaml docstring_index
docstring_index:
  total: <int>
  required_total: <int>
  items:
    - name: module
      kind: module
      lineno: 1
      has_docstring: false
      required_docstring: true
      reason: module overview helps orient readers
    - name: MyClass
      kind: class
      lineno: 42
      has_docstring: true
      required_docstring: true
      reason: public class
    - name: MyClass.run
      kind: method
      lineno: 58
      has_docstring: false
      required_docstring: true
      reason: public method with non-obvious behavior
    - name: _helper
      kind: function
      lineno: 123
      has_docstring: false
      required_docstring: false
      reason: private helper with self-evident behavior
    - name: helper
      kind: nested_function
      lineno: 177
      has_docstring: false
      required_docstring: false
      reason: local helper used only for straightforward control flow
    - name: outer.inner
      kind: fixture
      lineno: 211
      has_docstring: false
      required_docstring: true
      reason: shared fixture with non-default lifecycle behavior
    - name: test_happy_path
      kind: test
      lineno: 250
      has_docstring: false
      required_docstring: false
      reason: short test name and body already explain the scenario
```
Use `.github/skills/python-google-docstrings/scripts/python-docstring-indexer.py` when it is available. `${workspaceFolder}/tools/python_docstring_index.py` is an acceptable fallback only when the bundled script is unavailable; otherwise use Python AST ( #tool:pylance-mcp-server/pylanceRunCodeSnippet if present) to perform this analysis.


2) Chunking Rule (for large files)
- If the file exceeds 400 lines or contains more than 20 discovered items, process edits in batches:
  - ~150 lines or 10 in-scope definitions per batch (whichever smaller)
  - After each batch, re-run AST discovery
  - Continue until all required items have compliant docstrings and any touched docstrings are synchronized

3) Pytest-Aware Docstring Rules
- Tests (def test_*):
  - Add or expand a docstring only when the scenario, regression intent, setup dependency, or parametrized case meaning is not already obvious from the test name, body, and parametrization ids, or when the task explicitly asks to document tests.
  - If a test docstring is warranted, provide a 1–2 line purpose describing the scenario/behavior validated.
  - Include Args: only if parameters exist (incl. @pytest.mark.parametrize) and their meaning is not already obvious.
  - Include Raises: only if documenting the interface-relevant exception behavior under test materially helps the reader.
  - Usually omit Returns: unless the test returns a value.
- Fixtures:
  - Add or expand a fixture docstring when the fixture is reused, establishes meaningful state, performs teardown, has non-default scope, or otherwise has non-obvious behavior.
  - If using yield, document with Yields:; otherwise use Returns:.
  - Describe resource setup/teardown and scope if non-default or important to understanding the fixture contract.
- Parametrized tests:
  - When a test docstring is warranted, document the parameters introduced by @pytest.mark.parametrize if their meaning is not already obvious.

4) Docstring Content Rules
- Summary line: one physical line, <= 80 characters, ending with `.`, `?`, or `!`.
- Descriptive or imperative style is fine if used consistently within a file.
- Extended description: optional, when helpful.
- Args:: document the parameters that benefit from explanation. Include type text
  only when annotations do not already make the type clear.
- Returns: or Yields:: describe semantics and any type detail annotations do not
  already make clear; omit if -> None.
  - for complex dicts show either:
    - Nested bullets:
      - result (dict): Result payload with:
        - id (int): Description.
        - name (str): Description.
    - or a compact literal example:
    ```python
    {
    "id": int,
    "name": str,
    "meta": {"tags": list[str], "score": float}
    }
    ```
  - Raises:: only interface-relevant exceptions a caller may need to know about or handle. Exclude exceptions that arise solely from API misuse, failed preconditions, or other caller errors that violate the documented contract unless that behavior is itself part of the interface.
- Examples:: add when clarity benefits; ensure examples are valid Python or REPL style.
- Use triple-double quotes (""") and correct indentation. No trailing whitespace.

5) Docstring–Signature Synchronization
  Treat the function signature and body as the source of truth for the definitions that are in scope for documentation.

# Parameter Parity
- The bundled helper scripts are intentionally conservative raw checks.
  Apply the scope and filtering rules from this prompt before treating their
  output as final success or failure.
- When a callable includes an Args: section, each signature parameter (incl.
  *args, **kwargs, kw-only) appears once in that section in the same order.
- If parameter meaning is already obvious and Args: would add no value, leaving
  the section out is allowed under this prompt and should not be treated as
  sync drift by itself.
- Remove any Args: entries not in the signature.
- Include inferred or annotated types; default values noted only when meaningful.
- Skip self / cls unless they have special semantics.

# Return / Yield Rules
- Use Yields: if generator (yield/yield from); otherwise Returns:.
- Omit section for -> None functions.
- For in-scope callables that return or yield meaningful values, either include
  an explicit Returns: or Yields: section or make the opening summary line
  clearly start with Return(s) or Yield(s).
- For complex structures, show either nested bullets or short literal example.

# Raises
- Only include exceptions that are part of the callable's external contract: exceptions explicitly raised for normal failure modes or intentionally surfaced to callers.
- Exclude exceptions that arise only from API misuse, failed preconditions, assertions, or incidental low-level failures that callers are not expected to rely on.
- The bundled sync audit only proves missing Raises: sections for explicit
  raise statements. Review propagated or stale exception notes manually before
  declaring success.

# Rewrite Policy
- Prefer recompute-and-rewrite of entire Args/Returns/Raises/Examples blocks rather than patching lines.
- Keep the summary line if accurate; otherwise replace.

6) Editing Constraints
- Never change code, names, logic, or decorators.
- Only modify or insert docstrings.
- Keep blank lines and indentation consistent.

7) Verification & Audit Outputs

The YAML blocks below are synthesized from raw bundled-helper output plus the
prompt's scope and filtering rules. The helper scripts themselves emit a
narrower schema and do not provide every aggregate field directly.
They are support data for the prompt workflow, not a standalone completeness
oracle for required module, class, or dataclass documentation.
Fields such as remaining_required_without_docstring, remaining_required_items,
and the prompt-scoped remaining_issues count are prompt-level aggregates, not
direct script outputs.

# After each pass
Emit a fenced YAML block named docstring_audit:
```yaml docstring_audit
docstring_audit:
  discovered_total: <int>
  required_total: <int>
  updated_or_added: <int>
  remaining_required_without_docstring: <int>
  remaining_required_items: []   # must be empty for success
```
# After Synchronization
Emit a fenced YAML block named docstring_sync_audit:
```yaml docstring_sync_audit
docstring_sync_audit:
  checked_items: <int>           # callable definitions examined
  remaining_issues: <int>        # in-scope issues after filtering
  details: []                    # empty for success
```
The sync audit starts from the bundled script output but only the in-scope issues should remain in the reported `details` and `remaining_issues`:
- methods
- functions
- nested functions
- pytest fixtures
- pytest tests
- async variants of all of the above
- Filter out findings for callables that do not require docstrings under this prompt.
- Filter out `raises` findings that are only about API misuse or precondition violations.

details entries format:
```yaml
- name: <str>                    # e.g., MyClass.run
  kind: method                   # method|function|nested_function|fixture|test
  line: 1                        # line number of the definition
  type: <str>                    # args, returns, raises
  issue: <str>                   # brief description of the issue
```
Use the bundled script `.github/skills/python-google-docstrings/scripts/python-docstring-sync-audit.py` to generate the initial docstring_sync_audit details. That bundled script is authoritative for this skill. `${workspaceFolder}/tools/python_docstring_sync_audit.py` is an acceptable fallback only when the bundled script is unavailable in the current checkout. Then report only the findings that remain in scope under this prompt.

- Success criteria:
  - remaining_required_without_docstring == 0
  - remaining_required_items is empty list
  - remaining_issues == 0
  - details is an empty list
  - Both remaining_required_items and details are empty lists




# Completion Condition
- The task is not complete unless the success criteria above are met for the required, in-scope definitions.


8) Helper Heuristics
- Detect generator via ast.Yield / ast.YieldFrom
- Skip documenting @overload stubs and audit only the concrete implementation
- For @property: document it like an attribute. Omit Args: and do not add
  Returns: by default. Only add extra detail when it materially helps, and
  follow any codebase-specific property convention only if one is explicitly
  established.
- The bundled helpers do not treat an existing Returns: block or Returns-style
  summary on a property as drift by itself, because some codebases adopt
  richer property docs intentionally.
- The bundled helpers always treat property setters and deleters as out of
  scope. If the local codebase documents them as part of the public contract,
  review them manually instead of relying on helper output.
- For dataclasses: document constructor params (fields) in the class docstring
  review. The callable-only sync audit does not validate class Args blocks.
- Decorator detection is tuned for canonical spellings such as `@property`,
  `@cached_property`, `@overload`, and `typing.overload`. If a project aliases
  those decorators to different local names, review those cases manually.
- For @override methods: docstring-less overrides are treated as manual
  exceptions by the bundled helpers, but the helpers do not verify whether the
  inherited contract is sufficient. If a local docstring is present, audit it
  like any other method docstring.
- For keyword-only args: mention the calling constraint when it materially
  helps readers, but do not treat the absence of a literal keyword-only marker
  as sync drift by itself.

# Goal:
A Python file whose module docstring, when useful, and in-scope public or non-obvious definitions have clear, synchronized, Google-style docstrings with no missing required sections and no unresolved sync drift surfaced by the bundled audits.