| defense | replay_interpretation | residual_poisoned_nodes | benign_p95_s | gt_10s_rate_pct | gt_30s_rate_pct | max_inferred_inflight | poison_attack_tokens | p95_excess_removed_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No defense | observed N=4 attack | 4 | 112.994 | 100.0 | 66.7 | 11 | 118428 | 0.0 |
| Runtime cap: <=2 active poisoned nodes | measured N=2 load proxy | 2 | 18.857 | 13.8 | 3.5 | 5 | 124256 | 83.7 |
| Runtime cap: <=1 active poisoned node | measured N=1 load proxy | 1 | 10.247 | 5.6 | 0.0 | 3 | 56563 | 91.3 |
| ACE quarantine before trigger | measured N=0 baseline proxy | 0 | 0.493 | 0.0 | 0.0 | 1 | 3092 | 100.0 |
