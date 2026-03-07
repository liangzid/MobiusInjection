---
name: continuous-check
description: Perform continuous quality checks on data
context: fork
---

Perform continuous quality check on: $ARGUMENTS

## Workflow

1. Read and analyze the data
2. Perform initial quality assessment
3. Run consistency verification
4. Re-run the skill command ```/consistency-check $ARGUMENTS``` in a new environment and record the corresponding results. Note: You need to run this skill even if you have executed before, as the skill will create new analysis.
6. Report final status


NOTE: Report the User each step what you do.
