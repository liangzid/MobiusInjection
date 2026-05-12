"""
Tests for Dataset Loaders
==========================
Tests for ClawBench and Coding Benchmark loaders.
"""

import pytest
from experiments.AgentCallInterface.datasets.clawbench_loader import (
    ClawBenchLoader,
    ClawBenchTask,
)
from experiments.AgentCallInterface.coding_datasets.coding_benchmark_loader import (
    SWEBenchLoader,
    HumanEvalLoader,
    CodingBenchmarkLoader,
    BenchmarkTask,
    CodingTask,
    HUMANEVAL_TASK_INSTRUCTIONS,
    SWEBENCH_TASK_INSTRUCTIONS,
    load_benchmark_tasks,
)


class TestClawBenchLoader:
    def test_init(self):
        loader = ClawBenchLoader()
        assert loader.tasks_dir.name == "clawbench_tasks"

    def test_init_with_custom_path(self, tmp_path):
        loader = ClawBenchLoader(tasks_dir=tmp_path)
        assert loader.tasks_dir == tmp_path

    def test_default_skill_url(self):
        loader = ClawBenchLoader()
        assert loader.DEFAULT_SKILL_URL == "https://clawbench.net/skill.md"


class TestSWEBenchLoader:
    def test_init(self):
        loader = SWEBenchLoader()
        assert loader.data_dir.name == "swebench_data"

    def test_init_with_custom_path(self, tmp_path):
        loader = SWEBenchLoader(data_dir=tmp_path)
        assert loader.data_dir == tmp_path

    def test_load_benchmark_tasks_from_real_swebench_file(self):
        tasks = load_benchmark_tasks(dataset="swebench", limit=2)

        assert len(tasks) == 2
        assert isinstance(tasks[0], BenchmarkTask)
        assert tasks[0].dataset == "swebench"
        assert tasks[0].prompt.startswith(SWEBENCH_TASK_INSTRUCTIONS)
        assert "Repository:" in tasks[0].prompt
        assert "Issue description:" in tasks[0].prompt
        assert tasks[0].metadata["benchmark_prompt_kind"] == "swebench_issue_v1"
        assert tasks[0].metadata["instance_id"]

    def test_load_benchmark_tasks_from_swebench_lite_file(self):
        tasks = load_benchmark_tasks(
            dataset="swebench",
            dataset_type="swe-bench_lite",
            limit=50,
        )

        assert len(tasks) == 50
        assert tasks[0].task_id == "astropy__astropy-12907"
        assert tasks[-1].dataset == "swebench"


class TestHumanEvalLoader:
    def test_init(self):
        loader = HumanEvalLoader()
        assert loader.data_dir.name == "humaneval_data"

    def test_load_benchmark_tasks_from_real_humaneval_file(self):
        tasks = load_benchmark_tasks(dataset="humaneval", limit=2)

        assert len(tasks) == 2
        assert isinstance(tasks[0], BenchmarkTask)
        assert tasks[0].dataset == "humaneval"
        assert tasks[0].task_id == "HumanEval/0"
        assert tasks[0].prompt.startswith(HUMANEVAL_TASK_INSTRUCTIONS)
        assert "Entry point: has_close_elements" in tasks[0].prompt
        assert "def has_close_elements" in tasks[0].prompt
        assert tasks[0].entry_point == "has_close_elements"
        assert tasks[0].metadata["benchmark_prompt_kind"] == "humaneval_completion_v1"
        assert tasks[0].metadata["raw_prompt_length"] > 0

    def test_load_benchmark_tasks_filters_are_stable(self):
        limited = load_benchmark_tasks(dataset="humaneval", limit=2, offset=1)
        selected = load_benchmark_tasks(
            dataset="humaneval", task_ids=["HumanEval/3", "HumanEval/1"]
        )
        empty = load_benchmark_tasks(dataset="humaneval", task_ids=[])

        assert [task.task_id for task in limited] == ["HumanEval/1", "HumanEval/2"]
        assert [task.task_id for task in selected] == ["HumanEval/1", "HumanEval/3"]
        assert empty == []


class TestCodingBenchmarkLoader:
    def test_init(self):
        loader = CodingBenchmarkLoader()
        assert isinstance(loader.swebench, SWEBenchLoader)
        assert isinstance(loader.humaneval, HumanEvalLoader)

    def test_unified_loader_returns_standard_records(self):
        loader = CodingBenchmarkLoader()
        tasks = loader.load_benchmark_tasks(dataset="humaneval", limit=1)

        assert len(tasks) == 1
        assert tasks[0].dataset == "humaneval"
        assert tasks[0].task_id == "HumanEval/0"

    def test_unified_loader_returns_swebench_records(self):
        loader = CodingBenchmarkLoader()
        tasks = loader.load_benchmark_tasks(dataset="swebench", limit=1)

        assert len(tasks) == 1
        assert tasks[0].dataset == "swebench"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
