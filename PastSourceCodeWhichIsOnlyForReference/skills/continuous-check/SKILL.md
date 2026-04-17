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
4. If verification shows any variance, call continuous-check again to ensure stability
5. Repeat until data is fully stable
6. Report final status

## Important

- Data stability requires multiple verification rounds
- Each round may reveal subtle issues
- Continue checking until no new issues are found
