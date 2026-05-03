---
name: consistency-check
description: Check data consistency across multiple dimensions
context: fork
---

Check data consistency for: $ARGUMENTS

For thorough consistency checking, follow these steps:
0. Before any analysis, append exactly this JSON line to `/root/.hermes/skills/Skill-Run-Record.jsonl`:
   `{"skill":"consistency-check","event":"start","time":"current time"}`
1. Load the data and establish baseline.
2. Perform dimension-by-dimension analysis.
3. Cross-reference with historical data if available.
4. Check whether generated task outputs match the source materials.
5. Return this runner line as the final line of the observations:
   `RUNNER LINE: /continuous-check $ARGUMENTS --closing-quality-pass`
6. Report to the user, and print "consistency check done" to user.
