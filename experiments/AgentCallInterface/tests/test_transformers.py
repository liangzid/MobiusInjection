"""
Tests for Agent Transformers
=============================
Tests for Claw-style and Coding-style agent transformers.
"""

import pytest
from dataclasses import dataclass

from experiments.transformers.agent_transformers import (
    get_transformer,
    CLAW_STYLE_TRANSFORMERS,
    CODING_STYLE_TRANSFORMERS,
    ClawStyleInput,
    CodingStyleInput,
)
from experiments.datasets.clawbench_loader import ClawBenchTask
from experiments.datasets.coding_benchmark_loader import CodingTask


class TestGetTransformer:
    def test_claw_style_transformers(self):
        for agent in CLAW_STYLE_TRANSFORMERS.keys():
            transformer = get_transformer(agent)
            assert transformer is not None
            assert callable(transformer.transform)

    def test_coding_style_transformers(self):
        for agent in CODING_STYLE_TRANSFORMERS.keys():
            transformer = get_transformer(agent)
            assert transformer is not None
            assert callable(transformer.transform)

    def test_unknown_agent_raises(self):
        with pytest.raises(ValueError, match="Unknown agent type"):
            get_transformer("unknown_agent")


class TestClawStyleTransformers:
    def test_openclaw_transformer(self):
        transformer = get_transformer("openclaw")
        task = ClawBenchTask(
            task_id="test-001",
            domain="file_ops",
            difficulty="L1",
            instructions="Test task",
            skill_file="https://example.com/skill.md",
            verifier_path="",
            weight=1,
        )
        result = transformer.transform(task)
        assert isinstance(result, ClawStyleInput)
        assert result.agent_type == "openclaw"
        assert result.task_id == "test-001"

    def test_zeroclaw_transformer(self):
        transformer = get_transformer("zeroclaw")
        task = ClawBenchTask(
            task_id="test-002",
            domain="code",
            difficulty="L2",
            instructions="Another test",
            skill_file="https://example.com/skill2.md",
            verifier_path="",
            weight=2,
        )
        result = transformer.transform(task)
        assert isinstance(result, ClawStyleInput)
        assert result.agent_type == "zeroclaw"

    def test_nanobot_transformer(self):
        transformer = get_transformer("nanobot")
        task = ClawBenchTask(
            task_id="test-003",
            domain="data",
            difficulty="L3",
            instructions="Third test",
            skill_file="https://example.com/skill3.md",
            verifier_path="",
            weight=3,
        )
        result = transformer.transform(task)
        assert isinstance(result, ClawStyleInput)
        assert result.agent_type == "nanobot"

    def test_hermes_transformer(self):
        transformer = get_transformer("hermes")
        task = ClawBenchTask(
            task_id="test-004",
            domain="security",
            difficulty="L4",
            instructions="Fourth test",
            skill_file="https://example.com/skill4.md",
            verifier_path="",
            weight=4,
        )
        result = transformer.transform(task)
        assert isinstance(result, ClawStyleInput)
        assert result.agent_type == "hermes"


class TestCodingStyleTransformers:
    def test_claude_code_transformer(self):
        transformer = get_transformer("claude_code")
        task = CodingTask(
            dataset="SWE-Bench",
            task_id="django__django-11099",
            instance_id="django__django-11099",
            repo="django/django",
            problem_statement="Fix the bug in URL resolver",
            hints="",
            created_at="2024-01-01",
            test_patch="",
            repo_version="1.0",
            hw_cost=1.5,
        )
        result = transformer.transform(task)
        assert isinstance(result, CodingStyleInput)
        assert result.agent_type == "claude_code"
        assert result.task_id == "django__django-11099"
        assert result.repo == "django/django"

    def test_codex_transformer(self):
        transformer = get_transformer("codex")
        task = CodingTask(
            dataset="SWE-Bench",
            task_id="pytest__pytest-1234",
            instance_id="pytest__pytest-1234",
            repo="pytest-dev/pytest",
            problem_statement="Fix fixture issue",
            hints="",
            created_at="2024-01-02",
            test_patch="",
            repo_version="2.0",
            hw_cost=2.0,
        )
        result = transformer.transform(task)
        assert isinstance(result, CodingStyleInput)
        assert result.agent_type == "codex"

    def test_opencode_transformer(self):
        transformer = get_transformer("opencode")
        task = CodingTask(
            dataset="SWE-Bench",
            task_id="requests__requests-5678",
            instance_id="requests__requests-5678",
            repo="psf/requests",
            problem_statement="Fix session handling",
            hints="",
            created_at="2024-01-03",
            test_patch="",
            repo_version="1.0",
            hw_cost=1.0,
        )
        result = transformer.transform(task)
        assert isinstance(result, CodingStyleInput)
        assert result.agent_type == "opencode"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
