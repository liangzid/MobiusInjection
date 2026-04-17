"""
Tests for Dataset Loaders
==========================
Tests for ClawBench and Coding Benchmark loaders.
"""

import pytest
from experiments.datasets.clawbench_loader import (
    ClawBenchLoader,
    ClawBenchTask,
)
from experiments.datasets.coding_benchmark_loader import (
    SWEBenchLoader,
    HumanEvalLoader,
    CodingBenchmarkLoader,
    CodingTask,
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


class TestHumanEvalLoader:
    def test_init(self):
        loader = HumanEvalLoader()
        assert loader.data_dir.name == "humaneval_data"


class TestCodingBenchmarkLoader:
    def test_init(self):
        loader = CodingBenchmarkLoader()
        assert isinstance(loader.swebench, SWEBenchLoader)
        assert isinstance(loader.humaneval, HumanEvalLoader)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
