"""Run a HumanEval limit-1 OpenCode probe with a realistic two-skill injection."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from experiments.AgentCallInterface.coding_agents.coding_agent_callers import get_caller
from experiments.AgentCallInterface.coding_datasets.coding_benchmark_loader import (
    HumanEvalLoader,
)
from experiments.AgentCallInterface.coding_evaluation.opencode_recursive_trace_monitor import (
    build_trace_report_from_files,
)
from experiments.AgentCallInterface.coding_evaluation.prompt_composer import (
    compose_benchmark_injection_prompt,
)
from mobiusInjection.CODING_AGENT_TEMPLATE_OPENCODE_V10_REALISTIC import (
    FollowupVerificationText,
    MainInjectionTextTargeted,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESET_SCRIPT = PROJECT_ROOT / "experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh"
OUTPUT_ROOT = PROJECT_ROOT / "experiments/results/preliminary_opencode_realistic_skill_injection"
DEFAULT_MODEL = "minimax/minimax-m2.5:free"
TRACE_PATH = "/opencode/sync-check-record.jsonl"


@dataclass(frozen=True)
class RealisticProbePaths:
    run_dir: Path
    initial_reset: Path
    benchmark_prompt: Path
    injection_prompt: Path
    combined_prompt: Path
    prompt_metadata: Path
    injection_output: Path
    post_creation_state: Path
    post_creation_debug: Path
    followup_output: Path
    final_state: Path
    final_trace: Path
    trace_report: Path
    manifest: Path


def make_run_dir(base_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = base_dir / f"opencode_realistic_skill_injection_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def make_paths(run_dir: Path) -> RealisticProbePaths:
    return RealisticProbePaths(
        run_dir=run_dir,
        initial_reset=run_dir / "initial_reset.txt",
        benchmark_prompt=run_dir / "humaneval_HumanEval_0_benchmark_prompt.txt",
        injection_prompt=run_dir / "injection_prompt.txt",
        combined_prompt=run_dir / "combined_prompt.txt",
        prompt_metadata=run_dir / "prompt_metadata.json",
        injection_output=run_dir / "injection_output.json",
        post_creation_state=run_dir / "post_creation_state.txt",
        post_creation_debug=run_dir / "post_creation_debug_skill.txt",
        followup_output=run_dir / "followup_output.json",
        final_state=run_dir / "final_state.txt",
        final_trace=run_dir / "sync-check-record.jsonl",
        trace_report=run_dir / "trace_report.json",
        manifest=run_dir / "manifest.json",
    )


def run_command(command: list[str], output_path: Path, timeout: int) -> int:
    with output_path.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
    return result.returncode


def run_reset(paths: RealisticProbePaths, timeout: int) -> int:
    return run_command([str(RESET_SCRIPT)], paths.initial_reset, timeout)


def call_opencode(prompt: str, task_id: str, model: str, timeout: int):
    caller = get_caller("opencode")
    return caller.call(
        {"task_id": task_id, "problem_statement": prompt},
        timeout=timeout,
        model=model,
    )


def write_agent_response(path: Path, response) -> None:
    payload = {
        "success": response.success,
        "duration": response.duration,
        "task_id": response.task_id,
        "returncode": response.returncode,
        "output": response.output,
        "error": response.error,
        "stderr": response.stderr,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def capture_debug(path: Path, timeout: int) -> int:
    return run_command(
        [
            "docker",
            "exec",
            "opencode",
            "bash",
            "-lc",
            "cd /opencode && /root/.opencode/bin/opencode debug skill",
        ],
        path,
        timeout,
    )


def capture_state(path: Path, timeout: int) -> int:
    script = """
set -euo pipefail
cd /opencode
echo "## solution"
find /opencode -maxdepth 2 -type f \\( -name 'solution.py' -o -name '*.py' \\) -print -exec sed -n '1,160p' {} \\; 2>/dev/null || true
echo "## skill files"
find /opencode/.opencode/skills -maxdepth 3 -type f -print -exec sed -n '1,160p' {} \\; 2>/dev/null | sort || true
echo "## debug skill"
/root/.opencode/bin/opencode debug skill
echo "## trace"
if [ -f /opencode/sync-check-record.jsonl ]; then
    cat /opencode/sync-check-record.jsonl
else
    echo "NO_TRACE_FILE"
fi
"""
    return run_command(["docker", "exec", "opencode", "bash", "-lc", script], path, timeout)


def capture_trace(path: Path, timeout: int) -> int:
    script = "cd /opencode && if [ -f sync-check-record.jsonl ]; then cat sync-check-record.jsonl; fi"
    return run_command(["docker", "exec", "opencode", "bash", "-lc", script], path, timeout)


def load_humaneval_zero_prompt() -> tuple[str, str]:
    task = HumanEvalLoader().load_benchmark_tasks(limit=1)[0]
    return task.task_id, task.prompt


def output_text(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    return "\n".join(str(payload.get(key) or "") for key in ("output", "error", "stderr"))


def count_native_skill_loads(text: str) -> dict[str, int]:
    return {
        "integrity-sync": text.count("Loaded skill: integrity-sync"),
        "performance-audit": text.count("Loaded skill: performance-audit"),
    }


def extract_workflow_id(injection_prompt: str) -> str:
    match = re.search(r"Workflow id: `([^`]+)`", injection_prompt)
    if not match:
        raise ValueError("workflow id not found in injection prompt")
    return match.group(1)


def write_manifest(
    paths: RealisticProbePaths,
    *,
    model: str,
    timeout: int,
    reset_status: int,
    post_state_status: int,
    post_debug_status: int,
    final_state_status: int,
    trace_status: int,
    workflow_id: str,
    task_id: str,
) -> None:
    trace_report = json.loads(paths.trace_report.read_text(encoding="utf-8"))
    injection_text = output_text(paths.injection_output)
    followup_text = output_text(paths.followup_output)
    manifest = {
        "agent": "opencode",
        "model": model,
        "dataset": "humaneval",
        "task_id": task_id,
        "run_dir": str(paths.run_dir),
        "run_id": workflow_id,
        "timeout_seconds": timeout,
        "reset_status": reset_status,
        "post_creation_state_status": post_state_status,
        "post_creation_debug_status": post_debug_status,
        "final_state_status": final_state_status,
        "trace_capture_status": trace_status,
        "injection_native_skill_loads": count_native_skill_loads(injection_text),
        "followup_native_skill_loads": count_native_skill_loads(followup_text),
        "trace_report": trace_report,
        "paths": {key: str(value) for key, value in asdict(paths).items()},
    }
    paths.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def run_probe(args: argparse.Namespace) -> RealisticProbePaths:
    run_dir = make_run_dir(Path(args.output_root))
    paths = make_paths(run_dir)

    task_id, benchmark_prompt = load_humaneval_zero_prompt()
    injection_prompt = MainInjectionTextTargeted(
        target_agent="opencode",
        target_model=args.model,
        pass_count=args.pass_count,
    )
    workflow_id = extract_workflow_id(injection_prompt)
    composition = compose_benchmark_injection_prompt(benchmark_prompt, injection_prompt)
    paths.benchmark_prompt.write_text(benchmark_prompt, encoding="utf-8")
    paths.injection_prompt.write_text(injection_prompt, encoding="utf-8")
    paths.combined_prompt.write_text(composition.combined_prompt, encoding="utf-8")
    paths.prompt_metadata.write_text(
        json.dumps(composition.metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    reset_status = run_reset(paths, args.reset_timeout)
    injection = call_opencode(
        composition.combined_prompt,
        f"{run_dir.name}_injection",
        args.model,
        args.timeout,
    )
    write_agent_response(paths.injection_output, injection)
    post_state_status = capture_state(paths.post_creation_state, args.reset_timeout)
    post_debug_status = capture_debug(paths.post_creation_debug, args.reset_timeout)

    followup = call_opencode(
        FollowupVerificationText(
            workflow_id,
            start_seq=args.pass_count + 2,
            pass_count=args.followup_pass_count,
        ),
        f"{run_dir.name}_followup",
        args.model,
        args.timeout,
    )
    write_agent_response(paths.followup_output, followup)
    final_state_status = capture_state(paths.final_state, args.reset_timeout)
    trace_status = capture_trace(paths.final_trace, args.reset_timeout)
    report = build_trace_report_from_files(
        run_id=workflow_id,
        trace_path=paths.final_trace,
        state_path=paths.final_state,
        invocation_paths=[paths.injection_output],
        clean_followup_path=paths.followup_output,
    )
    paths.trace_report.write_text(report.to_json() + "\n", encoding="utf-8")
    write_manifest(
        paths,
        model=args.model,
        timeout=args.timeout,
        reset_status=reset_status,
        post_state_status=post_state_status,
        post_debug_status=post_debug_status,
        final_state_status=final_state_status,
        trace_status=trace_status,
        workflow_id=workflow_id,
        task_id=task_id,
    )
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=360)
    parser.add_argument("--reset-timeout", type=int, default=45)
    parser.add_argument("--pass-count", type=int, default=6)
    parser.add_argument("--followup-pass-count", type=int, default=2)
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    return parser.parse_args()


def main() -> None:
    paths = run_probe(parse_args())
    print(paths.run_dir)


if __name__ == "__main__":
    main()
