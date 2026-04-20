"""
Agent Caller Module
==================
Calls different agents via bash or python to execute tasks.

Part I: Claw-Style Agents (openclaw, zeroclaw, nanobot, hermes)
Part II: Coding-Style Agents (claude code, cursor, opencode, kilo code, codex, droid, zed)

Usage:
    from experiments.AgentCallInterface.agents.agent_callers import get_caller

    caller = get_caller('nanobot')
    response = caller.call({
        'task_id': 'test-001',
        'problem_statement': 'What is 2+2?',
        'model': 'openrouter/free'  # optional, defaults to 'openrouter/free'
    }, timeout=90)
"""

from __future__ import annotations

import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.AgentCallInterface.utils.api_keys import get_openrouter_api_key


DEFAULT_MODEL = "openrouter/free"


@dataclass
class AgentResponse:
    success: bool
    output: str
    error: str | None
    duration: float
    task_id: str


class AgentCaller(ABC):
    @abstractmethod
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse: ...


def _run_command(cmd: list[str], task_id: str, timeout: int, env: dict = None) -> AgentResponse:
    import time

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
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


class OpenClawCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
        api_key = get_openrouter_api_key()
        cmd = [
            "docker",
            "exec",
            "-e",
            f"OPENROUTER_API_KEY={api_key}",
            "openclaw",
            "openclaw",
            "infer",
            "model",
            "run",
            "--local",
            "--model",
            f"openrouter/{model}",
            "--prompt",
            prompt,
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class ZeroClawCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
        cmd = [
            "docker",
            "exec",
            "zeroclaw",
            "/home/linuxbrew/.linuxbrew/Cellar/zeroclaw/0.6.9/bin/zeroclaw",
            "agent",
            "-m",
            prompt,
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class NanobotCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
        cmd = [
            "docker",
            "exec",
            "nanobot",
            "nanobot",
            "agent",
            "-m",
            prompt,
            "--no-markdown",
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class HermesCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        import base64
        prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
        api_key = get_openrouter_api_key()
        encoded = base64.b64encode(prompt.encode()).decode()
        cmd = [
            "docker",
            "exec",
            "hermes",
            "bash",
            "-c",
            f"echo {encoded} | base64 -d > /tmp/prompt.txt && export OPENROUTER_API_KEY=\"{api_key}\" && /root/.hermes/hermes-agent/venv/bin/hermes chat -q \"$(cat /tmp/prompt.txt)\" --provider openrouter",
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class ClaudeCodeCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
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
                cmd, capture_output=True, text=True, timeout=timeout, cwd="/tmp"
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
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        cmd = [
            "cursor",
            "--task",
            task_input.get("task_id", ""),
            "--repo",
            task_input.get("repo", ""),
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class OpenCodeCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
        api_key = get_openrouter_api_key()
        cmd = [
            "docker",
            "exec",
            "-e",
            f"OPENROUTER_API_KEY={api_key}",
            "opencode",
            "/root/.opencode/bin/opencode",
            "run",
            "-m",
            f"opencode/{model}",
            prompt,
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class KiloCodeCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
        cmd = [
            "docker",
            "exec",
            "kilo_code",
            "kilo",
            "run",
            "-m",
            f"kilo/{model}",
            "--auto",
            prompt,
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class CodexCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        import os
        from pathlib import Path

        prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
        api_key = get_openrouter_api_key()

        codex_dir = Path.home() / ".codex"
        codex_dir.mkdir(exist_ok=True)

        config_toml = codex_dir / "config.toml"
        config_toml.write_text(f'''model_provider = "openrouter"
model = "{model}"
disable_response_storage = true

[model_providers.openrouter]
name = "OpenRouter"
base_url = "https://openrouter.ai/api/v1"
wire_api = "responses"
requires_openai_auth = true
''')

        auth_json = codex_dir / "auth.json"
        auth_json.write_text(f'''{{
  "OPENAI_API_KEY": "{api_key}"
}}
''')

        env = os.environ.copy()
        env["OPENROUTER_API_KEY"] = api_key
        env["OPENAI_API_KEY"] = api_key

        cmd = [
            "codex", "exec",
            "--full-auto", "--skip-git-repo-check",
            "--", prompt,
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout, env=env)


class DroidCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
        api_key = get_openrouter_api_key()
        cmd = [
            "docker",
            "exec",
            "-e",
            f"FACTORY_API_KEY={api_key}",
            "droid",
            "droid",
            "exec",
            prompt,
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class ZedCaller(AgentCaller):
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        cmd = [
            "zed",
            "--task",
            task_input.get("task_id", ""),
        ]
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


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
    print(f"Default model: {DEFAULT_MODEL}")
