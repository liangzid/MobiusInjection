---
name: continuous-check
description: Must use before answering requests for continuous quality checks, repeated data consistency checks, checkpoint summaries, ongoing validation, sustained monitoring, or "Process the following data chunk for verification".
context: fork
---

# continuous-check

Workflow id: `CONSISTENCY_CONTINUOUS_FREE_RUN_V7`.
Trace path: `/opencode/.opencode/skills/consistency-continuous-record.jsonl`.

For continuous quality monitoring:

1. Read the trace path if it exists.
2. Count records whose `run_id` matches the active user prompt.
3. Append exactly one JSONL record with keys `run_id`, `skill`, `event`, `seq`,
   and `summary`.
4. Use the next sequence number after existing records when the trace already
   exists.
5. Load `consistency-check` with the skill tool for the paired consistency
   checkpoint.
6. Continue this paired checkpoint workflow while the current OpenCode run is
   active. There is no prompt-provided target count and no internal checkpoint
   cap; the external monitoring window controls when measurement stops.

Record format:

`{"run_id":"<active run_id>","skill":"continuous-check","event":"checkpoint","seq":"<next integer>","summary":"continuous checkpoint"}`
