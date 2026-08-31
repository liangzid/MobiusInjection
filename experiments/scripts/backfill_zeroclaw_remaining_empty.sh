#!/usr/bin/env bash
# After the 900s ADD M/C/EDIT M ZeroClaw timeout queue, backfill remaining
# provider-failed ZeroClaw cells (not ADD S.; that has its own waiter).
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/zi/AgentCodingDos}"
RUN_ROOT="${RUN_ROOT:-/home/zi/agentcodingdos_context_injection_runs}"
TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml}"
TASK_ID_FILE="${TASK_ID_FILE:-$PROJECT_ROOT/tasks/claw_plan_a_new_task_ids.txt}"
MODEL="${MODEL:-qwen/qwen3.6-plus}"
WAIT_PID="${WAIT_PID:-1866255}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMEOUT="${TIMEOUT:-900}"
CALLING_TIMEOUT="${CALLING_TIMEOUT:-480}"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

load_task_ids() {
    grep -v '^#' "$TASK_ID_FILE" | grep -v '^$' | tr '\n' ' ' | xargs
}

pending_for() {
    local run_id="$1"
    python3 "$SCRIPT_DIR/pending_claw_task_ids.py" \
        --log-dir "$RUN_ROOT/logs/$run_id" \
        $(load_task_ids)
}

unset OPENROUTER_API_KEY || true
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}" PYTHONPATH="$PROJECT_ROOT"
cd "$PROJECT_ROOT"

if [[ -n "$WAIT_PID" ]]; then
    log "Waiting for ZeroClaw 900s queue pid $WAIT_PID"
    while kill -0 "$WAIT_PID" 2>/dev/null; do
        sleep 20
    done
    log "ZeroClaw 900s queue exited"
fi

MAX_ROUNDS="${MAX_ROUNDS:-4}"
for round in $(seq 1 "$MAX_ROUNDS"); do
    ran=0
    log "remaining-empty round $round/$MAX_ROUNDS"

pending="$(pending_for edit_s_zeroclaw_plan_a_newtasks_qwen36_20260827)"
pending="$(printf '%s' "$pending" | xargs || true)"
if [[ -n "$pending" ]]; then
    ran=1
    log "EDIT S ZeroClaw pending ($pending)"
    PROJECT_ROOT="$PROJECT_ROOT" \
    TASKSET_PATH="$TASKSET_PATH" \
    TASK_IDS="$pending" \
    AGENTS=zeroclaw \
    MODEL_NAME="$MODEL" \
    TIMEOUT_SECONDS="$TIMEOUT" \
    CALLING_TIMEOUT_SECONDS=240 \
    VARIANTS=poisoned \
    RUN_ID=edit_s_zeroclaw_plan_a_newtasks_qwen36_20260827 \
    INJECTION_TEMPLATE_PATH="$PROJECT_ROOT/mobiusInjection/MI_V2.6_edit_s_zeroclaw.py" \
    bash "$SCRIPT_DIR/effectiveness_injection_claw_0.2.6.context_injection_edit_s_hermes.sh"
else
    log "EDIT S ZeroClaw has no pending IDs"
fi

pending="$(pending_for add_m_zeroclaw_plan_a_newtasks_qwen36_20260827)"
pending="$(printf '%s' "$pending" | xargs || true)"
if [[ -n "$pending" ]]; then
    ran=1
    log "ADD M ZeroClaw pending ($pending)"
    # shellcheck disable=SC2086
    uv run python "$SCRIPT_DIR/effectiveness_injection_claw_0.2.5.context_injection_add_m_claw_agents.py" \
        --agent zeroclaw \
        --run-id add_m_zeroclaw_plan_a_newtasks_qwen36_20260827 \
        --run-root "$RUN_ROOT" \
        --taskset "$TASKSET_PATH" \
        --model "$MODEL" \
        --timeout "$TIMEOUT" \
        --calling-timeout "$CALLING_TIMEOUT" \
        --task-ids $pending
else
    log "ADD M ZeroClaw has no pending IDs"
fi

pending="$(pending_for add_c_plan_a_newtasks_qwen36_20260827_zeroclaw)"
pending="$(printf '%s' "$pending" | xargs || true)"
if [[ -n "$pending" ]]; then
    ran=1
    n="$(printf '%s' "$pending" | wc -w | tr -d ' ')"
    log "ADD C ZeroClaw pending ($pending)"
    PROJECT_ROOT="$PROJECT_ROOT" \
    TASKSET_PATH="$TASKSET_PATH" \
    TASK_IDS="$pending" \
    AGENTS=zeroclaw \
    MODEL="$MODEL" \
    LIMIT="$n" \
    TIMEOUT="$TIMEOUT" \
    CALLING_TIMEOUT="$CALLING_TIMEOUT" \
    RUN_ID=add_c_plan_a_newtasks_qwen36_20260827 \
    bash "$SCRIPT_DIR/effectiveness_injection_claw_0.2.7.context_injection_add_c_batch.sh"
else
    log "ADD C ZeroClaw has no pending IDs"
fi

pending="$(pending_for edit_m_zeroclaw_plan_a_newtasks_qwen36_20260827)"
pending="$(printf '%s' "$pending" | xargs || true)"
if [[ -n "$pending" ]]; then
    ran=1
    log "EDIT M ZeroClaw pending ($pending)"
    # shellcheck disable=SC2086
    uv run python "$SCRIPT_DIR/effectiveness_injection_claw_0.2.6.context_injection_edit_m_claw_agents.py" \
        --agent zeroclaw \
        --run-id edit_m_zeroclaw_plan_a_newtasks_qwen36_20260827 \
        --run-root "$RUN_ROOT" \
        --taskset "$TASKSET_PATH" \
        --model "$MODEL" \
        --timeout "$TIMEOUT" \
        --calling-timeout "$CALLING_TIMEOUT" \
        --task-ids $pending
else
    log "EDIT M ZeroClaw has no pending IDs"
fi

pending="$(pending_for edit_c_plan_a_newtasks_qwen36_20260827_zeroclaw)"
pending="$(printf '%s' "$pending" | xargs || true)"
if [[ -n "$pending" ]]; then
    ran=1
    n="$(printf '%s' "$pending" | wc -w | tr -d ' ')"
    log "EDIT C ZeroClaw pending ($pending)"
    PROJECT_ROOT="$PROJECT_ROOT" \
    TASKSET_PATH="$TASKSET_PATH" \
    TASK_IDS="$pending" \
    AGENTS=zeroclaw \
    MODEL="$MODEL" \
    LIMIT="$n" \
    TIMEOUT="$TIMEOUT" \
    CALLING_TIMEOUT="$CALLING_TIMEOUT" \
    RUN_ID=edit_c_plan_a_newtasks_qwen36_20260827 \
    bash "$SCRIPT_DIR/effectiveness_injection_claw_0.2.8.context_injection_edit_c_batch.sh"
else
    log "EDIT C ZeroClaw has no pending IDs"
fi

    if [[ "$ran" -eq 0 ]]; then
        log "no pending ZeroClaw cells"
        break
    fi
done

log "ZeroClaw remaining empty backfills complete"
