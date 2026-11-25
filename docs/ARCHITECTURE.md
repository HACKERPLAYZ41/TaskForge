# TaskForge Architecture

## Overview
TaskForge is an automated, rigorous coding task factory designed for the Innodata Frontier AI Hackathon (Track 1). It takes any working software repository and generates realistic, multi-difficulty feature-development benchmark tasks packaged in the official **Harbor** task format.

Every task includes:
1. Complete behavior-focused `instruction.md` without solution leakage
2. Canonical reference solution applied via `solution/solve.sh`
3. Dual-layer test harness: `tests/test_feature.py` for feature requirements and repo-wide regression verification in `tests/test.sh`
4. Strict containerized verification evidence (`validation_report.json`) across 7 distinct gates (G1 through G7)

---

## System Architecture Diagram

```mermaid
flowchart TD
    Repo["Target Repository (shopcore)"] --> Adapter["RepoAdapter (Python / Polyglot)"]
    Adapter --> Analyzer["AST Codebase Analyzer"]
    
    subgraph Pipeline["TaskForge Core Pipeline"]
        Analyzer --> Proposer["Feature Proposer (Taxonomy x Difficulty)"]
        Proposer --> SpecWriter["Spec Writer (instruction.md)"]
        Proposer --> Solver["Reference Solver (solve.sh)"]
        Proposer --> TestWriter["Test Writer (test_feature.py & test.sh)"]
        SpecWriter --> Packager["Harbor Packager"]
        Solver --> Packager
        TestWriter --> Packager
    end
    
    Packager --> HarborTask["Harbor Task Package (task.toml)"]
    
    subgraph Gates["Validation Gates Engine (G1 - G7)"]
        HarborTask --> G1["G1: Baseline Invalidation"]
        G1 --> G2["G2: Reference Verification"]
        G2 --> G3["G3: AST Mutation Testing (>= 80% kill)"]
        G3 --> G4["G4: Regression Sensitivity"]
        G4 --> G5["G5: Multi-Run Flakiness Check"]
        G5 --> G6["G6: Spec-Test Alignment"]
        G6 --> G7["G7: Agent Solvability Sanity"]
    end
    
    Gates --> ValReport["validation_report.json"]
    ValReport --> PromotedTasks["tasks/final/ (8-10 Diversified Packages)"]
    PromotedTasks --> Eval["Harbor Evaluation Sweep (harbor run)"]
    Eval --> Report["Static HTML & CLI Dashboard"]
```

---

## Core Components

### 1. Repository Adapter (`taskforge.adapters`)
Decouples repository specifics (commit hashing, module indexing, test runner execution) behind an abstract interface (`RepoAdapter`). The included `PythonAdapter` fully discovers AST trees, module dependencies, and test targets.

### 2. AST Codebase Analyzer (`taskforge.analyzer`)
Parses target source files into abstract syntax trees without execution. Extracts class structures, method signatures, parameter names, docstrings, imports, and cross-module dependency links.

### 3. Feature Proposer (`taskforge.proposer`)
Maintains a 3D coverage matrix (`Taxonomy x Difficulty x Module`). Rejects near-duplicates using signature similarity. Ensures meaningful variation across 8 distinct feature classes:
- New endpoint/function
- Validation rule
- Config-driven behavior
- CLI option
- Cross-module change
- Edge-case policy
- Refactor-then-extend
- Error-handling policy

### 4. Spec Writer & Reference Solver (`taskforge.spec_writer`, `taskforge.solver`)
Generates actionable requirements in `instruction.md` detailing public signatures and behavioral specifications without leaking implementation details. Concurrently generates minimal, senior-engineer reference implementations exported as patch scripts in `solution/solve.sh`.

### 5. Harbor Packager (`taskforge.packager`)
Builds standard Harbor task structures conforming to Harbor v1.4 schema, complete with `task.toml`, `environment/Dockerfile`, starting repository version snapshot, and verification runner.
