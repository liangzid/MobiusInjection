#!/usr/bin/env bash
# Sequential Table-1 remaining strategies on the 28 new plan_a folder tasks.
# Reuses the original 11×4 sample; waits for the live ADD S. newtasks run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TASK_ID_FILE="${TASK_ID_FILE:-$PROJECT_ROOT/tasks/claw_plan_a_new_task_ids.txt}"
TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml}"
RUN_ROOT="${RUN_ROOT:-/home/zi/agentcodingdos_context_injection_runs}"
MODEL="${MODEL:-qwen/qwen3.6-plus}"
STAMP="${STAMP:-20260827}"
ADD_S_WAIT_PID="${ADD_S_WAIT_PID:-}"
ADD_S_CONTAINER_PREFIX="${ADD_S_CONTAINER_PREFIX:-ctx_add_s_plan_a_newtasks}"
DRY_RUN="${DRY_RUN:-0}"
UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}"
export UV_CACHE_DIR PYTHONPATH="$PROJECT_ROOT"

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

load_task_ids() {
    grep -v '^#' "$TASK_ID_FILE" | grep -v '^$' | tr '\n' ' ' | xargs
}

TASK_IDS="$(load_task_ids)"
TASK_COUNT="$(printf '%s' "$TASK_IDS" | wc -w | tr -d ' ')"
[[ "$TASK_COUNT" -eq 28 ]] || {
    echo "Expected 28 new task IDs, got $TASK_COUNT" >&2
    exit 2
}

run_cmd() {
    log "CMD: $*"
    if is_truthy "$DRY_RUN"; then
        return 0
    fi
    "$@"
}

prefix_is_active() {
    local needle="$1"
    docker ps --format '{{.Names}}' | grep -q "$needle" && return 0
    pgrep -af "$needle" | grep -v grep | grep -v run_plan_a_newtasks_remaining_strategies | grep -q "$needle" && return 0
    return 1
}

wait_until_prefix_idle() {
    local needle="$1"
    if is_truthy "$DRY_RUN"; then
        log "DRY_RUN=1 skip wait for $needle"
        return 0
    fi
    log "Waiting until no $needle containers/processes remain"
    while prefix_is_active "$needle"; do
        sleep 30
    done
    log "$needle is idle"
}

pending_ids_for_run() {
    local run_id="$1"
    python3 "$SCRIPT_DIR/pending_claw_task_ids.py" \
        --log-dir "$RUN_ROOT/logs/$run_id" \
        $TASK_IDS
}

wait_for_add_s() {
    if is_truthy "$DRY_RUN"; then
        log "DRY_RUN=1 skip wait for ADD S."
        return 0
    fi
    if [[ -n "$ADD_S_WAIT_PID" ]]; then
        log "Waiting for ADD S. pid $ADD_S_WAIT_PID"
        while kill -0 "$ADD_S_WAIT_PID" 2>/dev/null; do
            sleep 30
        done
    fi
    wait_until_prefix_idle "$ADD_S_CONTAINER_PREFIX"
    log "ADD S. newtasks is idle"
    local add_s_log="${RUN_ROOT}/logs/${ADD_S_RUN_ID:-add_s_plan_a_newtasks_qwen36_20260827_run2}"
    # Remaining strategies are already in flight with skip_if_complete backfill.
    # A single ADD S. 401 must not abort EDIT/ADD M/C pending retries.
    if grep -R -qE 'HTTP 401|User not found' "$add_s_log" --include='stdout.txt' --include='stderr.txt' 2>/dev/null; then
        log "WARN: ADD S. traces contain OpenRouter 401; skip/backfill still runs per-run pending IDs"
    fi
}

run_edit_s() {
    local agent="$1" template="$2" run_id="$3"
    wait_until_prefix_idle "ctx_${run_id}"
    local pending
    pending="$(pending_ids_for_run "$run_id")"
    pending="$(printf '%s' "$pending" | xargs)"
    if [[ -z "$pending" ]]; then
        log "Skip EDIT S. $agent; $run_id already complete without 401"
        return 0
    fi
    log "EDIT S. $agent pending ($pending)"
    PROJECT_ROOT="$PROJECT_ROOT" \
    TASKSET_PATH="$TASKSET_PATH" \
    TASK_IDS="$pending" \
    AGENTS="$agent" \
    MODEL_NAME="$MODEL" \
    TIMEOUT_SECONDS="${EDIT_S_TIMEOUT_SECONDS:-900}" \
    CALLING_TIMEOUT_SECONDS="${EDIT_S_CALLING_TIMEOUT_SECONDS:-240}" \
    VARIANTS=poisoned \
    RUN_ID="$run_id" \
    INJECTION_TEMPLATE_PATH="$PROJECT_ROOT/mobiusInjection/$template" \
    run_cmd bash "$SCRIPT_DIR/effectiveness_injection_claw_0.2.6.context_injection_edit_s_hermes.sh"
}

run_python_agent() {
    local runner="$1"
    shift
    run_cmd uv run python "$SCRIPT_DIR/$runner" "$@"
}

skip_if_complete() {
    local run_id="$1"
    wait_until_prefix_idle "ctx_${run_id}"
    local pending
    pending="$(pending_ids_for_run "$run_id")"
    pending="$(printf '%s' "$pending" | xargs)"
    if [[ -z "$pending" ]]; then
        log "Skip $run_id; already complete without 401"
        return 1
    fi
    PENDING_IDS="$pending"
    log "$run_id pending ($PENDING_IDS)"
    return 0
}

run_python_agent_for_run() {
    local run_id="$1"
    shift
    skip_if_complete "$run_id" || return 0
    run_python_agent "$@" --task-ids $PENDING_IDS
}

run_c_batch() {
    local script="$1"
    local run_id="$2"
    local agent n
    # Batch scripts write logs to ${RUN_ID}_${agent}. Skip or backfill per agent.
    for agent in openclaw zeroclaw hermes; do
        skip_if_complete "${run_id}_${agent}" || continue
        n="$(printf '%s' "$PENDING_IDS" | wc -w | tr -d ' ')"
        PROJECT_ROOT="$PROJECT_ROOT" \
        TASKSET_PATH="$TASKSET_PATH" \
        TASK_IDS="$PENDING_IDS" \
        AGENTS="$agent" \
        MODEL="$MODEL" \
        LIMIT="$n" \
        TIMEOUT=420 \
        CALLING_TIMEOUT=420 \
        RUN_ID="$run_id" \
        run_cmd bash "$SCRIPT_DIR/$script"
    done
}

wait_for_add_s

log "Remaining strategies on $TASK_COUNT tasks: $TASK_IDS"
unset OPENROUTER_API_KEY || true

run_edit_s openclaw MI_V3.0_edit_s_openclaw.py "edit_s_openclaw_plan_a_newtasks_qwen36_${STAMP}"
run_edit_s zeroclaw MI_V2.6_edit_s_zeroclaw.py "edit_s_zeroclaw_plan_a_newtasks_qwen36_${STAMP}"
run_edit_s hermes MI_V1_edit_s_hermes.py "edit_s_hermes_plan_a_newtasks_qwen36_${STAMP}"

run_python_agent_for_run "add_m_openclaw_plan_a_newtasks_qwen36_${STAMP}" \
    effectiveness_injection_claw_0.2.5.context_injection_add_m_openclaw.py \
    --run-id "add_m_openclaw_plan_a_newtasks_qwen36_${STAMP}" \
    --run-root "$RUN_ROOT" \
    --taskset "$TASKSET_PATH" \
    --model "$MODEL" \
    --timeout 420 \
    --calling-timeout 420

run_python_agent_for_run "add_m_zeroclaw_plan_a_newtasks_qwen36_${STAMP}" \
    effectiveness_injection_claw_0.2.5.context_injection_add_m_claw_agents.py \
    --agent zeroclaw \
    --run-id "add_m_zeroclaw_plan_a_newtasks_qwen36_${STAMP}" \
    --run-root "$RUN_ROOT" \
    --taskset "$TASKSET_PATH" \
    --model "$MODEL" \
    --timeout 420 \
    --calling-timeout 480

run_python_agent_for_run "add_m_hermes_plan_a_newtasks_qwen36_${STAMP}" \
    effectiveness_injection_claw_0.2.5.context_injection_add_m_claw_agents.py \
    --agent hermes \
    --run-id "add_m_hermes_plan_a_newtasks_qwen36_${STAMP}" \
    --run-root "$RUN_ROOT" \
    --taskset "$TASKSET_PATH" \
    --model "$MODEL" \
    --timeout 420 \
    --calling-timeout 480

run_c_batch effectiveness_injection_claw_0.2.7.context_injection_add_c_batch.sh \
    "add_c_plan_a_newtasks_qwen36_${STAMP}"

run_python_agent_for_run "edit_m_openclaw_plan_a_newtasks_qwen36_${STAMP}" \
    effectiveness_injection_claw_0.2.6.context_injection_edit_m_openclaw.py \
    --run-id "edit_m_openclaw_plan_a_newtasks_qwen36_${STAMP}" \
    --run-root "$RUN_ROOT" \
    --taskset "$TASKSET_PATH" \
    --model "$MODEL" \
    --timeout 420 \
    --calling-timeout 420

run_python_agent_for_run "edit_m_zeroclaw_plan_a_newtasks_qwen36_${STAMP}" \
    effectiveness_injection_claw_0.2.6.context_injection_edit_m_claw_agents.py \
    --agent zeroclaw \
    --run-id "edit_m_zeroclaw_plan_a_newtasks_qwen36_${STAMP}" \
    --run-root "$RUN_ROOT" \
    --taskset "$TASKSET_PATH" \
    --model "$MODEL" \
    --timeout 420 \
    --calling-timeout 480

run_python_agent_for_run "edit_m_hermes_plan_a_newtasks_qwen36_${STAMP}" \
    effectiveness_injection_claw_0.2.6.context_injection_edit_m_claw_agents.py \
    --agent hermes \
    --run-id "edit_m_hermes_plan_a_newtasks_qwen36_${STAMP}" \
    --run-root "$RUN_ROOT" \
    --taskset "$TASKSET_PATH" \
    --model "$MODEL" \
    --timeout 420 \
    --calling-timeout 480

run_c_batch effectiveness_injection_claw_0.2.8.context_injection_edit_c_batch.sh \
    "edit_c_plan_a_newtasks_qwen36_${STAMP}"

log "Remaining plan_a newtask strategies complete"
