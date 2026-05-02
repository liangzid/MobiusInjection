# Docker space inventory - 2026-04-24

## User request

Check whether the root filesystem has many Docker dangling images (`<none>:<none>`) and identify the main Docker image/storage space consumers.

## Scope

- Working directory: `/home/zi/AgentCodingDos`
- Local timestamp: `2026-04-24 19:24:15 HKT`
- This was a read-only inventory. No Docker images, containers, volumes, or files were deleted.

## Commands run

- `df -h /`
- `docker system df`
- `docker images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'`
- `docker images --filter dangling=true --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'`
- `docker images --filter dangling=true -q | wc -l`
- `docker images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}' | sort -k3 -hr | head -30`
- `docker images --filter dangling=true --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}' | sort -k3 -hr | head -40`
- `docker ps -a --format '{{.ID}} {{.Image}} {{.Status}} {{.Names}}'`
- `docker ps --size --format '{{.ID}} {{.Image}} {{.Size}} {{.Names}}'`
- `docker volume ls -q | wc -l`

## Key results

- Root filesystem `/`: 879G total, 756G used, 78G available, 91% used.
- Docker system summary:
  - Images: 928 total, 11 active, reported virtual size 610.7GB.
  - Containers: 24 total, all active, writable layer size 85.75GB.
  - Local volumes: 74 total, 15 active, 84.95GB total, 82.23GB reclaimable.
  - Build cache: 0B.
- Dangling image count: 873.

## Largest named images by `docker images` display size

- `ghcr.io/tongyi-mai/mobile_world:latest` - 21.1GB.
- `opencode:injected_001` - 12.7GB.
- `opencode:pre_eval_backup` - 12.6GB.
- Multiple `hermes:*` images - about 8.69GB to 8.73GB each.
- Multiple `openclaw:*` images - about 4.47GB each.
- `kilo_code:injected_001` - 4.39GB.
- `kilo_code:pre_eval_backup` - 4.38GB.

## Largest dangling images by `docker images` display size

The largest dangling images are all `<none>:<none>`, including:

- `51bfb0156355` - 12.8GB.
- `2dedaf7a4327` - 12.8GB.
- `e66602810b20` - 12.7GB.
- `dd17df2ebb61` - 12.7GB.
- `ca9d74012e5e` - 12.7GB.
- `b384b3554f2f` - 12.7GB.
- `96c854e15680` - 12.7GB.
- `7a95d2e82974` - 12.7GB.
- `57d22e89c59d` - 12.7GB.
- `57af419649b5` - 12.7GB.

## Active container space notes

- There are 14 running containers based on `ghcr.io/tongyi-mai/mobile_world:latest`.
- Each of those containers has about 6.37GB to 6.38GB of writable layer data.
- These running containers are a major non-image Docker space consumer and are not dangling images.
- Other active containers include `opencode`, `hermes`, `kilo_code`, `memobase`, `redis`, `pgvector`, `droid`, `codex`, `claude_code`, `zed`, and `grok_cli`.

## Interpretation

The collaborator's report is supported: the Docker host has a very large number of dangling images. The largest visible dangling images are 12GB-class images, and there are also many 8GB-, 4GB-, 3GB-, and 1.66GB-class dangling entries.

The easiest clear cleanup candidate by Docker's own summary is unused local volumes: 82.23GB reclaimable. Dangling images are also numerous, but Docker image size reporting can be confusing because shared layers and active references affect what is truly reclaimable.

## Follow-up: dangling image deletion risk

User asked whether dangling images can be deleted, whether deletion has impact, and what produces them.

Additional read-only checks:

- `docker ps -a --filter ancestor=51bfb0156355 --format '{{.ID}} {{.Image}} {{.Status}} {{.Names}}'`
- `docker ps -a --filter ancestor=2dedaf7a4327 --format '{{.ID}} {{.Image}} {{.Status}} {{.Names}}'`
- `docker ps -a --format '{{.ID}} {{.Image}} {{.Status}} {{.Names}}' | rg '^[^ ]+ [0-9a-f]{12} '`
- `docker image inspect 6ee25bef4a17 --format '{{.Id}} {{.RepoTags}} {{.Size}}'`
- `docker images --filter dangling=true --format '{{.ID}} {{.Size}}' | rg '^6ee25bef4a17'`
- `docker ps -a --filter ancestor=6ee25bef4a17 --format '{{.ID}} {{.Image}} {{.Status}} {{.Names}}'`

Results:

- No containers were found using dangling images `51bfb0156355` or `2dedaf7a4327`.
- One active paused container, `kilo_code`, uses bare image ID `6ee25bef4a17`.
- Image `6ee25bef4a17` has no repo tags, but it did not appear in `docker images --filter dangling=true`, so normal dangling-image pruning should not target it.
- No deletion was performed.
