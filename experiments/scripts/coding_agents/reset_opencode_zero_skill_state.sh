#!/bin/bash
# Reset the OpenCode project workspace to a zero-skill state for add-skill experiments.

set -euo pipefail

OPENCODE_CONTAINER="${OPENCODE_CONTAINER:-opencode}"
OPENCODE_PROJECT_DIR="${OPENCODE_PROJECT_DIR:-/opencode}"
DRY_RUN="${DRY_RUN:-0}"
VERIFY_DEBUG_SKILL="${VERIFY_DEBUG_SKILL:-1}"

EXPERIMENT_SKILL_NAMES=(
    "integrity-sync"
    "performance-audit"
    "explain-code"
)

SKILL_ROOTS=(
    ".opencode/skills"
    ".agents/skills"
    ".claude/skills"
    ".kilo/skills"
    ".kilocode/skills"
    "skills"
    "skill"
)

RUNTIME_ARTIFACTS=(
    "sync-check-record.jsonl"
    "mobius-loop-trace.jsonl"
    "*ledger*.jsonl"
    "*trace*.jsonl"
    "explain-code-status-ledger.jsonl"
    "integrity-sync-ledger.jsonl"
    "performance-audit-ledger.jsonl"
)

INSTRUCTION_HOOKS=(
    "AGENTS.md"
    "CLAUDE.md"
    ".opencode/AGENTS.md"
    ".opencode/instructions.md"
    ".opencode/instructions"
)

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

quote_join() {
    local item
    for item in "$@"; do
        printf ' %q' "$item"
    done
}

print_config() {
    printf 'OPENCODE_CONTAINER=%s\n' "$OPENCODE_CONTAINER"
    printf 'OPENCODE_PROJECT_DIR=%s\n' "$OPENCODE_PROJECT_DIR"
    printf 'DRY_RUN=%s\n' "$DRY_RUN"
    printf 'VERIFY_DEBUG_SKILL=%s\n' "$VERIFY_DEBUG_SKILL"
    printf 'SKILL_ROOTS=%s\n' "$(quote_join "${SKILL_ROOTS[@]}")"
    printf 'RUNTIME_ARTIFACTS=%s\n' "$(quote_join "${RUNTIME_ARTIFACTS[@]}")"
    printf 'INSTRUCTION_HOOKS=%s\n' "$(quote_join "${INSTRUCTION_HOOKS[@]}")"
}

require_docker() {
    command -v docker >/dev/null || {
        printf 'ERROR: docker is not available\n' >&2
        exit 1
    }
}

require_running_container() {
    docker ps --format '{{.Names}}' | grep -Fxq "$OPENCODE_CONTAINER" || {
        printf 'ERROR: required container is not running: %s\n' "$OPENCODE_CONTAINER" >&2
        exit 1
    }
}

reset_workspace() {
    if is_truthy "$DRY_RUN"; then
        printf 'DRY_RUN: would remove OpenCode skill roots, runtime artifacts, and instruction hooks\n'
        return 0
    fi

    docker exec -e "OPENCODE_PROJECT_DIR=$OPENCODE_PROJECT_DIR" \
        "$OPENCODE_CONTAINER" bash -lc "$(cat <<'RESET_SCRIPT'
set -euo pipefail
project_dir="${OPENCODE_PROJECT_DIR:?}"
mkdir -p "$project_dir"
cd "$project_dir"
rm -rf \
    .opencode/skills \
    .agents/skills \
    .claude/skills \
    .kilo/skills \
    .kilocode/skills \
    skills \
    skill
rm -f \
    sync-check-record.jsonl \
    mobius-loop-trace.jsonl \
    explain-code-status-ledger.jsonl \
    integrity-sync-ledger.jsonl \
    performance-audit-ledger.jsonl \
    AGENTS.md \
    CLAUDE.md \
    .opencode/AGENTS.md \
    .opencode/instructions.md \
    .opencode/instructions
find . -maxdepth 1 -type f \( -name '*ledger*.jsonl' -o -name '*trace*.jsonl' \) -delete
RESET_SCRIPT
)"
    printf 'Reset OpenCode project workspace to zero-skill state: %s:%s\n' \
        "$OPENCODE_CONTAINER" "$OPENCODE_PROJECT_DIR"
}

verify_skill_roots_clean() {
    if is_truthy "$DRY_RUN"; then
        printf 'DRY_RUN: would verify skill roots are absent or empty\n'
        return 0
    fi

    docker exec -e "OPENCODE_PROJECT_DIR=$OPENCODE_PROJECT_DIR" \
        "$OPENCODE_CONTAINER" bash -lc "$(cat <<'VERIFY_SCRIPT'
set -euo pipefail
project_dir="${OPENCODE_PROJECT_DIR:?}"
cd "$project_dir"
for root in \
    .opencode/skills \
    .agents/skills \
    .claude/skills \
    .kilo/skills \
    .kilocode/skills \
    skills \
    skill
do
    if [ -d "$root" ] && find "$root" -mindepth 1 -print -quit | grep -q .; then
        printf 'ERROR: skill root is not empty: %s/%s\n' "$project_dir" "$root" >&2
        exit 1
    fi
done
VERIFY_SCRIPT
)"
    printf 'Verified OpenCode skill roots are absent or empty.\n'
}

verify_artifacts_clean() {
    if is_truthy "$DRY_RUN"; then
        printf 'DRY_RUN: would verify runtime artifacts and instruction hooks are absent\n'
        return 0
    fi

    docker exec -e "OPENCODE_PROJECT_DIR=$OPENCODE_PROJECT_DIR" \
        "$OPENCODE_CONTAINER" bash -lc "$(cat <<'VERIFY_SCRIPT'
set -euo pipefail
project_dir="${OPENCODE_PROJECT_DIR:?}"
cd "$project_dir"
for path in \
    sync-check-record.jsonl \
    mobius-loop-trace.jsonl \
    explain-code-status-ledger.jsonl \
    integrity-sync-ledger.jsonl \
    performance-audit-ledger.jsonl \
    AGENTS.md \
    CLAUDE.md \
    .opencode/AGENTS.md \
    .opencode/instructions.md \
    .opencode/instructions
do
    if [ -e "$path" ]; then
        printf 'ERROR: stale runtime artifact or instruction hook remains: %s/%s\n' "$project_dir" "$path" >&2
        exit 1
    fi
done
if find . -maxdepth 1 -type f \( -name '*ledger*.jsonl' -o -name '*trace*.jsonl' \) -print -quit | grep -q .; then
    printf 'ERROR: stale ledger or trace JSONL remains under %s\n' "$project_dir" >&2
    find . -maxdepth 1 -type f \( -name '*ledger*.jsonl' -o -name '*trace*.jsonl' \) -print >&2
    exit 1
fi
VERIFY_SCRIPT
)"
    printf 'Verified OpenCode runtime artifacts and instruction hooks are absent.\n'
}

verify_debug_skill_clean() {
    if ! is_truthy "$VERIFY_DEBUG_SKILL"; then
        printf 'Skipped OpenCode debug skill verification.\n'
        return 0
    fi
    if is_truthy "$DRY_RUN"; then
        printf 'DRY_RUN: would run opencode debug skill and verify experiment skill names are absent\n'
        return 0
    fi

    docker exec -e "OPENCODE_PROJECT_DIR=$OPENCODE_PROJECT_DIR" \
        "$OPENCODE_CONTAINER" bash -lc "$(cat <<'VERIFY_SCRIPT'
set -euo pipefail
project_dir="${OPENCODE_PROJECT_DIR:?}"
cd "$project_dir"
/root/.opencode/bin/opencode debug skill > /tmp/opencode-zero-skill-debug.json
for skill_name in integrity-sync performance-audit explain-code; do
    if grep -Fq "\"name\": \"$skill_name\"" /tmp/opencode-zero-skill-debug.json ||
       grep -Fq "name: $skill_name" /tmp/opencode-zero-skill-debug.json; then
        printf 'ERROR: opencode debug skill still lists experiment skill: %s\n' "$skill_name" >&2
        cat /tmp/opencode-zero-skill-debug.json >&2
        exit 1
    fi
done
cat /tmp/opencode-zero-skill-debug.json
VERIFY_SCRIPT
)"
    printf 'Verified opencode debug skill does not list experiment skills.\n'
}

main() {
    print_config
    if ! is_truthy "$DRY_RUN"; then
        require_docker
        require_running_container
    fi
    reset_workspace
    verify_skill_roots_clean
    verify_artifacts_clean
    verify_debug_skill_clean
    printf 'OpenCode zero-skill reset complete.\n'
}

main "$@"
