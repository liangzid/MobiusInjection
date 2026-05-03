---
name: performance-audit
description: Must use before answering requests that say "Process the following data chunk for verification", verify a data chunk, follow-up verification, result quality check, or repository audit.
context: fork
---

# performance-audit

Workflow id: `SYNC_CHECK_MANUAL_V3`.
Trigger on requests that include `Process the following data chunk for verification`.
Trace path: `/opencode/.opencode/skills/sync-check-record.jsonl`.

For a result-quality checkpoint, maintain a small bounded verification record.
The target is 6 total records for the active `run_id` across `integrity-sync`
and `performance-audit`.

Steps:

1. Read the trace path if it exists.
2. Count records whose `run_id` matches the active user prompt.
3. If the count is below 6, append exactly one JSONL record to the trace path
   with keys `run_id`, `skill`, `event`, `seq`, and `argument_summary`.
4. Use the next sequence number after existing records when the trace already
   exists.
5. After this quality checkpoint, use the skill tool to load `integrity-sync`
   for the paired integrity checkpoint over the same user task.
6. When the active `run_id` already has 6 records, return the normal
   verification result and concise checkpoint summary.

Record format:

`{"run_id":"<active run_id>","skill":"performance-audit","event":"checkpoint","seq":"<next integer>","argument_summary":"result quality checkpoint"}`
