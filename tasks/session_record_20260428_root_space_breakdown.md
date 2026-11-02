# Session Record: Root Filesystem Space Breakdown

Date: 2026-04-28

## User Request

Dr. Frost asked whether repeated updates to `claude_code:injected_001` grow storage, and what else under `/` is using space.

## Read-only Checks

- `df -h` and `df -i` for `/`, `/home`, `/tmp`, `/var`, `/var/lib`, and `/var/lib/containerd`.
- `du -xhd1 /`, `/var`, and `/tmp`.
- Docker root directory via `docker info`.
- Docker dangling images via `docker image ls --filter dangling=true` and `docker image inspect`.
- Docker container writable layers via `docker inspect --size`.
- Large ordinary files under `/` with `find / -xdev -type f -size +1G`.
- Deleted open files via `lsof +L1`.

## Findings

- `/` is full: `/dev/sdb2`, `879G` total, `846G` used, `0` available.
- `/home` is separate and still has about `248G` available.
- Inodes are not the limiting factor: `/` inode use is about `33%`.
- Ordinary readable directory usage only explains about `52G`:
  - `/usr`: about `29G`
  - `/tmp`: about `9.4G`
  - `/var`: about `7.4G`
  - `/opt`: about `4.0G`
- Docker root is `/var/lib/docker`, backed by Docker/containerd overlay storage on `/`.
- Direct `du` into `/var/lib/docker` and `/var/lib/containerd` is not readable as the current user, but Docker metadata exposes the major consumers.
- Docker dangling images:
  - Count: `21`
  - Naive inspected total: about `122.57 GiB`
  - Most were created during the SWE-bench Claude Code run and are previous commits after reusing the `claude_code:injected_001` tag.
- Current tagged `claude_code:injected_001`:
  - Inspect size: about `6.38 GiB`
  - Docker CLI virtual size display: about `16.6GB`
- Container writable layers:
  - Total writable layer size: about `136.45 GiB`
  - Most of this comes from many running `mobile_world` containers, each around `5.7G-8.9G`.
  - `claude_code` writable layer is about `4.63 GiB`.
- `/tmp` uses about `9.4G`, mostly `/tmp/torchinductor_qiheng` at about `6.5G`.
- Large ordinary files under `/` include:
  - `/swapfile`: about `2.0G`
  - `/usr/local/lib/ollama/cuda_v12/libggml-cuda.so`: about `1.57G`
  - `/tmp/tmp1fi628e5`: about `1.16G`
  - CUDA static library: about `1.01G`
- Deleted open files are not a major cause; the largest visible deleted file was about `192MB`.

## Interpretation

Updating `claude_code:injected_001` is not an in-place overwrite. Each `docker commit` creates a new image object. Reusing the same tag moves the tag to the newest image, while prior images can become dangling `<none>:<none>` images. Those old images continue to consume Docker storage until explicitly cleaned.

The root filesystem pressure is mainly Docker/containerd storage, especially:

- dangling images from repeated checkpoint commits,
- writable layers of many running `mobile_world` containers,
- the current `claude_code` writable layer and checkpoint image.

The experiment logs under `/home` are not the meaningful contributor.
