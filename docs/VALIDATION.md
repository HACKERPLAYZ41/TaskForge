# TaskForge Validation Gates (G1 - G7)

Validation evidence is central to TaskForge. A task is only promoted to `tasks/final/` if it passes all seven strict validation gates.

---

## Gate Summary

| Gate | Name | Goal | Failure Condition |
|------|------|------|-------------------|
| **G1** | Baseline Invalidation | Confirm task is not pre-solved | Feature tests PASS on clean baseline repo |
| **G2** | Reference Verification | Confirm solution solves task | Feature or regression tests FAIL after `solve.sh` |
| **G3** | Mutation Testing | Confirm test suite kills buggy code | Feature tests kill < 80% of auto-generated mutants |
| **G4** | Regression Sensitivity | Confirm base suite catches breakages | Regression tests PASS on broken existing paths |
| **G5** | Flakiness Check | Confirm test suite is deterministic | Non-identical outcomes across 3 container runs |
| **G6** | Spec-Test Alignment | Confirm contract adherence | Tests assert unspecified behaviors or leak internal variables |
| **G7** | Solvability Sanity | Confirm task is actionable by AI | Task contains undefined external symbols or unachievable criteria |

---

## Detailed Gate Mechanics

### G1: Baseline Invalidation
- **Why it exists**: An evaluation task is meaningless if the starting code already passes the test suite.
- **Protocol**: Feature tests (`test_feature.py`) are mounted against the baseline repository at the starting commit hash. Feature tests MUST fail with `ImportError`, `AttributeError`, or behavioral assertion failure. Existing regression tests MUST pass.

### G2: Reference Verification
- **Why it exists**: Guarantees that the supplied reference solution (`solution/solve.sh`) represents a valid, complete, working implementation.
- **Protocol**: In a clean temporary environment, `solve.sh` is applied. Both `test_feature.py` and the existing regression test suite are executed. Both MUST pass with exit code 0.

### G3: Mutation Testing (>= 80% Kill Rate, >= 15 Mutants)
- **Why it exists**: Prevents weak tests that pass regardless of implementation flaws (e.g., trivial assertions, missing edge case checks).
- **Protocol**: AST-guided mutation produces >= 15 distinct mutants using 9 AST operators:
  - `flip_comparison`: `<` inverted to `>=`, `==` inverted to `!=`, `in` to `not in`
  - `off_by_one`: numeric boundary changed by ±1
  - `remove_branch`: conditional branch body replaced with `pass`
  - `return_default`: return value mutated to `None`, `0`, or `False`
  - `drop_validation`: validation exception `raise` statement dropped
  - `invert_boolean`: logical `and` <-> `or`, `not x` <-> `x`, `True` <-> `False`
  - `binary_op`: `+` <-> `-`, `*` <-> `/`
  - `swap_arguments`: positional argument order reversed in multi-arg calls
  - `swallow_exception`: exception handler body replaced with `pass`
- Feature tests are run against each mutant. If >= 80% of mutants trigger test failure and >= 5 mutants tested, G3 passes. All mutant diffs and kill/survive outcomes are logged in `g3_mutants.json`.

### G4: Regression Sensitivity
- **Why it exists**: Ensures that the repository's existing regression suite actively protects touched code paths from collateral regressions.
- **Protocol**: Existing touched base modules are mutated. The base regression suite must catch the breakage.

### G5: Flakiness & Non-Determinism Check
- **Why it exists**: AI evaluations require rock-solid determinism. Flaky tests reward lucky guesses and penalize correct solutions.
- **Protocol**: The full verification pipeline runs 3 times in independent fresh containers. All 3 runs must return identical pass/fail statuses and exit codes.

### G6: Spec-Test Alignment (Independent LLM Judge)
- **Why it exists**: Prevents test suites from checking unspecified implementation quirks or leaking solution secrets.
- **Protocol**: An independent LLM judge (`nvidia/nemotron-3.5-lightning:free` or `baidu/ernie-5.5-flash-preview:free`) evaluates whether tests strictly evaluate stated requirements without asserting unspecified behavior or leaking the reference solution.

### G7: Solvability Sanity (Autonomous Agent Attempt)
- **Why it exists**: Confirms that an AI coding agent supplied strictly with `instruction.md` has all necessary context, types, and dependencies to solve the task.
- **Protocol**: An autonomous agent attempt is run against `instruction.md` and the clean repository. The outcome and execution trace are preserved in `g7_agent_attempt.log`.
