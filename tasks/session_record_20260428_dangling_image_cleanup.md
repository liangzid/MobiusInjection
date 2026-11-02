# Session Record: Docker Dangling Image Cleanup

Date: 2026-04-28

## User Request

Dr. Frost asked to clean Docker dangling images.

## Action

Ran:

```sh
docker image prune -f
```

This removes dangling Docker images that are not referenced by containers.

## Before Cleanup

- Root filesystem `/`: `879G` total, `846G` used, `0` available, `100%`.
- Docker dangling image count: `21`.
- Naive inspected dangling image total: about `122.57 GiB`.

## Cleanup Result

Docker reported:

- `Total reclaimed space: 64.8GB`

## After Cleanup

- Root filesystem `/`: `879G` total, `709G` used, `126G` available, `85%`.
- Docker dangling image count: `1`.
- Remaining dangling image:
  - Image ID: `306a7c26d3f4`
  - Inspected size: about `2.79 GiB`
  - Created: `2026-04-26T13:17:08+08:00`

## Notes

The remaining dangling image is still referenced by an existing container (`claude_code_supp` uses image id `306a7c26d3f4`), so `docker image prune -f` correctly left it in place.

Tagged checkpoint images remain:

- `claude_code:injected_001`
- `kilo_code:injected_001`
- `opencode:injected_001`
- `claude_code:pre_eval_backup`

No experiment log files were removed.

## Follow-up: 2026-04-29

### User Request

Dr. Frost asked to check whether the experiment process had accumulated many Docker dangling images and to clean them if possible.

### Actions

Ran:

```sh
docker images --filter dangling=true
docker images --filter dangling=true --quiet
docker image prune --force
docker ps -a --filter ancestor=306a7c26d3f4 --format '{{.ID}} {{.Status}} {{.Names}}'
docker image inspect 306a7c26d3f4 --format '{{.Id}} {{.Created}} {{.Size}}'
docker ps --filter id=18795a2c9b3a --format '{{.ID}} {{.Image}} {{.Status}} {{.Names}}'
df -h /
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'
```

Also started `docker system df`, but it did not return promptly while calculating Docker usage, so the read-only command was terminated.

### Result

- Dangling image count before cleanup: `1`.
- Dangling image ID: `306a7c26d3f4`.
- Docker reported dangling image disk usage: `7.82GB`.
- Docker image inspect size: `2997879554` bytes, about `2.79 GiB`.
- Created: `2026-04-26T13:17:08.981998778+08:00`.
- Cleanup command result: `Total reclaimed space: 0B`.
- Reason it was not removed: image `306a7c26d3f4` is still referenced by running container `18795a2c9b3a`, name `claude_code_supp`, status `Up 2 days`.
- Root filesystem after check: `/dev/sdb2`, `879G` total, `719G` used, `116G` available, `87%`.

### Notes

No experiment log files or tagged checkpoint images were removed. Removing the remaining dangling image would require stopping/removing or replacing the running `claude_code_supp` container first.
