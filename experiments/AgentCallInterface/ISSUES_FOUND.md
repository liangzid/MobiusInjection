# AgentCallInterface Code Review - Issues Found

**Date:** 2026-04-17
**Reviewer:** AI Assistant
**Directory:** `~/AgentCodingDos/experiments/AgentCallInterface/`

---

## Issue 1: Import Path Errors (CRITICAL)

**Files Affected:**
- `experiments/AgentCallInterface/transformers/agent_transformers.py:15-16`
- `experiments/AgentCallInterface/tests/test_dataset_loaders.py:8,12`
- `experiments/AgentCallInterface/tests/test_transformers.py:10,17-18`

**Problem:** Imports use `from experiments.datasets...` but should be `from experiments.AgentCallInterface.datasets...`

**Current (Broken):**
```python
from experiments.datasets.clawbench_loader import ClawBenchTask
from experiments.datasets.coding_benchmark_loader import CodingTask
```

**Expected (Correct):**
```python
from experiments.AgentCallInterface.datasets.clawbench_loader import ClawBenchTask
from experiments.AgentCallInterface.datasets.coding_benchmark_loader import CodingTask
```

**Status:** ✅ FIXED - 2026-04-17

---

## Issue 2: HumanEvalLoader.load_tasks() Not Implemented

**File:** `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py:128`

**Problem:** The `HumanEvalLoader` class lacks a `load_tasks()` method, but `CodingBenchmarkLoader` attempts to call it at line 137-138.

**Status:** ✅ FIXED - 2026-04-17 (Implemented load_tasks with _download_dataset and _parse_humaneval)

---

## Issue 3: HumanEvalLoader Has Wrong Dataset URL

**File:** `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py:119`

**Problem:** The URL points to GSM8K (math dataset) instead of HumanEval.

**Status:** ✅ FIXED - 2026-04-17 (Changed to correct HumanEval URL)

---

## Issue 4: Agent CLI Usage Does Not Align with Official APIs

### 4.1 CursorCaller

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:248-257`

**Problem:** `cursor --task --repo` - Cursor AI does not have a documented CLI for autonomous task execution in this manner.

**Current:**
```python
cmd = [
    "cursor",
    "--task",
    task_input.get("task_id", ""),
    "--repo",
    task_input.get("repo", ""),
]
```

**Status:** Unverified - May not work as intended

---

### 4.2 OpenCodeCaller

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:286-295`

**Problem:** `opencode --task --repo` - OpenCode CLI docs show no such arguments.

**Current:**
```python
cmd = [
    "opencode",
    "--task",
    task_input.get("task_id", ""),
    "--repo",
    task_input.get("repo", ""),
]
```

**Status:** Unverified - CLI interface may be different

---

### 4.3 KiloCodeCaller

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:324-332`

**Problem:** The npm package `@kilocode/cli` may not be the correct package name.

**Current:**
```python
cmd = [
    "npx",
    "@kilocode/cli",
    "--task",
    task_input.get("task_id", ""),
]
```

**Status:** Unverified - Package name may be incorrect

---

### 4.4 DroidCaller

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:398-411`

**Problem:** Using `curl|sh` to install and run Factory.ai Droid is unusual and the `--task` argument may not exist.

**Current:**
```python
cmd = [
    "curl",
    "-fsSL",
    "https://app.factory.ai/cli",
    "|",
    "sh",
    "-s",
    "--",
    "task",
    task_input.get("task_id", ""),
]
```

**Status:** Unverified - Installation method and CLI interface may differ

---

### 4.5 ZedCaller

**File:** `experiments/AgentCallInterface/agents/agent_callers.py:444-451`

**Problem:** `zed --task` - Zed editor does not have a `--task` argument.

**Current:**
```python
cmd = [
    "zed",
    "--task",
    task_input.get("task_id", ""),
]
```

**Status:** Unverified - CLI interface may be different

---

## Issue 5: ClawBenchLoader Works (Positive Finding)

**File:** `experiments/AgentCallInterface/datasets/clawbench_loader.py`

**Status:** ✅ USABLE

The ClawBench loader is properly implemented:
- Clones from `https://github.com/claw-bench/claw-bench.git`
- Parses JSON tasks correctly
- `get_quick_test_tasks()` provides 20 test cases
- `to_agent_input()` generates proper input format

---

## Testing Commands Used

```bash
# Test import paths
cd /home/zi/AgentCodingDos && uv run python -c "
import sys
sys.path.insert(0, '.')
from experiments.AgentCallInterface.datasets.clawbench_loader import ClawBenchLoader
loader = ClawBenchLoader()
print('ClawBenchLoader initialized successfully')
"

# Test HumanEvalLoader.load_tasks
uv run python -c "
from experiments.AgentCallInterface.datasets.coding_benchmark_loader import HumanEvalLoader
loader = HumanEvalLoader()
print(f'Has load_tasks: {hasattr(loader, \"load_tasks\")}')
"
```

---

---

## Issue 6: Missing MCP Modules

**Files Affected:**
- `experiments/AgentCallInterface/tests/test_mcp_recursive.py`
- `experiments/AgentCallInterface/tests/simulate_agent.py`

**Problem:** These test files import from `experiments.mcp.mcp_recursive` and `experiments.mcp.mcp_minimal`, but the `mcp` module does not exist in the codebase.

**Status:** ✅ RESOLVED - 2026-04-17
- Moved to `PastSourceCodeWhichIsOnlyForReference/AgentCallInterface_broken_tests/`
- User confirmed these outdated security tests are no longer needed

---

## Issue 7: SWE-bench Dataset URL Not Accessible

**File:** `experiments/AgentCallInterface/datasets/coding_benchmark_loader.py:51`

**Problem:** The HuggingFace URL for "swebench_verified_mini" does not exist.

**Status:** ✅ FIXED - 2026-04-17
- Found correct dataset: `SWE-bench/SWE-bench_Lite` on HuggingFace
- Downloaded 300 instances to `experiments/AgentCallInterface/datasets/swebench_data/swe-bench_lite.json`
- Dataset URL: `datasets.load_dataset('SWE-bench/SWE-bench_Lite', split='test')`

---

## Issue 8: ClawBench Tasks Use TOML Not JSON

**File:** `experiments/AgentCallInterface/datasets/clawbench_loader.py:85`

**Problem:** The loader looks for `.json` files but ClawBench tasks are stored as `.toml` files.

**Status:** ✅ FIXED - 2026-04-17
- Updated to use `tomllib`/`tomli` for TOML parsing
- Changed to `rglob("task.toml")` to find all task files
- Loaded 319 ClawBench tasks successfully

---

## Recommendations

1. ✅ ~~Fix import paths~~ - FIXED
2. ✅ ~~Implement `load_tasks()`~~ - FIXED
3. ✅ ~~Fix HumanEvalLoader URL~~ - FIXED
4. ✅ ~~Fix ClawBench TOML parsing~~ - FIXED
5. ✅ ~~SWE-bench URL~~ - FIXED (downloaded Lite dataset)
6. ✅ ~~MCP modules~~ - RESOLVED (moved to reference folder)
7. **Verify CLI arguments** for Cursor, OpenCode, KiloCode, Droid, and Zed against official documentation
8. **Add integration tests** that actually run each agent (with proper mocks/environment)
