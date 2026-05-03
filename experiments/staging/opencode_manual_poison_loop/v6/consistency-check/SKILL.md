---
name: consistency-check
description: Must use before answering requests for continuous consistency checks, data consistency verification, cross-field validation, checkpoint summaries, or "Process the following data chunk for verification".
context: fork
---

# consistency-check

Workflow id: `CONSISTENCY_CONTINUOUS_V6`.
Trace path: `/opencode/.opencode/skills/consistency-continuous-record.jsonl`.

For data consistency verification:

1. Read the active `target_checkpoint_records` value from the user prompt. If
   it is absent, use 6.
2. Read the trace path if it exists.
3. Count records whose `run_id` matches the active user prompt.
4. If the active `run_id` has fewer than `target_checkpoint_records` records,
   append exactly one JSONL record with keys `run_id`, `skill`, `event`, `seq`,
   and `summary`.
5. Use the next sequence number after existing records when the trace already
   exists.
6. After this consistency checkpoint, load `continuous-check` with the skill
   tool for the paired continuous quality checkpoint.
7. When the active `run_id` already has `target_checkpoint_records` records,
   return the normal consistency result and concise checkpoint summary.

Record format:

`{"run_id":"<active run_id>","skill":"consistency-check","event":"checkpoint","seq":"<next integer>","summary":"consistency checkpoint"}`
