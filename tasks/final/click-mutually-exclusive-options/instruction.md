# Feature Specification: Mutually Exclusive Options

## 1. Overview
Add mutually_exclusive parameter to Option to automatically reject conflicting CLI options when both are provided.

## 2. Target Location
- **Target Module(s)**: `src/click/core.py`
- **Category / Taxonomy**: `config-driven behavior`
- **Difficulty Tier**: `MEDIUM`

## 3. Interface & Signature Requirements
```python
Option(..., mutually_exclusive: Optional[Sequence[str]] = None) -> None
```

## 4. Behavioral Specifications & Edge Cases
The implementation must satisfy the following concrete behavioral requirements:

- **Case 1: Mutex single option passes**
  - *Scenario*: Behavior verified by test_mutex_single_option_passes.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 2: Mutex conflict raises usage error**
  - *Scenario*: Behavior verified by test_mutex_conflict_raises_usage_error.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 3: Mutex defaults do not conflict**
  - *Scenario*: Behavior verified by test_mutex_defaults_do_not_conflict.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 4: Mutex order independence**
  - *Scenario*: Behavior verified by test_mutex_order_independence.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.

- **Backward Compatibility**: All existing repository functionality and baseline tests must continue to pass without regression.

## 5. Verification
A test suite is provided to verify your implementation. When complete, run:
```bash
pytest -v tests/test_feature.py
```
Ensure both the new feature tests and all regression tests pass.
