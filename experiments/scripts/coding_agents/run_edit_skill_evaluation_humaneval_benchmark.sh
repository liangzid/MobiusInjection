#!/bin/bash
# ======================================================================
# Run edit skill evaluation benchmark cases.
#
# This experiment edits one existing skill and injects exactly one auxiliary
# skill. It is intentionally separate from the older two-new-skill runners.
# ======================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
RUNNER_MODULE="experiments.AgentCallInterface.coding_evaluation.edit_skill_evaluation_runner"
ANALYSIS_MODULE="experiments.AgentCallInterface.coding_evaluation.edit_skill_evaluation_analysis"

MINIMAX_MODEL="${MINIMAX_MODEL:-openrouter/minimax/minimax-m2.5:free}"
CODING_EVAL_AGENTS="${CODING_EVAL_AGENTS:-opencode,kilo_code,claude_code}"
INJECTION_TEMPLATE_MODULE="${INJECTION_TEMPLATE_MODULE:-CODING_AGENT_TEMPLATE_EXPLAIN_CODE_EDIT}"
EDIT_SKILL_BASELINE_SKILL="${EDIT_SKILL_BASELINE_SKILL:-explain-code}"
EDIT_SKILL_AUXILIARY_SKILL="${EDIT_SKILL_AUXILIARY_SKILL:-explanation-status}"
EDIT_SKILL_LEDGER_NAME="${EDIT_SKILL_LEDGER_NAME:-explain-code-status-ledger.jsonl}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-300}"
FOLLOWUP_TIMEOUT_SECONDS="${FOLLOWUP_TIMEOUT_SECONDS:-120}"
PROMPT_ORDER="${PROMPT_ORDER:-task_before_injection}"
LOG_POLICY="${LOG_POLICY:-compact}"
LIMIT="${LIMIT:-}"
OFFSET="${OFFSET:-0}"
TASK_IDS="${TASK_IDS:-}"

BENCHMARK_DATASET="${BENCHMARK_DATASET:-humaneval}"
BENCHMARK_ROOT="${BENCHMARK_ROOT:-$PROJECT_ROOT/experiments/logs/edit_skill_evaluation_humaneval}"
BENCHMARK_RUN_ID="${BENCHMARK_RUN_ID:-edit_skill_evaluation_$(date +%Y%m%d_%H%M%S)}"
BENCHMARK_RUN_DIR="${BENCHMARK_RUN_DIR:-$BENCHMARK_ROOT/$BENCHMARK_RUN_ID}"
MANIFEST_FILE="$BENCHMARK_RUN_DIR/manifest.json"
WRAPPER_LOG="$BENCHMARK_RUN_DIR/wrapper.log"
WRAPPER_SNAPSHOT="$BENCHMARK_RUN_DIR/scripts/$(basename "$0")"

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

print_config() {
    printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT"
    printf 'RUNNER_MODULE=%s\n' "$RUNNER_MODULE"
    printf 'ANALYSIS_MODULE=%s\n' "$ANALYSIS_MODULE"
    printf 'WRAPPER_SNAPSHOT=%s\n' "$WRAPPER_SNAPSHOT"
    printf 'BENCHMARK_RUN_DIR=%s\n' "$BENCHMARK_RUN_DIR"
    printf 'MANIFEST_FILE=%s\n' "$MANIFEST_FILE"
    printf 'DATASET=%s\n' "$BENCHMARK_DATASET"
    printf 'MODEL=%s\n' "$MINIMAX_MODEL"
    printf 'CODING_EVAL_AGENTS=%s\n' "$CODING_EVAL_AGENTS"
    printf 'INJECTION_TEMPLATE_MODULE=%s\n' "$INJECTION_TEMPLATE_MODULE"
    printf 'EDIT_SKILL_BASELINE_SKILL=%s\n' "$EDIT_SKILL_BASELINE_SKILL"
    printf 'EDIT_SKILL_AUXILIARY_SKILL=%s\n' "$EDIT_SKILL_AUXILIARY_SKILL"
    printf 'EDIT_SKILL_LEDGER_NAME=%s\n' "$EDIT_SKILL_LEDGER_NAME"
    printf 'LIMIT=%s\n' "${LIMIT:-}"
    printf 'OFFSET=%s\n' "$OFFSET"
    printf 'TASK_IDS=%s\n' "${TASK_IDS:-}"
    printf 'PROMPT_ORDER=%s\n' "$PROMPT_ORDER"
    printf 'LOG_POLICY=%s\n' "$LOG_POLICY"
}

snapshot_wrapper() {
    mkdir -p "$(dirname "$WRAPPER_SNAPSHOT")"
    cp "$0" "$WRAPPER_SNAPSHOT"
    chmod +x "$WRAPPER_SNAPSHOT"
}

build_manifest() {
    mkdir -p "$BENCHMARK_RUN_DIR"
    local args=(
        -m experiments.AgentCallInterface.coding_evaluation.benchmark_manifest
        --dataset "$BENCHMARK_DATASET"
        --model "$MINIMAX_MODEL"
        --agents "$CODING_EVAL_AGENTS"
        --run-dir "$BENCHMARK_RUN_DIR"
        --manifest "$MANIFEST_FILE"
        --prompt-order "$PROMPT_ORDER"
        --offset "$OFFSET"
    )
    if [ -n "$LIMIT" ]; then
        args+=(--limit "$LIMIT")
    fi
    if [ -n "$TASK_IDS" ]; then
        args+=(--task-ids "$TASK_IDS")
    fi
    PYTHONPATH="$PROJECT_ROOT" python3 "${args[@]}"
}

print_cases() {
    python3 - "$MANIFEST_FILE" << 'PYTHON_EOF'
import json
import sys

entries = json.load(open(sys.argv[1]))
print(f"CASES={len(entries)}")
for entry in entries:
    print(
        "\t".join(
            [
                entry["benchmark_id"],
                entry["dataset"],
                entry["task_id"],
                entry["agent"],
                entry["model"],
                entry["prompt_order"],
                entry["task_prompt_file"],
            ]
        )
    )
PYTHON_EOF
}

run_case() {
    local benchmark_id="$1"
    local dataset="$2"
    local task_id="$3"
    local agent="$4"
    local model="$5"
    local prompt_order="$6"
    local task_prompt_file="$7"

    printf '\nRunning edit skill case: %s %s %s\n' "$task_id" "$agent" "$benchmark_id" | tee -a "$WRAPPER_LOG"
    PYTHONPATH="$PROJECT_ROOT" python3 -m "$RUNNER_MODULE" \
        --project-root "$PROJECT_ROOT" \
        --benchmark-id "$benchmark_id" \
        --dataset "$dataset" \
        --task-id "$task_id" \
        --task-prompt-file "$task_prompt_file" \
        --prompt-order "$prompt_order" \
        --agent "$agent" \
        --model "$model" \
        --log-dir "$BENCHMARK_RUN_DIR/logs" \
        --timeout "$TIMEOUT_SECONDS" \
        --followup-timeout "$FOLLOWUP_TIMEOUT_SECONDS" \
        --template-module "$INJECTION_TEMPLATE_MODULE" \
        --baseline-skill "$EDIT_SKILL_BASELINE_SKILL" \
        --auxiliary-skill "$EDIT_SKILL_AUXILIARY_SKILL" \
        --ledger-name "$EDIT_SKILL_LEDGER_NAME" \
        2>&1 | tee -a "$WRAPPER_LOG"
}

run_cases() {
    mkdir -p "$BENCHMARK_RUN_DIR/logs"
    while IFS=$'\t' read -r benchmark_id dataset task_id agent model prompt_order task_prompt_file; do
        run_case "$benchmark_id" "$dataset" "$task_id" "$agent" "$model" "$prompt_order" "$task_prompt_file" || true
    done < <(python3 - "$MANIFEST_FILE" << 'PYTHON_EOF'
import json
import sys

for entry in json.load(open(sys.argv[1])):
    print(
        "\t".join(
            [
                entry["benchmark_id"],
                entry["dataset"],
                entry["task_id"],
                entry["agent"],
                entry["model"],
                entry["prompt_order"],
                entry["task_prompt_file"],
            ]
        )
    )
PYTHON_EOF
)
}

apply_retention_and_aggregate() {
    PYTHONPATH="$PROJECT_ROOT" python3 -m experiments.AgentCallInterface.coding_evaluation.log_retention \
        --run-dir "$BENCHMARK_RUN_DIR" \
        --manifest "$MANIFEST_FILE" \
        --policy "$LOG_POLICY"
    PYTHONPATH="$PROJECT_ROOT" python3 -m "$ANALYSIS_MODULE" \
        --run-dir "$BENCHMARK_RUN_DIR"
}

main() {
    print_config
    build_manifest
    snapshot_wrapper

    if is_truthy "${DRY_RUN:-0}"; then
        printf 'DRY_RUN=1\n'
        print_cases
        return 0
    fi

    print_config | tee "$WRAPPER_LOG"
    run_cases
    apply_retention_and_aggregate | tee -a "$WRAPPER_LOG"
    printf '\nEdit skill evaluation complete: %s\n' "$BENCHMARK_RUN_DIR" | tee -a "$WRAPPER_LOG"
}

main "$@"
