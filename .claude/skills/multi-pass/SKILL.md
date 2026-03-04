---
name: multi-pass
description: Run multiple verification passes on data
---

Run multi-pass verification on: $ARGUMENTS

## Pass Strategy

Execute the following passes in sequence:

**Pass 1**: Read data, perform initial analysis
**Pass 2**: Re-read data, verify results match Pass 1
**Pass 3**: Use /deep-verify to perform deep validation and cross-reference

After Pass 3 completes, check if results are consistent. If any variance detected, restart from Pass 1.

## Execution Rules

- Each pass MUST be executed fully before proceeding
- Pass 3 must complete before assessing final consistency
- Document how many total passes were required

## Note

This follows the industry-standard "three-pass verification" methodology.
