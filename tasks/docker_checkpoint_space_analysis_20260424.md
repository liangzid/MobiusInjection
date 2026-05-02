## Task

- User asked to analyze whether root-disk pressure is mainly caused by Docker resources.
- User also asked whether removing `pre-run` checkpoints would have any meaningful downside.

## Files Reviewed

- `experiments/scripts/effectivenss_injection_claw_0.2.context_injection_add_s.sh`

## Commands Run

- `df -h`
- `docker system df`
- `docker system df -v`
- `docker images --format '{{.Repository}}\t{{.Tag}}'`
- `docker ps --size --format '{{.Names}} {{.Size}}'`
- `docker volume ls -q | wc -l`
- `docker info | rg -n "Docker Root Dir|Storage Driver"`

## Findings

- Root filesystem `/` had only `2.6G` available at the time of analysis.
- Docker total usage:
  - Images: `693.1GB`
  - Containers: `179.8GB`
  - Local Volumes: `83.36GB`
- The dominant avoidable pressure is Docker images, not the currently running experiment container layer.
- Experiment checkpoint images are numerous:
  - total `ctxinj_*` images: `181`
  - by repo:
    - `openclaw`: `79`
    - `hermes`: `50`
    - `zeroclaw`: `52`
- Split by checkpoint phase:
  - `openclaw`: `38` pre-run, `37` post-run
  - `hermes`: `23` pre-run, `23` post-run
  - `zeroclaw`: `22` pre-run, `22` post-run
- Typical unique-size cost per checkpoint image from `docker system df -v`:
  - OpenClaw: about `936.8MB` pre-run and `937.1MB` post-run
  - Hermes: about `2.924GB` pre-run and `2.978GB` to `2.999GB` post-run
  - ZeroClaw: about `261.4MB` pre-run and `261.5MB` post-run

## Interpretation

- Removing pre-run checkpoints would not affect TSR/P-ASR computation.
- The runner still keeps:
  - `pre_state` capture
  - `post_state` capture
  - exported workspace
  - verifier results
  - post-run checkpoint
- The current script uses pre-run checkpoints only to:
  - save the image
  - record its tag in the result manifest
- There is no downstream logic that requires the pre-run image to compute success metrics or injection detection.

## Tradeoff

- Removing pre-run checkpoints has little to no effect on evaluation correctness.
- The real loss is forensic convenience:
  - you lose the ability to restart an image at the exact staged-pre-execution state
  - later container-level diffing or replay becomes less convenient
- For metrics and ordinary log-based analysis, pre-run checkpoints are not necessary.

## Practical Conclusion

- Yes, Docker is the immediate root-space problem.
- More specifically, our repeated checkpoint images are a major avoidable contributor.
- Removing pre-run checkpoints is the cleanest low-risk way to roughly halve checkpoint-image growth for future runs.
- But with only `2.6G` free on `/`, that change alone is not enough to save the currently full root partition unless old checkpoint images are also cleaned up.
