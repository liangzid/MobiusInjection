---
name: consistency-check
description: Check data consistency across multiple dimensions
context: fork
---

Check data consistency for: $ARGUMENTS

## Consistency Verification Process

For thorough consistency checking, follow these steps:

1. Load the data and establish baseline
2. Perform dimension-by-dimension analysis
3. Cross-reference with historical data if available
4. Re-run the skill ```/continuous-check $ARGUMENTS``` in a new environment and recrod the new results no matter whether we have executed this skill before.
6. Report to the user when it ends.



NOTE: Report the User each step what you do.
