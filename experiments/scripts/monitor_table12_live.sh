#!/usr/bin/env bash
# Live monitor for Table 1/2 expansion. Unbuffered-friendly; drops
# ZeroClaw eval containers past runner timeout so the serial queue advances.
set -u

HE_RUN2_PID="${HE_RUN2_PID:-217430}"
QUEUE_PID="${QUEUE_PID:-2149534}"
FOLLOWUP_PID="${FOLLOWUP_PID:-1983385}"
ADD_S_WAITER_PID="${ADD_S_WAITER_PID:-2106892}"
WATCHDOG_PID="${WATCHDOG_PID:-2109324}"
POLLS="${POLLS:-30}"
SLEEP_SECS="${SLEEP_SECS:-90}"
CODE_ROOT="${CODE_ROOT:-/home/zi/AgentCodingDos_CodeAgent}"
FOLLOWUP_LOG="${FOLLOWUP_LOG:-/home/zi/AgentCodingDos/tasks/zeroclaw_remaining_empty_followup_20260827.log}"

echo "=== monitor start $(date -Is) ==="
for i in $(seq 1 "$POLLS"); do
  echo "--- poll $i $(date '+%H:%M:%S') ---"
  for p in "$HE_RUN2_PID" "$QUEUE_PID" "$FOLLOWUP_PID" "$ADD_S_WAITER_PID" "$WATCHDOG_PID"; do
    if kill -0 "$p" 2>/dev/null; then s=up; else s=down; fi
    printf ' %s=%s' "$p" "$s"
  done
  echo
  docker ps --format '{{.Names}}' | grep -E '^ctx_|opencode$|kilo_code$|claude_code$' | grep -v queue_poison | tr '\n' ' '
  echo

  python3 - <<'PY'
from pathlib import Path
import re
import importlib.util

code = Path("/home/zi/AgentCodingDos_CodeAgent")
kroot = code / "experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_kilo_20_97_20260827/models/openrouter_qwen_qwen3.6-plus/logs"
done = []
if kroot.exists():
    for p in kroot.glob("humaneval_HumanEval_*_kilo_code_output.txt"):
        m = re.search(r"HumanEval_(\d+)_kilo_code", p.name)
        if m and p.stat().st_size >= 200:
            done.append(int(m.group(1)))
root = code / "experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_offset20_limit144_20260827_run2/models/openrouter_qwen_qwen3.6-plus/logs"

def mx(agent: str):
    nums = [
        int(m.group(1))
        for p in root.glob(f"humaneval_HumanEval_*_{agent}_output.txt")
        if (m := re.search(rf"HumanEval_(\d+)_{agent}", p.name))
    ]
    return (max(nums) if nums else None, len(nums))

print(
    "kilo2097",
    len(done),
    "max",
    max(done) if done else None,
    "OC",
    mx("opencode"),
    "CC",
    mx("claude_code"),
)
w = (code / "experiments/logs/humaneval_model_benchmark/qwen36_v10_humaneval_offset20_limit144_20260827_run2/wrapper.log").read_text(errors="replace")
print("wrapper_done", "Benchmark run complete" in w)
spec = importlib.util.spec_from_file_location(
    "cov", code / "experiments/scripts/expansion_matrix_coverage.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
rep = m.report()
print("HE_add", rep["sections"]["humaneval_add_s"]["valid"], "claw_new", rep["sections"]["claw_new_28"])
ids = m.load_new_task_ids()
holes = []
for strat in m.CLAW_STRATEGIES:
    for agent in m.CLAW_AGENTS:
        for tid in ids:
            st = m.claw_cell_status(
                m.CLAW_NEW_DIRS[(strat, agent)],
                agent,
                tid,
                require_nonempty_stdout=True,
            )
            if st != "valid":
                holes.append(f"{strat}/{agent}/{tid}")
print("holes", len(holes), *holes)
PY

  name=$(docker ps --format '{{.Names}}' | grep zeroclaw | grep -v calling | head -1 || true)
  if [[ -n "$name" ]]; then
    echo "live=$name"
    docker top "$name" -eo pid,etime,comm 2>/dev/null | tail -n +2 || true
    docker exec "$name" sh -c 'c=$(ls -d /tmp/mobius_zeroclaw_eval_config /tmp/zeroclaw-eval-config.* 2>/dev/null | head -1); wc -l $c/workspace/state/costs.jsonl 2>/dev/null; tail -c 100 $c/workspace/state/costs.jsonl 2>/dev/null; echo' 2>/dev/null || echo exec_fail
    python3 - "$name" <<'PY'
import subprocess
import sys
from datetime import datetime, timezone

name = sys.argv[1]
out = subprocess.check_output(
    ["docker", "inspect", "-f", "{{.State.StartedAt}}", name], text=True
).strip().replace("Z", "+00:00")
if "." in out:
    head, rest = out.split(".", 1)
    frac, tz = rest.split("+", 1)
    frac = (frac + "000000")[:6]
    out = f"{head}.{frac}+{tz}"
elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(out)).total_seconds()
try:
    top = subprocess.check_output(
        ["docker", "top", name, "-eo", "pid,comm"], text=True
    )
except subprocess.CalledProcessError:
    print("elapsed_s", round(elapsed), "top_failed")
    raise SystemExit(0)
procs = [ln.split()[-1] for ln in top.splitlines()[1:] if ln.strip()]
has_zc = any("zeroclaw" in p for p in procs)
print("elapsed_s", round(elapsed), "has_zeroclaw", has_zc, "procs", procs)
# Runner timeout is 900+20; force-drop so the serial parent can continue.
if elapsed >= 960:
    subprocess.call(["docker", "rm", "-f", name])
    print("removed_past_timeout", name)
elif elapsed >= 45 and not has_zc:
    subprocess.call(["docker", "rm", "-f", name])
    print("removed_exhausted", name)
PY
  else
    echo no_ctx
    tail -n 4 "$FOLLOWUP_LOG" 2>/dev/null || true
  fi

  docker top kilo_code -eo pid,etime,comm 2>/dev/null | awk 'NR>1' | head -5 || true
  sleep "$SLEEP_SECS"
done
echo "=== monitor done $(date -Is) ==="
