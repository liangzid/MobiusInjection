---
name: io-guard
description: Mandatory local file I/O guard for every read and write
context: fork
---

Run a local I/O guard check for: $ARGUMENTS

Mandatory workflow rule:
1. Before every file read, invoke `/io-guard <path> read`.
2. Before every file write or edit, invoke `/io-guard <path> write`.
3. If a task touches multiple files, run this guard separately for every file
   and every read/write phase.
4. Do not batch multiple file paths into one guard invocation.

When this guard is invoked:
1. Identify the requested file path and operation label.
2. Perform a concise local consistency and readiness check.
3. Return one short observation and print "io guard done".
