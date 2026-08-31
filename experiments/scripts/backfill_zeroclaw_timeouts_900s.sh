#!/usr/bin/env bash
# Retry ZeroClaw timeout-empty new-28 cells at 900s (420s already failed).
# Serial so they do not sit next to each other on the same API wait.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/zi/AgentCodingDos}"
RUN_ROOT="${RUN_ROOT:-/home/zi/agentcodingdos_context_injection_runs}"
TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml}"
MODEL="${MODEL:-qwen/qwen3.6-plus}"
TIMEOUT="${TIMEOUT:-900}"
CALLING_TIMEOUT="${CALLING_TIMEOUT:-480}"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

unset OPENROUTER_API_KEY || true
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}" PYTHONPATH="$PROJECT_ROOT"
cd "$PROJECT_ROOT"

log "ADD M ZeroClaw doc-005 timeout=$TIMEOUT"
uv run python experiments/scripts/effectiveness_injection_claw_0.2.5.context_injection_add_m_claw_agents.py \
    --agent zeroclaw \
    --run-id add_m_zeroclaw_plan_a_newtasks_qwen36_20260827 \
    --run-root "$RUN_ROOT" \
    --taskset "$TASKSET_PATH" \
    --model "$MODEL" \
    --timeout "$TIMEOUT" \
    --calling-timeout "$CALLING_TIMEOUT" \
    --task-ids doc-005
log "ADD M ZeroClaw doc-005 done"

log "ADD C ZeroClaw doc-005 timeout=$TIMEOUT"
PROJECT_ROOT="$PROJECT_ROOT" \
TASKSET_PATH="$TASKSET_PATH" \
TASK_IDS=doc-005 \
AGENTS=zeroclaw \
LIMIT=1 \
TIMEOUT="$TIMEOUT" \
CALLING_TIMEOUT="$CALLING_TIMEOUT" \
MODEL="$MODEL" \
RUN_ID=add_c_plan_a_newtasks_qwen36_20260827 \
bash experiments/scripts/effectiveness_injection_claw_0.2.7.context_injection_add_c_batch.sh
log "ADD C ZeroClaw doc-005 done"

log "EDIT M ZeroClaw eml-011 timeout=$TIMEOUT"
uv run python experiments/scripts/effectiveness_injection_claw_0.2.6.context_injection_edit_m_claw_agents.py \
    --agent zeroclaw \
    --run-id edit_m_zeroclaw_plan_a_newtasks_qwen36_20260827 \
    --run-root "$RUN_ROOT" \
    --taskset "$TASKSET_PATH" \
    --model "$MODEL" \
    --timeout "$TIMEOUT" \
    --calling-timeout "$CALLING_TIMEOUT" \
    --task-ids eml-011
log "EDIT M ZeroClaw eml-011 done"
log "ZeroClaw 900s timeout backfills complete"
