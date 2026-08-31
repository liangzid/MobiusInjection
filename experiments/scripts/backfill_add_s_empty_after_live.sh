#!/usr/bin/env bash
# After live ADD S. run2 ZeroClaw/Hermes PIDs exit, rerun empty/401 cells
# for those agents only (OpenClaw ADD S. is already 28/28).
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/zi/AgentCodingDos}"
RUN_ID="${RUN_ID:-add_s_plan_a_newtasks_qwen36_20260827_run2}"
RUN_ROOT="${RUN_ROOT:-/home/zi/agentcodingdos_context_injection_runs}"
TASK_ID_FILE="${TASK_ID_FILE:-$PROJECT_ROOT/tasks/claw_plan_a_new_task_ids.txt}"
TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml}"
MODEL_NAME="${MODEL_NAME:-qwen/qwen3.6-plus}"
ZEROCLAW_PID="${ZEROCLAW_PID:-1292370}"
HERMES_PID="${HERMES_PID:-1289230}"
LOG_DIR="$RUN_ROOT/logs/$RUN_ID"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

wait_pid() {
    local pid="$1" name="$2"
    if [[ -z "$pid" ]]; then
        return 0
    fi
    log "Waiting for live ADD S. $name pid $pid"
    while kill -0 "$pid" 2>/dev/null; do
        sleep 20
    done
    log "Live ADD S. $name pid $pid exited"
}

pending_for_agent() {
    local agent="$1"
    python3 - "$LOG_DIR" "$TASK_ID_FILE" "$agent" <<'PY'
from pathlib import Path
import json
import sys
log = Path(sys.argv[1])
ids = [
    line.strip()
    for line in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.startswith("#")
]
agent = sys.argv[3]

def trace_text(tid: str) -> str:
    root = log / agent / tid / "poisoned"
    chunks = []
    for name in ("stdout.txt", "stdout.json", "stderr.txt"):
        path = root / name
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)

def is_empty(text: str) -> bool:
    if '"payloads"' in text:
        return False
    if "[runner]" in text and "timed out" in text:
        return True
    if "All providers/models failed" in text:
        return True
    return not text.strip()

pending = []
for tid in ids:
    text = trace_text(tid)
    if is_empty(text) or ("HTTP 401" in text) or ("User not found" in text):
        pending.append(tid)
        continue
    # Last jsonl row for this agent with caller_success false is not a keep.
    results = log / "results.jsonl"
    last_ok = None
    if results.exists():
        for line in results.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("agent") == agent and row.get("task_id") == tid:
                last_ok = row.get("caller_success")
    if last_ok is False:
        pending.append(tid)
print(" ".join(pending))
PY
}

run_agent_backfill() {
    local agent="$1"
    local pending=""
    pending="$(pending_for_agent "$agent" || true)"
    pending="$(printf '%s' "${pending:-}" | xargs || true)"
    pending="${pending:-}"
    if [[ -z "$pending" ]]; then
        log "Nothing to backfill for ADD S. $agent"
        return 0
    fi
    log "Backfilling ADD S. $agent IDs: $pending"
    env -u OPENROUTER_API_KEY \
        PROJECT_ROOT="$PROJECT_ROOT" \
        TASKSET_PATH="$TASKSET_PATH" \
        TASK_IDS="$pending" \
        AGENTS="$agent" \
        MODEL_NAME="$MODEL_NAME" \
        TIMEOUT_SECONDS=900 \
        CALLING_TIMEOUT_SECONDS=180 \
        VARIANTS=poisoned \
        RUN_ID="$RUN_ID" \
        bash "$PROJECT_ROOT/experiments/scripts/effectivenss_injection_claw_0.2.5.context_injection_add_s_calling.sh"
    log "Backfill finished for ADD S. $agent"
}

wait_pid "$ZEROCLAW_PID" zeroclaw
wait_pid "$HERMES_PID" hermes
while docker ps --format '{{.Names}}' | grep -q "add_s_plan_a_newtasks_qwen36_20260827_run2"; do
    sleep 10
done
unset OPENROUTER_API_KEY || true
run_agent_backfill zeroclaw
run_agent_backfill hermes
log "ADD S. empty/401 backfill complete"
