#!/usr/bin/env bash
# Run a 5-task targeted probe, then launch the 44-task full batch if any
# diagonal cell has non-zero P-ASR.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUN_ROOT="${TARGETED_RUN_ROOT:-/home/zi/agentcodingdos_targeted_runs}"
STAMP="${STAMP:-$(date +%Y%m%d_%H%M%S)}"
PROBE_RUN_ID="${PROBE_RUN_ID:-targeted_5task_probe_${STAMP}}"
FULL_RUN_ID="${FULL_RUN_ID:-targeted_44task_full_${STAMP}}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-900}"

PROBE_TASKSET="$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_5task_tmp.toml"
FULL_TASKSET="$PROJECT_ROOT/experiments/configs/context_injection_add_s_taskset_plan_a.toml"
RUNNER="$PROJECT_ROOT/experiments/scripts/targeted_mobius_0.0.1.run_4x4_smoke.py"
PLOTTER="$PROJECT_ROOT/experiments/scripts/targeted_mobius_0.1.0.plot_4x4_matrix.py"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

diagonal_has_success() {
    local results_jsonl="$1"
    python3 - "$results_jsonl" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
diag = [row for row in rows if row["target_profile"] == row["env_profile"]]
successes = [row for row in diag if row.get("p_asr")]
print(f"diagonal_successes={len(successes)}/{len(diag)}")
raise SystemExit(0 if successes else 1)
PY
}

main() {
    cd "$PROJECT_ROOT"
    log "Starting 5-task targeted probe: $PROBE_RUN_ID"
    python3 "$RUNNER" \
        --run-id "$PROBE_RUN_ID" \
        --taskset "$PROBE_TASKSET" \
        --task-ids ALL \
        --repeats 1 \
        --timeout "$TIMEOUT_SECONDS"
    python3 "$PLOTTER" "$RUN_ROOT/logs/$PROBE_RUN_ID/targeted_metrics.json" \
        --out "$RUN_ROOT/logs/$PROBE_RUN_ID/targeted_4x4_heatmap.svg"

    log "Checking diagonal P-ASR in probe"
    if diagonal_has_success "$RUN_ROOT/logs/$PROBE_RUN_ID/targeted_results.jsonl"; then
        log "Probe has non-zero diagonal P-ASR; starting 44-task full batch: $FULL_RUN_ID"
        python3 "$RUNNER" \
            --run-id "$FULL_RUN_ID" \
            --taskset "$FULL_TASKSET" \
            --task-ids ALL \
            --repeats 1 \
            --timeout "$TIMEOUT_SECONDS"
        python3 "$PLOTTER" "$RUN_ROOT/logs/$FULL_RUN_ID/targeted_metrics.json" \
            --out "$RUN_ROOT/logs/$FULL_RUN_ID/targeted_4x4_heatmap.svg"
        log "Full batch completed: $RUN_ROOT/logs/$FULL_RUN_ID"
    else
        log "Probe diagonal P-ASR is all zero; full batch not started."
        exit 2
    fi
}

main "$@"
