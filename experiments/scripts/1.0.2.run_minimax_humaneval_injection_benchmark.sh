#!/bin/bash
# ======================================================================
# Run a MiniMax HumanEval + TEMPLATE_V3 injection benchmark.
# ======================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
EVAL_SCRIPT="$SCRIPT_DIR/1.0.1.run_basic_coding_agent_eval_v3.sh"

MINIMAX_MODEL="${MINIMAX_MODEL:-openrouter/minimax/minimax-m2.5:free}"
CODING_EVAL_AGENTS="${CODING_EVAL_AGENTS:-opencode,kilo_code,claude_code}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-300}"
FOLLOWUP_TIMEOUT_SECONDS="${FOLLOWUP_TIMEOUT_SECONDS:-60}"
SLEEP_BETWEEN="${SLEEP_BETWEEN:-0}"
PROMPT_ORDER="${PROMPT_ORDER:-task_before_injection}"
LOG_POLICY="${LOG_POLICY:-compact}"
LIMIT="${LIMIT:-}"
OFFSET="${OFFSET:-0}"
TASK_IDS="${TASK_IDS:-}"

BENCHMARK_DATASET="humaneval"
BENCHMARK_ROOT="${BENCHMARK_ROOT:-$PROJECT_ROOT/experiments/logs/humaneval_minimax_benchmark}"
BENCHMARK_RUN_ID="${BENCHMARK_RUN_ID:-humaneval_minimax_$(date +%Y%m%d_%H%M%S)}"
BENCHMARK_RUN_DIR="${BENCHMARK_RUN_DIR:-$BENCHMARK_ROOT/$BENCHMARK_RUN_ID}"
MANIFEST_FILE="$BENCHMARK_RUN_DIR/manifest.json"
WRAPPER_LOG="$BENCHMARK_RUN_DIR/wrapper.log"
EVAL_SCRIPT_SNAPSHOT="$BENCHMARK_RUN_DIR/scripts/$(basename "$EVAL_SCRIPT")"

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

print_config() {
    printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT"
    printf 'EVAL_SCRIPT=%s\n' "$EVAL_SCRIPT"
    printf 'EVAL_SCRIPT_SNAPSHOT=%s\n' "$EVAL_SCRIPT_SNAPSHOT"
    printf 'BENCHMARK_RUN_DIR=%s\n' "$BENCHMARK_RUN_DIR"
    printf 'MANIFEST_FILE=%s\n' "$MANIFEST_FILE"
    printf 'DATASET=%s\n' "$BENCHMARK_DATASET"
    printf 'MODEL=%s\n' "$MINIMAX_MODEL"
    printf 'CODING_EVAL_AGENTS=%s\n' "$CODING_EVAL_AGENTS"
    printf 'LIMIT=%s\n' "${LIMIT:-}"
    printf 'OFFSET=%s\n' "$OFFSET"
    printf 'TASK_IDS=%s\n' "${TASK_IDS:-}"
    printf 'PROMPT_ORDER=%s\n' "$PROMPT_ORDER"
    printf 'LOG_POLICY=%s\n' "$LOG_POLICY"
}

snapshot_eval_script() {
    mkdir -p "$(dirname "$EVAL_SCRIPT_SNAPSHOT")"
    cp "$EVAL_SCRIPT" "$EVAL_SCRIPT_SNAPSHOT"
    chmod +x "$EVAL_SCRIPT_SNAPSHOT"
}

build_manifest() {
    mkdir -p "$BENCHMARK_RUN_DIR"
    local args=(
        -m experiments.AgentCallInterface.evaluation.benchmark_manifest
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

    printf '\nRunning case: %s %s %s\n' "$task_id" "$agent" "$benchmark_id" | tee -a "$WRAPPER_LOG"
    PROJECT_ROOT="$PROJECT_ROOT" \
    LOG_DIR="$BENCHMARK_RUN_DIR/logs" \
    EVAL_ID="$benchmark_id" \
    CODING_EVAL_AGENTS="$agent" \
    BENCHMARK_DATASET="$dataset" \
    BENCHMARK_TASK_ID="$task_id" \
    BENCHMARK_TASK_PROMPT_FILE="$task_prompt_file" \
    PROMPT_ORDER="$prompt_order" \
    LOG_POLICY="$LOG_POLICY" \
    FOLLOWUP_TIMEOUT_SECONDS="$FOLLOWUP_TIMEOUT_SECONDS" \
    bash "$EVAL_SCRIPT_SNAPSHOT" "$model" "$TIMEOUT_SECONDS" "$SLEEP_BETWEEN" \
        2>&1 | tee -a "$WRAPPER_LOG"
}

run_cases() {
    mkdir -p "$BENCHMARK_RUN_DIR/logs"
    while IFS=$'\t' read -r benchmark_id dataset task_id agent model prompt_order task_prompt_file; do
        run_case "$benchmark_id" "$dataset" "$task_id" "$agent" "$model" "$prompt_order" "$task_prompt_file"
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
    PYTHONPATH="$PROJECT_ROOT" python3 -m experiments.AgentCallInterface.evaluation.log_retention \
        --run-dir "$BENCHMARK_RUN_DIR" \
        --manifest "$MANIFEST_FILE" \
        --policy "$LOG_POLICY"
    PYTHONPATH="$PROJECT_ROOT" python3 -m experiments.AgentCallInterface.evaluation.benchmark_analysis \
        --run-dir "$BENCHMARK_RUN_DIR"
}

main() {
    print_config
    build_manifest
    snapshot_eval_script

    if is_truthy "${DRY_RUN:-0}"; then
        printf 'DRY_RUN=1\n'
        print_cases
        return 0
    fi

    print_config | tee "$WRAPPER_LOG"
    run_cases
    apply_retention_and_aggregate | tee -a "$WRAPPER_LOG"
    printf '\nBenchmark run complete: %s\n' "$BENCHMARK_RUN_DIR" | tee -a "$WRAPPER_LOG"
}

main "$@"
