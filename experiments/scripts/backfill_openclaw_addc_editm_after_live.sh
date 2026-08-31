#!/usr/bin/env bash
# After a live OpenClaw ADD C or EDIT M worker exits, backfill pending/empty
# cells immediately instead of waiting for ADD S. ZeroClaw to finish.
# BACKFILL_WHICH=add_c|edit_m
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/zi/AgentCodingDos}"
RUN_ROOT="${RUN_ROOT:-/home/zi/agentcodingdos_context_injection_runs}"
TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml}"
TASK_ID_FILE="${TASK_ID_FILE:-$PROJECT_ROOT/tasks/claw_plan_a_new_task_ids.txt}"
MODEL="${MODEL:-qwen/qwen3.6-plus}"
BACKFILL_WHICH="${BACKFILL_WHICH:?set BACKFILL_WHICH=add_c or edit_m}"
ADD_C_OPENCLAW_PID="${ADD_C_OPENCLAW_PID:-1021300}"
EDIT_M_OPENCLAW_PID="${EDIT_M_OPENCLAW_PID:-1064025}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

load_task_ids() {
    grep -v '^#' "$TASK_ID_FILE" | grep -v '^$' | tr '\n' ' ' | xargs
}

wait_pid() {
    local pid="$1" name="$2"
    if [[ -z "$pid" ]]; then
        return 0
    fi
    log "Waiting for $name pid $pid"
    while kill -0 "$pid" 2>/dev/null; do
        sleep 20
    done
    log "$name pid $pid exited"
}

wait_docker_idle() {
    local needle="$1"
    while docker ps --format '{{.Names}}' | grep -q "$needle"; do
        sleep 10
    done
}

pending_for() {
    local run_id="$1"
    python3 "$SCRIPT_DIR/pending_claw_task_ids.py" \
        --log-dir "$RUN_ROOT/logs/$run_id" \
        $(load_task_ids)
}

unset OPENROUTER_API_KEY || true
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}" PYTHONPATH="$PROJECT_ROOT"

case "$BACKFILL_WHICH" in
    add_c)
        wait_pid "$ADD_C_OPENCLAW_PID" "ADD C OpenClaw"
        wait_docker_idle "ctx_add_c_plan_a_newtasks_qwen36_20260827_openclaw"
        pending="$(pending_for add_c_plan_a_newtasks_qwen36_20260827_openclaw)"
        pending="$(printf '%s' "$pending" | xargs || true)"
        if [[ -z "$pending" ]]; then
            log "ADD C OpenClaw has no pending IDs"
            exit 0
        fi
        n="$(printf '%s' "$pending" | wc -w | tr -d ' ')"
        log "ADD C OpenClaw pending ($pending)"
        PROJECT_ROOT="$PROJECT_ROOT" \
        TASKSET_PATH="$TASKSET_PATH" \
        TASK_IDS="$pending" \
        AGENTS=openclaw \
        MODEL="$MODEL" \
        LIMIT="$n" \
        TIMEOUT=420 \
        CALLING_TIMEOUT=420 \
        RUN_ID=add_c_plan_a_newtasks_qwen36_20260827 \
        bash "$SCRIPT_DIR/effectiveness_injection_claw_0.2.7.context_injection_add_c_batch.sh"
        log "ADD C OpenClaw backfill finished"
        ;;
    edit_m)
        wait_pid "$EDIT_M_OPENCLAW_PID" "EDIT M OpenClaw"
        wait_docker_idle "ctx_edit_m_openclaw_plan_a_newtasks_qwen36_20260827"
        pending="$(pending_for edit_m_openclaw_plan_a_newtasks_qwen36_20260827)"
        pending="$(printf '%s' "$pending" | xargs || true)"
        if [[ -z "$pending" ]]; then
            log "EDIT M OpenClaw has no pending IDs"
            exit 0
        fi
        log "EDIT M OpenClaw pending ($pending)"
        # shellcheck disable=SC2086
        uv run python "$SCRIPT_DIR/effectiveness_injection_claw_0.2.6.context_injection_edit_m_openclaw.py" \
            --run-id edit_m_openclaw_plan_a_newtasks_qwen36_20260827 \
            --run-root "$RUN_ROOT" \
            --taskset "$TASKSET_PATH" \
            --model "$MODEL" \
            --timeout 420 \
            --calling-timeout 420 \
            --task-ids $pending
        log "EDIT M OpenClaw backfill finished"
        ;;
    *)
        echo "BACKFILL_WHICH must be add_c or edit_m" >&2
        exit 2
        ;;
esac
