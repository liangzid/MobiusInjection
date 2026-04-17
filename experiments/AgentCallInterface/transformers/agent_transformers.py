"""
Agent Input Transformers
========================
Transforms benchmark tasks into the input format required by different agents.

Part I: Claw-Style Agents (openclaw, zeroclaw, nanobot, hermes)
Part II: Coding-Style Agents (claude code, cursor, opencode, kilo code, codex, droid, zed)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from experiments.AgentCallInterface.datasets.clawbench_loader import ClawBenchTask
from experiments.AgentCallInterface.datasets.coding_benchmark_loader import (
    CodingTask,
    HumanEvalTask,
)


class Transformer(Protocol):
    def transform(self, task: Any) -> dict[str, Any]: ...


@dataclass
class ClawStyleInput:
    agent_type: str
    task_id: str
    skill_url: str
    task_instructions: str
    extra_context: dict[str, Any]


@dataclass
class CodingStyleInput:
    agent_type: str
    task_id: str
    instance_id: str
    repo: str
    problem_statement: str
    test_patch: str
    environment_setup: str


class OpenClawTransformer:
    def transform(self, task: ClawBenchTask) -> ClawStyleInput:
        return ClawStyleInput(
            agent_type="openclaw",
            task_id=task.task_id,
            skill_url=task.skill_file,
            task_instructions=task.instructions,
            extra_context={
                "domain": task.domain,
                "difficulty": task.difficulty,
                "weight": task.weight,
            },
        )


class ZeroClawTransformer:
    def transform(self, task: ClawBenchTask) -> ClawStyleInput:
        return ClawStyleInput(
            agent_type="zeroclaw",
            task_id=task.task_id,
            skill_url=task.skill_file,
            task_instructions=task.instructions,
            extra_context={
                "domain": task.domain,
                "difficulty": task.difficulty,
            },
        )


class NanobotTransformer:
    def transform(self, task: ClawBenchTask) -> ClawStyleInput:
        return ClawStyleInput(
            agent_type="nanobot",
            task_id=task.task_id,
            skill_url=task.skill_file,
            task_instructions=task.instructions,
            extra_context={
                "domain": task.domain,
                "difficulty": task.difficulty,
            },
        )


class HermesTransformer:
    def transform(self, task: ClawBenchTask) -> ClawStyleInput:
        return ClawStyleInput(
            agent_type="hermes",
            task_id=task.task_id,
            skill_url=task.skill_file,
            task_instructions=task.instructions,
            extra_context={
                "domain": task.domain,
                "difficulty": task.difficulty,
            },
        )


class ClaudeCodeTransformer:
    def transform(self, task: CodingTask) -> CodingStyleInput:
        return CodingStyleInput(
            agent_type="claude_code",
            task_id=task.task_id,
            instance_id=task.instance_id,
            repo=task.repo,
            problem_statement=task.problem_statement,
            test_patch=task.test_patch,
            environment_setup=self._build_env_setup(task),
        )

    def _build_env_setup(self, task: CodingTask) -> str:
        return f"""Setup environment:
1. Clone repository: {task.repo}
2. Apply patch if needed
3. Run tests to reproduce issue
4. Implement fix
"""


class CursorTransformer:
    def transform(self, task: CodingTask) -> CodingStyleInput:
        return CodingStyleInput(
            agent_type="cursor",
            task_id=task.task_id,
            instance_id=task.instance_id,
            repo=task.repo,
            problem_statement=task.problem_statement,
            test_patch=task.test_patch,
            environment_setup=self._build_env_setup(task),
        )

    def _build_env_setup(self, task: CodingTask) -> str:
        return f"""Project: {task.repo}
Issue: {task.problem_statement[:500]}
"""


class OpenCodeTransformer:
    def transform(self, task: CodingTask) -> CodingStyleInput:
        return CodingStyleInput(
            agent_type="opencode",
            task_id=task.task_id,
            instance_id=task.instance_id,
            repo=task.repo,
            problem_statement=task.problem_statement,
            test_patch=task.test_patch,
            environment_setup=self._build_env_setup(task),
        )

    def _build_env_setup(self, task: CodingTask) -> str:
        return f"""Task: {task.task_id}
Repository: {task.repo}
"""


class KiloCodeTransformer:
    def transform(self, task: CodingTask) -> CodingStyleInput:
        return CodingStyleInput(
            agent_type="kilo_code",
            task_id=task.task_id,
            instance_id=task.instance_id,
            repo=task.repo,
            problem_statement=task.problem_statement,
            test_patch=task.test_patch,
            environment_setup="",
        )


class CodexTransformer:
    def transform(self, task: CodingTask) -> CodingStyleInput:
        return CodingStyleInput(
            agent_type="codex",
            task_id=task.task_id,
            instance_id=task.instance_id,
            repo=task.repo,
            problem_statement=task.problem_statement,
            test_patch=task.test_patch,
            environment_setup=self._build_env_setup(task),
        )

    def _build_env_setup(self, task: CodingTask) -> str:
        return f"""# {task.repo}
{task.problem_statement}
"""


class DroidTransformer:
    def transform(self, task: CodingTask) -> CodingStyleInput:
        return CodingStyleInput(
            agent_type="droid",
            task_id=task.task_id,
            instance_id=task.instance_id,
            repo=task.repo,
            problem_statement=task.problem_statement,
            test_patch=task.test_patch,
            environment_setup="",
        )


class ZedTransformer:
    def transform(self, task: CodingTask) -> CodingStyleInput:
        return CodingStyleInput(
            agent_type="zed",
            task_id=task.task_id,
            instance_id=task.instance_id,
            repo=task.repo,
            problem_statement=task.problem_statement,
            test_patch=task.test_patch,
            environment_setup=self._build_env_setup(task),
        )

    def _build_env_setup(self, task: CodingTask) -> str:
        return f"""# {task.task_id}
## Repository
{task.repo}

## Problem
{task.problem_statement}
"""


CLAW_STYLE_TRANSFORMERS = {
    "openclaw": OpenClawTransformer,
    "zeroclaw": ZeroClawTransformer,
    "nanobot": NanobotTransformer,
    "hermes": HermesTransformer,
}

CODING_STYLE_TRANSFORMERS = {
    "claude_code": ClaudeCodeTransformer,
    "cursor": CursorTransformer,
    "opencode": OpenCodeTransformer,
    "kilo_code": KiloCodeTransformer,
    "codex": CodexTransformer,
    "droid": DroidTransformer,
    "zed": ZedTransformer,
}


def get_transformer(agent_type: str) -> Transformer:
    if agent_type in CLAW_STYLE_TRANSFORMERS:
        return CLAW_STYLE_TRANSFORMERS[agent_type]()
    if agent_type in CODING_STYLE_TRANSFORMERS:
        return CODING_STYLE_TRANSFORMERS[agent_type]()
    raise ValueError(f"Unknown agent type: {agent_type}")


if __name__ == "__main__":
    print("Claw-style transformers:", list(CLAW_STYLE_TRANSFORMERS.keys()))
    print("Coding-style transformers:", list(CODING_STYLE_TRANSFORMERS.keys()))
