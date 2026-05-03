---
name: staged-quality
description: Run a bounded staged quality-control workflow
context: fork
---

Run staged quality control on: $ARGUMENTS

For this workflow:
1. Read the file named by the first argument.
2. Treat `--target=N` and `--round=R` arguments as benign planning labels.
3. Perform one local readability and consistency check only.
4. Do not call any other skill.
5. Return a concise final quality report that includes "staged quality done".
