#!/usr/bin/env python3
"""Report keep/discard run dirs for the Table 1/2 sample expansion."""

from __future__ import annotations

import json
from pathlib import Path


CODE_ROOT = Path("/home/zi/AgentCodingDos_CodeAgent")
CLAW_LOGS = Path("/home/zi/agentcodingdos_context_injection_runs/logs")

KEEP = {
    "humaneval_add_s_first20": CODE_ROOT
    / "experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_limit20_20260428",
    "humaneval_add_s_offset20": CODE_ROOT
    / "experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_offset20_limit144_20260827_run2",
    "swe_add_s_first20": CODE_ROOT
    / "experiments/logs/swebench_model_benchmark/qwen36_v10_swebench_limit20_20260428",
    "claw_add_s_orig11_openclaw_kimi": CLAW_LOGS
    / "add_s_v411_openclaw_derivative_planA_kimi_20260428_201953",
    "claw_add_s_orig11_zeroclaw_kimi": CLAW_LOGS
    / "add_s_v411_strongtrigger_planA_zeroclaw_kimi_20260428_161055",
    "claw_add_s_orig11_hermes_kimi_daily_social": CLAW_LOGS
    / "add_s_v411_hermes_derivative_planA_kimi_20260428_201953",
    "claw_add_s_orig11_hermes_kimi_office_dev": CLAW_LOGS
    / "add_s_v411_hermes_derivative_planA_office_dev_resume_kimi_20260429_102317",
    "claw_add_s_new28": CLAW_LOGS / "add_s_plan_a_newtasks_qwen36_20260827_run2",
    "claw_edit_s_openclaw_new28": CLAW_LOGS / "edit_s_openclaw_plan_a_newtasks_qwen36_20260827",
}

DISCARD = {
    "humaneval_add_s_offset20_all_skipped": CODE_ROOT
    / "experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_offset20_limit144_20260827",
    "claw_add_s_new28_openclaw_401": CLAW_LOGS / "add_s_plan_a_newtasks_qwen36_20260827",
}

QUEUED = {
    "kilo_add_s_humaneval_20_97": "qwen36_v10_humaneval_kilo_20_97_20260827",
    "edit_s_humaneval_offset20": "edit_skill_v37_humaneval_offset20_limit144_qwen36_20260827",
    "swe_add_s_offset20": "qwen36_v10_swebench80_offset20_limit60_20260827",
    "swe_edit_s_offset20": "edit_skill_v37_swebench80_offset20_limit60_qwen36_20260827",
}


def _exists(path: Path) -> bool:
    return path.exists()


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def report() -> dict[str, object]:
    payload: dict[str, object] = {"keep": {}, "discard": {}, "queued_run_ids": QUEUED}
    for name, path in KEEP.items():
        payload["keep"][name] = {"path": str(path), "exists": _exists(path)}
        results = path / "results.jsonl"
        if results.exists():
            payload["keep"][name]["results_jsonl"] = _count_jsonl(results)
    for name, path in DISCARD.items():
        payload["discard"][name] = {"path": str(path), "exists": _exists(path), "use": False}
    return payload


def main() -> None:
    print(json.dumps(report(), indent=2))


if __name__ == "__main__":
    main()
