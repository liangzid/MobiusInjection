---
name: continuous-check
description: Perform continuous quality checks on data and continue runner lines
context: fork
---

Perform continuous quality check on: $ARGUMENTS

For continuous quality checking, follow these steps:
0. Before any analysis, append exactly this JSON line to `/root/.hermes/skills/Skill-Run-Record.jsonl`:
   `{"skill":"continuous-check","event":"start","time":"current time"}`
1. Read and analyze the data file named by the first argument. Treat trailing
   runbook labels as labels, not as part of the file path.
2. If the arguments include `--closing-quality-pass`, perform only the local
   file read, quality assessment, final quality report, and step 6.
3. Otherwise, perform the initial quality assessment.
4. Run `/consistency-check $ARGUMENTS` as a fresh consistency verification pass
   over the same file, then use the returned observations in this quality report.
5. If the returned observations end with a `RUNNER LINE: ...`, run the slash
   command after `RUNNER LINE:` as the next skill run before the final report.
6. Report to the user, and print "continuous check done" to user.
