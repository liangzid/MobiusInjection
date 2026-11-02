#!/bin/bash
# ======================================================================
# Run coding benchmark + TEMPLATE_V3 injection benchmarks across models.
#
# Concurrency model:
#   - models run serially, so the same container names are not reused by
#     multiple model batches at the same time.
#   - agents run concurrently within each model batch.
#   - tasks for the same agent/container run serially.
# ======================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
EVAL_SCRIPT="$SCRIPT_DIR/1.0.1.run_basic_coding_agent_eval_v3.sh"

MODEL_NAMES="${MODEL_NAMES:-openrouter/minimax/minimax-m2.5:free,openrouter/qwen/qwen3-coder:free,openrouter/deepseek/deepseek-r1-distill-qwen-32b:free}"
CODING_EVAL_AGENTS="${CODING_EVAL_AGENTS:-opencode,kilo_code,claude_code}"
BENCHMARK_DATASET="${BENCHMARK_DATASET:-humaneval}"
SWEBENCH_DATASET_TYPE="${SWEBENCH_DATASET_TYPE:-verified_mini}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-300}"
FOLLOWUP_TIMEOUT_SECONDS="${FOLLOWUP_TIMEOUT_SECONDS:-60}"
SLEEP_BETWEEN="${SLEEP_BETWEEN:-0}"
PROMPT_ORDER="${PROMPT_ORDER:-task_before_injection}"
LOG_POLICY="${LOG_POLICY:-compact}"
LIMIT="${LIMIT:-50}"
OFFSET="${OFFSET:-0}"
TASK_IDS="${TASK_IDS:-}"

BENCHMARK_ROOT="${BENCHMARK_ROOT:-$PROJECT_ROOT/experiments/logs/${BENCHMARK_DATASET}_model_benchmark}"
BENCHMARK_RUN_ID="${BENCHMARK_RUN_ID:-${BENCHMARK_DATASET}_models_$(date +%Y%m%d_%H%M%S)}"
BENCHMARK_RUN_DIR="${BENCHMARK_RUN_DIR:-$BENCHMARK_ROOT/$BENCHMARK_RUN_ID}"
WRAPPER_LOG="$BENCHMARK_RUN_DIR/wrapper.log"
EVAL_SCRIPT_SNAPSHOT="$BENCHMARK_RUN_DIR/scripts/$(basename "$EVAL_SCRIPT")"

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

safe_segment() {
    printf '%s' "$1" | tr -c 'A-Za-z0-9_.-' '_' | sed 's/^[._-]*//; s/[._-]*$//'
}

split_csv() {
    local raw="$1"
    python3 - "$raw" << 'PYTHON_EOF'
import sys

for item in sys.argv[1].split(","):
    item = item.strip()
    if item:
        print(item)
PYTHON_EOF
}

print_config() {
    printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT"
    printf 'EVAL_SCRIPT=%s\n' "$EVAL_SCRIPT"
    printf 'EVAL_SCRIPT_SNAPSHOT=%s\n' "$EVAL_SCRIPT_SNAPSHOT"
    printf 'BENCHMARK_RUN_DIR=%s\n' "$BENCHMARK_RUN_DIR"
    printf 'DATASET=%s\n' "$BENCHMARK_DATASET"
    printf 'SWEBENCH_DATASET_TYPE=%s\n' "$SWEBENCH_DATASET_TYPE"
    printf 'MODEL_NAMES=%s\n' "$MODEL_NAMES"
    printf 'CODING_EVAL_AGENTS=%s\n' "$CODING_EVAL_AGENTS"
    printf 'LIMIT=%s\n' "$LIMIT"
    printf 'OFFSET=%s\n' "$OFFSET"
    printf 'TASK_IDS=%s\n' "${TASK_IDS:-}"
    printf 'PROMPT_ORDER=%s\n' "$PROMPT_ORDER"
    printf 'LOG_POLICY=%s\n' "$LOG_POLICY"
    printf 'CONCURRENCY=one worker per agent; tasks serial inside each agent\n'
}

snapshot_eval_script() {
    mkdir -p "$(dirname "$EVAL_SCRIPT_SNAPSHOT")"
    cp "$EVAL_SCRIPT" "$EVAL_SCRIPT_SNAPSHOT"
    chmod +x "$EVAL_SCRIPT_SNAPSHOT"
}

model_run_dir() {
    local model="$1"
    local model_safe
    model_safe="$(safe_segment "$model")"
    printf '%s/models/%s' "$BENCHMARK_RUN_DIR" "${model_safe:-model}"
}

model_manifest_file() {
    printf '%s/manifest.json' "$(model_run_dir "$1")"
}

build_manifest_for_model() {
    local model="$1"
    local run_dir manifest_file
    run_dir="$(model_run_dir "$model")"
    manifest_file="$(model_manifest_file "$model")"
    mkdir -p "$run_dir"

    local args=(
        -m experiments.AgentCallInterface.evaluation.benchmark_manifest
        --dataset "$BENCHMARK_DATASET"
        --dataset-type "$SWEBENCH_DATASET_TYPE"
        --model "$model"
        --agents "$CODING_EVAL_AGENTS"
        --run-dir "$run_dir"
        --manifest "$manifest_file"
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

build_manifests() {
    while IFS= read -r model; do
        build_manifest_for_model "$model"
    done < <(split_csv "$MODEL_NAMES")
}

print_cases_for_manifest() {
    local manifest_file="$1"
    python3 - "$manifest_file" << 'PYTHON_EOF'
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

print_all_cases() {
    while IFS= read -r model; do
        printf '\nMODEL=%s\n' "$model"
        print_cases_for_manifest "$(model_manifest_file "$model")"
    done < <(split_csv "$MODEL_NAMES")
}

run_case() {
    local benchmark_id="$1" dataset="$2" task_id="$3" agent="$4"
    local model="$5" prompt_order="$6" task_prompt_file="$7" worker_log="$8"

    printf '\nRunning case: %s %s %s %s\n' "$model" "$task_id" "$agent" "$benchmark_id" | tee -a "$worker_log"
    PROJECT_ROOT="$PROJECT_ROOT" \
    LOG_DIR="$(model_run_dir "$model")/logs" \
    EVAL_ID="$benchmark_id" \
    CODING_EVAL_AGENTS="$agent" \
    BENCHMARK_DATASET="$dataset" \
    BENCHMARK_TASK_ID="$task_id" \
    BENCHMARK_TASK_PROMPT_FILE="$task_prompt_file" \
    PROMPT_ORDER="$prompt_order" \
    LOG_POLICY="$LOG_POLICY" \
    FOLLOWUP_TIMEOUT_SECONDS="$FOLLOWUP_TIMEOUT_SECONDS" \
    bash "$EVAL_SCRIPT_SNAPSHOT" "$model" "$TIMEOUT_SECONDS" "$SLEEP_BETWEEN" \
        2>&1 | tee -a "$worker_log"
}

run_agent_worker() {
    local model="$1" agent="$2"
    local manifest_file run_dir worker_log
    manifest_file="$(model_manifest_file "$model")"
    run_dir="$(model_run_dir "$model")"
    worker_log="$run_dir/worker_${agent}.log"
    mkdir -p "$run_dir/logs"

    while IFS=$'\t' read -r benchmark_id dataset task_id entry_agent entry_model prompt_order task_prompt_file; do
        run_case "$benchmark_id" "$dataset" "$task_id" "$entry_agent" "$entry_model" "$prompt_order" "$task_prompt_file" "$worker_log"
    done < <(python3 - "$manifest_file" "$agent" << 'PYTHON_EOF'
import json
import sys

entries = json.load(open(sys.argv[1]))
target_agent = sys.argv[2]
for entry in entries:
    if entry["agent"] != target_agent:
        continue
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

wait_for_workers() {
    local failures=0
    local pid
    for pid in "$@"; do
        if ! wait "$pid"; then
            failures=$((failures + 1))
        fi
    done
    return "$failures"
}

run_model_cases() {
    local model="$1"
    local pids=()
    printf '\nStarting model batch: %s\n' "$model" | tee -a "$WRAPPER_LOG"

    while IFS= read -r agent; do
        run_agent_worker "$model" "$agent" &
        pids+=("$!")
    done < <(split_csv "$CODING_EVAL_AGENTS")

    if ! wait_for_workers "${pids[@]}"; then
        printf 'Model batch failed: %s\n' "$model" | tee -a "$WRAPPER_LOG"
        return 1
    fi
    printf 'Model batch complete: %s\n' "$model" | tee -a "$WRAPPER_LOG"
}

apply_retention_and_aggregate_for_model() {
    local model="$1"
    local run_dir manifest_file
    run_dir="$(model_run_dir "$model")"
    manifest_file="$(model_manifest_file "$model")"

    PYTHONPATH="$PROJECT_ROOT" python3 -m experiments.AgentCallInterface.evaluation.log_retention \
        --run-dir "$run_dir" \
        --manifest "$manifest_file" \
        --policy "$LOG_POLICY"
    PYTHONPATH="$PROJECT_ROOT" python3 -m experiments.AgentCallInterface.evaluation.benchmark_analysis \
        --run-dir "$run_dir"
}

run_all_models() {
    while IFS= read -r model; do
        run_model_cases "$model"
        apply_retention_and_aggregate_for_model "$model" | tee -a "$WRAPPER_LOG"
    done < <(split_csv "$MODEL_NAMES")
}

main() {
    print_config
    build_manifests
    snapshot_eval_script

    if is_truthy "${DRY_RUN:-0}"; then
        printf 'DRY_RUN=1\n'
        print_all_cases
        return 0
    fi

    mkdir -p "$BENCHMARK_RUN_DIR"
    print_config | tee "$WRAPPER_LOG"
    run_all_models
    printf '\nBenchmark run complete: %s\n' "$BENCHMARK_RUN_DIR" | tee -a "$WRAPPER_LOG"
}

main "$@"
