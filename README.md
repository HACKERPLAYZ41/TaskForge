# TaskForge: Autonomous Coding Task Factory

**Innodata Frontier AI Hackathon — Track 1 (Coding Task Factory)**

TaskForge is an automated, repeatable pipeline that inspects an arbitrary software repository and generates realistic, high-fidelity feature development benchmark tasks packaged in the official **Harbor** task format.

Every generated task package includes complete requirements, a canonical reference solution, dual-layer feature and regression tests, starting commit hashes, and rigorous containerized validation evidence across 7 gates.

---

## Quick Start

### 1. Prerequisites
- Linux / Ubuntu (or Docker)
- Python 3.12+ (or `uv`)
- Docker

### 2. Run the Full Demo in One Command
```bash
./bin/taskforge demo
# Or via Makefile:
make demo
```

The demo command executes the entire lifecycle:
1. `taskforge analyze`: Inspects repository AST, modules, and tests.
2. `taskforge generate`: Synthesizes 10 diversified feature tasks across 8 taxonomy categories.
3. `taskforge validate`: Runs 7 validation gates (G1-G7) inside isolated sandboxes.
4. `taskforge evaluate`: Benchmarks task difficulty and model tiers with Harbor.
5. `taskforge report`: Compiles a self-contained static HTML dashboard and CLI summary table.
6. `taskforge rebuild`: Proves bitwise cryptographic reproducibility from seeds.

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `taskforge analyze` | AST-based module/function map, test discovery, and dependency graph |
| `taskforge generate --n 10 --seed 42` | Generates N diverse tasks covering the taxonomy matrix |
| `taskforge validate` | Runs validation gates G1-G7; writes `validation_report.json` |
| `taskforge evaluate` | Evaluates tasks against model tiers using Harbor harness |
| `taskforge report` | Builds HTML dashboard at `report/index.html` and CLI summary |
| `taskforge rebuild` | Regenerates packages and verifies cryptographic hash identity |
| `taskforge demo` | Runs end-to-end pipeline automatically |

---

## Swapping the Target Repository

TaskForge is repo-agnostic. To use your own target repository:
1. Edit `config.yaml`:
   ```yaml
   repo_path: /path/to/your/repository
   language: python
   test_command: pytest -v
   python_version: "3.12"
   seed: 42
   ```
2. Run `taskforge analyze` to verify discovery.
3. Run `taskforge generate --n 10` to generate tasks for your repository.

---

## Harbor Task Layout

Every task follows the Harbor standard format:
```
tasks/final/<task_id>/
  ├── task.toml                  # Harbor v1.4 task configuration & metadata
  ├── instruction.md             # Clean, unambiguous specification
  ├── validation_report.json     # G1-G7 validation evidence
  ├── environment/
  │   ├── Dockerfile             # Container definition for reproducible evaluation
  │   └── repo/                  # Pinned snapshot of target repository
  ├── solution/
  │   └── solve.sh               # Reference solution applying surgical changes
  └── tests/
      ├── test_feature.py        # Behavioral unit tests for the new feature
      └── test.sh                # Verifier script writing reward (1 or 0)
```

---

## Validation Gates (G1 - G7)
- **G1 Baseline**: Feature tests FAIL and regression tests PASS on clean repo.
- **G2 Reference**: Feature and regression tests both PASS after `solve.sh`.
- **G3 Mutation**: Auto-generated AST mutants killed at >= 80% rate.
- **G4 Regression Sensitivity**: Base test suite catches injected mutations.
- **G5 Flakiness**: 3 consecutive fresh runs produce identical outcomes.
- **G6 Spec Alignment**: Test assertions strictly map to stated requirements.
- **G7 Solvability Sanity**: Confirms actionable problem description for AI agents.

---

## Deliverables & Documentation
- Architecture Diagram: `docs/ARCHITECTURE.md`
- Validation Gate Details: `docs/VALIDATION.md`
- HTML Dashboard: `report/index.html`
- Submission Brief: `SUBMISSION_BRIEF.txt`
- Execution Log: `logs/PROGRESS.md`
