#!/usr/bin/env bash
# Build clean targeted environment images for the Mobius 4x4 targeted ADD_S run.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MODEL_A="${MODEL_A:-moonshotai/kimi-k2.6}"
MODEL_B="${MODEL_B:-qwen/qwen3.5-plus-20260420}"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

json_b64() {
    python3 - "$@" <<'PY'
import base64
import json
import sys

profile, agent, provider, model, resource, surface = sys.argv[1:7]
payload = {
    "profile": profile,
    "agent": agent,
    "provider": provider,
    "model": model,
    "resource": resource,
    "surface": surface,
}
print(base64.b64encode(json.dumps(payload, sort_keys=True).encode()).decode())
PY
}

prepare_container() {
    local container="$1"
    local agent="$2"
    local env_b64="$3"
    docker exec -e TARGET_ENV_JSON_B64="$env_b64" "$container" bash -lc '
        set -euo pipefail
        rm -f /tmp/mobius_target_activation_trace.jsonl /tmp/mobius_target_cancel_trace.jsonl
        printf %s "$TARGET_ENV_JSON_B64" | base64 -d > /tmp/mobius_target_env.json
        chmod 644 /tmp/mobius_target_env.json
    '

    case "$agent" in
        openclaw)
            docker exec "$container" bash -lc '
                rm -rf /root/.openclaw/skills/consistency-check /root/.openclaw/skills/continuous-check
                rm -f /root/.openclaw/skills/Skill-Run-Record.jsonl
                mkdir -p /root/.openclaw/skills
            '
            ;;
        zeroclaw)
            docker exec "$container" bash -lc '
                rm -rf /root/.zeroclaw/skills/consistency-check /root/.zeroclaw/skills/continuous-check
                rm -rf /root/.zeroclaw/workspace/.zeroclaw/workspace/skills/consistency-check
                rm -rf /root/.zeroclaw/workspace/.zeroclaw/workspace/skills/continuous-check
                rm -f /root/.zeroclaw/skills/Skill-Run-Record.jsonl
                mkdir -p /root/.zeroclaw
            '
            ;;
        hermes)
            docker exec "$container" bash -lc '
                rm -rf /root/.hermes/skills/consistency-check /root/.hermes/skills/continuous-check
                rm -f /root/.hermes/skills/Skill-Run-Record.jsonl
                mkdir -p /root/.hermes/skills
            '
            ;;
        *)
            echo "Unsupported agent: $agent" >&2
            exit 1
            ;;
    esac
}

build_one() {
    local profile="$1"
    local agent="$2"
    local provider="$3"
    local model="$4"
    local resource="$5"
    local surface="$6"
    local base_image="$7"
    local target_image="$8"
    local container="targeted_build_${profile,,}_$$"
    local env_b64

    log "Building $target_image from $base_image ($profile)"
    docker image inspect "$base_image" >/dev/null
    docker rm -f "$container" >/dev/null 2>&1 || true
    docker run -d --name "$container" --entrypoint bash "$base_image" -lc 'sleep infinity' >/dev/null
    env_b64="$(json_b64 "$profile" "$agent" "$provider" "$model" "$resource" "$surface")"
    prepare_container "$container" "$agent" "$env_b64"
    docker commit "$container" "$target_image" >/dev/null
    docker rm -f "$container" >/dev/null
    log "Built $target_image"
}

main() {
    cd "$PROJECT_ROOT"
    build_one E1 openclaw openrouter "$MODEL_A" target-mcp-a ADD_S \
        openclaw:mobius_eval_config_fixed_20260421 openclaw:targeted-e1
    build_one E2 zeroclaw openrouter "$MODEL_A" target-mcp-a ADD_S \
        zeroclaw:pre_eval_backup zeroclaw:targeted-e2
    build_one E3 hermes openrouter "$MODEL_A" openrouter-api ADD_S \
        hermes:pre_eval_backup hermes:targeted-e3
    build_one E4 openclaw openrouter "$MODEL_B" target-mcp-b ADD_S \
        openclaw:mobius_eval_config_fixed_20260421 openclaw:targeted-e4
}

main "$@"
