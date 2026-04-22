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
import re
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
    MODEL_ERROR_PATTERNS = (
        "Error calling LLM:",
        "Model request failed after",
        "Connection error.",
    )

    def _build_nanobot_config(self, model: str, api_key: str) -> dict[str, Any]:
        return {
            "providers": {
                "openrouter": {
                    "api_key": api_key,
                    "api_base": "https://openrouter.ai/api/v1",
                }
            },
            "agents": {
                "defaults": {
                    "model": model,
                    "provider": "openrouter",
                }
            },
        }

    def _parse_nanobot_response(self, response: AgentResponse) -> AgentResponse:
        if response.returncode != 0:
            return response
        for pattern in self.MODEL_ERROR_PATTERNS:
            if pattern in response.output:
                return AgentResponse(
                    success=False,
                    output=response.output,
                    error=pattern,
                    duration=response.duration,
                    task_id=response.task_id,
                    stderr=response.stderr,
                    returncode=response.returncode,
                )
        return response

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
        response = _run_command(cmd, task_input.get("task_id", ""), timeout)
        return self._parse_nanobot_response(response)


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
    RUNTIME_USER = "zi"
    RUN_ROOT = "/tmp/claude-code-runs"
    DEFAULT_BASE_URL = "https://openrouter.ai/api"
    OPENROUTER_PREFIX = "openrouter/"
    DEFAULT_OPENROUTER_MODEL = "minimax/minimax-m2.5:free"
    DEFAULT_MAX_TURNS = "8"

    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        task_id = task_input.get("task_id", "")
        claude_model = self._resolve_claude_model(model)

        prompt = self._build_task_prompt(task_input)
        run_id = str(task_input.get("run_id", task_input.get("task_id", "claude-code-run")))
        api_key = get_openrouter_api_key()
        cmd = self._build_claude_command(prompt, run_id, claude_model, api_key)
        return self._run_claude_command(cmd, task_id, timeout)

    def _resolve_claude_model(self, model: str) -> str:
        if model.startswith(self.OPENROUTER_PREFIX):
            model = model[len(self.OPENROUTER_PREFIX) :]

        if model in {"free", "auto"}:
            return self.DEFAULT_OPENROUTER_MODEL

        return model

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

    def _safe_run_id(self, run_id: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", run_id).strip("._-")
        return safe[:80] or "claude-code-run"

    def _build_claude_command(
        self,
        prompt: str,
        run_id: str = "claude-code-run",
        model: str = DEFAULT_MODEL,
        api_key: str = "",
    ) -> list[str]:
        safe_run_id = self._safe_run_id(run_id)
        max_turns = os.environ.get("CLAUDE_CODE_MAX_TURNS", self.DEFAULT_MAX_TURNS)
        run_dir = f"{self.RUN_ROOT}/{safe_run_id}"
        runtime_home = f"{run_dir}/home"
        runtime_workspace = f"{run_dir}/workspace"
        shell_command = (
            'set -e; '
            'export HOME="$CLAUDE_RUNTIME_HOME"; '
            'mkdir -p "$HOME/.claude" "$HOME/.cache" "$HOME/.config" "$CLAUDE_WORKSPACE"; '
            'if [ -f /home/zi/.claude/settings.json ] && [ ! -f "$HOME/.claude/settings.json" ]; then '
            'cp /home/zi/.claude/settings.json "$HOME/.claude/settings.json"; '
            'fi; '
            'cd "$CLAUDE_WORKSPACE"; '
            'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"; '
            'claude --dangerously-skip-permissions --verbose --model "$CLAUDE_MODEL" '
            '--max-turns "$CLAUDE_CODE_MAX_TURNS" '
            '--output-format stream-json --include-partial-messages -p "$1"'
        )
        return [
            "docker",
            "exec",
            "-u",
            self.RUNTIME_USER,
            "-w",
            "/tmp",
            "-e",
            f"HOME={runtime_home}",
            "-e",
            f"CLAUDE_RUNTIME_HOME={runtime_home}",
            "-e",
            f"CLAUDE_WORKSPACE={runtime_workspace}",
            "-e",
            f"ANTHROPIC_BASE_URL={self.DEFAULT_BASE_URL}",
            "-e",
            f"OPENROUTER_BASE_URL={self.DEFAULT_BASE_URL}",
            "-e",
            f"ANTHROPIC_AUTH_TOKEN={api_key}",
            "-e",
            "ANTHROPIC_API_KEY=",
            "-e",
            f"CLAUDE_MODEL={model}",
            "-e",
            f"ANTHROPIC_MODEL={model}",
            "-e",
            f"ANTHROPIC_SMALL_FAST_MODEL={model}",
            "-e",
            f"ANTHROPIC_DEFAULT_OPUS_MODEL={model}",
            "-e",
            f"ANTHROPIC_DEFAULT_SONNET_MODEL={model}",
            "-e",
            f"ANTHROPIC_DEFAULT_HAIKU_MODEL={model}",
            "-e",
            f"CLAUDE_CODE_SUBAGENT_MODEL={model}",
            "-e",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
            "-e",
            f"CLAUDE_CODE_MAX_TURNS={max_turns}",
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
        start = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return self._parse_claude_stream_response(
                result.stdout,
                result.stderr,
                result.returncode,
                time.time() - start,
                task_id,
            )
        except subprocess.TimeoutExpired as exc:
            response = self._parse_claude_stream_response(
                self._to_text(exc.stdout),
                self._to_text(exc.stderr),
                returncode=124,
                duration=timeout,
                task_id=task_id,
            )
            response.success = False
            response.error = response.error or f"Timeout after {timeout}s"
            response.returncode = None
            return response

    def _to_text(self, value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode(errors="replace")
        return value

    def _parse_claude_stream_response(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
        duration: float,
        task_id: str,
    ) -> AgentResponse:
        raw_output = stdout or ""
        stderr = stderr or ""
        if not raw_output.strip():
            return AgentResponse(
                success=False,
                output="",
                error=stderr.strip() or "Claude Code returned no stdout.",
                duration=duration,
                task_id=task_id,
                stderr=stderr,
                returncode=returncode,
            )

        text_parts: list[str] = []
        assistant_texts: list[str] = []
        final_payload: dict[str, Any] | None = None
        parse_errors = 0

        for line in raw_output.splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue

            if payload.get("type") == "result":
                final_payload = payload
                continue

            if payload.get("type") == "stream_event":
                event = payload.get("event") or {}
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta") or {}
                    if delta.get("type") == "text_delta":
                        text_parts.append(delta.get("text") or "")
                continue

            if payload.get("type") == "assistant":
                message = payload.get("message") or {}
                content = message.get("content") or []
                texts = [
                    item.get("text") or ""
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ]
                if texts:
                    assistant_texts.append("".join(texts))

        result_text = "".join(text_parts).strip()
        if not result_text and assistant_texts:
            result_text = "\n".join(text for text in assistant_texts if text.strip()).strip()
        if not result_text and final_payload and final_payload.get("result"):
            result_text = str(final_payload.get("result") or "").strip()

        is_error = bool(final_payload and final_payload.get("is_error"))
        success = returncode == 0 and not is_error and bool(result_text.strip())
        error = None

        if is_error:
            error = (
                (final_payload or {}).get("result")
                or result_text
                or stderr
                or "Claude Code returned an error result."
            )
        elif returncode != 0:
            error = stderr or result_text or "Claude Code command failed."
        elif not result_text.strip():
            used_models = ", ".join(((final_payload or {}).get("modelUsage") or {}).keys())
            model_note = f" Used model(s): {used_models}." if used_models else ""
            error = (
                "Claude Code stream did not contain assistant text."
                f"{model_note}"
            )
        elif parse_errors:
            error = None

        return AgentResponse(
            success=success,
            output=result_text,
            error=error,
            duration=duration,
            task_id=task_id,
            stderr=stderr,
            returncode=returncode,
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
    DEFAULT_OPENCODE_MODEL = "openrouter/minimax/minimax-m2.5:free"
    MODEL_ALIASES = {
        "openrouter/free": DEFAULT_OPENCODE_MODEL,
        "nvidia/nemotron-3-super-120b-a12b:free": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
        "nemotron-3-super-free": "opencode/nemotron-3-super-free",
    }

    def _resolve_model(self, model: str) -> str:
        if model in self.MODEL_ALIASES:
            return self.MODEL_ALIASES[model]
        if model.startswith(("opencode/", "openrouter/")):
            return model
        if "/" in model:
            return f"openrouter/{model}"
        if "/" not in model:
            return f"opencode/{model}"
        return model

    def _prepare_prompt(self, prompt: str) -> str:
        return (
            "OpenCode environment note: run inside project directory /opencode. "
            "When creating OpenCode skills, use exactly "
            "/opencode/.opencode/skills/<skill-name>/SKILL.md. "
            "Do not use /opencode/skills/*.md or /opencode/skill/*. "
            "The directory name must match the YAML name field. "
            "Every SKILL.md must start with YAML frontmatter delimited by --- lines "
            "and include at least name and description fields. "
            "For each skill, first create /opencode/.opencode/skills/<skill-name>, "
            "then write SKILL.md inside that directory. After writing skills, you can run "
            "/root/.opencode/bin/opencode debug skill to verify discovery before invoking a skill.\n\n"
            + prompt
        )

    def _build_opencode_command(self, prompt: str, model: str, api_key: str) -> list[str]:
        prepared_prompt = self._prepare_prompt(prompt)
        script = (
            f"mkdir -p {self.PROJECT_DIR} && cd {self.PROJECT_DIR} && "
            f"/root/.opencode/bin/opencode run --dir {self.PROJECT_DIR} "
            f"-m {shlex.quote(self._resolve_model(model))} "
            "--format json "
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
    CONTAINER_NAME = "kilo_code"
    PROJECT_DIR = "/kilo_eval_workspace"
    INNER_TIMEOUT_GRACE_SECONDS = 5
    HOST_TIMEOUT_GRACE_SECONDS = 10

    def _normalize_model(self, model: str) -> str:
        if model.startswith(("kilo/", "openrouter/")):
            return model
        if "/" in model:
            return f"openrouter/{model}"
        return f"kilo/{model}"

    def _run_id(self, task_id: str) -> str:
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in task_id)
        return f"kilo-eval-{safe or 'task'}"

    def _build_kilo_command(
        self,
        prompt: str,
        model: str,
        api_key: str,
        task_id: str,
        timeout: int,
    ) -> tuple[list[str], str]:
        run_id = self._run_id(task_id)
        project_dir = shlex.quote(self.PROJECT_DIR)
        quoted_model = shlex.quote(self._normalize_model(model))
        quoted_timeout = shlex.quote(str(timeout))
        script = (
            "set -u; "
            f"mkdir -p {project_dir}; "
            f"cd {project_dir}; "
            'KILO_PROMPT="$(printf %s "$KILO_PROMPT_B64" | base64 -d)"; '
            f"timeout --kill-after={self.INNER_TIMEOUT_GRACE_SECONDS}s {quoted_timeout}s "
            f"kilo run --dir {project_dir} -m {quoted_model} --auto "
            "--format json "
            '--title "$KILO_EVAL_RUN_ID" "$KILO_PROMPT"'
        )
        return (
            _docker_bash_command(
                self.CONTAINER_NAME,
                script,
                {
                    "OPENROUTER_API_KEY": api_key,
                    "KILO_PROMPT_B64": _encode_text(prompt),
                    "KILO_EVAL_RUN_ID": run_id,
                },
            ),
            run_id,
        )

    def _to_text(self, value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode(errors="replace")
        return value

    def _combine_output(self, stdout: str | bytes | None, stderr: str | bytes | None) -> str:
        stdout_text = self._to_text(stdout)
        stderr_text = self._to_text(stderr)
        sections = []
        if stdout_text:
            sections.append("=== STDOUT ===\n" + stdout_text)
        if stderr_text:
            sections.append("=== STDERR ===\n" + stderr_text)
        return "\n".join(sections)

    def _cleanup_after_timeout(self, run_id: str) -> None:
        script = r'''
marker="${KILO_EVAL_RUN_ID:?}"
terminate_matches() {
    signal="$1"
    for d in /proc/[0-9]*; do
        pid="${d#/proc/}"
        [ "$pid" = "$$" ] && continue
        cmd="$(tr '\0' ' ' < "$d/cmdline" 2>/dev/null || true)"
        case "$cmd" in
            *"kilo run"*"$marker"*|*".kilo run"*"$marker"*)
                kill "-$signal" "$pid" 2>/dev/null || true
                ;;
        esac
    done
}
terminate_matches TERM
sleep 1
terminate_matches KILL
'''
        try:
            subprocess.run(
                _docker_bash_command(
                    self.CONTAINER_NAME,
                    script,
                    {"KILO_EVAL_RUN_ID": run_id},
                ),
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass

    def _run_kilo_command(
        self, cmd: list[str], task_id: str, timeout: int, run_id: str
    ) -> AgentResponse:
        start = time.time()
        host_timeout = timeout + self.HOST_TIMEOUT_GRACE_SECONDS
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=host_timeout)
        except subprocess.TimeoutExpired as exc:
            stdout = self._to_text(exc.stdout)
            stderr = self._to_text(exc.stderr)
            self._cleanup_after_timeout(run_id)
            return AgentResponse(
                success=False,
                output=self._combine_output(stdout, stderr),
                error=f"Timeout after {timeout}s",
                duration=time.time() - start,
                task_id=task_id,
                stderr=stderr,
                returncode=None,
            )

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        combined = self._combine_output(stdout, stderr)
        timed_out = result.returncode in (124, 137)
        if timed_out:
            self._cleanup_after_timeout(run_id)
        success = result.returncode == 0
        error = None
        if timed_out:
            error = f"Timeout after {timeout}s"
        elif not success:
            error = stderr or stdout or "Kilo Code command failed"
        return AgentResponse(
            success=success,
            output=combined,
            error=error,
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
        task_id = task_input.get("task_id", "")
        api_key = get_openrouter_api_key()
        cmd, run_id = self._build_kilo_command(prompt, model, api_key, task_id, timeout)
        return self._run_kilo_command(cmd, task_id, timeout, run_id)


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
