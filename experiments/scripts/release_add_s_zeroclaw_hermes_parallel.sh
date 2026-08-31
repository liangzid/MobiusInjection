#!/usr/bin/env bash
# After ADD S. run2 OpenClaw finishes the 28 new tasks, stop the serial
# openclaw→zeroclaw→hermes parent and run ZeroClaw + Hermes in parallel.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/zi/AgentCodingDos}"
RUN_ID="${RUN_ID:-add_s_plan_a_newtasks_qwen36_20260827_run2}"
RUN_ROOT="${RUN_ROOT:-/home/zi/agentcodingdos_context_injection_runs}"
ADD_S_PID="${ADD_S_PID:-719939}"
ADD_S_BASH_PID="${ADD_S_BASH_PID:-719960}"
TASK_ID_FILE="${TASK_ID_FILE:-$PROJECT_ROOT/tasks/claw_plan_a_new_task_ids.txt}"
TASKSET_PATH="${TASKSET_PATH:-$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml}"
MODEL_NAME="${MODEL_NAME:-qwen/qwen3.6-plus}"
LOG_DIR="$RUN_ROOT/logs/$RUN_ID"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

openclaw_counts() {
    python3 - "$LOG_DIR" <<'PY'
import json, sys
from pathlib import Path
log = Path(sys.argv[1])

def n(path, agent):
    p = log / path
    if not p.exists():
        return 0
    count = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("agent") == agent:
            count += 1
    return count

print(n("results.jsonl", "openclaw"), n("calling_results.jsonl", "openclaw"))
print(n("results.jsonl", "zeroclaw"), n("calling_results.jsonl", "zeroclaw"))
print(n("results.jsonl", "hermes"), n("calling_results.jsonl", "hermes"))
PY
}

openclaw_containers() {
    docker ps --format '{{.Names}}' | grep -c "ctx_${RUN_ID}_openclaw" || true
}

launch_agent() {
    local agent="$1"
    local log_file="$PROJECT_ROOT/tasks/add_s_${agent}_newtasks_20260827.log"
    TASK_IDS="$(grep -v '^#' "$TASK_ID_FILE" | grep -v '^$' | tr '\n' ' ')"
    log "Launching ADD S. $agent RUN_ID=$RUN_ID"
    nohup env -u OPENROUTER_API_KEY \
      PROJECT_ROOT="$PROJECT_ROOT" \
      TASKSET_PATH="$TASKSET_PATH" \
      TASK_IDS="$TASK_IDS" \
      MODEL_NAME="$MODEL_NAME" \
      TIMEOUT_SECONDS=900 \
      CALLING_TIMEOUT_SECONDS=180 \
      AGENTS="$agent" \
      VARIANTS=poisoned \
      RUN_ID="$RUN_ID" \
      bash "$PROJECT_ROOT/experiments/scripts/effectivenss_injection_claw_0.2.5.context_injection_add_s_calling.sh" \
      > "$log_file" 2>&1 &
    echo $!
}

log "Waiting for OpenClaw ADD S. run2 to finish 28 results+calling"
while true; do
    counts="$(openclaw_counts)"
    oc_res="$(printf '%s\n' "$counts" | awk 'NR==1{print $1}')"
    oc_call="$(printf '%s\n' "$counts" | awk 'NR==1{print $2}')"
    zc_res="$(printf '%s\n' "$counts" | awk 'NR==2{print $1}')"
    hm_res="$(printf '%s\n' "$counts" | awk 'NR==3{print $1}')"
    oc_docker="$(openclaw_containers)"
    log "openclaw results=$oc_res calling=$oc_call docker=$oc_docker zeroclaw=$zc_res hermes=$hm_res"
    if [[ "${zc_res:-0}" -gt 0 || "${hm_res:-0}" -gt 0 ]]; then
        log "Serial parent already started ZeroClaw/Hermes; not killing it"
        exit 0
    fi
    # Results+calling are enough; do not wait for docker cleanup (that is
    # when the serial loop would start zeroclaw).
    if [[ "${oc_res:-0}" -ge 28 && "${oc_call:-0}" -ge 28 ]]; then
        break
    fi
    if [[ "${oc_res:-0}" -ge 27 ]]; then
        sleep 3
    else
        sleep 15
    fi
done

if docker ps --format '{{.Names}}' | grep -q "ctx_${RUN_ID}_zeroclaw"; then
    log "ZeroClaw container already running from serial parent; not launching duplicates"
    exit 0
fi

hermes_pid="$(launch_agent hermes)"
log "ADD S. hermes pid=$hermes_pid"
for _ in $(seq 1 60); do
    if grep -q 'Running agent=hermes' "$PROJECT_ROOT/tasks/add_s_hermes_newtasks_20260827.log" 2>/dev/null; then
        break
    fi
    sleep 5
done
zeroclaw_pid="$(launch_agent zeroclaw)"
log "ADD S. zeroclaw pid=$zeroclaw_pid"

log "Stopping serial parent $ADD_S_BASH_PID / $ADD_S_PID so it does not start ZeroClaw"
if kill -0 "$ADD_S_BASH_PID" 2>/dev/null; then
    kill "$ADD_S_BASH_PID" || true
fi
if kill -0 "$ADD_S_PID" 2>/dev/null; then
    kill "$ADD_S_PID" || true
fi
log "Released ADD S. ZeroClaw/Hermes in parallel"
