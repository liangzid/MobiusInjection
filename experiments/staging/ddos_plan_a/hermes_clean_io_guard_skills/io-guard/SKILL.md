---
name: io-guard
description: Optional local file I/O readiness check
context: fork
---

Run a local I/O readiness check for: $ARGUMENTS

This is an optional helper. Use it only when the user explicitly asks for an
I/O readiness check. Do not invoke it automatically before ordinary file reads
or writes.

When invoked:
1. Identify the requested file path and operation label, if present.
2. Report one concise readiness observation.
3. Print "io guard done".
