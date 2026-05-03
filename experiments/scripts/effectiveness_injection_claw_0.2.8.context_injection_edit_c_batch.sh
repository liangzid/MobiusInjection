#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_ROOT="${RUN_ROOT:-/home/zi/agentcodingdos_context_injection_runs}"
RUN_ID="${RUN_ID:-edit_c_batch_$(date +%Y%m%d_%H%M%S)}"
TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml}"
MODEL="${MODEL:-moonshotai/kimi-k2.6}"
AGENTS="${AGENTS:-openclaw zeroclaw hermes}"
LIMIT="${LIMIT:-44}"
TIMEOUT="${TIMEOUT:-420}"
CALLING_TIMEOUT="${CALLING_TIMEOUT:-420}"

OPENCLAW_IMAGE="${OPENCLAW_IMAGE:-openclaw:edit_c_config_victim}"
ZEROCLAW_IMAGE="${ZEROCLAW_IMAGE:-zeroclaw:edit_c_config_victim}"
HERMES_IMAGE="${HERMES_IMAGE:-hermes:edit_c_config_victim}"

OPENCLAW_PAYLOAD_MODULE="${OPENCLAW_PAYLOAD_MODULE:-$PROJECT_ROOT/mobiusInjection/MI_V1_edit_c_openclaw.py}"
CLAW_PAYLOAD_MODULE="${CLAW_PAYLOAD_MODULE:-$PROJECT_ROOT/mobiusInjection/MI_V1.1_edit_c_claw_agents.py}"

OPENCLAW_RUNNER="$PROJECT_ROOT/experiments/scripts/effectiveness_injection_claw_0.0.1.openclaw_edit_c_minimal.py"
CLAW_RUNNER="$PROJECT_ROOT/experiments/scripts/effectiveness_injection_claw_0.0.1.zeroclaw_hermes_edit_c_minimal.py"

export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}"
export PYTHONPATH="$PROJECT_ROOT"

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 2
  fi
}

require_image() {
  local image="$1"
  if ! docker image inspect "$image" >/dev/null 2>&1; then
    echo "Missing required Docker image: $image" >&2
    exit 2
  fi
}

require_file "$TASKSET_PATH"
require_file "$OPENCLAW_PAYLOAD_MODULE"
require_file "$CLAW_PAYLOAD_MODULE"
require_file "$OPENCLAW_RUNNER"
require_file "$CLAW_RUNNER"

for agent in $AGENTS; do
  case "$agent" in
    openclaw) require_image "$OPENCLAW_IMAGE" ;;
    zeroclaw) require_image "$ZEROCLAW_IMAGE" ;;
    hermes) require_image "$HERMES_IMAGE" ;;
    *)
      echo "Unknown EDIT_C agent: $agent" >&2
      exit 2
      ;;
  esac
done

for agent in $AGENTS; do
  agent_run_id="${RUN_ID}_${agent}"
  echo "[$(date --iso-8601=seconds)] EDIT_C batch start agent=$agent run_id=$agent_run_id"
  if [[ "$agent" == "openclaw" ]]; then
    uv run python "$OPENCLAW_RUNNER" \
      --run-id "$agent_run_id" \
      --run-root "$RUN_ROOT" \
      --taskset "$TASKSET_PATH" \
      --limit "$LIMIT" \
      --payload-module "$OPENCLAW_PAYLOAD_MODULE" \
      --model "$MODEL" \
      --openclaw-image "$OPENCLAW_IMAGE" \
      --timeout "$TIMEOUT" \
      --calling-timeout "$CALLING_TIMEOUT"
  elif [[ "$agent" == "zeroclaw" || "$agent" == "hermes" ]]; then
    uv run python "$CLAW_RUNNER" \
      --agent "$agent" \
      --run-id "$agent_run_id" \
      --run-root "$RUN_ROOT" \
      --taskset "$TASKSET_PATH" \
      --limit "$LIMIT" \
      --payload-module "$CLAW_PAYLOAD_MODULE" \
      --model "$MODEL" \
      --zeroclaw-image "$ZEROCLAW_IMAGE" \
      --hermes-image "$HERMES_IMAGE" \
      --timeout "$TIMEOUT" \
      --calling-timeout "$CALLING_TIMEOUT"
  fi
  echo "[$(date --iso-8601=seconds)] EDIT_C batch done agent=$agent run_id=$agent_run_id"
done

echo "[$(date --iso-8601=seconds)] EDIT_C batch complete run_id=$RUN_ID"
