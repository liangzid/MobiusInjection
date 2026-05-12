"""Run one clean follow-up task against already-installed edit-skill artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.AgentCallInterface.coding_agents.coding_agent_callers import get_caller
from experiments.AgentCallInterface.coding_evaluation.edit_skill_evaluation_monitor import (
    AUXILIARY_SKILL,
    BASELINE_SKILL,
    LEDGER_NAME,
    build_report_from_files,
    update_metrics_file,
)
from experiments.AgentCallInterface.coding_evaluation.edit_skill_evaluation_runner import (
    CasePaths,
    capture_state,
    case_paths,
    main_run_id,
    read_clean_followup_prompt,
    response_metrics,
    utc_now,
    write_json,
    write_response,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--benchmark-id", required=True)
    parser.add_argument("--dataset", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--task-prompt-file", required=True)
    parser.add_argument("--prompt-order", default="task_before_injection")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--followup-timeout", type=int, default=120)
    parser.add_argument("--baseline-skill", default=BASELINE_SKILL)
    parser.add_argument("--auxiliary-skill", default=AUXILIARY_SKILL)
    parser.add_argument("--ledger-name", default=LEDGER_NAME)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = case_paths(Path(args.log_dir), args.benchmark_id, args.agent)
    paths.output_file.parent.mkdir(parents=True, exist_ok=True)
    write_json(paths.metrics_file, initial_metrics(args, paths))

    state_files: list[Path] = []
    capture_state(args, paths, "post_injection_baseline", state_files)
    write_baseline_output(paths.output_file)

    followup_prompt = write_followup_prompt(args, paths)
    response = call_clean_task(args, followup_prompt)
    write_response(paths.followup_file, "FOLLOWUP", response)
    update_phase(paths.metrics_file, "followup", response_metrics(response))

    capture_state(args, paths, "post_followup", state_files)
    analyze(paths, state_files, args)


def initial_metrics(args: argparse.Namespace, paths: CasePaths) -> dict[str, Any]:
    return {
        "eval_id": args.benchmark_id,
        "agent": args.agent,
        "model": args.model,
        "template_module": "followup_only",
        "baseline_skill": args.baseline_skill,
        "auxiliary_skill": args.auxiliary_skill,
        "ledger_name": args.ledger_name,
        "benchmark": {
            "dataset": args.dataset,
            "task_id": args.task_id,
            "prompt_order": args.prompt_order,
        },
        "files": {key: str(value) for key, value in paths.__dict__.items()},
        "phases": {},
        "indicators": {},
        "counters": {},
        "timestamps": {"start": utc_now()},
        "mode": "followup_only",
    }


def write_baseline_output(path: Path) -> None:
    path.write_text(
        "===RESPONSE_START===\n"
        "Success: True\n"
        "Duration: 0.00s\n"
        "Returncode: 0\n"
        "---Output---\n"
        "Follow-up-only run: baseline state captured before clean task.\n"
        "===RESPONSE_END===\n",
        encoding="utf-8",
    )


def write_followup_prompt(args: argparse.Namespace, paths: CasePaths) -> Path:
    followup_prompt = paths.state_prefix.with_name(
        f"{paths.state_prefix.name}_followup_prompt.txt"
    )
    followup_prompt.write_text(read_clean_followup_prompt(args) + "\n", encoding="utf-8")
    return followup_prompt


def call_clean_task(args: argparse.Namespace, prompt_file: Path) -> Any:
    caller = get_caller(args.agent)
    return caller.call(
        {
            "task_id": f"{main_run_id(args)}_followup_only",
            "run_id": main_run_id(args),
            "problem_statement": prompt_file.read_text(encoding="utf-8"),
        },
        timeout=args.followup_timeout,
        model=args.model,
    )


def update_phase(metrics_file: Path, phase: str, payload: dict[str, Any]) -> None:
    metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
    metrics.setdefault("phases", {})[phase] = payload
    metrics.setdefault("timestamps", {})[f"{phase}_end"] = utc_now()
    metrics_file.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")


def analyze(paths: CasePaths, state_files: list[Path], args: argparse.Namespace) -> None:
    report = build_report_from_files(
        paths.output_file,
        paths.followup_file,
        state_files,
        baseline_skill=args.baseline_skill,
        auxiliary_skill=args.auxiliary_skill,
    )
    paths.analysis_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    update_metrics_file(paths.metrics_file, report)


if __name__ == "__main__":
    main()
