#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OPENCLAW_BASE_RUNNER = PROJECT_ROOT / "experiments/scripts/effectiveness_injection_claw_0.2.5.context_injection_add_m_openclaw.py"
CLAW_BASE_RUNNER = PROJECT_ROOT / "experiments/scripts/effectiveness_injection_claw_0.2.5.context_injection_add_m_claw_agents.py"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load runner module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


openclaw_base = load_module(OPENCLAW_BASE_RUNNER, "add_m_openclaw_runner")
claw_base = load_module(CLAW_BASE_RUNNER, "add_m_claw_agents_runner")


def image_for_agent(args: argparse.Namespace) -> str:
    if args.agent == "openclaw":
        return args.openclaw_image
    if args.agent == "hermes":
        return args.hermes_image
    return args.zeroclaw_image


def base_for_agent(agent: str) -> Any:
    return openclaw_base if agent == "openclaw" else claw_base


def agent_turn(
    *,
    agent: str,
    base: Any,
    container: str,
    prompt: str,
    model: str,
    timeout_seconds: int,
    stdout_file: Path,
    stderr_file: Path,
    api_key: str,
    session_id: str,
) -> int:
    if agent == "openclaw":
        return base.openclaw_agent_turn(
            container=container,
            prompt=prompt,
            model=model,
            timeout_seconds=timeout_seconds,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
            api_key=api_key,
            session_id=session_id,
        )
    return base.run_agent_turn(
        agent=agent,
        container=container,
        prompt=prompt,
        model=model,
        timeout_seconds=timeout_seconds,
        stdout_file=stdout_file,
        stderr_file=stderr_file,
        api_key=api_key,
    )


def run_one(selection: Any, args: argparse.Namespace, paths: dict[str, Path], api_key: str) -> dict[str, Any]:
    base = base_for_agent(args.agent)
    task_slug = base.sanitize(selection.task_id)
    container = f"clean_{base.sanitize(args.run_id)}_{args.agent}_{task_slug}"
    variant_root = paths["staging"] / selection.task_id / "clean" / args.agent
    log_dir = paths["logs"] / args.agent / selection.task_id / "clean"
    export_workspace = paths["exports"] / args.agent / selection.task_id / "clean" / "workspace"
    verify_dir = paths["verifiers"] / args.agent / selection.task_id / "clean"
    container_workspace = f"/tmp/task_runs/session/{args.agent}/{selection.task_id}/clean/workspace"
    stdout_name = "stdout.json" if args.agent == "openclaw" else "stdout.txt"
    log_dir.mkdir(parents=True, exist_ok=True)

    base.build_clean_workspace(selection, variant_root)
    base.start_container(container, image_for_agent(args))
    try:
        base.copy_workspace_to_container(container, variant_root / "workspace", container_workspace)
        prompt = base.prompt_for_task(selection, variant_root, container_workspace)
        (log_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        caller_rc = agent_turn(
            agent=args.agent,
            base=base,
            container=container,
            prompt=prompt,
            model=args.model,
            timeout_seconds=args.timeout,
            stdout_file=log_dir / stdout_name,
            stderr_file=log_dir / "stderr.txt",
            api_key=api_key,
            session_id=f"{args.run_id}-{selection.task_id}-clean",
        )
        base.copy_workspace_from_container(container, container_workspace, export_workspace)
        verifier_rc = base.run_verifier(selection, export_workspace, verify_dir)
        return {
            "agent": args.agent,
            "category": selection.category,
            "category_label": selection.label,
            "task_id": selection.task_id,
            "variant": "clean",
            "caller_returncode": caller_rc,
            "caller_success": caller_rc == 0,
            "verifier_returncode": verifier_rc,
            "verifier_passed": verifier_rc == 0,
            "image": image_for_agent(args),
            "log_dir": str(log_dir),
        }
    finally:
        if not args.keep_containers:
            base.run(["docker", "rm", "-f", container])


def rate(num: int, den: int) -> float | None:
    return None if den == 0 else num / den


def summarize_bucket(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "runs": len(rows),
        "caller_successes": sum(1 for row in rows if row["caller_success"]),
        "task_successes": sum(1 for row in rows if row["verifier_passed"]),
        "caller_success_rate": rate(sum(1 for row in rows if row["caller_success"]), len(rows)),
        "tsr": rate(sum(1 for row in rows if row["verifier_passed"]), len(rows)),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    categories = sorted({row["category"] for row in rows})
    return {
        "overall": summarize_bucket(rows),
        "categories": {
            category: summarize_bucket([row for row in rows if row["category"] == category])
            for category in categories
        },
    }


def fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def render_summary(summary: dict[str, Any], agent: str) -> str:
    lines = [
        f"# Clean {agent} ClawBench TSR Baseline",
        "",
        "| category | TSR | caller success | task successes | runs |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for category, bucket in [("overall", summary["overall"]), *summary["categories"].items()]:
        lines.append(
            f"| {category} | {fmt(bucket['tsr'])} | {fmt(bucket['caller_success_rate'])} | "
            f"{bucket['task_successes']} | {bucket['runs']} |"
        )
    return "\n".join(lines) + "\n"


def select_tasks(args: argparse.Namespace) -> list[Any]:
    selections = openclaw_base.select_tasks(args)
    if not selections:
        raise ValueError("No tasks selected")
    return selections


def write_manifest(args: argparse.Namespace, paths: dict[str, Path], selections: list[Any]) -> None:
    manifest = {
        "run_id": args.run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent": args.agent,
        "experiment": "clean_clawbench_tsr_baseline",
        "model": args.model,
        "taskset": str(args.taskset),
        "tasks": [selection.task_id for selection in selections],
        "timeout_seconds": args.timeout,
        "image": image_for_agent(args),
    }
    (paths["logs"] / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["openclaw", "hermes", "zeroclaw"], required=True)
    parser.add_argument("--run-id", default=f"clean_claw_tsr_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    parser.add_argument("--run-root", type=Path, default=Path("/home/zi/agentcodingdos_context_injection_runs"))
    parser.add_argument("--taskset", type=Path, default=PROJECT_ROOT / "experiments/configs/context_injection_add_s_taskset_plan_a.toml")
    parser.add_argument("--categories", nargs="*", default=None)
    parser.add_argument("--task-ids", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", default="moonshotai/kimi-k2.6")
    parser.add_argument("--openclaw-image", default="openclaw:edit_m_mcp_victim")
    parser.add_argument("--hermes-image", default="hermes:edit_m_mcp_victim")
    parser.add_argument("--zeroclaw-image", default="zeroclaw:edit_m_mcp_workspace_victim")
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--keep-containers", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = openclaw_base.read_openrouter_key()
    paths = {
        "staging": args.run_root / "staging" / args.run_id,
        "logs": args.run_root / "logs" / args.run_id,
        "exports": args.run_root / "container_exports" / args.run_id,
        "verifiers": args.run_root / "verifier_results" / args.run_id,
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    selections = select_tasks(args)
    write_manifest(args, paths, selections)
    results: list[dict[str, Any]] = []
    for index, selection in enumerate(selections, start=1):
        print(
            f"[{datetime.now().isoformat(timespec='seconds')}] CLEAN {args.agent} {index}/{len(selections)} "
            f"{selection.category}/{selection.task_id}",
            flush=True,
        )
        result_payload = run_one(selection, args, paths, api_key)
        results.append(result_payload)
        openclaw_base.write_jsonl(paths["logs"] / "results.jsonl", result_payload)
        summary = summarize(results)
        (paths["logs"] / "batch_metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (paths["logs"] / "batch_metrics.md").write_text(render_summary(summary, args.agent), encoding="utf-8")
    print(f"Done: {paths['logs']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
