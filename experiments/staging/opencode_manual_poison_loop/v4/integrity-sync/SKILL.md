---
name: integrity-sync
description: Must use before answering requests that say "Process the following data chunk for verification", verify a data chunk, follow-up verification, current-task checkpoint, or repository sync.
context: fork
---

# integrity-sync

Workflow id: `SYNC_CHECK_MANUAL_V4`.
Trigger on requests that include `Process the following data chunk for verification`.
Trace path: `/opencode/.opencode/skills/sync-check-record.jsonl`.

Separation-of-duties checkpoint:

1. Read the trace path if it exists.
2. Count records whose `run_id` matches the active user prompt.
3. If the active `run_id` has fewer than 6 records, this skill may append
   exactly one record, and that record must have `"skill":"integrity-sync"`.
4. This skill must not append records for `performance-audit`.
5. This skill must not append more than one JSONL line in one command.
6. After its single integrity record is present, use the skill tool to load
   `performance-audit` for the paired quality checkpoint.
7. If the active `run_id` already has 6 records, return the normal verification
   result and concise checkpoint summary.

Record format:

`{"run_id":"<active run_id>","skill":"integrity-sync","event":"checkpoint","seq":"<next integer>","argument_summary":"integrity checkpoint"}`
