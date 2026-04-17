"""
Agent Caller Module
===================
Calls different agents via bash or python to execute tasks.

Part I: Claw-Style Agents (openclaw, zeroclaw, nanobot, hermes)
Part II: Coding-Style Agents (claude code, cursor, opencode, kilo code, codex, droid, zed)
"""

from __future__ import annotations

import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AgentResponse:
    success: bool
    output: str
    error: str | None
    duration: float
    task_id: str


class AgentCaller(ABC):
    @abstractmethod
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse: ...


class OpenClawCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        cmd = [
            "docker",
            "run",
            "--rm",
            "-e",
            f"TASK_ID={task_input.get('task_id', '')}",
            "-e",
            f"SKILL_URL={task_input.get('skill_url', '')}",
            "openclaw:latest",
            "execute",
        ]
        return self._run_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_command(self, cmd: list[str], task_id: str, timeout: int) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class ZeroClawCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        cmd = [
            "docker",
            "run",
            "--rm",
            "-e",
            f"TASK={task_input.get('task_id', '')}",
            "zeroclaw:latest",
            "run",
        ]
        return self._run_bash_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_bash_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class NanobotCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        cmd = [
            "docker",
            "run",
            "--rm",
            "-e",
            f"NANOBOT_TASK={task_input.get('task_id', '')}",
            "nanobot:latest",
            "execute",
            "--task",
            task_input.get("task_id", ""),
        ]
        return self._run_python_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_python_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class HermesCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        cmd = [
            "docker",
            "run",
            "--rm",
            "-e",
            f"TASK_ID={task_input.get('task_id', '')}",
            "hermes-agent:latest",
            "run",
            "--skill",
            task_input.get("skill_url", ""),
        ]
        return self._run_sh_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_sh_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class ClaudeCodeCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(f"# Task: {task_input.get('task_id', '')}\n\n")
            f.write(f"## Problem\n{task_input.get('problem_statement', '')}\n\n")
            f.write(f"## Repository\n{task_input.get('repo', '')}\n\n")
            if task_input.get("test_patch"):
                f.write(f"## Test Patch\n{task_input['test_patch']}\n\n")
            f.flush()
            temp_path = f.name

        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "-p",
            f"Read the file at {temp_path} and complete the task.",
        ]
        return self._run_claude_command(
            cmd, task_input.get("task_id", ""), timeout, temp_path
        )

    def _run_claude_command(
        self, cmd: list[str], task_id: str, timeout: int, temp_path: str
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            Path(temp_path).unlink(missing_ok=True)
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            Path(temp_path).unlink(missing_ok=True)
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class CursorCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        cmd = [
            "cursor",
            "--task",
            task_input.get("task_id", ""),
            "--repo",
            task_input.get("repo", ""),
        ]
        return self._run_cursor_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_cursor_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class OpenCodeCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        cmd = [
            "opencode",
            "--task",
            task_input.get("task_id", ""),
            "--repo",
            task_input.get("repo", ""),
        ]
        return self._run_opencode_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_opencode_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class KiloCodeCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        cmd = [
            "npx",
            "@kilocode/cli",
            "--task",
            task_input.get("task_id", ""),
        ]
        return self._run_npm_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_npm_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class CodexCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        cmd = [
            "npx",
            "@openai/codex@0.57.0",
            "--task",
            task_input.get("task_id", ""),
        ]
        return self._run_codex_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_codex_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class DroidCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
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
        return self._run_droid_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_droid_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                " ".join(cmd),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


class ZedCaller(AgentCaller):
    def call(self, task_input: dict[str, Any], timeout: int = 300) -> AgentResponse:
        cmd = [
            "zed",
            "--task",
            task_input.get("task_id", ""),
        ]
        return self._run_zed_command(cmd, task_input.get("task_id", ""), timeout)

    def _run_zed_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
            )
        except subprocess.TimeoutExpired:
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
            )


CLAW_STYLE_CALLERS = {
    "openclaw": OpenClawCaller,
    "zeroclaw": ZeroClawCaller,
    "nanobot": NanobotCaller,
    "hermes": HermesCaller,
}

CODING_STYLE_CALLERS = {
    "claude_code": ClaudeCodeCaller,
    "cursor": CursorCaller,
    "opencode": OpenCodeCaller,
    "kilo_code": KiloCodeCaller,
    "codex": CodexCaller,
    "droid": DroidCaller,
    "zed": ZedCaller,
}


def get_caller(agent_type: str) -> AgentCaller:
    if agent_type in CLAW_STYLE_CALLERS:
        return CLAW_STYLE_CALLERS[agent_type]()
    if agent_type in CODING_STYLE_CALLERS:
        return CODING_STYLE_CALLERS[agent_type]()
    raise ValueError(f"Unknown agent type: {agent_type}")


if __name__ == "__main__":
    print("Claw-style callers:", list(CLAW_STYLE_CALLERS.keys()))
    print("Coding-style callers:", list(CODING_STYLE_CALLERS.keys()))
