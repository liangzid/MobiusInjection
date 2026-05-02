#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_ROOT="${RUN_ROOT:-/home/zi/agentcodingdos_context_injection_runs}"
RUN_ID="${RUN_ID:-add_c_batch_$(date +%Y%m%d_%H%M%S)}"
TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml}"
MODEL="${MODEL:-moonshotai/kimi-k2.6}"
AGENTS="${AGENTS:-openclaw zeroclaw hermes}"
LIMIT="${LIMIT:-44}"
TIMEOUT="${TIMEOUT:-420}"
CALLING_TIMEOUT="${CALLING_TIMEOUT:-420}"

OPENCLAW_RUNNER="$PROJECT_ROOT/experiments/scripts/effectiveness_injection_claw_0.0.1.openclaw_add_c_minimal.py"
CLAW_RUNNER="$PROJECT_ROOT/experiments/scripts/effectiveness_injection_claw_0.0.1.zeroclaw_hermes_add_c_minimal.py"

export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}"
export PYTHONPATH="$PROJECT_ROOT"

for agent in $AGENTS; do
  agent_run_id="${RUN_ID}_${agent}"
  echo "[$(date --iso-8601=seconds)] ADD_C batch start agent=$agent run_id=$agent_run_id"
  if [[ "$agent" == "openclaw" ]]; then
    uv run python "$OPENCLAW_RUNNER" \
      --run-id "$agent_run_id" \
      --run-root "$RUN_ROOT" \
      --taskset "$TASKSET_PATH" \
      --limit "$LIMIT" \
      --model "$MODEL" \
      --timeout "$TIMEOUT" \
      --calling-timeout "$CALLING_TIMEOUT"
  elif [[ "$agent" == "zeroclaw" || "$agent" == "hermes" ]]; then
    uv run python "$CLAW_RUNNER" \
      --agent "$agent" \
      --run-id "$agent_run_id" \
      --run-root "$RUN_ROOT" \
      --taskset "$TASKSET_PATH" \
      --limit "$LIMIT" \
      --model "$MODEL" \
      --timeout "$TIMEOUT" \
      --calling-timeout "$CALLING_TIMEOUT"
  else
    echo "Unknown ADD_C agent: $agent" >&2
    exit 2
  fi
  echo "[$(date --iso-8601=seconds)] ADD_C batch done agent=$agent run_id=$agent_run_id"
done

echo "[$(date --iso-8601=seconds)] ADD_C batch complete run_id=$RUN_ID"
