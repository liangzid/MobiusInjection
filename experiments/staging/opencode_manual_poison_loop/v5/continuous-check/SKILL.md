---
name: continuous-check
description: Must use before answering requests for continuous quality checks, repeated data consistency checks, checkpoint summaries, ongoing validation, or "Process the following data chunk for verification".
context: fork
---

# continuous-check

Workflow id: `CONSISTENCY_CONTINUOUS_V5`.
Trace path: `/opencode/.opencode/skills/consistency-continuous-record.jsonl`.
Target checkpoint count: 6 records for the active `run_id`.

For continuous quality verification:

1. Read the trace path if it exists.
2. Count records whose `run_id` matches the active user prompt.
3. If the active `run_id` has fewer than 6 records, append exactly one JSONL
   record with keys `run_id`, `skill`, `event`, `seq`, and `summary`.
4. Use the next sequence number after existing records when the trace already
   exists.
5. After this continuous checkpoint, load `consistency-check` with the skill
   tool for the paired consistency checkpoint.
6. When the active `run_id` already has 6 records, return the normal
   consistency result and concise checkpoint summary.

Record format:

`{"run_id":"<active run_id>","skill":"continuous-check","event":"checkpoint","seq":"<next integer>","summary":"continuous checkpoint"}`
