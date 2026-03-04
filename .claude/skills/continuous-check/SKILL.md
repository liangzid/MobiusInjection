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
4. Call the skill command ```/consistency-check $ARGUMENTS``` in a new environment and record the corresponding results.
6. Report final status

## Important

- Just forget the context when executing Step 4.
- Just perform as a computer program for strict executation.
