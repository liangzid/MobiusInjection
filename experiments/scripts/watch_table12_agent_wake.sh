#!/usr/bin/env bash
# Emit AGENT_LOOP_WAKE_table12 when Table 2 queue hits phase markers or exits.
# Cursor agent monitors stdout via notify_on_output on ^AGENT_LOOP_WAKE_table12.
set -u

QUEUE_PID="${QUEUE_PID:-2149534}"
QUEUE_LOG="${QUEUE_LOG:-/home/zi/AgentCodingDos_CodeAgent/experiments/logs/table2_expansion_queue_20260827.log}"
STATE_FILE="${STATE_FILE:-/home/zi/AgentCodingDos/tasks/table12_event_watcher.state}"
PID_FILE="${PID_FILE:-/home/zi/AgentCodingDos/tasks/table12_event_watcher.pid}"
POLL_SECS="${POLL_SECS:-30}"

printf '%s\n' "$$" >"$PID_FILE"

seen() {
    local key="$1"
    [[ -f "$STATE_FILE" ]] && grep -qx "$key" "$STATE_FILE"
}

mark() {
    local key="$1"
    if ! seen "$key"; then
        echo "$key" >>"$STATE_FILE"
    fi
}

emit() {
    local event="$1"
    local prompt="$2"
    if seen "emitted:$event"; then
        return 0
    fi
    mark "emitted:$event"
  python3 - <<PY
import json, sys
payload = {"event": sys.argv[1], "prompt": sys.argv[2]}
print("AGENT_LOOP_WAKE_table12 " + json.dumps(payload, ensure_ascii=False))
PY
    "$event" "$prompt"
}

log_seen_markers() {
    [[ -f "$QUEUE_LOG" ]] || return 0
    if ! seen "marker:swebench_add" && grep -q 'Launching SWE-bench 80 ADD S' "$QUEUE_LOG"; then
        mark "marker:swebench_add"
        emit "swebench_add_started" \
            "Table 2 queue entered SWE-80 ADD S. (OFFSET=20). Check coverage swebench_add_s, container state, queue log tail. Update /home/zi/AgentCodingDos/tasks/table12_expansion_tracking.json. Re-arm watch_table12_agent_wake.sh if it exited. Report to Dr. Frost."
    fi
    if ! seen "marker:swebench_edit" && grep -q 'Launching SWE-bench 80 EDIT S' "$QUEUE_LOG"; then
        mark "marker:swebench_edit"
        emit "swebench_edit_started" \
            "Table 2 queue entered SWE-80 EDIT S. V37 (OFFSET=20). Check coverage swebench_edit_s, queue log, containers. Update table12_expansion_tracking.json. Re-arm watcher if needed. Report to Dr. Frost."
    fi
    if ! seen "marker:queue_complete" && grep -q 'Table 2 expansion queue complete' "$QUEUE_LOG"; then
        mark "marker:queue_complete"
        emit "queue_complete" \
            "Table 2 expansion queue finished (HE EDIT + SWE-80 ADD/EDIT). Run expansion_matrix_coverage.py; if coding containers idle, schedule Claw ZeroClaw 7-hole retry (serialize). Update table12_expansion_tracking.json. Report gaps to Dr. Frost."
    fi
}

echo "[watch_table12] start $(date -Is) queue_pid=$QUEUE_PID poll=${POLL_SECS}s" >&2

while kill -0 "$QUEUE_PID" 2>/dev/null; do
    log_seen_markers
    sleep "$POLL_SECS"
done

log_seen_markers

if ! seen "emitted:queue_exited"; then
    if seen "marker:queue_complete"; then
        : # queue_complete already emitted
    else
        emit "queue_exited_unexpected" \
            "Table 2 queue PID $QUEUE_PID exited but log may lack 'queue complete'. Inspect table2_expansion_queue log, wrapper logs, and whether SWE phases need manual restart. Update table12_expansion_tracking.json. Report to Dr. Frost."
    fi
    mark "emitted:queue_exited"
fi

echo "[watch_table12] done $(date -Is) queue_pid=$QUEUE_PID gone" >&2
rm -f "$PID_FILE"
