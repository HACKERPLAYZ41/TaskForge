# TaskForge: 3-Minute Demo Video Script

> **Note**: This document provides the structured recording script and terminal command sequence for presenting TaskForge. (Video recording pending final upload).

---

## Video Metadata
- **Title**: TaskForge: Automated Coding Task Factory for Harbor
- **Target Duration**: 2 minutes 45 seconds
- **Repository**: `https://github.com/HACKERPLAYZ41/TaskForge.git`
- **Target Project**: `pallets/click` (release version 8.1.8, commit `934813e4d421071a1b3db3973c02fe2721359a6e`)
- **Harbor Version**: `0.25.0`

---

## Scene 1: System Health & Doctor (0:00 - 0:30)

### Terminal Command:
```bash
./bin/taskforge doctor
```

### Narration:
> "Welcome to TaskForge, an autonomous coding benchmark task generator built for the Innodata Frontier AI Hackathon.
> We start by running `taskforge doctor`. TaskForge verifies system health: it checks for orphaned test processes to prevent runaway loops, verifies Docker daemon responsiveness, checks disk headroom, and monitors the LLM daily call budget."

### Visual Milestone:
- Doctor summary prints `[OK]` for Stale Processes, Docker daemon, and Disk space.

---

## Scene 2: Pinned Target Baseline Verification (0:30 - 1:00)

### Terminal Command:
```bash
cat logs/baseline_click.txt | tail -n 25
```

### Narration:
> "TaskForge targets `pallets/click`, the standard Python CLI library.
> Before generating any tasks, TaskForge clones Click at pinned release commit `934813e4d4` inside a clean container and executes the full existing test suite three consecutive times.
> Across all three runs, 628 tests pass with 0 failures, establishing a rock-solid, non-flaky baseline."

### Visual Milestone:
- Baseline test execution log displaying 3 runs of 628 passed tests in 2.0s.

---

## Scene 3: Automated Task Generation & Harbor Packaging (1:00 - 1:40)

### Terminal Command:
```bash
./bin/taskforge generate --n 4 --offline
./bin/taskforge analyze
```

### Narration:
> "Next, we generate 4 diverse feature tasks across our taxonomy matrix:
> 1. `click-command-aliases`: Command and group alias routing in `core.py`.
> 2. `click-dynamic-choice-callback`: Dynamic choice callback support in `types.py`.
> 3. `click-echo-json`: Standardized JSON terminal output utility in `utils.py`.
> 4. `click-mutually-exclusive-options`: Mutual exclusivity conflict detection in `core.py`.
>
> Every task is packaged in the official Harbor v0.25 layout: `task.toml`, `instruction.md`, `environment/Dockerfile`, `solution/solve.sh`, `tests/test_feature.py`, `tests/fail_to_pass.json`, `tests/pass_to_pass.json`, and `tests/test.sh`."

### Visual Milestone:
- Directory tree showing task layout matching Harbor 0.25 specification.

---

## Scene 4: Rigorous Quality Gates & Harbor Lint (1:40 - 2:15)

### Terminal Command:
```bash
harbor lint tasks/final/*
./bin/taskforge validate --offline
```

### Narration:
> "Quality and repeatability beat task volume. We run Harbor's official linter with `harbor lint tasks/final/*`—it exits with zero findings.
> Then, our validation engine runs every task through 7 containerized quality gates:
> - G1 Baseline Invalidation: New feature tests fail on untouched base commit.
> - G2 Reference Verification: The reference patch satisfies all feature and regression tests.
> - G3 Diff-Scoped Mutation Testing: Over 15 AST mutations on the modified code lines with over 80% kill rate.
> - G4 Regression Sensitivity: Touched modules detect injected defects.
> - G5 Multi-Run Determinism: 3 fresh runs with zero flakiness."

### Visual Milestone:
- Clean `harbor lint` output followed by green gate passes for all 4 tasks.

---

## Scene 5: Evaluation Harness Proof & Live Dashboard (2:15 - 2:45)

### Terminal Command:
```bash
./bin/taskforge evaluate
./bin/taskforge report
```

### Narration:
> "Finally, we demonstrate the evaluation harness proof.
> An Oracle agent applying `solve.sh` scores a verified `1.0`, while a No-Op agent scores `0.0`.
> TaskForge automatically generates a live HTML report at `report/index.html` displaying provenance badges, AST mutant diffs, and validation receipts.
> TaskForge provides an end-to-end, reproducible, zero-hallucination benchmark pipeline for Harbor."

### Visual Milestone:
- `logs/harness_proof.txt` showing Oracle 1.0 / No-Op 0.0, and the HTML dashboard in `report/index.html`.
