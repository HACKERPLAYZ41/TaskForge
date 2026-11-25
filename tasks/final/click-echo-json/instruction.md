# Feature Specification: Click JSON Echo Utility

## 1. Overview
Add click.echo_json for standardized JSON output serialization with indentation, sort keys, and fallback serializer.

## 2. Target Location
- **Target Module(s)**: `src/click/utils.py, src/click/__init__.py`
- **Category / Taxonomy**: `new endpoint/function`
- **Difficulty Tier**: `EASY`

## 3. Interface & Signature Requirements
```python
echo_json(obj: Any, file: Optional[IO] = None, nl: bool = True, err: bool = False, indent: Optional[int] = 2, sort_keys: bool = False, default: Optional[Callable] = None) -> None
```

## 4. Behavioral Specifications & Edge Cases
The implementation must satisfy the following concrete behavioral requirements:

- **Case 1: Echo json basic**
  - *Scenario*: Behavior verified by test_echo_json_basic.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 2: Echo json indent and sort keys**
  - *Scenario*: Behavior verified by test_echo_json_indent_and_sort_keys.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 3: Echo json custom default**
  - *Scenario*: Behavior verified by test_echo_json_custom_default.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 4: Echo json stderr**
  - *Scenario*: Behavior verified by test_echo_json_stderr.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 5: Echo json negative indent**
  - *Scenario*: Behavior verified by test_echo_json_negative_indent.
  - *Expected Outcome*: Raises ValueError
- **Case 6: Echo json non callable default**
  - *Scenario*: Behavior verified by test_echo_json_non_callable_default.
  - *Expected Outcome*: Raises TypeError
- **Case 7: Echo json exported**
  - *Scenario*: Behavior verified by test_echo_json_exported.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.

- **Backward Compatibility**: All existing repository functionality and baseline tests must continue to pass without regression.

## 5. Verification
A test suite is provided to verify your implementation. When complete, run:
```bash
pytest -v tests/test_feature.py
```
Ensure both the new feature tests and all regression tests pass.
