# Master Tree Merge Plan - Coding-Agent Isolation

## User Instruction

Dr. Frost asked to inspect whether anything from the main branch can be merged
into the current worktree, try merging useful parts, then commit a backup. The
turn was interrupted before any merge or commit was performed. Dr. Frost then
asked for the main gap between the current worktree and main.

## Files Reviewed

- Current branch/status via `git status --short --branch`
- Branch tips via `git branch --all --verbose --no-abbrev`
- Remote state via `git remote --verbose`
- Main branch updates via `git fetch origin`
- Divergence via `git log --oneline --left-right --cherry-pick HEAD...origin/master`
- File-level differences via `git diff --stat HEAD..origin/master`
- Merge shape via `git merge-tree 137ceb60ec456a1c81c3fa5efdcaf2526c257572 HEAD origin/master`

## Results

- Current branch: `codeagent/experiments-copy`.
- Upstream tracking branch: `origin/codeagent/experiments-copy`.
- Current branch is ahead of its upstream by 19 commits.
- `origin/master` is at `aeed0b5` (`a better version of mobius injection.`).
- Merge base between current `HEAD` and `origin/master`:
  `137ceb60ec456a1c81c3fa5efdcaf2526c257572`.
- The worktree already had many modified and untracked files before any merge.
- No merge or commit was performed before the interruption.

## Main Gap Summary

- `origin/master` mainly advances the Mobius/context-injection experiment line:
  new `context_injection_add_s.py`, ADD_S taskset configs, multiple
  `mobiusInjection/MI_V3.x` and `MI_V4.x` files, and new effectiveness scripts.
- `origin/master` removes or renames several benchmark/evaluation assets that
  the current branch still keeps or has modified, including benchmark analysis,
  manifest/log-retention/prompt-composer files, HumanEval-related scripts, and
  several tests.
- Both sides changed core caller/test files such as
  `experiments/AgentCallInterface/agents/agent_callers.py`,
  `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py`, and
  multiple tests, so a direct full merge is likely to require careful conflict
  resolution.
- `origin/master` also adds a root `AGENTS.md` whose commit rule conflicts with
  the active user-provided instructions in this worktree.

## Recommendation After Follow-up Question

Dr. Frost clarified that `origin/master` is mainly for claw-like agent
experiments, while the current worktree is mainly for coding-agent experiments.
The recommended approach is not to full-merge `origin/master` into this branch.
Instead, keep the two experiment lines separated and selectively import only
shared infrastructure changes when they are demonstrably useful.

Recommended strategy:

- Treat `mobiusInjection/`, ADD_S taskset configs, and claw-specific
  effectiveness scripts as claw-line ownership from `master`.
- Treat HumanEval/SWE-bench/free-model coding-agent scripts, benchmark
  manifests, and coding-agent evaluation records as coding-line ownership from
  this branch.
- For shared files such as `agent_callers.py`,
  `coding_benchmark_loader.py`, `.gitignore`, and shared tests, import changes
  surgically by patch or path-level checkout rather than a full merge.
- Avoid accepting main's deletions of coding-agent benchmark/evaluation files
  unless a replacement path is confirmed.
- Consider later extracting shared caller utilities into smaller modules so
  claw-agent and coding-agent changes stop colliding in the same files.

## Proposed Isolation Refactor

Dr. Frost proposed copying files touched by the main branch into coding-agent
specific names and switching coding-agent experiment scripts to those names,
while keeping files deleted on main if the coding-agent line still uses them.

Assessment:

- This is a viable way to split the two experiment lines.
- It should be implemented as an explicit isolation/refactor commit before any
  later selective merge from `master`.
- The copy set should be based on actual coding-agent dependencies, not every
  file touched by `master`, to avoid unnecessary duplication.
- After the coding-agent scripts no longer depend on the shared paths, future
  merges can let `master` own claw-specific shared files and deletions without
  breaking the coding-agent experiments.

Suggested implementation shape:

- Create coding-agent specific modules or paths for caller/evaluation/dataset
  code that `master` also modifies or deletes.
- Update coding-agent experiment scripts and tests to import or invoke the
  coding-specific paths.
- Keep the original files only where they remain needed by claw-like agent
  experiments or backward compatibility.
- Run the coding-agent test/script syntax checks after every migration batch.

## Detailed Migration And Merge Plan

### Goal

Separate the coding-agent experiment line from the claw-like agent experiment
line before attempting any meaningful merge from `origin/master`.

The desired final state:

- Coding-agent experiments invoke coding-agent specific modules and scripts.
- Claw-like experiments can keep using the main-branch paths.
- Files deleted on `master` but still required by coding-agent experiments are
  preserved under coding-agent specific names.
- Future merges from `master` should not delete or overwrite active
  coding-agent experiment code.

### Non-Goals

- Do not full-merge `origin/master` before isolation is complete.
- Do not accept `master` deletions of coding-agent benchmark/evaluation files
  until every coding-agent dependency has moved away from those paths.
- Do not rewrite unrelated experiment records or historical logs.
- Do not rename large result/data directories unless a script directly depends
  on their path.

### Phase 0 - Baseline Inventory

1. Capture current worktree status:
   `git status --short --branch`.
2. Capture current divergence from `origin/master`:
   `git log --oneline --left-right --cherry-pick HEAD...origin/master`.
3. Build a list of paths changed or deleted by `origin/master`:
   `git diff --name-status HEAD..origin/master`.
4. Build a coding-agent dependency list by searching current scripts/tests for
   imports and path references:
   - `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
   - `experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh`
   - HumanEval and SWE-bench tests under
     `experiments/AgentCallInterface/tests/`
   - coding-agent dataset/evaluation modules under
     `experiments/AgentCallInterface/`
5. Record the exact dependency list in this document before moving files.

Exit criteria:

- There is a concrete path list split into:
  - coding-agent owned paths,
  - claw-like owned paths,
  - shared infrastructure paths,
  - deleted-on-master but still-used-by-coding-agent paths.

Execution result on 2026-04-28:

- Coding-agent owned paths selected for isolation:
  - `experiments/AgentCallInterface/coding_agents/coding_agent_callers.py`
  - `experiments/AgentCallInterface/coding_datasets/coding_benchmark_loader.py`
  - `experiments/AgentCallInterface/coding_evaluation/benchmark_analysis.py`
  - `experiments/AgentCallInterface/coding_evaluation/benchmark_manifest.py`
  - `experiments/AgentCallInterface/coding_evaluation/humaneval_log_analysis.py`
  - `experiments/AgentCallInterface/coding_evaluation/log_retention.py`
  - `experiments/AgentCallInterface/coding_evaluation/mobius_monitor.py`
  - `experiments/AgentCallInterface/coding_evaluation/prompt_composer.py`
  - `experiments/scripts/coding_agents/run_basic_coding_agent_eval_v3.sh`
  - `experiments/scripts/coding_agents/run_free_models_humaneval_injection_benchmark.sh`
  - `experiments/scripts/coding_agents/run_minimax_humaneval_injection_benchmark.sh`
  - `experiments/scripts/coding_agents/run_minimax_coding_agents_full_eval.sh`
  - `experiments/scripts/coding_agents/analyze_humaneval_minimax_logs.py`
- Claw-like owned paths left on shared/main-line paths:
  - `experiments/AgentCallInterface/datasets/clawbench_loader.py`
  - `experiments/AgentCallInterface/datasets/clawbench_tasks/`
  - `experiments/AgentCallInterface/tests/test_openclaw_model_normalization.py`
  - `experiments/scripts/1.0.1.run_basic_eval_v3.sh`
  - `mobiusInjection/MI_V*.py`
- Shared infrastructure intentionally left shared:
  - `experiments/AgentCallInterface/utils/api_keys.py`
  - `experiments/AgentCallInterface/evaluation/opencode_skill_session.py`
  - `experiments/AgentCallInterface/transformers/agent_transformers.py`
- Deleted-on-master but still used by coding-agent line:
  - `experiments/AgentCallInterface/evaluation/benchmark_analysis.py`
  - `experiments/AgentCallInterface/evaluation/benchmark_manifest.py`
  - `experiments/AgentCallInterface/evaluation/humaneval_log_analysis.py`
  - `experiments/AgentCallInterface/evaluation/log_retention.py`
  - `experiments/AgentCallInterface/evaluation/prompt_composer.py`
  - HumanEval/minimax/free-model benchmark shell scripts under
    `experiments/scripts/`

### Phase 1 - Create Coding-Agent Owned Namespace

Preferred layout:

- `experiments/AgentCallInterface/coding_agents/`
  for coding-agent caller wrappers and coding-agent specific runtime helpers.
- `experiments/AgentCallInterface/coding_datasets/`
  for HumanEval/SWE-bench/free-model benchmark loaders if the shared loader
  remains contested.
- `experiments/AgentCallInterface/coding_evaluation/`
  for benchmark manifests, HumanEval log analysis, log retention, prompt
  composition, and other evaluation code deleted or changed by `master`.
- `experiments/scripts/coding_agents/`
  for coding-agent experiment shell entrypoints.

Migration rules:

- Copy only code that the coding-agent line actually imports or executes.
- Keep compatibility wrappers at old paths only if existing tests or scripts
  still require them during the transition.
- Preserve behavior first; do not refactor internals unless required for import
  boundaries.
- Use names that make ownership explicit, for example:
  - `coding_agent_callers.py`
  - `coding_benchmark_loader.py`
  - `coding_benchmark_manifest.py`
  - `coding_humaneval_log_analysis.py`
  - `run_humaneval_injection_benchmark.sh`
  - `run_swebench_coding_agent_eval.sh`

Exit criteria:

- New coding-agent owned files exist.
- Old shared files are not yet deleted.
- No script has been switched until the copied targets compile or pass syntax
  checks.

Execution result on 2026-04-28:

- Created the coding-agent package namespaces:
  - `experiments/AgentCallInterface/coding_agents/`
  - `experiments/AgentCallInterface/coding_datasets/`
  - `experiments/AgentCallInterface/coding_evaluation/`
  - `experiments/scripts/coding_agents/`
- Copied the current coding-agent caller, loader, evaluation modules, and
  benchmark scripts into those namespaces.
- Adjusted the copied benchmark loader so it still reads the real existing
  benchmark data from `experiments/AgentCallInterface/datasets/` rather than
  expecting duplicated data under `coding_datasets/`.

### Phase 2 - Switch Coding-Agent Imports And Scripts

Update imports and script invocations in small batches:

1. Switch Python imports in coding-agent tests from shared modules to
   coding-agent owned modules.
2. Switch Python imports in coding-agent scripts and CLI snippets.
3. Move shell entrypoints into `experiments/scripts/coding_agents/` or create
   coding-agent specific wrappers there.
4. Update shell scripts to call the coding-agent owned Python modules.
5. Keep old script names as thin wrappers only if external commands or old
   records still depend on those names.

Files likely requiring edits:

- `experiments/AgentCallInterface/tests/test_agent_callers.py`
- `experiments/AgentCallInterface/tests/test_dataset_loaders.py`
- `experiments/AgentCallInterface/tests/test_free_models_humaneval_benchmark_script.py`
- `experiments/AgentCallInterface/tests/test_mobius_monitor.py`
- `experiments/scripts/1.0.1.run_basic_coding_agent_eval_v3.sh`
- `experiments/scripts/1.0.3.run_free_models_humaneval_injection_benchmark.sh`

Exit criteria:

- Coding-agent scripts and tests no longer require files that `origin/master`
  deletes.
- Any shared import that remains is intentionally shared and documented in this
  plan.

Execution result on 2026-04-28:

- New coding-agent scripts now call:
  - `experiments.AgentCallInterface.coding_agents.coding_agent_callers`
  - `experiments.AgentCallInterface.coding_evaluation.prompt_composer`
  - `experiments.AgentCallInterface.coding_evaluation.mobius_monitor`
  - `experiments.AgentCallInterface.coding_evaluation.benchmark_manifest`
  - `experiments.AgentCallInterface.coding_evaluation.log_retention`
  - `experiments.AgentCallInterface.coding_evaluation.benchmark_analysis`
- New benchmark wrapper scripts now snapshot
  `run_basic_coding_agent_eval_v3.sh` from
  `experiments/scripts/coding_agents/`.
- Updated coding-agent tests to target the new coding-agent namespaces and
  script paths.
- Left `experiments.AgentCallInterface.evaluation.opencode_skill_session` as an
  intentional shared dependency because it is not currently deleted by
  `origin/master`.

### Phase 3 - Verification After Migration

Run focused checks after each migration batch:

1. Python compile checks for changed coding-agent modules:
   `env UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile <changed files>`.
2. Shell syntax checks for changed scripts:
   `bash -n <changed shell scripts>`.
3. Focused pytest checks for migrated behavior:
   `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest <changed related tests>`.
4. If a script is an experiment launcher that would call external models or
   Docker, run only syntax/preflight checks unless Dr. Frost explicitly asks
   for a live experiment run.

Exit criteria:

- Compile and syntax checks pass.
- Focused tests pass.
- Any test not run is listed with the reason.

Execution result on 2026-04-28:

- Shell syntax checks passed:
  - `bash -n experiments/scripts/coding_agents/run_basic_coding_agent_eval_v3.sh`
  - `bash -n experiments/scripts/coding_agents/run_free_models_humaneval_injection_benchmark.sh`
  - `bash -n experiments/scripts/coding_agents/run_minimax_humaneval_injection_benchmark.sh`
  - `bash -n experiments/scripts/coding_agents/run_minimax_coding_agents_full_eval.sh`
- `uv run python -m py_compile ...` could not be completed in this environment:
  - First attempt failed because `/tmp` is on a full root filesystem.
  - Second attempt with `UV_CACHE_DIR=/home/zi/.cache/uv-codex` failed because
    `pyarrow==24.0.0` has no compatible Linux wheel for this platform according
    to uv's resolver.
- Fallback syntax verification passed with system Python:
  - `python3 -m py_compile` for the new coding-agent Python modules and
    `analyze_humaneval_minimax_logs.py`.
- Focused pytest passed:
  - 25 passed for dataset loaders, benchmark manifest, and benchmark wrappers.
  - 55 passed for prompt composer, Mobius monitor, coding eval script,
    HumanEval log analysis, and coding caller tests.
- Known tests not made passing in this step:
  - `test_benchmark_analysis.py` and `test_log_retention.py` still require
    missing real log files under
    `experiments/logs/basic_coding_eval_20260422_105848_opencode_*`.
  - No mock or synthetic replacement data was created.

### Phase 4 - Backup Commit For Isolation Refactor

Once the migration passes verification:

1. Stage only the isolation refactor files and this plan.
2. Avoid staging unrelated result directories, datasets, logs, or previously
   existing untracked work unless they are necessary for the refactor.
3. Commit with a message such as:
   `Isolate coding-agent experiment paths from master`
4. Record the commit hash in this document.

Exit criteria:

- A backup commit exists for the completed isolation refactor.
- Worktree status is reviewed after commit.

Execution result on 2026-04-28:

- Created backup commit:
  - `744aec3 Isolate coding-agent experiment paths from master`
- Staged only the isolation refactor files, coding-agent test path updates, new
  coding-agent scripts, and this plan document.
- Left unrelated existing worktree changes unstaged.

### Phase 5 - Selective Merge From `origin/master`

After the isolation commit, evaluate `origin/master` again and import only safe
changes.

Safe candidates:

- `.gitignore` entries for generated local data, caches, logs, and result
  directories.
- New claw-like agent files that do not affect coding-agent paths:
  - `mobiusInjection/MI_V3.x*`
  - `mobiusInjection/MI_V4.x*`
  - `experiments/AgentCallInterface/context_injection_add_s.py`
  - ADD_S taskset configs
  - claw-like effectiveness scripts
- Generic utility changes only if coding-agent tests still pass after import.

Unsafe candidates unless manually reviewed:

- Deletions under `experiments/AgentCallInterface/evaluation/`.
- Deletions under HumanEval or benchmark test/script paths.
- Large rewrites of `agent_callers.py`.
- Main-branch `AGENTS.md` if it conflicts with the active instructions for this
  worktree.

Preferred import methods:

- For isolated new files: path-level checkout from `origin/master`.
- For small shared changes: manual patch based on `git diff`.
- For whole commits: cherry-pick only if the commit touches a narrow,
  non-conflicting ownership area.

Exit criteria:

- Imported main-branch content does not change coding-agent experiment behavior.
- Focused verification still passes.
- A second backup commit records the selective merge/import.

Execution result on 2026-04-28:

- Imported safe claw-like additions from `origin/master`:
  - `experiments/AgentCallInterface/context_injection_add_s.py`
  - ADD_S taskset configs under `experiments/configs/`
  - claw-like effectiveness scripts under `experiments/scripts/`
  - `mobiusInjection/MI_V3.2*`, `MI_V3.3*`, `MI_V3.4*`,
    `MI_V3.5*`, `MI_V3.6*`, `MI_V4*`, `MI_V4.1*`, and `MI_V4.2*`
  - passing context-injection and MI tests from `origin/master`
- Merged `.gitignore` by preserving current coding-agent ignore entries and
  adding useful main-branch entries for `.codex`, dataset directories,
  `package-lock.json`, `pytest-of-zi`, and `tasks/old_tasks`.
- Explicitly did not import:
  - root `AGENTS.md`, because its commit rule conflicts with the active
    Dr. Frost instructions for this worktree.
  - `package.json`, because it is an empty `{}` file on `origin/master` and is
    not needed for either imported scripts or tests.
  - main-branch deletions of coding-agent benchmark/evaluation files.
  - `test_mi_v353_agent_specific.py`, because it references
    `mobiusInjection/MI_V3.5.3_*` files that do not exist on `origin/master`.
- Adjusted imported V4/V4.1 tests to match the actual current main-branch
  template text, then verified them.
- Verification:
  - `python3 -m py_compile` passed for imported context-injection and
    MI template Python files.
  - `bash -n` passed for the three imported claw-like shell scripts.
  - Focused pytest passed: 62 tests.

### Phase 6 - Future Structure Cleanup

After the immediate merge risk is removed, consider a later cleanup commit:

- Split caller code by agent family:
  - coding-agent callers,
  - claw-like callers,
  - shared subprocess/Docker helpers.
- Move experiment scripts into family directories:
  - `experiments/scripts/coding_agents/`
  - `experiments/scripts/claw_agents/`
- Keep shared tests small and move family-specific tests beside the
  corresponding code.

This phase is optional and should not block the immediate master synchronization
unless shared-file conflicts remain high.

## Current Follow-up Result

Dr. Frost asked to write the detailed plan into the same document and rename the
document to `master_tree_merge_plan`. The original
`tasks/session_record_20260428_master_gap_check.md` was renamed to
`tasks/master_tree_merge_plan.md`, and the detailed migration/merge plan was
added here. No code migration, merge, test run, or commit was performed in this
step.
