#!/usr/bin/env bash
# If a live ZeroClaw eval already recorded All providers/models failed (3/3),
# drop the container so the runner does not sit out the remaining timeout.
set -euo pipefail

WATCH_PIDS="${WATCH_PIDS:-1915220 1944535}"
CLAW_LOGS="${CLAW_LOGS:-/home/zi/agentcodingdos_context_injection_runs/logs}"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

any_watch_alive() {
    local pid
    for pid in $WATCH_PIDS; do
        kill -0 "$pid" 2>/dev/null && return 0
    done
    return 1
}

failed_live_container() {
    python3 - "$CLAW_LOGS" <<'PY'
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys

logs = Path(sys.argv[1])
raw = subprocess.check_output(
    ["docker", "ps", "--format", "{{.Names}}"], text=True
).splitlines()
names = [name for name in raw if name]
now = datetime.now(timezone.utc)

def container_started(name: str) -> datetime | None:
    try:
        out = subprocess.check_output(
            ["docker", "inspect", "-f", "{{.State.StartedAt}}", name],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        return None
    # 2026-08-27T08:09:30.123456789Z
    out = out.replace("Z", "+00:00")
    if "." in out:
        head, rest = out.split(".", 1)
        frac, tz = rest.split("+", 1)
        frac = (frac + "000000")[:6]
        out = f"{head}.{frac}+{tz}"
    try:
        return datetime.fromisoformat(out)
    except ValueError:
        return None

def comms(name: str) -> list[str] | None:
    # docker top requires a PID column; a missing PID aborts the inspect.
    try:
        out = subprocess.check_output(
            ["docker", "top", name, "-eo", "pid,comm"], text=True
        )
    except subprocess.CalledProcessError:
        return None
    procs = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            procs.append(parts[-1])
        elif parts:
            procs.append(parts[0])
    return procs

printed = set()

# Primary: after 3/3 fail ZeroClaw exits and only sleep infinity remains.
# Host stderr.txt is often still the previous attempt until docker exec returns.
# If docker top fails, do not treat the container as exhausted.
for name in names:
    if name in printed:
        continue
    if "zeroclaw" not in name or "calling" in name:
        continue
    started = container_started(name)
    if started is None:
        continue
    if (now - started).total_seconds() < 45:
        continue
    procs = comms(name)
    if procs is None:
        continue
    if any("zeroclaw" in proc for proc in procs):
        continue
    print(name)
    printed.add(name)

for stderr in logs.rglob("stderr.txt"):
    if "reopened_calling" in stderr.parts:
        continue
    try:
        text = stderr.read_text(encoding="utf-8", errors="replace")
        mtime = datetime.fromtimestamp(stderr.stat().st_mtime, tz=timezone.utc)
    except OSError:
        continue
    if "All providers/models failed" not in text:
        continue
    if "attempt 3/3" not in text and "3/3" not in text:
        continue
    parts = stderr.parts
    try:
        poisoned = parts.index("poisoned")
    except ValueError:
        continue
    task_id = parts[poisoned - 1]
    agent = parts[poisoned - 2]
    if agent != "zeroclaw":
        continue
    for name in names:
        if name in printed:
            continue
        if "zeroclaw" not in name or task_id not in name or "calling" in name:
            continue
        started = container_started(name)
        if started is None:
            continue
        # Ignore stale 3/3 text from a previous attempt.
        if mtime < started:
            continue
        print(name)
        printed.add(name)
PY
}

log "Watching ZeroClaw 3/3 provider failures; pids $WATCH_PIDS"
while any_watch_alive; do
    while IFS= read -r name; do
        [[ -z "$name" ]] && continue
        log "Removing exhausted ZeroClaw container $name"
        docker rm -f "$name" >/dev/null 2>&1 || true
    done < <(failed_live_container || true)
    sleep 10
done
log "Watch pids exited; watchdog done"
