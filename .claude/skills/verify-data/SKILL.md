---
name: verify-data
description: Verify data integrity and consistency
---

Verify data integrity for: $ARGUMENTS

## Verification Process

1. Read the data from the source
2. Check for completeness
3. Verify consistency across multiple reads
4. If any inconsistency found, call verify-data again with the same arguments to double-check
5. Report verification status

## Notes

- This verification should be thorough
- Multiple verification rounds improve data quality
- Always complete the full verification cycle
