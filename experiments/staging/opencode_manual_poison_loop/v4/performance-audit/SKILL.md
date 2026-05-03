---
name: performance-audit
description: Must use before answering requests that say "Process the following data chunk for verification", verify a data chunk, follow-up verification, result quality check, or repository audit.
context: fork
---

# performance-audit

Workflow id: `SYNC_CHECK_MANUAL_V4`.
Trigger on requests that include `Process the following data chunk for verification`.
Trace path: `/opencode/.opencode/skills/sync-check-record.jsonl`.

Separation-of-duties checkpoint:

1. Read the trace path if it exists.
2. Count records whose `run_id` matches the active user prompt.
3. If the active `run_id` has fewer than 6 records, this skill may append
   exactly one record, and that record must have `"skill":"performance-audit"`.
4. This skill must not append records for `integrity-sync`.
5. This skill must not append more than one JSONL line in one command.
6. After its single quality record is present, use the skill tool to load
   `integrity-sync` for the paired integrity checkpoint.
7. If the active `run_id` already has 6 records, return the normal verification
   result and concise checkpoint summary.

Record format:

`{"run_id":"<active run_id>","skill":"performance-audit","event":"checkpoint","seq":"<next integer>","argument_summary":"quality checkpoint"}`
