#!/usr/bin/env python3
"""Completion audit for the Table 1/2 sample expansion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CODE_ROOT = Path("/home/zi/AgentCodingDos_CodeAgent")
CLAW_ROOT = Path("/home/zi/AgentCodingDos")
CLAW_LOGS = Path("/home/zi/agentcodingdos_context_injection_runs/logs")
NEW_TASK_FILE = CLAW_ROOT / "tasks/claw_plan_a_new_task_ids.txt"

CODING_AGENTS = ("opencode", "kilo_code", "claude_code")
CLAW_AGENTS = ("openclaw", "zeroclaw", "hermes")
CLAW_STRATEGIES = ("add_s", "edit_s", "add_m", "add_c", "edit_m", "edit_c")
KILO_RERUN_HE = set(range(20, 98))

HE_ADD_S_FIRST20 = (
    CODE_ROOT
    / "experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_limit20_20260428/models/openrouter_qwen_qwen3.6-plus/logs"
)
HE_ADD_S_OFFSET20 = (
    CODE_ROOT
    / "experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_offset20_limit144_20260827_run2/models/openrouter_qwen_qwen3.6-plus/logs"
)
HE_ADD_S_KILO_20_97 = (
    CODE_ROOT
    / "experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_kilo_20_97_20260827/models/openrouter_qwen_qwen3.6-plus/logs"
)
HE_EDIT_S_FIRST20 = (
    CODE_ROOT
    / "experiments/logs/edit_skill_evaluation_humaneval/edit_skill_v37_no_seq_humaneval_limit20_20260501/logs"
)
HE_EDIT_S_OFFSET20 = (
    CODE_ROOT
    / "experiments/logs/edit_skill_evaluation_humaneval/edit_skill_v37_humaneval_offset20_limit144_qwen36_20260827/logs"
)
SWE_ADD_S_FIRST20 = (
    CODE_ROOT
    / "experiments/logs/swebench_model_benchmark/qwen36_v10_swebench_limit20_20260428/models/openrouter_qwen_qwen3.6-plus/logs"
)
SWE_ADD_S_OFFSET20 = (
    CODE_ROOT
    / "experiments/logs/swebench_model_benchmark/qwen36_v10_swebench80_offset20_limit60_20260827/models/openrouter_qwen_qwen3.6-plus/logs"
)
SWE_EDIT_S_FIRST20 = {
    "opencode": CODE_ROOT
    / "experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_no_seq_swebench_limit20_20260502_opencode/logs",
    "kilo_code": CODE_ROOT
    / "experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_no_seq_swebench_limit20_20260502_kilo_code/logs",
    "claude_code": CODE_ROOT
    / "experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_no_seq_swebench_limit20_20260502_claude_code/logs",
}
SWE_EDIT_S_OFFSET20 = (
    CODE_ROOT
    / "experiments/logs/edit_skill_evaluation_swebench/edit_skill_v37_swebench80_offset20_limit60_qwen36_20260827/logs"
)
SWEBENCH_80 = (
    CODE_ROOT / "experiments/AgentCallInterface/datasets/swebench_data/swebench_80.json"
)

CLAW_ORIG_DIRS: dict[tuple[str, str], list[Path]] = {
    ("add_s", "openclaw"): [CLAW_LOGS / "add_s_v411_openclaw_derivative_planA_kimi_20260428_201953"],
    ("add_s", "zeroclaw"): [CLAW_LOGS / "add_s_v411_strongtrigger_planA_zeroclaw_kimi_20260428_161055"],
    ("add_s", "hermes"): [
        CLAW_LOGS / "add_s_v411_hermes_derivative_planA_kimi_20260428_201953",
        CLAW_LOGS / "add_s_v411_hermes_derivative_planA_office_dev_resume_kimi_20260429_102317",
    ],
    ("edit_s", "openclaw"): [CLAW_LOGS / "edit_s_openclaw_v30_batch_20260501_000000"],
    ("edit_s", "zeroclaw"): [CLAW_LOGS / "edit_s_zeroclaw_v26_batch_20260430_210043"],
    ("edit_s", "hermes"): [CLAW_LOGS / "edit_s_hermes_v24_batch_20260429_192854"],
    ("add_m", "openclaw"): [CLAW_LOGS / "add_m_openclaw_v13_helper_planA_kimi_20260429_131719"],
    ("add_m", "zeroclaw"): [CLAW_LOGS / "add_m_zeroclaw_v14_planA_kimi_20260430_093916"],
    ("add_m", "hermes"): [CLAW_LOGS / "add_m_hermes_v13_planA_kimi_20260430_093909"],
    ("add_c", "openclaw"): [CLAW_LOGS / "add_c_batch_20260501_190100_openclaw"],
    ("add_c", "zeroclaw"): [CLAW_LOGS / "add_c_batch_20260501_190100_zeroclaw"],
    ("add_c", "hermes"): [CLAW_LOGS / "add_c_batch_20260501_190100_hermes"],
    ("edit_m", "openclaw"): [CLAW_LOGS / "edit_m_openclaw_planA_kimi_v11_20260501"],
    ("edit_m", "zeroclaw"): [CLAW_LOGS / "edit_m_zeroclaw_planA_kimi_v12_workspace_20260501"],
    ("edit_m", "hermes"): [CLAW_LOGS / "edit_m_hermes_planA_kimi_v11_20260501"],
    ("edit_c", "openclaw"): [CLAW_LOGS / "edit_c_batch_20260502_1339_openclaw"],
    ("edit_c", "zeroclaw"): [CLAW_LOGS / "edit_c_batch_20260502_1339_zeroclaw"],
    ("edit_c", "hermes"): [CLAW_LOGS / "edit_c_batch_20260502_1339_hermes"],
}

CLAW_NEW_DIRS: dict[tuple[str, str], list[Path]] = {
    ("add_s", "openclaw"): [CLAW_LOGS / "add_s_plan_a_newtasks_qwen36_20260827_run2"],
    ("add_s", "zeroclaw"): [CLAW_LOGS / "add_s_plan_a_newtasks_qwen36_20260827_run2"],
    ("add_s", "hermes"): [CLAW_LOGS / "add_s_plan_a_newtasks_qwen36_20260827_run2"],
    ("edit_s", "openclaw"): [CLAW_LOGS / "edit_s_openclaw_plan_a_newtasks_qwen36_20260827"],
    ("edit_s", "zeroclaw"): [CLAW_LOGS / "edit_s_zeroclaw_plan_a_newtasks_qwen36_20260827"],
    ("edit_s", "hermes"): [CLAW_LOGS / "edit_s_hermes_plan_a_newtasks_qwen36_20260827"],
    ("add_m", "openclaw"): [CLAW_LOGS / "add_m_openclaw_plan_a_newtasks_qwen36_20260827"],
    ("add_m", "zeroclaw"): [CLAW_LOGS / "add_m_zeroclaw_plan_a_newtasks_qwen36_20260827"],
    ("add_m", "hermes"): [CLAW_LOGS / "add_m_hermes_plan_a_newtasks_qwen36_20260827"],
    ("add_c", "openclaw"): [CLAW_LOGS / "add_c_plan_a_newtasks_qwen36_20260827_openclaw"],
    ("add_c", "zeroclaw"): [CLAW_LOGS / "add_c_plan_a_newtasks_qwen36_20260827_zeroclaw"],
    ("add_c", "hermes"): [CLAW_LOGS / "add_c_plan_a_newtasks_qwen36_20260827_hermes"],
    ("edit_m", "openclaw"): [CLAW_LOGS / "edit_m_openclaw_plan_a_newtasks_qwen36_20260827"],
    ("edit_m", "zeroclaw"): [CLAW_LOGS / "edit_m_zeroclaw_plan_a_newtasks_qwen36_20260827"],
    ("edit_m", "hermes"): [CLAW_LOGS / "edit_m_hermes_plan_a_newtasks_qwen36_20260827"],
    ("edit_c", "openclaw"): [CLAW_LOGS / "edit_c_plan_a_newtasks_qwen36_20260827_openclaw"],
    ("edit_c", "zeroclaw"): [CLAW_LOGS / "edit_c_plan_a_newtasks_qwen36_20260827_zeroclaw"],
    ("edit_c", "hermes"): [CLAW_LOGS / "edit_c_plan_a_newtasks_qwen36_20260827_hermes"],
}


def load_new_task_ids(path: Path = NEW_TASK_FILE) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def load_orig_task_ids() -> list[str]:
    path = CLAW_ORIG_DIRS[("add_s", "openclaw")][0] / "results.jsonl"
    ids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.append(json.loads(line)["task_id"])
    return ids


def load_swebench_ids() -> list[str]:
    rows = json.loads(SWEBENCH_80.read_text(encoding="utf-8"))
    return [row["instance_id"] for row in rows]


def humaneval_ids() -> list[str]:
    return [f"HumanEval/{i}" for i in range(164)]


def expected_counts() -> dict[str, int]:
    return {
        "humaneval_add_s": 164 * 3,
        "humaneval_edit_s": 164 * 3,
        "swebench_add_s": 80 * 3,
        "swebench_edit_s": 80 * 3,
        "claw_orig_11": 44 * 3 * 6,
        "claw_new_28": 28 * 3 * 6,
    }


def classify_coding_stdout(text: str) -> str:
    if "HTTP 401" in text or "User not found" in text:
        return "invalid_401"
    if len(text.strip()) < 200:
        return "invalid_empty"
    return "ok"


def _latest_output(log_dir: Path, task_token: str, agent: str) -> Path | None:
    needle = f"{task_token}_{agent}_"
    matches = [
        path
        for path in log_dir.glob("*_output.txt")
        if needle in path.name
    ]
    return sorted(matches)[-1] if matches else None


def _metrics_for_output(output: Path) -> Path | None:
    stem = output.name[: -len("_output.txt")]
    candidate = output.with_name(f"{stem}_metrics.json")
    if candidate.exists():
        return candidate
    alt = list(output.parent.glob(f"{stem}*_metrics.json"))
    return alt[-1] if alt else None


def coding_cell_status(log_dirs: list[Path], task_token: str, agent: str) -> str:
    for log_dir in log_dirs:
        if not log_dir.exists():
            continue
        output = _latest_output(log_dir, task_token, agent)
        if output is None:
            continue
        text = output.read_text(encoding="utf-8", errors="replace")
        status = classify_coding_stdout(text)
        if status != "ok":
            return status
        if _metrics_for_output(output) is None:
            return "present_no_asr"
        return "valid"
    return "missing"


def _jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def claw_stdout_text(log_dir: Path, agent: str, task_id: str) -> str | None:
    root = log_dir / agent / task_id / "poisoned"
    if not root.exists():
        return None
    chunks: list[str] = []
    found = False
    for name in ("stdout.txt", "stdout.json", "stderr.txt"):
        path = root / name
        if path.exists():
            found = True
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    if not found:
        return None
    return "\n".join(chunks)


def claw_trace_is_empty(text: str | None) -> bool:
    if text is None:
        return True
    if '"payloads"' in text:
        return False
    if "[runner]" in text and "timed out" in text:
        return True
    if "All providers/models failed" in text:
        return True
    return not text.strip()


def claw_stdout_401(log_dir: Path, agent: str, task_id: str) -> bool:
    text = claw_stdout_text(log_dir, agent, task_id)
    if not text:
        return False
    return "HTTP 401" in text or "User not found" in text


def claw_cell_status(
    log_dirs: list[Path],
    agent: str,
    task_id: str,
    *,
    require_nonempty_stdout: bool = False,
) -> str:
    for log_dir in log_dirs:
        results = {
            row.get("task_id"): row
            for row in _jsonl_rows(log_dir / "results.jsonl")
            if row.get("agent") == agent
        }
        calling = {
            row.get("task_id"): row
            for row in _jsonl_rows(log_dir / "calling_results.jsonl")
            if row.get("agent") == agent
        }
        if task_id not in results:
            continue
        text = claw_stdout_text(log_dir, agent, task_id)
        if require_nonempty_stdout and claw_trace_is_empty(text):
            return "invalid_empty"
        if require_nonempty_stdout and results[task_id].get("caller_success") is False:
            return "invalid_empty"
        if text and ("HTTP 401" in text or "User not found" in text):
            return "invalid_401"
        if task_id not in calling:
            return "present_no_asr"
        if "injection_observed" not in results[task_id] and "skill_started" not in calling[task_id]:
            return "present_no_asr"
        return "valid"
    return "missing"


def _bucket() -> dict[str, int]:
    return {"valid": 0, "missing": 0, "invalid_401": 0, "invalid_empty": 0, "present_no_asr": 0}


def _count(status: str, bucket: dict[str, int]) -> None:
    bucket[status] = bucket.get(status, 0) + 1


def humaneval_add_s_coverage() -> dict[str, int]:
    bucket = _bucket()
    for i in range(164):
        token = f"HumanEval_{i}"
        for agent in CODING_AGENTS:
            if agent == "kilo_code" and i in KILO_RERUN_HE:
                dirs = [HE_ADD_S_KILO_20_97]
            else:
                dirs = [HE_ADD_S_FIRST20, HE_ADD_S_OFFSET20]
            _count(coding_cell_status(dirs, token, agent), bucket)
    return bucket


def humaneval_edit_s_coverage() -> dict[str, int]:
    bucket = _bucket()
    for i in range(164):
        token = f"HumanEval_{i}"
        for agent in CODING_AGENTS:
            _count(
                coding_cell_status([HE_EDIT_S_FIRST20, HE_EDIT_S_OFFSET20], token, agent),
                bucket,
            )
    return bucket


def swe_add_s_coverage() -> dict[str, int]:
    bucket = _bucket()
    for instance_id in load_swebench_ids():
        for agent in CODING_AGENTS:
            _count(
                coding_cell_status([SWE_ADD_S_FIRST20, SWE_ADD_S_OFFSET20], instance_id, agent),
                bucket,
            )
    return bucket


def swe_edit_s_coverage() -> dict[str, int]:
    bucket = _bucket()
    for instance_id in load_swebench_ids():
        for agent in CODING_AGENTS:
            dirs = [SWE_EDIT_S_FIRST20[agent], SWE_EDIT_S_OFFSET20]
            _count(coding_cell_status(dirs, instance_id, agent), bucket)
    return bucket


def claw_coverage(kind: str) -> dict[str, int]:
    bucket = _bucket()
    task_ids = load_orig_task_ids() if kind == "orig" else load_new_task_ids()
    mapping = CLAW_ORIG_DIRS if kind == "orig" else CLAW_NEW_DIRS
    for strategy in CLAW_STRATEGIES:
        for agent in CLAW_AGENTS:
            for task_id in task_ids:
                status = claw_cell_status(
                    mapping[(strategy, agent)],
                    agent,
                    task_id,
                    require_nonempty_stdout=(kind == "new"),
                )
                _count(status, bucket)
    return bucket


def report() -> dict[str, Any]:
    sections = {
        "humaneval_add_s": humaneval_add_s_coverage(),
        "humaneval_edit_s": humaneval_edit_s_coverage(),
        "swebench_add_s": swe_add_s_coverage(),
        "swebench_edit_s": swe_edit_s_coverage(),
        "claw_orig_11": claw_coverage("orig"),
        "claw_new_28": claw_coverage("new"),
    }
    expected = expected_counts()
    complete = True
    for name, bucket in sections.items():
        if bucket["valid"] != expected[name]:
            complete = False
        if bucket["valid"] + bucket["missing"] + bucket["invalid_401"] + bucket[
            "invalid_empty"
        ] + bucket["present_no_asr"] != expected[name]:
            complete = False
    return {"expected": expected, "sections": sections, "complete": complete}


def main() -> None:
    print(json.dumps(report(), indent=2))


if __name__ == "__main__":
    main()
