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

import base64
import json
import os
import shlex
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
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
    stderr: str = ""
    returncode: int | None = None


class AgentCaller(ABC):
    @abstractmethod
    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse: ...


def _run_command(cmd: list[str], task_id: str, timeout: int, env: dict = None) -> AgentResponse:
    start = time.time()
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=run_env)
        return AgentResponse(
            success=result.returncode == 0,
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else None,
            duration=time.time() - start,
            task_id=task_id,
            stderr=result.stderr,
            returncode=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return AgentResponse(
            success=False,
            output="",
            error=f"Timeout after {timeout}s",
            duration=timeout,
            task_id=task_id,
            returncode=None,
        )


def _prompt_from(task_input: dict[str, Any]) -> str:
    return task_input.get("problem_statement", task_input.get("task_id", ""))


def _encode_text(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


def _docker_bash_command(container: str, script: str, env_vars: dict[str, str] | None = None) -> list[str]:
    cmd = ["docker", "exec"]
    for key, value in (env_vars or {}).items():
        cmd.extend(["-e", f"{key}={value}"])
    cmd.extend([container, "bash", "-lc", script])
    return cmd


def _decode_b64(var_name: str) -> str:
    return f'$(printf %s "${{{var_name}}}" | base64 -d)'


class OpenClawCaller(AgentCaller):
    PROFILE_NAME = "mobius-eval"

    def _normalize_openclaw_model(self, model: str) -> str:
        if model.startswith("openrouter/"):
            return model
        return f"openrouter/{model}"

    def _build_openclaw_command(self, prompt: str, model: str, api_key: str) -> list[str]:
        prompt_b64 = _encode_text(prompt)
        quoted_model = shlex.quote(self._normalize_openclaw_model(model))
        script = (
            f'openclaw --profile {self.PROFILE_NAME} infer model run '
            f'--local --json --model {quoted_model} --prompt "{_decode_b64("OPENCLAW_PROMPT_B64")}"'
        )
        return _docker_bash_command(
            "openclaw",
            script,
            {
                "OPENROUTER_API_KEY": api_key,
                "OPENCLAW_PROMPT_B64": prompt_b64,
            },
        )

    def _parse_openclaw_output(self, raw_output: str) -> tuple[bool, str, str | None]:
        json_start = raw_output.find("{")
        if json_start == -1:
            return False, raw_output, "OpenClaw did not return JSON output"
        payload = json.loads(raw_output[json_start:])
        outputs = payload.get("outputs", [])
        text_output = "\n".join(item.get("text", "") for item in outputs).strip()
        generated = "couldn't generate a response" not in text_output.lower()
        success = bool(payload.get("ok")) and generated
        error = None if success else text_output or raw_output.strip()
        return success, text_output or raw_output.strip(), error

    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = _prompt_from(task_input)
        api_key = get_openrouter_api_key()
        cmd = self._build_openclaw_command(prompt, model, api_key)
        response = _run_command(cmd, task_input.get("task_id", ""), timeout)
        if not response.output.strip():
            return response
        try:
            success, output, error = self._parse_openclaw_output(response.output)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            return AgentResponse(
                success=False,
                output=response.output,
                error=str(exc),
                duration=response.duration,
                task_id=response.task_id,
                stderr=response.stderr,
                returncode=response.returncode,
            )
        return AgentResponse(
            success=success,
            output=output,
            error=error,
            duration=response.duration,
            task_id=response.task_id,
            stderr=response.stderr,
            returncode=response.returncode,
        )


class ZeroClawCaller(AgentCaller):
    def _build_zeroclaw_command(self, prompt: str, model: str, api_key: str) -> list[str]:
        prompt_b64 = _encode_text(prompt)
        quoted_model = shlex.quote(model)
        script = (
            "/home/linuxbrew/.linuxbrew/Cellar/zeroclaw/0.6.9/bin/zeroclaw agent "
            f"-p openrouter --model {quoted_model} -m \"{_decode_b64('ZEROCLAW_PROMPT_B64')}\""
        )
        return _docker_bash_command(
            "zeroclaw",
            script,
            {
                "OPENROUTER_API_KEY": api_key,
                "ZEROCLAW_PROMPT_B64": prompt_b64,
            },
        )

    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = _prompt_from(task_input)
        api_key = get_openrouter_api_key()
        cmd = self._build_zeroclaw_command(prompt, model, api_key)
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class NanobotCaller(AgentCaller):
    TEMP_CONFIG_PATH = "/tmp/nanobot_eval_config.json"

    def _build_nanobot_config(self, model: str, api_key: str) -> dict[str, Any]:
        return {
            "providers": {
                "openrouter": {
                    "api_key": api_key,
                    "base_url": "https://openrouter.ai/api/v1",
                }
            },
            "agents": {
                "defaults": {
                    "model": model,
                }
            },
        }

    def _build_nanobot_command(self, prompt: str, model: str, api_key: str) -> list[str]:
        config_text = json.dumps(self._build_nanobot_config(model, api_key))
        script = (
            "python -c \"import base64, os, pathlib; "
            f"pathlib.Path('{self.TEMP_CONFIG_PATH}').write_text(base64.b64decode(os.environ['NANOBOT_CONFIG_B64']).decode())\""
            f" && nanobot agent --config {self.TEMP_CONFIG_PATH} -m \"{_decode_b64('NANOBOT_PROMPT_B64')}\" --no-markdown"
        )
        return _docker_bash_command(
            "nanobot",
            script,
            {
                "NANOBOT_CONFIG_B64": _encode_text(config_text),
                "NANOBOT_PROMPT_B64": _encode_text(prompt),
            },
        )

    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = _prompt_from(task_input)
        api_key = get_openrouter_api_key()
        cmd = self._build_nanobot_command(prompt, model, api_key)
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class HermesCaller(AgentCaller):
    def _build_hermes_command(self, prompt: str, model: str, api_key: str) -> list[str]:
        script = (
            "source ~/.local/bin/env && /root/.hermes/hermes-agent/venv/bin/hermes chat "
            f"--provider openrouter --model {shlex.quote(model)} -Q -q \"{_decode_b64('HERMES_PROMPT_B64')}\""
        )
        return _docker_bash_command(
            "hermes",
            script,
            {
                "OPENROUTER_API_KEY": api_key,
                "HERMES_PROMPT_B64": _encode_text(prompt),
            },
        )

    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = _prompt_from(task_input)
        api_key = get_openrouter_api_key()
        cmd = self._build_hermes_command(prompt, model, api_key)
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class ClaudeCodeCaller(AgentCaller):
    CONTAINER_NAME = "claude_code"

    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = self._build_task_prompt(task_input)
        cmd = self._build_claude_command(prompt)
        return self._run_claude_command(cmd, task_input.get("task_id", ""), timeout)

    def _build_task_prompt(self, task_input: dict[str, Any]) -> str:
        prompt = [
            f"# Task: {task_input.get('task_id', '')}",
            "",
            f"## Problem\n{task_input.get('problem_statement', '')}",
            "",
            f"## Repository\n{task_input.get('repo', '')}",
        ]
        if task_input.get("test_patch"):
            prompt.extend(["", f"## Test Patch\n{task_input['test_patch']}"])
        return "\n".join(prompt)

    def _build_claude_command(self, prompt: str) -> list[str]:
        shell_command = (
            'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)" && '
            'claude --dangerously-skip-permissions -p "$1"'
        )
        return [
            "docker",
            "exec",
            "-w",
            "/tmp",
            self.CONTAINER_NAME,
            "bash",
            "-lc",
            shell_command,
            "claude-code-runner",
            prompt,
        ]

    def _run_claude_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        import time

        start = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return AgentResponse(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                duration=time.time() - start,
                task_id=task_id,
                stderr=result.stderr,
                returncode=result.returncode,
            )
        except subprocess.TimeoutExpired:
            # Path(temp_path).unlink(missing_ok=True)
            return AgentResponse(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                duration=timeout,
                task_id=task_id,
                returncode=None,
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
    PROJECT_DIR = "/opencode"
    DEFAULT_OPENCODE_MODEL = "opencode/big-pickle"
    MODEL_ALIASES = {
        "openrouter/free": DEFAULT_OPENCODE_MODEL,
        "nvidia/nemotron-3-super-120b-a12b:free": "opencode/nemotron-3-super-free",
        "nemotron-3-super-free": "opencode/nemotron-3-super-free",
    }

    def _resolve_model(self, model: str) -> str:
        if model in self.MODEL_ALIASES:
            return self.MODEL_ALIASES[model]
        if model.startswith("opencode/"):
            return model
        if "/" not in model:
            return f"opencode/{model}"
        return model

    def _prepare_prompt(self, prompt: str) -> str:
        return (
            "OpenCode environment note: run inside project directory /opencode. "
            "When creating OpenCode skills, use exactly "
            ".opencode/skills/<skill-name>/SKILL.md under /opencode. "
            "Do not use /opencode/skills/*.md or /opencode/skill/*. "
            "The directory name must match the YAML name field.\n\n"
            + prompt
        )

    def _build_opencode_command(self, prompt: str, model: str, api_key: str) -> list[str]:
        prepared_prompt = self._prepare_prompt(prompt)
        script = (
            f"mkdir -p {self.PROJECT_DIR} && cd {self.PROJECT_DIR} && "
            f"/root/.opencode/bin/opencode run --dir {self.PROJECT_DIR} "
            f"-m {shlex.quote(self._resolve_model(model))} "
            "--dangerously-skip-permissions "
            f"\"{_decode_b64('OPENCODE_PROMPT_B64')}\""
        )
        return _docker_bash_command(
            "opencode",
            script,
            {
                "OPENROUTER_API_KEY": api_key,
                "OPENCODE_PROMPT_B64": _encode_text(prepared_prompt),
            },
        )

    def _combine_output(self, stdout: str | bytes | None, stderr: str | bytes | None) -> str:
        stdout_text = self._to_text(stdout)
        stderr_text = self._to_text(stderr)
        sections = []
        if stdout_text:
            sections.append("=== STDOUT ===\n" + stdout_text)
        if stderr_text:
            sections.append("=== STDERR ===\n" + stderr_text)
        return "\n".join(sections)

    def _to_text(self, value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode(errors="replace")
        return value

    def _looks_like_error(self, stderr: str) -> bool:
        error_markers = (
            "Error:",
            "ProviderModelNotFoundError",
            "Model not found",
            "API Error:",
        )
        return any(marker in stderr for marker in error_markers)

    def _cleanup_after_timeout(self, cmd: list[str]) -> None:
        if "docker" not in cmd[:1] or "opencode" not in cmd:
            return
        try:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    "opencode",
                    "bash",
                    "-lc",
                    "pkill -f '/root/.opencode/bin/opencode run --dir /opencode' || true",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass

    def _run_opencode_command(
        self, cmd: list[str], task_id: str, timeout: int
    ) -> AgentResponse:
        start = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            stdout = self._to_text(exc.stdout)
            stderr = self._to_text(exc.stderr)
            combined = self._combine_output(stdout, stderr)
            self._cleanup_after_timeout(cmd)
            return AgentResponse(
                success=False,
                output=combined,
                error=f"Timeout after {timeout}s",
                duration=time.time() - start,
                task_id=task_id,
                stderr=stderr,
                returncode=None,
            )

        stderr = result.stderr or ""
        combined = self._combine_output(result.stdout, stderr)
        success = result.returncode == 0 and not self._looks_like_error(stderr)
        return AgentResponse(
            success=success,
            output=combined,
            error=None if success else stderr or "OpenCode command failed",
            duration=time.time() - start,
            task_id=task_id,
            stderr=stderr,
            returncode=result.returncode,
        )

    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = task_input.get("problem_statement", task_input.get("task_id", ""))
        api_key = get_openrouter_api_key()
        cmd = self._build_opencode_command(prompt, model, api_key)
        return self._run_opencode_command(cmd, task_input.get("task_id", ""), timeout)


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
