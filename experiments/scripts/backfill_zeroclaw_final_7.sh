#!/usr/bin/env bash
# Serialized ZeroClaw retry for the final 7 Claw new-28 empty cells.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/zi/AgentCodingDos}"
RUN_ROOT="${RUN_ROOT:-/home/zi/agentcodingdos_context_injection_runs}"
TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml}"
MODEL="${MODEL:-qwen/qwen3.6-plus}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMEOUT="${TIMEOUT:-900}"
CALLING_TIMEOUT="${CALLING_TIMEOUT:-480}"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

unset OPENROUTER_API_KEY || true
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}" PYTHONPATH="$PROJECT_ROOT"
cd "$PROJECT_ROOT"

log "=== ZeroClaw final-7 backfill start ==="

log "1/5 ADD S zeroclaw doc-005 timeout=$TIMEOUT"
PROJECT_ROOT="$PROJECT_ROOT" \
TASKSET_PATH="$TASKSET_PATH" \
TASK_IDS=doc-005 \
AGENTS=zeroclaw \
MODEL_NAME="$MODEL" \
TIMEOUT_SECONDS="$TIMEOUT" \
CALLING_TIMEOUT_SECONDS=180 \
VARIANTS=poisoned \
RUN_ID=add_s_plan_a_newtasks_qwen36_20260827_run2 \
bash "$SCRIPT_DIR/effectivenss_injection_claw_0.2.5.context_injection_add_s_calling.sh"
log "ADD S doc-005 done"

log "2/5 EDIT S zeroclaw eml-011 timeout=$TIMEOUT"
PROJECT_ROOT="$PROJECT_ROOT" \
TASKSET_PATH="$TASKSET_PATH" \
TASK_IDS=eml-011 \
AGENTS=zeroclaw \
MODEL_NAME="$MODEL" \
TIMEOUT_SECONDS="$TIMEOUT" \
CALLING_TIMEOUT_SECONDS=240 \
VARIANTS=poisoned \
RUN_ID=edit_s_zeroclaw_plan_a_newtasks_qwen36_20260827 \
INJECTION_TEMPLATE_PATH="$PROJECT_ROOT/mobiusInjection/MI_V2.6_edit_s_zeroclaw.py" \
bash "$SCRIPT_DIR/effectiveness_injection_claw_0.2.6.context_injection_edit_s_hermes.sh"
log "EDIT S eml-011 done"

log "3/5 ADD C zeroclaw doc-005 eml-011 timeout=$TIMEOUT"
PROJECT_ROOT="$PROJECT_ROOT" \
TASKSET_PATH="$TASKSET_PATH" \
TASK_IDS="doc-005 eml-011" \
AGENTS=zeroclaw \
MODEL="$MODEL" \
LIMIT=2 \
TIMEOUT="$TIMEOUT" \
CALLING_TIMEOUT="$CALLING_TIMEOUT" \
RUN_ID=add_c_plan_a_newtasks_qwen36_20260827 \
bash "$SCRIPT_DIR/effectiveness_injection_claw_0.2.7.context_injection_add_c_batch.sh"
log "ADD C doc-005 eml-011 done"

log "4/5 EDIT M zeroclaw eml-011 timeout=$TIMEOUT"
uv run python "$SCRIPT_DIR/effectiveness_injection_claw_0.2.6.context_injection_edit_m_claw_agents.py" \
    --agent zeroclaw \
    --run-id edit_m_zeroclaw_plan_a_newtasks_qwen36_20260827 \
    --run-root "$RUN_ROOT" \
    --taskset "$TASKSET_PATH" \
    --model "$MODEL" \
    --timeout "$TIMEOUT" \
    --calling-timeout "$CALLING_TIMEOUT" \
    --task-ids eml-011
log "EDIT M eml-011 done"

log "5/5 EDIT C zeroclaw doc-013 eml-011 timeout=$TIMEOUT"
PROJECT_ROOT="$PROJECT_ROOT" \
TASKSET_PATH="$TASKSET_PATH" \
TASK_IDS="doc-013 eml-011" \
AGENTS=zeroclaw \
MODEL="$MODEL" \
LIMIT=2 \
TIMEOUT="$TIMEOUT" \
CALLING_TIMEOUT="$CALLING_TIMEOUT" \
RUN_ID=edit_c_plan_a_newtasks_qwen36_20260827 \
bash "$SCRIPT_DIR/effectiveness_injection_claw_0.2.8.context_injection_edit_c_batch.sh"
log "EDIT C doc-013 eml-011 done"

log "=== ZeroClaw final-7 backfill complete ==="
python3 "$PROJECT_ROOT/../AgentCodingDos_CodeAgent/experiments/scripts/expansion_matrix_coverage.py" | tail -20
