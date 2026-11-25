"""CLI Entrypoint for TaskForge.
Includes stale process detection, system doctor, Docker validation, and evaluation harness proof.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List

from taskforge.config import TaskForgeConfig
from taskforge.adapters.python_adapter import PythonAdapter
from taskforge.analyzer import CodeAnalyzer
from taskforge.proposer import FeatureProposer
from taskforge.packager import HarborPackager
from taskforge.gates.validator import TaskValidator
from taskforge.evaluator import HarborEvaluator
from taskforge.report import ReportGenerator
from taskforge.rebuilder import TaskRebuilder
from taskforge.llm import LLMClient

def find_stale_pytest_processes() -> List[Dict[str, Any]]:
    """Identifies any lingering pytest or test runner processes from previous runs."""
    stale = []
    try:
        res = subprocess.run(["ps", "-eo", "pid,ppid,args"], capture_output=True, text=True)
        if res.returncode == 0:
            my_pid = str(os.getpid())
            for line in res.stdout.splitlines()[1:]:
                parts = line.strip().split(None, 2)
                if len(parts) >= 3:
                    pid, ppid, cmd = parts[0], parts[1], parts[2]
                    if pid == my_pid:
                        continue
                    if "pytest" in cmd and any(k in cmd for k in ["taskforge", "demo_repo", "shopcore", ".venv", "tests"]):
                        stale.append({"pid": pid, "ppid": ppid, "cmd": cmd})
    except Exception:
        pass
    return stale

def cmd_doctor(args, config: TaskForgeConfig):
    """Diagnoses environment health: stale processes, LLM budget, Docker, disk."""
    print("=" * 80)
    print("                     TASKFORGE SYSTEM DOCTOR                            ")
    print("=" * 80)

    # 1. Stale processes
    stale = find_stale_pytest_processes()
    print("\n[1] Stale Processes Check:")
    if stale:
        print(f"  [!] {len(stale)} STALE pytest process(es) detected:")
        for p in stale:
            print(f"      PID {p['pid']} (PPID {p['ppid']}): {p['cmd'][:85]}")
        pids = " ".join(p['pid'] for p in stale)
        print(f"      Action required: kill -9 {pids}")
    else:
        print("  [OK] No stale pytest/taskforge processes running.")

    # 2. LLM Budget Status
    llm = LLMClient(config=config.raw_config)
    b_stat = llm.get_budget_status()
    print("\n[2] LLM Daily Budget Status:")
    if b_stat.get("exhausted"):
        print("  [EXHAUSTED] OpenRouter free-models-per-day quota limit is EXHAUSTED.")
        print(f"      Reason: {b_stat.get('reason')}")
        print(f"      Recorded: {b_stat.get('date', b_stat.get('timestamp'))}")
        print("      Status: Fast-fail active (0 network requests made; no retry loops).")
    else:
        print(f"  [OK] LLM Provider: {llm.provider_name} (API key configured: {llm.is_available()})")

    # 3. Docker Status
    print("\n[3] Docker Container Engine Status:")
    doc_res = subprocess.run(["docker", "info"], capture_output=True, text=True)
    if doc_res.returncode == 0:
        ps_res = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True)
        running_count = len(ps_res.stdout.strip().splitlines()) if ps_res.stdout.strip() else 0
        print(f"  [OK] Docker daemon is active and responsive.")
        print(f"      Running containers: {running_count}")
    else:
        print(f"  [FAILED] Docker daemon unavailable: {doc_res.stderr.strip()[:100]}")

    # 4. Disk Free
    print("\n[4] Disk Free Space:")
    df_res = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
    if df_res.returncode == 0:
        lines = df_res.stdout.strip().splitlines()
        for l in lines[:2]:
            print(f"      {l}")
    else:
        total, used, free = shutil.disk_usage("/")
        print(f"      Root filesystem: {free // (1024**3)} GB free / {total // (1024**3)} GB total")
    print("\n" + "=" * 80)

def cmd_analyze(args, config: TaskForgeConfig):
    print("=== Running TaskForge Analyzer ===")
    adapter = PythonAdapter(config.repo_path)
    analyzer = CodeAnalyzer(adapter)
    analysis = analyzer.analyze()
    print(f"Repository: {analysis.repo_path}")
    print(f"Commit Hash: {analysis.commit_hash}")
    print(f"Total Lines of Code: {analysis.total_loc}")
    print(f"Modules Discovered ({len(analysis.modules)}):")
    for mod_name, mod in analysis.modules.items():
        print(f"  - {mod_name:<30} ({mod.loc} lines, {len(mod.classes)} classes, {len(mod.functions)} functions)")
    print(f"Test Files ({len(analysis.test_files)}): {', '.join(analysis.test_files)}")

def cmd_generate(args, config: TaskForgeConfig):
    n = getattr(args, "n", 4) or 4
    seed = args.seed if args.seed is not None else config.seed
    offline = getattr(args, "offline", False)
    print(f"=== Generating {n} Tasks for pallets/click (seed={seed}, offline={offline}) ===")

    out_dir = Path.home() / "taskforge" / "tasks" / "final"
    out_dir.mkdir(parents=True, exist_ok=True)
    proposer = FeatureProposer(config_dict=config.raw_config, offline=offline)
    proposals = proposer.propose_tasks(count=n, target_repo_path=config.repo_path, seed=seed)
    packager = HarborPackager(config.repo_path, config_dict=config.raw_config, offline=offline)

    generated = []
    for p in proposals:
        t_dir = packager.package(p, out_dir, config.base_commit)
        print(f"  [+] Packaged: {p.task_id} ({p.feature_type} | {p.difficulty}) -> {t_dir}")
        generated.append(p.task_id)

    print(f"Successfully generated {len(generated)} tasks into {out_dir}")

def cmd_validate(args, config: TaskForgeConfig):
    offline = getattr(args, "offline", False)
    tasks_dir = Path.home() / "taskforge" / "tasks" / "final"
    print(f"=== Validating Tasks in {tasks_dir.name} Across Gates G1 - G7 + H1 (Docker-backed, offline={offline}) ===")

    validator = TaskValidator(use_docker=True, offline=offline, config_dict=config.raw_config)
    valid_count = 0

    for t_dir in sorted(tasks_dir.iterdir()):
        if t_dir.is_dir() and (t_dir / "task.toml").exists():
            print(f"Validating task: {t_dir.name}...")
            report = validator.validate_task(t_dir)
            gates = report["gates"]
            passed_count = sum(1 for g in gates.values() if g.get("passed"))
            print(f"  Outcome: {report['overall_status']} ({passed_count}/{len(gates)} gates passed)")
            if report["overall_status"] == "PASSED":
                valid_count += 1

    print(f"Validation complete: {valid_count} tasks passed all gates in {tasks_dir}")

def cmd_evaluate(args, config: TaskForgeConfig):
    print("=== Evaluating Tasks & Harness Proof ===")
    evaluator = HarborEvaluator(config_dict=config.raw_config)
    
    final_dir = Path.home() / "taskforge" / "tasks" / "final"
    target_task = None
    if final_dir.exists():
        cand = [t for t in sorted(final_dir.iterdir()) if t.is_dir() and (t / "task.toml").exists()]
        if cand:
            target_task = cand[0]

    if target_task:
        print(f"[*] Executing Harness Proof on: {target_task.name}...")
        evaluator.run_harness_proof(target_task)
    else:
        archive_dir = Path.home() / "taskforge" / "archive_offline"
        cand = [t for t in sorted(archive_dir.iterdir()) if t.is_dir() and (t / "task.toml").exists()]
        if cand:
            print(f"[*] Executing Harness Proof from archive: {cand[0].name}...")
            evaluator.run_harness_proof(cand[0])

    if final_dir.exists() and any(final_dir.iterdir()):
        results = evaluator.evaluate_all(final_dir)
        print(f"Evaluated {len(results)} tasks in final:")
        for r in results:
            print(f"  - {r['task_id']:<32}: {r.get('calibrated_difficulty', 'calibrated')} (Pass Rate: {r.get('composite_pass_rate', 0.0):.0%})")

def cmd_report(args, config: TaskForgeConfig):
    print("=== Generating Report and Dashboard ===")
    tasks_data = []
    seen_task_ids = set()

    search_dirs = [
        Path.home() / "taskforge" / "tasks" / "final",
        Path.home() / "taskforge" / "archive_offline",
        Path.home() / "taskforge" / "tasks" / "generated"
    ]

    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for t_dir in sorted(s_dir.iterdir()):
            if t_dir.is_dir() and (t_dir / "task.toml").exists():
                if t_dir.name in seen_task_ids:
                    continue
                seen_task_ids.add(t_dir.name)

                import toml
                toml_data = toml.loads((t_dir / "task.toml").read_text())
                meta = toml_data.get("metadata", {})
                
                val_rep = {}
                if (t_dir / "validation_report.json").exists():
                    try:
                        val_rep = json.loads((t_dir / "validation_report.json").read_text())
                    except Exception:
                        pass

                inst = ""
                if (t_dir / "instruction.md").exists():
                    inst = (t_dir / "instruction.md").read_text()

                mutants = []
                m_file = Path.home() / "taskforge" / "logs" / t_dir.name / "g3_mutants.json"
                if m_file.exists():
                    try:
                        mutants = json.loads(m_file.read_text())
                    except Exception:
                        pass

                target_mods = meta.get("target_modules", [])
                if not target_mods:
                    target_mods = [t_dir.name.split("-")[0]]

                tasks_data.append({
                    "task_id": t_dir.name,
                    "provider": meta.get("provider", "offline"),
                    "model": meta.get("model", ""),
                    "feature_type": meta.get("feature_type", "new endpoint/function"),
                    "difficulty": meta.get("difficulty", "medium"),
                    "target_modules": target_mods,
                    "summary": meta.get("summary", ""),
                    "validation": val_rep,
                    "instruction_md": inst,
                    "mutants": mutants
                })

    # Read proof file
    proof_text = ""
    proof_path = Path.home() / "taskforge" / "logs" / "harness_proof.txt"
    if proof_path.exists():
        proof_text = proof_path.read_text()

    commit_path = config.repo_path / "COMMIT_HASH"
    commit_hash = commit_path.read_text().strip() if commit_path.exists() else "27041ec1b6c6a4e1448c991beb99919beb2f9239"

    gen = ReportGenerator()
    cli_summary = gen.generate_cli_summary(tasks_data)
    print(cli_summary)

    html_path = Path.home() / "taskforge" / "report" / "index.html"
    gen.generate_html_report(tasks_data, html_path, harness_proof_text=proof_text, starting_commit=commit_hash)
    print(f"HTML dashboard generated at: {html_path}")

def cmd_rebuild(args, config: TaskForgeConfig):
    print("=== Rebuilding from Seed & Verifying Reproducibility ===")
    rebuilder = TaskRebuilder(config.repo_path)
    out_dir = Path.home() / "taskforge" / "tasks" / "rebuild_test"
    identical, details = rebuilder.rebuild_and_verify(seed=config.seed, output_dir=out_dir)
    if identical:
        print("REPRODUCIBILITY VERIFIED: Regenerated packages match bitwise 100% across runs!")
    else:
        print("REPRODUCIBILITY FAILED: Discrepancy detected in regenerated packages.")
        sys.exit(1)

def cmd_demo(args, config: TaskForgeConfig):
    print("=========================================================================")
    print("                    STARTING TASKFORGE END-TO-END DEMO                   ")
    print("=========================================================================")
    cmd_doctor(args, config)
    print()
    cmd_analyze(args, config)
    print()
    cmd_generate(args, config)
    print()
    cmd_validate(args, config)
    print()
    cmd_evaluate(args, config)
    print()
    cmd_report(args, config)
    print()
    cmd_rebuild(args, config)
    print("=========================================================================")
    print("               TASKFORGE DEMO PIPELINE COMPLETED SUCCESSFULLY            ")
    print("=========================================================================")

def main():
    parser = argparse.ArgumentParser(description="TaskForge: Harbor Coding Task Factory")
    parser.add_argument("--config", type=str, default=None, help="Path to config.yaml")
    parser.add_argument("--force", action="store_true", help="Bypass stale process safety checks")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("doctor")
    subparsers.add_parser("analyze")

    gen_p = subparsers.add_parser("generate")
    gen_p.add_argument("--n", type=int, default=10, help="Number of tasks to generate")
    gen_p.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    gen_p.add_argument("--offline", action="store_true", help="Use deterministic template catalog without LLM")

    val_p = subparsers.add_parser("validate")
    val_p.add_argument("--offline", action="store_true", help="Use offline heuristics for judge/agent gates")

    eval_p = subparsers.add_parser("evaluate")
    subparsers.add_parser("report")
    subparsers.add_parser("rebuild")

    demo_p = subparsers.add_parser("demo")
    demo_p.add_argument("--offline", action="store_true", help="Run full demo pipeline in offline mode")
    demo_p.add_argument("--n", type=int, default=10, help="Number of tasks to generate")
    demo_p.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    parsed = parser.parse_args()
    if not parsed.command:
        parser.print_help()
        sys.exit(1)

    # Startup safety check: Refuse to launch if stale taskforge pytest processes exist
    if parsed.command != "doctor" and not parsed.force:
        stale = find_stale_pytest_processes()
        if stale:
            print("=" * 80)
            print("[CRITICAL ERROR] STALE TASKFORGE PYTEST PROCESSES DETECTED!")
            print("Refusing to launch to prevent runaway execution / infinite loop hanging.")
            print("Found active processes:")
            for p in stale:
                print(f"  - PID {p['pid']} (PPID {p['ppid']}): {p['cmd'][:85]}")
            pids_str = " ".join(p['pid'] for p in stale)
            print(f"\nPlease kill them before proceeding:\n  kill -9 {pids_str}")
            print("Or pass --force to bypass this check.")
            print("=" * 80)
            sys.exit(1)

    config_path = Path(parsed.config).resolve() if parsed.config else None
    config = TaskForgeConfig.load(config_path)

    dispatch = {
        "doctor": cmd_doctor,
        "analyze": cmd_analyze,
        "generate": cmd_generate,
        "validate": cmd_validate,
        "evaluate": cmd_evaluate,
        "report": cmd_report,
        "rebuild": cmd_rebuild,
        "demo": cmd_demo
    }
    dispatch[parsed.command](parsed, config)

if __name__ == "__main__":
    main()
