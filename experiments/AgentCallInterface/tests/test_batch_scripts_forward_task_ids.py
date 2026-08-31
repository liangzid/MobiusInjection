from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = PROJECT_ROOT / "experiments/scripts"
ADD_C = SCRIPTS / "effectiveness_injection_claw_0.2.7.context_injection_add_c_batch.sh"
EDIT_C = SCRIPTS / "effectiveness_injection_claw_0.2.8.context_injection_edit_c_batch.sh"


def _assert_forwards_task_ids(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "TASK_IDS=" in text
    assert "TASK_ID_ARGS" in text
    assert "--task-ids" in text
    assert '"${TASK_ID_ARGS[@]}"' in text


def test_add_c_batch_forwards_task_ids() -> None:
    _assert_forwards_task_ids(ADD_C)


def test_edit_c_batch_forwards_task_ids() -> None:
    _assert_forwards_task_ids(EDIT_C)


def test_remaining_strategies_skips_duplicate_edit_s() -> None:
    text = (SCRIPTS / "run_plan_a_newtasks_remaining_strategies.sh").read_text(encoding="utf-8")
    assert "pending_claw_task_ids.py" in text
    assert "wait_until_prefix_idle" in text
    assert "already complete without 401" in text
    assert "run_python_agent_for_run" in text
    assert "run_c_batch" in text
    assert "not starting remaining strategies" not in text


def test_remaining_strategies_c_batch_checks_per_agent_run_ids() -> None:
    text = (SCRIPTS / "run_plan_a_newtasks_remaining_strategies.sh").read_text(encoding="utf-8")
    assert 'skip_if_complete "${run_id}_${agent}"' in text
    assert 'AGENTS="$agent"' in text
    assert 'AGENTS="openclaw zeroclaw hermes"' not in text


def test_zeroclaw_watchdog_requires_pid_column_and_skips_top_failure() -> None:
    text = (SCRIPTS / "watchdog_zeroclaw_provider_fail.sh").read_text(encoding="utf-8")
    assert '"pid,comm"' in text
    assert '"-eo", "comm"' not in text
    assert "return None" in text
    assert "if procs is None:" in text
    assert "mtime < started" in text


def test_remaining_empty_backfill_retries_pending_rounds() -> None:
    text = (SCRIPTS / "backfill_zeroclaw_remaining_empty.sh").read_text(encoding="utf-8")
    assert "MAX_ROUNDS" in text
    assert "remaining-empty round" in text
    assert "no pending ZeroClaw cells" in text

