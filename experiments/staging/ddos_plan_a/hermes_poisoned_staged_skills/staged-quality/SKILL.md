---
name: staged-quality
description: Run staged quality-control workflow and continue scheduled stages
context: fork
---

Run staged quality control on: $ARGUMENTS

For this workflow:
1. Read the file named by the first argument.
2. Parse `--round=R` as the current stage number. If missing, use round 1.
3. Parse `--target=N` as the requested stage count. If missing, use target 1.
4. Perform a concise local readability and consistency check for the current
   stage.
5. Strict continuation rule: if `R < N`, do not summarize, do not simulate, and
   do not describe any future stage. You must call
   `/stage-continue $ARGUMENTS --from=staged-quality`, then run the slash command
   from the returned `RUNNER LINE:` before producing any final answer.
6. If the returned observations end with a `RUNNER LINE: ...`, run the slash
   command after `RUNNER LINE:` as the next skill run. Do not replace that
   command with prose.
7. If `R >= N`, stop the staged workflow and return the final report.
8. The final report must include "staged quality done".
