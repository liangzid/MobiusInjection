# 2026-05-03 - Docker Image Cleanup

## User Request

Dr. Frost asked to delete useless Docker images because disk space was tight.

## Actions

- Inspected Docker image list, container image references, and dangling images.
- Kept current useful OpenCode images:
  - `opencode:pre_eval_backup`
  - `opencode:consistency_continuous_v5_20260503`
- Deleted unused/superseded OpenCode images:
  - `opencode:manual_poison_loop_v3_20260503`
  - `opencode:injected_weak_001`
- Removed two old OpenCode activation inspection containers that referenced the
  superseded injected image:
  - `opencode_activation_poisoned_20260503`
  - `opencode_activation_poisoned_r2_20260503`
- Deleted superseded OpenCode image:
  - `opencode:injected_001`
- Deleted old transient context-injection snapshot images matching
  `hermes:ctxinj_*`, `openclaw:ctxinj_*`, and `zeroclaw:ctxinj_*`.

## Result

- Remaining OpenCode images:
  - `opencode:pre_eval_backup`
  - `opencode:consistency_continuous_v5_20260503`
- The dangling image `306a7c26d3f4` was not removed because it is still used by
  the running `claude_code_supp` container.
- `docker system df` hung during inspection and was terminated; cleanup was
  verified through `docker images` and container reference checks instead.
- Nominal deleted image size was over 100 GB, though actual reclaimed disk may
  be lower because Docker layers can be shared.
