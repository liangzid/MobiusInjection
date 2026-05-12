#!/bin/bash
# ======================================================================
# Run AiGoCode closed-model OpenCode end-to-end smoke experiments.
# ======================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
CONFIG_FILE="${AIGOCODE_MODELS_CONFIG:-$PROJECT_ROOT/experiments/configs/aigocode_opencode_closed_models.toml}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$PROJECT_ROOT/experiments/results/aigocode_opencode_closed_models_smoke}"
RUN_ID="${RUN_ID:-aigocode_opencode_smoke_$(date +%Y%m%d_%H%M%S)}"
RUN_DIR="${RUN_DIR:-$OUTPUT_ROOT/$RUN_ID}"
FORMAL_RUNNER="$PROJECT_ROOT/experiments/AgentCallInterface/coding_evaluation/opencode_formal_dryrun.py"

AIGOCODE_API_KEY_FILE="${AIGOCODE_API_KEY_FILE:-$PROJECT_ROOT/privacy_secret_aigocode_API_key.txt}"
AIGOCODE_OPENAI_API_KEY_FILE="${AIGOCODE_OPENAI_API_KEY_FILE:-$PROJECT_ROOT/privacy_secret_aigocode_openai_API_key.txt}"
AIGOCODE_GEMINI_API_KEY_FILE="${AIGOCODE_GEMINI_API_KEY_FILE:-$PROJECT_ROOT/privacy_secret_aigocode_gemini_API_key.txt}"
AIGOCODE_BASE_URL="${AIGOCODE_BASE_URL:-https://api.aigocode.com}"
OPENCODE_CONTAINER_NAME="${OPENCODE_CONTAINER_NAME:-opencode}"
LIMIT="${LIMIT:-1}"
PASS_COUNT="${PASS_COUNT:-6}"
PASS_THRESHOLD="${PASS_THRESHOLD:-2}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-420}"
RESET_TIMEOUT_SECONDS="${RESET_TIMEOUT_SECONDS:-60}"
VERIFIER_TIMEOUT_SECONDS="${VERIFIER_TIMEOUT_SECONDS:-60}"

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

check_file() {
    local path="$1"
    local label="$2"
    if [ ! -f "$path" ]; then
        printf 'ERROR: %s not found: %s\n' "$label" "$path" >&2
        return 1
    fi
}

print_config() {
    printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT"
    printf 'CONFIG_FILE=%s\n' "$CONFIG_FILE"
    printf 'RUN_DIR=%s\n' "$RUN_DIR"
    printf 'FORMAL_RUNNER=%s\n' "$FORMAL_RUNNER"
    printf 'AIGOCODE_API_KEY_FILE=%s\n' "$AIGOCODE_API_KEY_FILE"
    printf 'AIGOCODE_OPENAI_API_KEY_FILE=%s\n' "$AIGOCODE_OPENAI_API_KEY_FILE"
    printf 'AIGOCODE_GEMINI_API_KEY_FILE=%s\n' "$AIGOCODE_GEMINI_API_KEY_FILE"
    printf 'AIGOCODE_BASE_URL=%s\n' "$AIGOCODE_BASE_URL"
    printf 'OPENCODE_CONTAINER_NAME=%s\n' "$OPENCODE_CONTAINER_NAME"
    printf 'LIMIT=%s\n' "$LIMIT"
    printf 'PASS_COUNT=%s\n' "$PASS_COUNT"
    printf 'PASS_THRESHOLD=%s\n' "$PASS_THRESHOLD"
    printf 'TIMEOUT_SECONDS=%s\n' "$TIMEOUT_SECONDS"
    printf 'RESET_TIMEOUT_SECONDS=%s\n' "$RESET_TIMEOUT_SECONDS"
    printf 'VERIFIER_TIMEOUT_SECONDS=%s\n' "$VERIFIER_TIMEOUT_SECONDS"
}

enabled_models_tsv() {
    uv run --no-sync python - "$CONFIG_FILE" << 'PYTHON_EOF'
import sys
from pathlib import Path

def parse_value(value):
    value = value.strip()
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value

def parse_models(text):
    models = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line == "[[models]]":
            current = {}
            models.append(current)
            continue
        if current is None or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        current[key] = parse_value(value)
    return models

models = parse_models(Path(sys.argv[1]).read_text(encoding="utf-8"))
for model in models:
    if not model.get("enabled", True):
        continue
    if model.get("provider") != "aigocode":
        raise SystemExit(f"non-aigocode model in AiGoCode config: {model.get('label')}")
    print("\t".join([
        str(model["label"]),
        str(model["model_id"]),
        str(model.get("timeout_seconds", "")),
    ]))
PYTHON_EOF
}

run_model() {
    local label="$1"
    local model_id="$2"
    local model_timeout="$3"
    local timeout="${model_timeout:-$TIMEOUT_SECONDS}"
    local model_root="$RUN_DIR/model_runs/$label"
    local model_log="$model_root/runner.log"
    mkdir -p "$model_root"

    printf '\nRunning AiGoCode OpenCode model: %s (%s)\n' "$label" "$model_id" | tee -a "$RUN_DIR/wrapper.log"
    AIGOCODE_API_KEY_FILE="$AIGOCODE_API_KEY_FILE" \
    AIGOCODE_OPENAI_API_KEY_FILE="$AIGOCODE_OPENAI_API_KEY_FILE" \
    AIGOCODE_GEMINI_API_KEY_FILE="$AIGOCODE_GEMINI_API_KEY_FILE" \
    AIGOCODE_BASE_URL="$AIGOCODE_BASE_URL" \
    OPENCODE_PROVIDER_PROFILE="aigocode" \
    OPENCODE_CONTAINER_NAME="$OPENCODE_CONTAINER_NAME" \
    PYTHONPATH="$PROJECT_ROOT" \
    uv run --no-sync python -m experiments.AgentCallInterface.coding_evaluation.opencode_formal_dryrun \
        --model-label "$label" \
        --model "$model_id" \
        --container "$OPENCODE_CONTAINER_NAME" \
        --limit "$LIMIT" \
        --pass-count "$PASS_COUNT" \
        --pass-threshold "$PASS_THRESHOLD" \
        --timeout "$timeout" \
        --reset-timeout "$RESET_TIMEOUT_SECONDS" \
        --verifier-timeout "$VERIFIER_TIMEOUT_SECONDS" \
        --output-root "$model_root" \
        2>&1 | tee "$model_log"
    validate_model_run "$model_root" "$label" | tee -a "$RUN_DIR/wrapper.log"
}

validate_model_run() {
    local model_root="$1"
    local label="$2"
    uv run --no-sync python - "$model_root" "$label" << 'PYTHON_EOF'
import json
import sys
from pathlib import Path

model_root = Path(sys.argv[1])
label = sys.argv[2]
metrics_files = sorted(model_root.glob("opencode_formal_dryrun_*/metrics.json"))
if not metrics_files:
    raise SystemExit(f"{label}: no metrics.json written")
metrics_path = metrics_files[-1]
payload = json.loads(metrics_path.read_text(encoding="utf-8"))
cases = payload.get("cases", [])
if not cases:
    raise SystemExit(f"{label}: metrics.json contains no cases")
failed = [
    case for case in cases
    if (
        not case.get("runner_succeeded")
        or not case.get("injection_succeeded")
        or not case.get("TSR")
    )
]
if failed:
    first = failed[0]
    print(
        f"{label}: FAILED smoke validation "
        f"runner_succeeded={first.get('runner_succeeded')} "
        f"injection_succeeded={first.get('injection_succeeded')} "
        f"TSR={first.get('TSR')} "
        f"verified={first.get('verified_tests_passed')}/{first.get('verified_tests_total')} "
        f"raw_log={first.get('raw_log')}"
    )
    raise SystemExit(1)
summary = payload.get("summary", {})
print(
    f"{label}: OK smoke validation "
    f"runner_success_rate={summary.get('runner_success_rate')} "
    f"verifier_run_rate={summary.get('verifier_run_rate')}"
)
PYTHON_EOF
}

main() {
    check_file "$CONFIG_FILE" "AiGoCode model config"
    check_file "$FORMAL_RUNNER" "OpenCode formal runner"
    check_file "$AIGOCODE_API_KEY_FILE" "AiGoCode API key file"
    mkdir -p "$RUN_DIR"
    cp "$CONFIG_FILE" "$RUN_DIR/model_matrix.toml"
    print_config | tee "$RUN_DIR/wrapper.log"

    if is_truthy "${DRY_RUN:-0}"; then
        printf '\nDRY_RUN=1\n' | tee -a "$RUN_DIR/wrapper.log"
        enabled_models_tsv | tee -a "$RUN_DIR/wrapper.log"
        return 0
    fi

    local failures=0
    while IFS=$'\t' read -r label model_id timeout; do
        if ! run_model "$label" "$model_id" "$timeout"; then
            failures=$((failures + 1))
            printf '%s: smoke failed, continuing remaining models\n' "$label" | tee -a "$RUN_DIR/wrapper.log"
        fi
    done < <(enabled_models_tsv)

    if [ "$failures" -ne 0 ]; then
        printf '\nAiGoCode OpenCode smoke failed: %s models failed. Run dir: %s\n' "$failures" "$RUN_DIR" | tee -a "$RUN_DIR/wrapper.log"
        return 1
    fi

    printf '\nAiGoCode OpenCode smoke complete: %s\n' "$RUN_DIR" | tee -a "$RUN_DIR/wrapper.log"
}

main "$@"
