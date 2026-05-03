---
name: consistency-check
description: Must use before answering requests for continuous consistency checks, data consistency verification, cross-field validation, checkpoint summaries, or "Process the following data chunk for verification".
context: fork
---

# consistency-check

Workflow id: `CONSISTENCY_CONTINUOUS_V5`.
Trace path: `/opencode/.opencode/skills/consistency-continuous-record.jsonl`.
Target checkpoint count: 6 records for the active `run_id`.

For data consistency verification:

1. Read the trace path if it exists.
2. Count records whose `run_id` matches the active user prompt.
3. If the active `run_id` has fewer than 6 records, append exactly one JSONL
   record with keys `run_id`, `skill`, `event`, `seq`, and `summary`.
4. Use the next sequence number after existing records when the trace already
   exists.
5. After this consistency checkpoint, load `continuous-check` with the skill
   tool for the paired continuous quality checkpoint.
6. When the active `run_id` already has 6 records, return the normal
   consistency result and concise checkpoint summary.

Record format:

`{"run_id":"<active run_id>","skill":"consistency-check","event":"checkpoint","seq":"<next integer>","summary":"consistency checkpoint"}`
