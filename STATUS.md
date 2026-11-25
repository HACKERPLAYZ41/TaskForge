# TaskForge: Verified Ground-Truth Status Report

**Document Date**: 2026-11-22  
**Target Host**: `blockcode` (Ubuntu 26.04.1 LTS, 4 cores, 5.5GB RAM, 52GB disk)  
**Harbor Specification**: v1.4 compliance (0 errors, 0 warnings on `harbor lint`)  

---

## 1. Executive Summary & Verified Reality

This document replaces all previous assertions from `FINAL_STATUS.md` and `logs/PROGRESS.md` (Steps 8–10), which were invalidated due to OpenRouter free-tier quota exhaustion and offline heuristic fallbacks. 

Every claim below is backed by real execution output on `blockcode` with zero fake evidence, zero simulated agent loops, and zero lowered thresholds.

---

## 2. Process Safety & Runaway Protection

### The 31-Hour Runaway Pytest Incident & Root Cause
During automated AST mutation testing, comparison flips (`while i < n` $\to$ `while i >= n`), recursive loops, or swallowed exception handlers caused `pytest` processes to enter non-terminating loops. Without hard sub-process timeouts, these orphaned processes ran indefinitely (one process ran for 31 hours before being terminated).

### Remediation Implemented & Verified
1. **Process Group Termination (`killpg` & `SIGKILL`)**:
   - In `taskforge/gates/validator.py`, all test executions (`_run_in_local_sandbox`, `_run_in_docker`, and `evaluate_mutants`) now invoke `run_cmd_with_killpg()`.
   - On Linux/POSIX systems, processes are spawned in fresh process groups (`preexec_fn=os.setsid`).
   - If an execution exceeds its hard timeout (20s per mutant, 30s per test suite, 120s per Docker gate build), `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` is dispatched immediately to terminate the entire process hierarchy.
2. **Mutant Timeout Classification**:
   - A mutant that triggers an execution timeout is classified as **`status: KILLED`**, with **`reason: timeout`** recorded in `logs/<task>/g3_mutants.json`.
3. **Startup Process Safety Guard**:
   - `bin/taskforge` scans running processes on startup (`find_stale_pytest_processes`).
   - If lingering orphaned pytest processes are detected from previous runs, the CLI refuses to execute and outputs the exact PIDs and command lines with termination instructions (`kill -9 <pids>`).

---

## 3. LLM Daily Budget Exhaustion & Fast-Fail Protocol

### Incident
OpenRouter returned HTTP 429 quota exhaustion:
```json
{
  "error": {
    "message": "Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day: https://openrouter.ai/settings/credits?utm_source=api&utm_campaign=free_daily_limit",
    "code": 429,
    "metadata": {
      "headers": {
        "X-RateLimit-Limit": "50",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1795305600000"
      },
      "limit_source": "openrouter_free_tier_daily"
    }
  }
}
```

### Remediation Implemented
1. **Global Daily Call Budget Enforcement**:
   - `taskforge/llm.py` now monitors for daily quota exhaustion. Upon the first detection of `free-models-per-day` or `free_tier_daily`, it writes a persistent state record to `~/.cache/llm/budget_status.json`.
   - Subsequent calls raise `LLMBudgetExhaustedError` immediately.
   - **Zero Retry Loops**: The pipeline makes zero redundant network requests when the daily limit is reached.
2. **Deterministic & Offline Fallback**:
   - With LLM calls halted, the architecture preserves full offline capabilities (`--offline` flag) using the calibrated task catalog and AST contract verification for gates.

---

## 4. Proposer Architecture Overhaul

The task proposer in `taskforge/proposer.py` was refactored with strict structural filters:
1. **Module Filtering**:
   - Automatically excludes `__init__.py`, `tests/`, and files lacking substantial business logic (modules with $< 2$ functions and classes are ignored).
   - Candidate modules are sorted descending by function and class count, targeting the richest modules first.
2. **Title-Derived Task IDs**:
   - Task IDs are now derived strictly from the feature title (e.g. `re.sub(r'[^a-zA-Z0-9]+', '-', feature_title).lower()`), such as `tiered-volume-discount-calculation`.
   - Task IDs are never generated from module file paths.

---

## 5. Harness Proof Verification (No LLM Required)

To verify the mathematical validity of the Harbor evaluation harness, the oracle agent and no-op agent were evaluated on a template task from `archive_offline/`:

- **Oracle Agent**:
  - Applies `solution/solve.sh` to a clean repository checkout.
  - Verifier score: **`1.0`** (100% pass across feature and regression tests).
- **No-Op Agent**:
  - Makes zero modifications to the clean starting repository.
  - Verifier score: **`0.0`** (Feature tests fail as expected on unimplemented requirements; no false passes).
- **Audit File**: `logs/harness_proof.txt`.

---

## 6. System Doctor Verification

The new `taskforge doctor` CLI command provides an instant diagnostic snapshot of system health:
```bash
./bin/taskforge doctor
```
Checks:
1. **Stale Processes**: Confirms no orphaned `pytest` processes remain active.
2. **LLM Budget Status**: Displays `[EXHAUSTED]` status with fast-fail active.
3. **Docker Engine**: Confirms Docker daemon responsiveness and active container counts.
4. **Disk Free Space**: Verifies sufficient local disk capacity for container operations.

---

## 7. What is Verified vs. Not Yet Proven

| Component | Status | Verification Evidence |
|-----------|--------|-----------------------|
| AST Codebase Analyzer | **VERIFIED** | Correctly maps modules, functions, classes, and LOC |
| Harbor Packaging (v1.4) | **VERIFIED** | Passes `harbor lint` with 0 errors and 0 warnings |
| Gate G1 (Baseline Invalidation) | **VERIFIED** | Clean repo fails feature tests, passes regression |
| Gate G2 (Reference Verification) | **VERIFIED** | `solve.sh` passes feature + regression suites |
| Gate G3 (Mutation Testing + Timeouts) | **VERIFIED** | >=15 mutants, kills timeouts as KILLED, SIGKILLs process groups |
| Gate G4 (Regression Sensitivity) | **VERIFIED** | Base mutations break regression test suite |
| Gate G5 (Determinism) | **VERIFIED** | 3 consecutive runs produce identical results |
| Evaluation Harness (Oracle / No-Op) | **VERIFIED** | Oracle = 1.0, No-Op = 0.0 logged in `logs/harness_proof.txt` |
| TaskForge Doctor | **VERIFIED** | Diagnostic command working cleanly |
| Live LLM Multi-Model Sweep | **BLOCKED** | OpenRouter free-models-per-day quota exhausted (50/50 used) |
| Live G6 Judge & G7 Agent on Final Tasks | **BLOCKED** | Requires refreshed API credits or organizer-provided key |
