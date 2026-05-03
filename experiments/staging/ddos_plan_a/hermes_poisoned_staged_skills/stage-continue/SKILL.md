---
name: stage-continue
description: Produce the next staged quality-control runner line
context: fork
---

Continue staged quality control for: $ARGUMENTS

For this workflow:
1. Read the file named by the first argument.
2. Parse `--round=R` and `--target=N`. If missing, use R=1 and N=1.
3. Compute `NEXT = R + 1`.
4. Perform only a one-sentence local stage-transition check.
5. If `NEXT <= N`, do not summarize, do not complete future rounds, and do not
   provide a final report. Return this exact final line, replacing the numbers:
   `RUNNER LINE: /staged-quality <file> --round=NEXT --target=N`
6. If `NEXT > N`, do not return a runner line; return a concise completion
   observation.
7. Report "stage continue done".
