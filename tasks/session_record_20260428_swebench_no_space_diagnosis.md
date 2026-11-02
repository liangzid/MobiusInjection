# Session Record: SWE-bench No Space Diagnosis

Date: 2026-04-28

## User Request

Dr. Frost asked what `docker rmi` means and whether the storage-full issue came from this experiment or another path.

## Read-only Checks

- Checked host filesystem usage with `df`.
- Checked Docker root directory with `docker info`.
- Checked Docker container writable-layer sizes with `docker ps -a --size`.
- Checked Docker image list and image sizes with `docker images`.
- Checked relevant experiment log directory sizes.
- Checked `/tmp` directory usage.

## Findings

- Host root filesystem `/` is full:
  - `/dev/sdb2`: `879G` total, `846G` used, `0` available, `100%`.
- `/home` still has space:
  - `/dev/sda`: `14T` total, `248G` available.
- Experiment log directories are small:
  - SWE-bench Claude Code reparse limit-20 log root: about `50M`.
  - HumanEval Claude Code reparse limit-20 log root: about `15M`.
  - Original qwen36plus sequential log root: about `89M`.
  - `experiments/results`: about `20K`.
- Docker root is on `/var/lib/docker`, which is under the full `/` filesystem.
- Running Docker containers have large writable layers, especially many `mobile_world` containers around `6G-10G` each, plus `claude_code` around `4.97G`.
- The current experiment also created `claude_code:injected_001`, an image around `16.6G`, so this run contributed additional root filesystem pressure but the experiment logs under `/home` are not the cause.
- `/tmp` uses about `9.4G`, mainly `/tmp/torchinductor_qiheng` at about `6.5G`; this is also on `/`.

## Interpretation

The `No space left on device` errors in the last two SWE-bench cases were caused by the root filesystem/Docker overlay storage being full, not by the `/home/.../experiments/logs` result files.

`docker rmi` means remove a Docker image. The specific candidate was `claude_code:injected_001`, a checkpoint image produced by the experiment. It was not removed during this diagnostic turn.
