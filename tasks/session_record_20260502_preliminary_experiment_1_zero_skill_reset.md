# Session Record - Preliminary Experiment 1 Zero Skill Reset - 2026-05-02

## User Request

- 根据 `tasks/session_record_20260502_cross_model_opencode_add_skill_requirements.md` 拆分计划。
- 先执行 Preliminary Experiment 1: 零 Skill Reset 纯净性预实验。
- 用 checklist 追踪进度。

## Files Changed

- `tasks/cross_model_opencode_add_skill_checklist_20260502.md`
  - 新增 cross-model OpenCode add-skill 实验 gate checklist。
  - 标记 Gate 1 已完成，并保留 Gate 2-8 的待办项。
- `experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh`
  - 新增 OpenCode-only reset 脚本。
  - 清理 `/opencode` 下的 OpenCode/project skill roots、旧 ledger/trace、instruction hooks。
  - 验证 skill roots 不存在或为空。
  - 验证 `opencode debug skill` 不再列出 `integrity-sync`、`performance-audit`、`explain-code`。
- `experiments/AgentCallInterface/tests/test_reset_opencode_zero_skill_state_script.py`
  - 新增脚本语法、dry-run target、未创建 baseline skill、debug skill absence 检查的测试。

## Preliminary Experiment 1 Execution

Live container: `opencode`

Procedure:

1. 人为污染 `/opencode`:
   - `/opencode/.opencode/skills/integrity-sync/SKILL.md`
   - `/opencode/.agents/skills/performance-audit/SKILL.md`
   - `/opencode/.claude/skills/explain-code/SKILL.md`
   - `/opencode/.kilo/skills/legacy-skill`
   - `/opencode/.kilocode/skills/legacy-kilo`
   - `/opencode/skills/freeform`
   - `/opencode/skill/singular`
   - `sync-check-record.jsonl`
   - `mobius-loop-trace.jsonl`
   - `explain-code-status-ledger.jsonl`
   - `integrity-sync-ledger.jsonl`
   - `performance-audit-ledger.jsonl`
   - `AGENTS.md`
   - `CLAUDE.md`
   - `.opencode/AGENTS.md`
   - `.opencode/instructions.md`
   - `.opencode/instructions`
2. 污染检查发现 `/opencode` 里还残留历史 ledger 变体文件，因此 reset 脚本扩展为清理顶层 `*ledger*.jsonl` 和 `*trace*.jsonl`。
3. 执行 `experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh`。
4. 独立检查 skill roots、ledger/trace、instruction hooks。
5. 再次执行 reset 脚本验证幂等性。
6. 最终独立检查 clean state。

## Results

- `bash -n experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh`: passed.
- `DRY_RUN=1 bash experiments/scripts/coding_agents/reset_opencode_zero_skill_state.sh`: passed.
- `uv run pytest ...`: blocked before tests by current dependency resolution issue:
  - `pyarrow==24.0.0` has no compatible Linux wheel for this environment.
- `uv run --no-sync pytest experiments/AgentCallInterface/tests/test_reset_opencode_zero_skill_state_script.py`: 4 passed.
- First live reset:
  - Skill roots absent or empty.
  - Runtime artifacts and instruction hooks absent.
  - `opencode debug skill` output: `[]`.
- Second live reset:
  - Same clean state.
  - `opencode debug skill` output: `[]`.
- Final independent check:
  - `PASS final clean state`.

## Internal Notes

- No model API request was made.
- No Docker image was committed.
- Existing unrelated dirty worktree changes were not modified.
- Gate 1 is ready as a prerequisite for later cross-model add-skill experiments.

