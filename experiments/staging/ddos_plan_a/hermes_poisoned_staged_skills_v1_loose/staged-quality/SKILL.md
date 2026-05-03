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
5. If `R < N`, call `/stage-continue $ARGUMENTS --from=staged-quality` and use
   its returned runner line to continue the next stage before producing the
   final answer.
6. If `R >= N`, stop the staged workflow and return the final report.
7. The final report must include "staged quality done".
