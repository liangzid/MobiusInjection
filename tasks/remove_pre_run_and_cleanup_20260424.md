## Task

Remove poisoned `pre_run` checkpoints, stop the old `0.2` ADD_S batch run that was still creating them, and clean old/minimal context-injection artifacts while preserving `clean` variants.

## Files

- `/home/zi/AgentCodingDos/experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh`
- `/home/zi/AgentCodingDos/experiments/AgentCallInterface/tests/test_context_injection_add_s.py`
- `/home/zi/AgentCodingDos/tasks/remove_pre_run_and_cleanup_20260424.md`

## What I changed

1. Patched the `0.2` runner so it no longer commits `pre_run` images.
2. Updated the focused regression test to assert that `pre_run` checkpoint storage stays disabled.
3. Stopped the old batch process `add_s_eval_plan_a_20260424_1530`, because it had been started before the script fix and was still creating poisoned `pre_run` images.
4. Removed poisoned checkpoint images from:
   - minimal ADD_S runs on `2026-04-24`
   - pre-V3.6 context-injection experiments
   - interrupted `Plan A` poisoned `pre_run` images
5. Removed minimal-category ADD_S experiment artifacts from:
   - `logs/`
   - `container_exports/`
   - `verifier_results/`
   - `manifests/`
6. Preserved `clean` variants.

## Results

- Removed containers: `1`
- Removed images: `163`
- Removed filesystem paths: `32`
- Remaining non-clean `ctxinj` images after cleanup: `2`
  - `openclaw:ctxinj_add_s_eval_plan_a_20260424_1530_doc001_poisoned_post_run`
  - `openclaw:ctxinj_add_s_eval_plan_a_20260424_1530_xdom001_poisoned_post_run`

## Validation

- `uv run pytest experiments/AgentCallInterface/tests/test_context_injection_add_s.py experiments/AgentCallInterface/tests/test_mi_v36_add_s.py -q`
- `bash -n experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh`
- `env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=/home/zi/AgentCodingDos uv run python -m py_compile experiments/AgentCallInterface/context_injection_add_s.py`
- `docker images --format '{{.Repository}}:{{.Tag}}' | rg 'ctxinj_' | rg -v '_clean_'`
- `df -h / /home /data`
- `docker system df`

## Notes

`/` remained effectively full after this targeted cleanup, so the remaining pressure is not only from the removed poisoned checkpoint set. The biggest remaining directly-related artifacts visible afterward were the two interrupted `Plan A` poisoned `post_run` images above.
