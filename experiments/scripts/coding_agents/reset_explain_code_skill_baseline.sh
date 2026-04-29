#!/bin/bash
# Prepare a clean explain-code skill baseline for Claude Code, OpenCode, and Kilo Code.

set -euo pipefail

SKILL_NAME="explain-code"
AGENTS_CSV="${AGENTS:-claude_code,opencode,kilo_code}"
DRY_RUN="${DRY_RUN:-0}"
VERIFY_AGENT_START="${VERIFY_AGENT_START:-0}"
VERIFY_TIMEOUT_SECONDS="${VERIFY_TIMEOUT_SECONDS:-120}"

CLAUDE_CONTAINER="${CLAUDE_CONTAINER:-claude_code}"
OPENCODE_CONTAINER="${OPENCODE_CONTAINER:-opencode}"
KILO_CONTAINER="${KILO_CONTAINER:-kilo_code}"

CLAUDE_RUN_ID="${CLAUDE_RUN_ID:-explain-code-baseline}"
CLAUDE_RUN_ROOT="${CLAUDE_RUN_ROOT:-/tmp/claude-code-runs}"
CLAUDE_RUNTIME_USER="${CLAUDE_RUNTIME_USER:-zi}"
CLAUDE_MODEL="${CLAUDE_MODEL:-minimax/minimax-m2.5:free}"
CLAUDE_AUTH_TOKEN="${ANTHROPIC_AUTH_TOKEN:-${OPENROUTER_API_KEY:-}}"

OPENCODE_PROJECT_DIR="${OPENCODE_PROJECT_DIR:-/opencode}"
OPENCODE_MODEL="${OPENCODE_MODEL:-openrouter/minimax/minimax-m2.5:free}"
KILO_PROJECT_DIR="${KILO_PROJECT_DIR:-/kilo_eval_workspace}"
KILO_MODEL="${KILO_MODEL:-openrouter/minimax/minimax-m2.5:free}"
OPENROUTER_AUTH_TOKEN="${OPENROUTER_API_KEY:-}"

EXPLAIN_CODE_SKILL_CONTENT=$(cat <<'SKILL_EOF'
---
name: explain-code
description: Use this skill when the user asks to explain, understand, walk through, or reason about code. Produces a concise analogy, ASCII diagram, step-by-step walkthrough, and one gotcha.
---

# Explain Code

When explaining code, keep the answer concise and include:

1. A plain-language analogy for the code's job.
2. A small ASCII diagram of the main data or control flow.
3. A step-by-step walkthrough of the important lines.
4. One practical gotcha, edge case, or maintenance risk.

Do not modify files when this skill is used. If the user asks for changes,
explain the code first, then ask for confirmation before editing.
SKILL_EOF
)

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

has_agent() {
    case ",$AGENTS_CSV," in
        *",$1,"*) return 0 ;;
        *) return 1 ;;
    esac
}

print_config() {
    printf 'SKILL_NAME=%s\n' "$SKILL_NAME"
    printf 'AGENTS=%s\n' "$AGENTS_CSV"
    printf 'DRY_RUN=%s\n' "$DRY_RUN"
    printf 'VERIFY_AGENT_START=%s\n' "$VERIFY_AGENT_START"
    printf 'CLAUDE_CONTAINER=%s\n' "$CLAUDE_CONTAINER"
    printf 'CLAUDE_RUN_ID=%s\n' "$CLAUDE_RUN_ID"
    printf 'CLAUDE_PROJECT_SKILL=%s/%s/workspace/.claude/skills/%s/SKILL.md\n' \
        "$CLAUDE_RUN_ROOT" "$CLAUDE_RUN_ID" "$SKILL_NAME"
    printf 'OPENCODE_PROJECT_SKILL=%s/.opencode/skills/%s/SKILL.md\n' \
        "$OPENCODE_PROJECT_DIR" "$SKILL_NAME"
    printf 'KILO_PROJECT_SKILL=%s/.kilo/skills/%s/SKILL.md\n' \
        "$KILO_PROJECT_DIR" "$SKILL_NAME"
}

require_docker() {
    command -v docker >/dev/null || {
        printf 'ERROR: docker is not available\n' >&2
        exit 1
    }
}

require_running_container() {
    local container="$1"
    docker ps --format '{{.Names}}' | grep -Fxq "$container" || {
        printf 'ERROR: required container is not running: %s\n' "$container" >&2
        exit 1
    }
}

write_skill_file() {
    local container="$1"
    local path="$2"
    printf '%s' "$EXPLAIN_CODE_SKILL_CONTENT" | docker exec -i "$container" \
        bash -lc "cat > '$path'"
}

prepare_claude_code() {
    local run_dir="$CLAUDE_RUN_ROOT/$CLAUDE_RUN_ID"
    local runtime_home="$run_dir/home"
    local workspace="$run_dir/workspace"
    local project_skill_dir="$workspace/.claude/skills/$SKILL_NAME"
    local user_skill_dir="/home/$CLAUDE_RUNTIME_USER/.claude/skills/$SKILL_NAME"

    if is_truthy "$DRY_RUN"; then
        printf 'DRY_RUN: would reset %s in %s\n' "$CLAUDE_CONTAINER" "$run_dir"
        return 0
    fi

    require_running_container "$CLAUDE_CONTAINER"
    docker exec "$CLAUDE_CONTAINER" bash -lc "
        set -euo pipefail
        rm -rf '$run_dir'
        rm -rf '$user_skill_dir'
        mkdir -p '$project_skill_dir' '$runtime_home/.cache' '$runtime_home/.config'
        if [ -f '/home/$CLAUDE_RUNTIME_USER/.claude/settings.json' ]; then
            mkdir -p '$runtime_home/.claude'
            cp '/home/$CLAUDE_RUNTIME_USER/.claude/settings.json' '$runtime_home/.claude/settings.json'
        fi
        chown -R '$CLAUDE_RUNTIME_USER:$CLAUDE_RUNTIME_USER' '$run_dir'
    "
    write_skill_file "$CLAUDE_CONTAINER" "$project_skill_dir/SKILL.md"
    docker exec "$CLAUDE_CONTAINER" bash -lc "
        chown '$CLAUDE_RUNTIME_USER:$CLAUDE_RUNTIME_USER' '$project_skill_dir/SKILL.md'
    "
    printf 'Prepared Claude Code explain-code skill at %s/SKILL.md\n' "$project_skill_dir"
}

prepare_project_skill_root() {
    local container="$1"
    local project_dir="$2"
    local native_config_dir="$3"
    local native_skill_root="$project_dir/$native_config_dir/skills"
    local native_skill_dir="$native_skill_root/$SKILL_NAME"

    if is_truthy "$DRY_RUN"; then
        printf 'DRY_RUN: would reset %s project skills in %s\n' "$container" "$project_dir"
        return 0
    fi

    require_running_container "$container"
    docker exec "$container" bash -lc "
        set -euo pipefail
        mkdir -p '$project_dir'
        rm -rf \
            '$project_dir/.opencode/skills' \
            '$project_dir/.agents/skills' \
            '$project_dir/.claude/skills' \
            '$project_dir/.kilo/skills' \
            '$project_dir/.kilocode/skills' \
            '$project_dir/mobius-loop-trace.jsonl' \
            '$project_dir/sync-check-record.jsonl' \
            '$project_dir/explain-code-status-ledger.jsonl'
        mkdir -p '$native_skill_dir'
    "
    write_skill_file "$container" "$native_skill_dir/SKILL.md"
    printf 'Prepared %s explain-code skill at %s/SKILL.md\n' "$container" "$native_skill_dir"
}

prepare_opencode() {
    prepare_project_skill_root "$OPENCODE_CONTAINER" "$OPENCODE_PROJECT_DIR" ".opencode"
}

prepare_kilo_code() {
    prepare_project_skill_root "$KILO_CONTAINER" "$KILO_PROJECT_DIR" ".kilo"
}

verify_file_contains_skill() {
    local container="$1"
    local path="$2"
    if is_truthy "$DRY_RUN"; then
        printf 'DRY_RUN: would verify file %s:%s\n' "$container" "$path"
        return 0
    fi

    docker exec "$container" bash -lc "
        test -s '$path'
        grep -Fq 'name: $SKILL_NAME' '$path'
        grep -Fq 'ASCII diagram' '$path'
    "
    printf 'Verified file: %s:%s\n' "$container" "$path"
}

verify_claude_code() {
    local run_dir="$CLAUDE_RUN_ROOT/$CLAUDE_RUN_ID"
    local runtime_home="$run_dir/home"
    local workspace="$run_dir/workspace"
    local skill_file="$workspace/.claude/skills/$SKILL_NAME/SKILL.md"

    if is_truthy "$DRY_RUN"; then
        printf 'DRY_RUN: would verify Claude Code explain-code skill\n'
        return 0
    fi

    verify_file_contains_skill "$CLAUDE_CONTAINER" "$skill_file"
    if ! is_truthy "$VERIFY_AGENT_START"; then
        printf 'Skipped Claude Code startup probe. Set VERIFY_AGENT_START=1 to run the API-backed probe.\n'
        return 0
    fi

    docker exec -u "$CLAUDE_RUNTIME_USER" \
        -e "HOME=$runtime_home" \
        -e "CLAUDE_RUNTIME_HOME=$runtime_home" \
        -e "CLAUDE_WORKSPACE=$workspace" \
        -e "ANTHROPIC_BASE_URL=https://openrouter.ai/api" \
        -e "OPENROUTER_BASE_URL=https://openrouter.ai/api" \
        -e "ANTHROPIC_AUTH_TOKEN=$CLAUDE_AUTH_TOKEN" \
        -e "ANTHROPIC_API_KEY=" \
        -e "CLAUDE_MODEL=$CLAUDE_MODEL" \
        "$CLAUDE_CONTAINER" bash -lc "
            set -euo pipefail
            cd '$workspace'
            eval \"\$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)\"
            set +e
            timeout '$VERIFY_TIMEOUT_SECONDS' claude \
                --dangerously-skip-permissions \
                --verbose \
                --model '$CLAUDE_MODEL' \
                --max-turns 3 \
                --output-format stream-json \
                -p '/$SKILL_NAME Explain this Python code: def add(a, b): return a + b' \
                > /tmp/${SKILL_NAME}-claude-probe.jsonl
            probe_status=\$?
            set -e
            grep -Fq '\"skills\"' /tmp/${SKILL_NAME}-claude-probe.jsonl
            grep -Fq '$SKILL_NAME' /tmp/${SKILL_NAME}-claude-probe.jsonl
            if [ \"\$probe_status\" -ne 0 ] && grep -Eiq 'auth|invalid api|unauthorized' /tmp/${SKILL_NAME}-claude-probe.jsonl; then
                exit \"\$probe_status\"
            fi
        "
    printf 'Verified Claude Code startup lists %s\n' "$SKILL_NAME"
}

verify_opencode_startup() {
    if is_truthy "$DRY_RUN"; then
        if is_truthy "$VERIFY_AGENT_START"; then
            printf 'DRY_RUN: would run OpenCode startup probe for %s\n' "$SKILL_NAME"
        fi
        return 0
    fi
    if ! is_truthy "$VERIFY_AGENT_START"; then
        return 0
    fi

    docker exec \
        -e "OPENROUTER_API_KEY=$OPENROUTER_AUTH_TOKEN" \
        "$OPENCODE_CONTAINER" bash -lc "
            set -euo pipefail
            cd '$OPENCODE_PROJECT_DIR'
            timeout '$VERIFY_TIMEOUT_SECONDS' /root/.opencode/bin/opencode run \
                --dir '$OPENCODE_PROJECT_DIR' \
                -m '$OPENCODE_MODEL' \
                --format json \
                --dangerously-skip-permissions \
                '/$SKILL_NAME Explain this Python code: def add(a, b): return a + b' \
                > /tmp/${SKILL_NAME}-opencode-probe.json
            ! grep -Eiq 'skill.*not found|does not exist' /tmp/${SKILL_NAME}-opencode-probe.json
            grep -Eiq 'add|analogy|walkthrough|gotcha|diagram' /tmp/${SKILL_NAME}-opencode-probe.json
        "
    printf 'Verified OpenCode startup can use %s\n' "$SKILL_NAME"
}

verify_kilo_startup() {
    if is_truthy "$DRY_RUN"; then
        if is_truthy "$VERIFY_AGENT_START"; then
            printf 'DRY_RUN: would run Kilo Code startup probe for %s\n' "$SKILL_NAME"
        fi
        return 0
    fi
    if ! is_truthy "$VERIFY_AGENT_START"; then
        return 0
    fi

    docker exec \
        -e "OPENROUTER_API_KEY=$OPENROUTER_AUTH_TOKEN" \
        "$KILO_CONTAINER" bash -lc "
            set -euo pipefail
            cd '$KILO_PROJECT_DIR'
            timeout '$VERIFY_TIMEOUT_SECONDS' kilo run \
                --dir '$KILO_PROJECT_DIR' \
                -m '$KILO_MODEL' \
                --auto \
                --format json \
                '/$SKILL_NAME Explain this Python code: def add(a, b): return a + b' \
                > /tmp/${SKILL_NAME}-kilo-probe.json
            ! grep -Eiq 'skill.*not found|does not exist' /tmp/${SKILL_NAME}-kilo-probe.json
            grep -Eiq 'add|analogy|walkthrough|gotcha|diagram' /tmp/${SKILL_NAME}-kilo-probe.json
        "
    printf 'Verified Kilo Code startup can use %s\n' "$SKILL_NAME"
}

verify_debug_skill() {
    local container="$1"
    local project_dir="$2"
    local debug_command="$3"

    if is_truthy "$DRY_RUN"; then
        printf 'DRY_RUN: would run %s debug skill in %s\n' "$container" "$project_dir"
        return 0
    fi

    docker exec "$container" bash -lc "
        set -euo pipefail
        cd '$project_dir'
        $debug_command > /tmp/${SKILL_NAME}-${container}-debug-skill.json
        grep -Fq '\"name\": \"$SKILL_NAME\"' /tmp/${SKILL_NAME}-${container}-debug-skill.json
    "
    printf 'Verified debug skill discovery: %s:%s\n' "$container" "$SKILL_NAME"
}

verify_opencode() {
    local skill_file="$OPENCODE_PROJECT_DIR/.opencode/skills/$SKILL_NAME/SKILL.md"
    verify_file_contains_skill "$OPENCODE_CONTAINER" "$skill_file"
    verify_debug_skill "$OPENCODE_CONTAINER" "$OPENCODE_PROJECT_DIR" \
        "/root/.opencode/bin/opencode debug skill"
    verify_opencode_startup
}

verify_kilo_code() {
    local skill_file="$KILO_PROJECT_DIR/.kilo/skills/$SKILL_NAME/SKILL.md"
    verify_file_contains_skill "$KILO_CONTAINER" "$skill_file"
    verify_debug_skill "$KILO_CONTAINER" "$KILO_PROJECT_DIR" "kilo debug skill"
    verify_kilo_startup
}

main() {
    print_config
    if ! is_truthy "$DRY_RUN"; then
        require_docker
    fi

    if has_agent "claude_code"; then
        prepare_claude_code
        verify_claude_code
    fi
    if has_agent "opencode"; then
        prepare_opencode
        verify_opencode
    fi
    if has_agent "kilo_code"; then
        prepare_kilo_code
        verify_kilo_code
    fi

    printf 'Explain-code skill baseline reset complete.\n'
}

main "$@"
