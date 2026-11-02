#!/usr/bin/env bash
# After HumanEval ADD S. run2: rerun Kilo 20-97, then EDIT S. V37, then SWE-80.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
HE_RUN2_DIR="${HE_RUN2_DIR:-$PROJECT_ROOT/experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_offset20_limit144_20260827_run2}"
HE_RUN2_PID="${HE_RUN2_PID:-}"
MODEL_NAMES="${MODEL_NAMES:-openrouter/qwen/qwen3.6-plus}"
STAMP="${STAMP:-20260827}"
DRY_RUN="${DRY_RUN:-0}"
export PROJECT_ROOT RESTORE_KILO_BEFORE_RUN=0
# Cursor/eval-process OPENROUTER_API_KEY can be a dead key (HTTP 401).
# The privacy file is the working eval key; prefer it for queued launches.
unset OPENROUTER_API_KEY || true

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

kilo_he_task_ids() {
    python3 - <<'PY'
print(",".join(f"HumanEval/{i}" for i in range(20, 98)))
PY
}

run_cmd() {
    log "CMD: $*"
    if is_truthy "$DRY_RUN"; then
        return 0
    fi
    "$@"
}

kilo_idle() {
    # kilo_code images often lack pgrep. Prefer docker top for .kilo /
    # MainThread / kilo processes; if docker top fails, treat as busy.
    local top_out=""
    if ! top_out="$(docker top kilo_code -eo pid,comm 2>/dev/null)"; then
        return 1
    fi
    if printf '%s\n' "$top_out" | awk 'NR>1 {print $NF}' | grep -Eqi '^(kilo|\.kilo|MainThread)$'; then
        return 1
    fi
    return 0
}

kilo_163_ready() {
    local marker="$1"
    local f size
    # 0-byte output files appear at prompt-compose time; require real bytes.
    for f in "$marker"/humaneval_HumanEval_163_*_kilo_code_output.txt; do
        [[ -e "$f" ]] || continue
        size="$(wc -c < "$f" | tr -d ' ')"
        if [[ "$size" -ge 200 ]]; then
            return 0
        fi
    done
    return 1
}

wait_for_kilo_run2() {
    local marker="$HE_RUN2_DIR/models/openrouter_qwen_qwen3.6-plus/logs"
    log "Waiting for run2 Kilo HumanEval/163 nonempty output + idle kilo"
    if is_truthy "$DRY_RUN"; then
        return 0
    fi
    while true; do
        if kilo_163_ready "$marker" && kilo_idle; then
            break
        fi
        sleep 30
    done
    log "Run2 Kilo worker is idle"
}

wait_for_he_run2() {
    log "Waiting for HumanEval ADD S. run2 to finish"
    if is_truthy "$DRY_RUN"; then
        return 0
    fi
    if [[ -n "$HE_RUN2_PID" ]]; then
        while kill -0 "$HE_RUN2_PID" 2>/dev/null; do
            sleep 30
        done
    fi
    while ! grep -q 'Benchmark run complete:' "$HE_RUN2_DIR/wrapper.log" 2>/dev/null; do
        sleep 30
    done
    log "HumanEval ADD S. run2 complete"
}

wait_for_kilo_run2

KILO_TASK_IDS="$(kilo_he_task_ids)"
log "Launching Kilo ADD S. HumanEval/20-97"
PROJECT_ROOT="$PROJECT_ROOT" \
MODEL_NAMES="$MODEL_NAMES" \
CODING_EVAL_AGENTS=kilo_code \
BENCHMARK_DATASET=humaneval \
LIMIT=78 \
OFFSET=0 \
TASK_IDS="$KILO_TASK_IDS" \
INJECTION_TEMPLATE_MODULE=CODING_AGENT_TEMPLATE_V10_LOOP \
LOG_POLICY=keep_all \
TIMEOUT_SECONDS=600 \
FOLLOWUP_TIMEOUT_SECONDS=180 \
RESTORE_KILO_BEFORE_RUN=0 \
BENCHMARK_RUN_ID="qwen36_v10_humaneval_kilo_20_97_${STAMP}" \
run_cmd bash "$SCRIPT_DIR/1.0.3.run_free_models_humaneval_injection_benchmark.sh"

wait_for_he_run2

log "Launching EDIT S. V37 HumanEval OFFSET=20"
PROJECT_ROOT="$PROJECT_ROOT" \
MINIMAX_MODEL="$MODEL_NAMES" \
CODING_EVAL_AGENTS=opencode,kilo_code,claude_code \
INJECTION_TEMPLATE_MODULE=CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V37_LOOP \
BENCHMARK_DATASET=humaneval \
BENCHMARK_ROOT="$PROJECT_ROOT/experiments/logs/edit_skill_evaluation_humaneval" \
BENCHMARK_RUN_ID="edit_skill_v37_humaneval_offset20_limit144_qwen36_${STAMP}" \
LIMIT=144 \
OFFSET=20 \
LOG_POLICY=keep_all \
TIMEOUT_SECONDS=600 \
FOLLOWUP_TIMEOUT_SECONDS=600 \
RESTORE_KILO_BEFORE_RUN=0 \
run_cmd bash "$SCRIPT_DIR/coding_agents/run_edit_skill_evaluation_humaneval_benchmark.sh"

log "Launching SWE-bench 80 ADD S. OFFSET=20"
PROJECT_ROOT="$PROJECT_ROOT" \
MODEL_NAMES="$MODEL_NAMES" \
CODING_EVAL_AGENTS=opencode,kilo_code,claude_code \
BENCHMARK_DATASET=swebench \
SWEBENCH_DATASET_TYPE=swebench_80 \
LIMIT=60 \
OFFSET=20 \
INJECTION_TEMPLATE_MODULE=CODING_AGENT_TEMPLATE_V10_LOOP \
LOG_POLICY=keep_all \
TIMEOUT_SECONDS=600 \
FOLLOWUP_TIMEOUT_SECONDS=180 \
RESTORE_KILO_BEFORE_RUN=0 \
BENCHMARK_RUN_ID="qwen36_v10_swebench80_offset20_limit60_${STAMP}" \
run_cmd bash "$SCRIPT_DIR/1.0.3.run_free_models_humaneval_injection_benchmark.sh"

log "Launching SWE-bench 80 EDIT S. V37 OFFSET=20"
PROJECT_ROOT="$PROJECT_ROOT" \
MINIMAX_MODEL="$MODEL_NAMES" \
CODING_EVAL_AGENTS=opencode,kilo_code,claude_code \
INJECTION_TEMPLATE_MODULE=CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT_V37_LOOP \
BENCHMARK_DATASET=swebench \
SWEBENCH_DATASET_TYPE=swebench_80 \
BENCHMARK_ROOT="$PROJECT_ROOT/experiments/logs/edit_skill_evaluation_swebench" \
BENCHMARK_RUN_ID="edit_skill_v37_swebench80_offset20_limit60_qwen36_${STAMP}" \
LIMIT=60 \
OFFSET=20 \
LOG_POLICY=keep_all \
TIMEOUT_SECONDS=600 \
FOLLOWUP_TIMEOUT_SECONDS=600 \
RESTORE_KILO_BEFORE_RUN=0 \
run_cmd bash "$SCRIPT_DIR/coding_agents/run_edit_skill_evaluation_humaneval_benchmark.sh"

log "Table 2 expansion queue complete"
