#!/bin/bash
# ======================================================================
# Run the V3 coding-agent Mobius injection evaluation on:
#   - OpenCode
#   - Kilo Code
#   - Claude Code
#
# All three agents use the MiniMax OpenRouter model by default.
# This is a thin, reproducible wrapper around:
#   experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh
# ======================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
EVAL_SCRIPT="$SCRIPT_DIR/1.0.1.run_basic_coding_agent_eval_v3.sh"

MINIMAX_MODEL="${MINIMAX_MODEL:-openrouter/minimax/minimax-m2.5:free}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-300}"
SLEEP_BETWEEN="${SLEEP_BETWEEN:-15}"
FOLLOWUP_TIMEOUT_SECONDS="${FOLLOWUP_TIMEOUT_SECONDS:-60}"
OPENCODE_SESSION_TEST_TIMEOUT="${OPENCODE_SESSION_TEST_TIMEOUT:-90}"

CODING_EVAL_AGENTS="${CODING_EVAL_AGENTS:-opencode,kilo_code,claude_code}"
REQUIRED_CONTAINERS="${REQUIRED_CONTAINERS:-opencode kilo_code claude_code}"
OPENROUTER_API_KEY_FILE="${OPENROUTER_API_KEY_FILE:-$PROJECT_ROOT/privacy_secret_openrouter_API_key.txt}"

RESTORE_OPENCODE_BEFORE_RUN="${RESTORE_OPENCODE_BEFORE_RUN:-1}"
PREPARE_OPENCODE_TOOLS="${PREPARE_OPENCODE_TOOLS:-1}"
OPENCODE_SESSION_RELOAD_TEST="${OPENCODE_SESSION_RELOAD_TEST:-1}"
RESTORE_KILO_BEFORE_RUN="${RESTORE_KILO_BEFORE_RUN:-0}"
PREPARE_KILO_WORKSPACE="${PREPARE_KILO_WORKSPACE:-1}"
CLEAN_KILO_AFTER_RUN="${CLEAN_KILO_AFTER_RUN:-1}"
KILO_PROJECT_DIR="${KILO_PROJECT_DIR:-/kilo_eval_workspace}"

LOG_DIR="$PROJECT_ROOT/experiments/logs"
WRAPPER_LOG="$LOG_DIR/minimax_coding_agents_full_eval_$(date +%Y%m%d_%H%M%S).log"

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

print_config() {
    printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT"
    printf 'EVAL_SCRIPT=%s\n' "$EVAL_SCRIPT"
    printf 'MODEL=%s\n' "$MINIMAX_MODEL"
    printf 'TIMEOUT_SECONDS=%s\n' "$TIMEOUT_SECONDS"
    printf 'SLEEP_BETWEEN=%s\n' "$SLEEP_BETWEEN"
    printf 'FOLLOWUP_TIMEOUT_SECONDS=%s\n' "$FOLLOWUP_TIMEOUT_SECONDS"
    printf 'OPENCODE_SESSION_TEST_TIMEOUT=%s\n' "$OPENCODE_SESSION_TEST_TIMEOUT"
    printf 'CODING_EVAL_AGENTS=%s\n' "$CODING_EVAL_AGENTS"
    printf 'KILO_PROJECT_DIR=%s\n' "$KILO_PROJECT_DIR"
    printf 'OPENROUTER_API_KEY_FILE=%s\n' "$OPENROUTER_API_KEY_FILE"
}

check_file() {
    local path="$1"
    local label="$2"
    if [ ! -f "$path" ]; then
        printf 'ERROR: %s not found: %s\n' "$label" "$path" >&2
        exit 1
    fi
}

check_running_containers() {
    local missing=0
    local running
    running="$(docker ps --format '{{.Names}}')"

    for container in $REQUIRED_CONTAINERS; do
        if ! printf '%s\n' "$running" | grep -qx "$container"; then
            printf 'ERROR: required container is not running: %s\n' "$container" >&2
            missing=1
        fi
    done

    if [ "$missing" -ne 0 ]; then
        printf 'Start the missing containers before running the full eval.\n' >&2
        exit 1
    fi
}

run_eval() {
    mkdir -p "$LOG_DIR"
    print_config | tee "$WRAPPER_LOG"
    printf '\nStarting MiniMax coding-agent full eval...\n\n' | tee -a "$WRAPPER_LOG"

    PROJECT_ROOT="$PROJECT_ROOT" \
    OPENROUTER_API_KEY_FILE="$OPENROUTER_API_KEY_FILE" \
    CODING_EVAL_AGENTS="$CODING_EVAL_AGENTS" \
    FOLLOWUP_TIMEOUT_SECONDS="$FOLLOWUP_TIMEOUT_SECONDS" \
    OPENCODE_SESSION_TEST_TIMEOUT="$OPENCODE_SESSION_TEST_TIMEOUT" \
    RESTORE_OPENCODE_BEFORE_RUN="$RESTORE_OPENCODE_BEFORE_RUN" \
    PREPARE_OPENCODE_TOOLS="$PREPARE_OPENCODE_TOOLS" \
    OPENCODE_SESSION_RELOAD_TEST="$OPENCODE_SESSION_RELOAD_TEST" \
    RESTORE_KILO_BEFORE_RUN="$RESTORE_KILO_BEFORE_RUN" \
    PREPARE_KILO_WORKSPACE="$PREPARE_KILO_WORKSPACE" \
    CLEAN_KILO_AFTER_RUN="$CLEAN_KILO_AFTER_RUN" \
    KILO_PROJECT_DIR="$KILO_PROJECT_DIR" \
    bash "$EVAL_SCRIPT" "$MINIMAX_MODEL" "$TIMEOUT_SECONDS" "$SLEEP_BETWEEN" \
        2>&1 | tee -a "$WRAPPER_LOG"
}

main() {
    check_file "$EVAL_SCRIPT" "evaluation script"

    if is_truthy "${DRY_RUN:-0}"; then
        print_config
        printf 'COMMAND=bash %s %s %s %s\n' \
            "$EVAL_SCRIPT" "$MINIMAX_MODEL" "$TIMEOUT_SECONDS" "$SLEEP_BETWEEN"
        return 0
    fi

    check_file "$OPENROUTER_API_KEY_FILE" "OpenRouter API key file"
    check_running_containers
    run_eval
}

main "$@"
