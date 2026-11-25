# Feature Specification: Dynamic Choice Callback

## 1. Overview
Allow Choice param type to accept either a sequence of choices or a dynamic callable callback returning choices on demand, enabling lazy runtime evaluation of choices.

## 2. Target Location
- **Target Module(s)**: `src/click/types.py`
- **Category / Taxonomy**: `validation rule`
- **Difficulty Tier**: `EASY`

## 3. Interface & Signature Requirements
```python
Choice(choices: Union[Sequence[str], Callable[[], Sequence[str]]], case_sensitive: bool = True) -> None
```

## 4. Behavioral Specifications & Edge Cases
The implementation must satisfy the following concrete behavioral requirements:

- **Case 1: Dynamic choice basic**
  - *Scenario*: Behavior verified by test_dynamic_choice_basic.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 2: Dynamic choice validation failure**
  - *Scenario*: Behavior verified by test_dynamic_choice_validation_failure.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 3: Dynamic choice case insensitive**
  - *Scenario*: Behavior verified by test_dynamic_choice_case_insensitive.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 4: Dynamic choice setter override**
  - *Scenario*: Behavior verified by test_dynamic_choice_setter_override.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 5: Dynamic choice metavar**
  - *Scenario*: Behavior verified by test_dynamic_choice_metavar.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.

- **Backward Compatibility**: All existing repository functionality and baseline tests must continue to pass without regression.

## 5. Verification
A test suite is provided to verify your implementation. When complete, run:
```bash
pytest -v tests/test_feature.py
```
Ensure both the new feature tests and all regression tests pass.
