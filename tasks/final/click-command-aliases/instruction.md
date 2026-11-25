# Feature Specification: Command and Group Aliases

## 1. Overview
Add aliases support to Click Command and Group classes. Commands accept an optional aliases list/tuple allowing commands to be looked up and invoked by primary name or any registered alias, while keeping list_commands clean.

## 2. Target Location
- **Target Module(s)**: `src/click/core.py`
- **Category / Taxonomy**: `CLI option`
- **Difficulty Tier**: `MEDIUM`

## 3. Interface & Signature Requirements
```python
Command(name: Optional[str], ..., aliases: Optional[Sequence[str]] = None) -> None
```

## 4. Behavioral Specifications & Edge Cases
The implementation must satisfy the following concrete behavioral requirements:

- **Case 1: Command aliases basic**
  - *Scenario*: Behavior verified by test_command_aliases_basic.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 2: Command multiple aliases**
  - *Scenario*: Behavior verified by test_command_multiple_aliases.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 3: Subgroup aliases**
  - *Scenario*: Behavior verified by test_subgroup_aliases.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 4: Aliases not duplicated in list commands**
  - *Scenario*: Behavior verified by test_aliases_not_duplicated_in_list_commands.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.
- **Case 5: Unknown alias error**
  - *Scenario*: Behavior verified by test_unknown_alias_error.
  - *Expected Outcome*: Succeeds and updates state/returns expected value.

- **Backward Compatibility**: All existing repository functionality and baseline tests must continue to pass without regression.

## 5. Verification
A test suite is provided to verify your implementation. When complete, run:
```bash
pytest -v tests/test_feature.py
```
Ensure both the new feature tests and all regression tests pass.
