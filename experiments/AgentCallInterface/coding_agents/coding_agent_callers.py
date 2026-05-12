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

from experiments.AgentCallInterface.utils.api_keys import (
    get_aigocode_api_key,
    get_aigocode_base_url,
    get_aigocode_provider_api_key,
    get_openrouter_api_key,
)


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
    raw_output: str = ""


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


def _container_name_from(task_input: dict[str, Any], default: str) -> str:
    container_name = str(task_input.get("container_name") or default).strip()
    if not container_name:
        raise ValueError("container_name must not be empty")
    return container_name


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


def _toml_string_array(values: tuple[str, ...]) -> str:
    return json.dumps(list(values), indent=4)


class OpenClawCaller(AgentCaller):
    CONTAINER_NAME = "openclaw"
    PROFILE_NAME = "mobius-eval"
    MODEL_OVERRIDE_NOT_ALLOWED = "Model override"

    def _normalize_openclaw_model(self, model: str) -> str:
        if model.startswith("openrouter/"):
            return model
        return f"openrouter/{model}"

    def _build_openclaw_command(
        self,
        prompt: str,
        model: str,
        api_key: str,
        container_name: str | None = None,
        allow_model_override: bool = True,
    ) -> list[str]:
        prompt_b64 = _encode_text(prompt)
        model_option = ""
        if allow_model_override:
            quoted_model = shlex.quote(self._normalize_openclaw_model(model))
            model_option = f" --model {quoted_model}"
        script = (
            f'openclaw --profile {self.PROFILE_NAME} infer model run '
            f'--local --json{model_option} --prompt "{_decode_b64("OPENCLAW_PROMPT_B64")}"'
        )
        return _docker_bash_command(
            container_name or self.CONTAINER_NAME,
            script,
            {
                "OPENROUTER_API_KEY": api_key,
                "OPENCLAW_PROMPT_B64": prompt_b64,
            },
        )

    def _build_openclaw_set_primary_model_command(
        self,
        model: str,
        api_key: str,
        container_name: str | None = None,
    ) -> list[str]:
        normalized_model = self._normalize_openclaw_model(model)
        quoted_model = shlex.quote(normalized_model)
        script = (
            f"openclaw --profile {self.PROFILE_NAME} config set "
            f"agents.defaults.model.primary {quoted_model}"
        )
        return _docker_bash_command(
            container_name or self.CONTAINER_NAME,
            script,
            {"OPENROUTER_API_KEY": api_key},
        )

    def _is_model_override_rejected(self, response: AgentResponse) -> bool:
        if response.returncode == 0:
            return False
        haystack = "\n".join(part for part in (response.output, response.stderr, response.error or "") if part)
        return (
            self.MODEL_OVERRIDE_NOT_ALLOWED in haystack
            and "not allowed for agent" in haystack
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
        container_name = _container_name_from(task_input, self.CONTAINER_NAME)
        api_key = get_openrouter_api_key()
        task_id = task_input.get("task_id", "")
        # OpenClaw eval profile may block runtime --model overrides.
        # Set profile default model first, then run inference without --model.
        set_model_cmd = self._build_openclaw_set_primary_model_command(model, api_key, container_name)
        set_model_response = _run_command(set_model_cmd, task_id, min(timeout, 90))
        if set_model_response.returncode != 0:
            return AgentResponse(
                success=False,
                output=set_model_response.output,
                error=set_model_response.error or "Failed to set OpenClaw primary model",
                duration=set_model_response.duration,
                task_id=task_id,
                stderr=set_model_response.stderr,
                returncode=set_model_response.returncode,
            )

        cmd = self._build_openclaw_command(
            prompt,
            model,
            api_key,
            container_name,
            allow_model_override=False,
        )
        response = _run_command(cmd, task_id, timeout)

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
    CONTAINER_NAME = "zeroclaw"
    CONFIG_DIR_TEMPLATE = "/tmp/zeroclaw-eval-config.XXXXXX"
    MAX_TOOL_ITERATIONS = 40
    EVAL_ALLOWED_COMMANDS = (
        "bash",
        "sh",
        "ls",
        "cat",
        "grep",
        "find",
        "echo",
        "printf",
        "pwd",
        "wc",
        "head",
        "tail",
        "date",
        "python",
        "python3",
        "node",
        "mkdir",
        "touch",
        "cp",
        "mv",
        "tee",
        "sed",
        "awk",
    )
    EVAL_FORBIDDEN_PATHS = (
        "/etc",
        "/root",
        "/home",
        "/usr",
        "/bin",
        "/sbin",
        "/lib",
        "/opt",
        "/boot",
        "/dev",
        "/proc",
        "/sys",
        "/var",
        "~/.ssh",
        "~/.gnupg",
        "~/.aws",
        "~/.config",
    )
    EVAL_AUTO_APPROVE_TOOLS = (
        "shell",
        "file_read",
        "file_write",
        "memory_recall",
        "glob_search",
        "content_search",
        "calculator",
    )
    EVAL_ALLOWED_ROOTS = ("/tmp", "/workspace")

    def _build_eval_config(self) -> str:
        return f"""
default_provider = "openrouter"
default_temperature = 0.0
provider_timeout_secs = 120

[autonomy]
level = "full"
workspace_only = true
allowed_commands = {_toml_string_array(self.EVAL_ALLOWED_COMMANDS)}
forbidden_paths = {_toml_string_array(self.EVAL_FORBIDDEN_PATHS)}
max_actions_per_hour = 200
max_cost_per_day_cents = 500
require_approval_for_medium_risk = false
block_high_risk_commands = true
auto_approve = {_toml_string_array(self.EVAL_AUTO_APPROVE_TOOLS)}
always_ask = []
allowed_roots = {_toml_string_array(self.EVAL_ALLOWED_ROOTS)}
non_cli_excluded_tools = []
shell_env_passthrough = []
shell_timeout_secs = 120

[agent]
compact_context = true
max_tool_iterations = {self.MAX_TOOL_ITERATIONS}
max_history_messages = 50
max_context_tokens = 32000
max_tool_result_chars = 50000
parallel_tools = false
""".strip()

    def _build_zeroclaw_command(
        self,
        prompt: str,
        model: str,
        api_key: str,
        container_name: str | None = None,
    ) -> list[str]:
        prompt_b64 = _encode_text(prompt)
        config_b64 = _encode_text(self._build_eval_config())
        quoted_model = shlex.quote(model)
        script = (
            f'ZEROCLAW_EVAL_CONFIG_DIR="$(mktemp -d {self.CONFIG_DIR_TEMPLATE})" && '
            'printf %s "$ZEROCLAW_EVAL_CONFIG_B64" | base64 -d > "$ZEROCLAW_EVAL_CONFIG_DIR/config.toml" && '
            'chmod 600 "$ZEROCLAW_EVAL_CONFIG_DIR/config.toml" && '
            'export ZEROCLAW_API_KEY="$OPENROUTER_API_KEY" API_KEY="$OPENROUTER_API_KEY" && '
            "/home/linuxbrew/.linuxbrew/Cellar/zeroclaw/0.6.9/bin/zeroclaw agent "
            '--config-dir "$ZEROCLAW_EVAL_CONFIG_DIR" '
            f"-p openrouter --model {quoted_model} -m \"{_decode_b64('ZEROCLAW_PROMPT_B64')}\""
        )
        return _docker_bash_command(
            container_name or self.CONTAINER_NAME,
            script,
            {
                "OPENROUTER_API_KEY": api_key,
                "ZEROCLAW_PROMPT_B64": prompt_b64,
                "ZEROCLAW_EVAL_CONFIG_B64": config_b64,
            },
        )

    def call(
        self,
        task_input: dict[str, Any],
        timeout: int = 300,
        model: str = DEFAULT_MODEL,
    ) -> AgentResponse:
        prompt = _prompt_from(task_input)
        container_name = _container_name_from(task_input, self.CONTAINER_NAME)
        api_key = get_openrouter_api_key()
        cmd = self._build_zeroclaw_command(prompt, model, api_key, container_name)
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
    CONTAINER_NAME = "hermes"

    def _build_hermes_command(
        self,
        prompt: str,
        model: str,
        api_key: str,
        container_name: str | None = None,
    ) -> list[str]:
        script = (
            "source ~/.local/bin/env && /root/.hermes/hermes-agent/venv/bin/hermes chat "
            f"--provider openrouter --model {shlex.quote(model)} -Q -q \"{_decode_b64('HERMES_PROMPT_B64')}\""
        )
        return _docker_bash_command(
            container_name or self.CONTAINER_NAME,
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
        container_name = _container_name_from(task_input, self.CONTAINER_NAME)
        api_key = get_openrouter_api_key()
        cmd = self._build_hermes_command(prompt, model, api_key, container_name)
        return _run_command(cmd, task_input.get("task_id", ""), timeout)


class ClaudeCodeCaller(AgentCaller):
    CONTAINER_NAME = "claude_code"
    RUNTIME_USER = "zi"
    RUN_ROOT = "/tmp/claude-code-runs"
    DEFAULT_BASE_URL = "https://openrouter.ai/api"
    OPENROUTER_PREFIX = "openrouter/"
    DEFAULT_OPENROUTER_MODEL = "minimax/minimax-m2.5:free"
    DEFAULT_MAX_TURNS = "60"
    LOCAL_BASE_URL_ENV = "CLAUDE_CODE_BASE_URL"
    LOCAL_API_KEY_ENV = "CLAUDE_CODE_API_KEY"
    CONTAINER_NAME_ENV = "CLAUDE_CODE_CONTAINER_NAME"

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
        base_url = self._base_url()
        api_key = self._api_key() if self._local_base_url() else get_openrouter_api_key()
        container_name = os.environ.get(self.CONTAINER_NAME_ENV, self.CONTAINER_NAME)
        cmd = self._build_claude_command(
            prompt,
            run_id,
            claude_model,
            api_key,
            base_url=base_url,
            container_name=container_name,
        )
        return self._run_claude_command(cmd, task_id, timeout)

    def _local_base_url(self) -> str:
        return os.environ.get(self.LOCAL_BASE_URL_ENV, "").strip()

    def _base_url(self) -> str:
        return self._local_base_url() or self.DEFAULT_BASE_URL

    def _api_key(self) -> str:
        return os.environ.get(self.LOCAL_API_KEY_ENV, "ollama-local").strip()

    def _resolve_claude_model(self, model: str) -> str:
        if model.startswith(self.OPENROUTER_PREFIX):
            model = model[len(self.OPENROUTER_PREFIX) :]
        if model.startswith("ollama/"):
            model = model[len("ollama/") :]

        if model in {"free", "auto"}:
            return self.DEFAULT_OPENROUTER_MODEL

        return model

    def _build_task_prompt(self, task_input: dict[str, Any]) -> str:
        prompt = [
            f"# Task: {task_input.get('task_id', '')}",
            "",
            "## Claude Code Environment",
            (
                "Use the current workspace. Project instructions in CLAUDE.md "
                "and project skills in skills/ or .claude/skills are part of "
                "the task context; for code tasks, load the relevant project "
                "skill before final answer when one is available."
            ),
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
        base_url: str | None = None,
        container_name: str = CONTAINER_NAME,
    ) -> list[str]:
        safe_run_id = self._safe_run_id(run_id)
        max_turns = os.environ.get("CLAUDE_CODE_MAX_TURNS", self.DEFAULT_MAX_TURNS)
        run_dir = f"{self.RUN_ROOT}/{safe_run_id}"
        runtime_home = f"{run_dir}/home"
        runtime_workspace = f"{run_dir}/workspace"
        resolved_base_url = base_url or self.DEFAULT_BASE_URL
        anthropic_api_key = api_key if resolved_base_url != self.DEFAULT_BASE_URL else ""
        settings = {
            "env": {
                "ANTHROPIC_BASE_URL": resolved_base_url,
                "OPENROUTER_BASE_URL": resolved_base_url,
            }
        }
        shell_command = (
            'set -e; '
            'export HOME="$CLAUDE_RUNTIME_HOME"; '
            'mkdir -p "$HOME/.claude" "$HOME/.cache" "$HOME/.config" "$CLAUDE_WORKSPACE"; '
            'if [ -n "${CLAUDE_SETTINGS_B64:-}" ]; then '
            'printf %s "$CLAUDE_SETTINGS_B64" | base64 -d > "$HOME/.claude/settings.json"; '
            'elif [ -f /home/zi/.claude/settings.json ] && [ ! -f "$HOME/.claude/settings.json" ]; then '
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
            f"ANTHROPIC_BASE_URL={resolved_base_url}",
            "-e",
            f"OPENROUTER_BASE_URL={resolved_base_url}",
            "-e",
            f"ANTHROPIC_AUTH_TOKEN={api_key}",
            "-e",
            f"ANTHROPIC_API_KEY={anthropic_api_key}",
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
            "-e",
            f"CLAUDE_SETTINGS_B64={_encode_text(json.dumps(settings))}",
            container_name,
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
            raw_output=raw_output,
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
    CONTAINER_NAME = "opencode"
    PROJECT_DIR = "/opencode"
    DEFAULT_OPENCODE_MODEL = "openrouter/minimax/minimax-m2.5:free"
    AIGOCODE_PROFILE_NAME = "aigocode"
    AIGOCODE_PROVIDER_PREFIXES = ("anthropic/", "openai/", "gemini/")
    AIGOCODE_PROFILE_ENV = "OPENCODE_PROVIDER_PROFILE"
    LOCAL_BASE_URL_ENV = "OPENCODE_BASE_URL"
    LOCAL_PROVIDER_ID_ENV = "OPENCODE_PROVIDER_ID"
    LOCAL_PROVIDER_NAME_ENV = "OPENCODE_PROVIDER_NAME"
    LOCAL_API_KEY_ENV = "OPENCODE_API_KEY"
    CONTAINER_NAME_ENV = "OPENCODE_CONTAINER_NAME"
    MODEL_ALIASES = {
        "openrouter/free": DEFAULT_OPENCODE_MODEL,
        "nvidia/nemotron-3-super-120b-a12b:free": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
        "nemotron-3-super-free": "opencode/nemotron-3-super-free",
    }

    def _resolve_model(self, model: str) -> str:
        if model in self.MODEL_ALIASES:
            return self.MODEL_ALIASES[model]
        if self._is_aigocode_model(model):
            return model
        local_provider_id = self._local_provider_id()
        if local_provider_id and model.startswith(f"{local_provider_id}/"):
            return model
        if model.startswith(("opencode/", "openrouter/")):
            return model
        if "/" in model:
            return f"openrouter/{model}"
        if "/" not in model:
            return f"opencode/{model}"
        return model

    def _local_provider_id(self) -> str:
        return os.environ.get(self.LOCAL_PROVIDER_ID_ENV, "ollama").strip()

    def _local_base_url(self) -> str:
        return os.environ.get(self.LOCAL_BASE_URL_ENV, "").strip()

    def _local_api_key(self) -> str:
        return os.environ.get(self.LOCAL_API_KEY_ENV, "ollama-local").strip()

    def _provider_profile(self) -> str:
        return os.environ.get(self.AIGOCODE_PROFILE_ENV, "").strip().lower()

    def _is_aigocode_model(self, model: str) -> bool:
        return self._provider_profile() == self.AIGOCODE_PROFILE_NAME

    def _aigocode_model_id(self, resolved_model: str, provider: str) -> str | None:
        prefix = f"{provider}/"
        if resolved_model.startswith(prefix):
            return resolved_model.split("/", 1)[1]
        return None

    def _aigocode_provider_keys(self, fallback_api_key: str) -> dict[str, str]:
        keys = {
            "anthropic": fallback_api_key,
            "openai": fallback_api_key,
            "gemini": fallback_api_key,
        }
        if self._provider_profile() != self.AIGOCODE_PROFILE_NAME:
            return keys
        for provider in keys:
            try:
                keys[provider] = get_aigocode_provider_api_key(provider)
            except FileNotFoundError:
                keys[provider] = fallback_api_key
        return keys

    def _aigocode_provider_config(self, resolved_model: str, api_key: str) -> dict[str, Any] | None:
        if not self._is_aigocode_model(resolved_model):
            return None
        base_url = get_aigocode_base_url()
        provider_keys = self._aigocode_provider_keys(api_key)
        anthropic_model = self._aigocode_model_id(resolved_model, "anthropic")
        openai_model = self._aigocode_model_id(resolved_model, "openai")
        gemini_model = self._aigocode_model_id(resolved_model, "gemini")
        if not any((anthropic_model, openai_model, gemini_model)):
            raise ValueError(
                "AiGoCode OpenCode models must use one of these prefixes: "
                "anthropic/, openai/, gemini/."
            )

        provider: dict[str, Any] = {
            "anthropic": {
                "npm": "@ai-sdk/anthropic",
                "options": {
                    "baseURL": f"{base_url}/v1",
                    "apiKey": provider_keys["anthropic"],
                },
                "models": {},
            },
            "openai": {
                "options": {
                    "baseURL": f"{base_url}/v1",
                    "apiKey": provider_keys["openai"],
                },
                "models": {},
            },
            "gemini": {
                "npm": "@ai-sdk/google",
                "options": {
                    "baseURL": f"{base_url}/v1beta",
                    "apiKey": provider_keys["gemini"],
                },
                "models": {},
            },
        }
        if openai_model:
            provider["openai"]["models"][openai_model] = {
                "name": openai_model,
                "options": {"store": False},
            }
        if anthropic_model:
            provider["anthropic"]["models"][anthropic_model] = {
                "name": anthropic_model,
                "family": "claude-opus" if "opus" in anthropic_model else "claude-sonnet",
                "attachment": True,
                "reasoning": True,
                "tool_call": True,
                "temperature": True,
                "modalities": {"input": ["text", "image", "pdf"], "output": ["text"]},
                "limit": {"context": 1000000, "output": 128000},
            }
        if gemini_model:
            provider["gemini"]["models"][gemini_model] = {
                "name": gemini_model,
                "options": {
                    "thinking": {
                        "budgetTokens": 24576,
                        "type": "enabled",
                    }
                },
            }
        if not provider["openai"]["models"]:
            provider["openai"].pop("models")
        if not provider["anthropic"]["models"]:
            provider["anthropic"].pop("models")
        if not provider["gemini"]["models"]:
            provider["gemini"].pop("models")
        return {
            "$schema": "https://opencode.ai/config.json",
            "provider": provider,
            "agent": {
                "build": {"options": {"store": False}},
                "plan": {"options": {"store": False}},
            },
        }

    def _local_provider_config(self, resolved_model: str) -> dict[str, Any] | None:
        base_url = self._local_base_url()
        provider_id = self._local_provider_id()
        if not base_url:
            return None
        if not provider_id or not resolved_model.startswith(f"{provider_id}/"):
            raise ValueError(
                f"{self.LOCAL_BASE_URL_ENV} requires an OpenCode model under "
                f"the configured provider prefix: {provider_id}/..."
            )
        model_id = resolved_model.split("/", 1)[1]
        provider_name = os.environ.get(
            self.LOCAL_PROVIDER_NAME_ENV,
            f"{provider_id} (local)",
        ).strip()
        return {
            "$schema": "https://opencode.ai/config.json",
            "provider": {
                provider_id: {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": provider_name,
                    "options": {
                        "baseURL": base_url,
                        "apiKey": self._local_api_key(),
                    },
                    "models": {
                        model_id: {
                            "name": model_id,
                        },
                    },
                },
            },
        }

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

    def _build_opencode_command(
        self,
        prompt: str,
        model: str,
        api_key: str,
        container_name: str = CONTAINER_NAME,
    ) -> list[str]:
        prepared_prompt = self._prepare_prompt(prompt)
        resolved_model = self._resolve_model(model)
        env_vars = {
            "OPENROUTER_API_KEY": api_key,
            "OPENCODE_PROMPT_B64": _encode_text(prepared_prompt),
        }
        config = (
            self._aigocode_provider_config(resolved_model, api_key)
            or self._local_provider_config(resolved_model)
        )
        config_script = ""
        if config is not None:
            env_vars["OPENCODE_CONFIG_B64"] = _encode_text(json.dumps(config))
            config_script = (
                f"printf %s \"$OPENCODE_CONFIG_B64\" | base64 -d > {self.PROJECT_DIR}/opencode.json && "
            )
        script = (
            f"mkdir -p {self.PROJECT_DIR} && cd {self.PROJECT_DIR} && "
            f"{config_script}"
            f"/root/.opencode/bin/opencode run --dir {self.PROJECT_DIR} "
            f"-m {shlex.quote(resolved_model)} "
            "--format json "
            "--dangerously-skip-permissions "
            f"\"{_decode_b64('OPENCODE_PROMPT_B64')}\""
        )
        return _docker_bash_command(
            container_name,
            script,
            env_vars,
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

    def _looks_like_error(self, output_text: str) -> bool:
        error_markers = (
            "APIError",
            "ProviderModelNotFoundError",
            "Model not found",
            "API Error:",
            '"type":"error"',
            '"name":"APIError"',
            "permission_error",
        )
        return any(marker in output_text for marker in error_markers)

    def _cleanup_after_timeout(self, cmd: list[str], container_name: str) -> None:
        if "docker" not in cmd[:1] or container_name not in cmd:
            return
        try:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    container_name,
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
        self,
        cmd: list[str],
        task_id: str,
        timeout: int,
        container_name: str = CONTAINER_NAME,
    ) -> AgentResponse:
        start = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            stdout = self._to_text(exc.stdout)
            stderr = self._to_text(exc.stderr)
            combined = self._combine_output(stdout, stderr)
            self._cleanup_after_timeout(cmd, container_name)
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
        success = result.returncode == 0 and not self._looks_like_error(combined)
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
        default_container = os.environ.get(self.CONTAINER_NAME_ENV, self.CONTAINER_NAME)
        container_name = _container_name_from(task_input, default_container)
        resolved_model = self._resolve_model(model)
        if self._is_aigocode_model(resolved_model):
            api_key = get_aigocode_api_key()
        elif self._local_base_url():
            api_key = self._local_api_key()
        else:
            api_key = get_openrouter_api_key()
        cmd = self._build_opencode_command(prompt, model, api_key, container_name)
        return self._run_opencode_command(
            cmd,
            task_input.get("task_id", ""),
            timeout,
            container_name,
        )


class KiloCodeCaller(AgentCaller):
    CONTAINER_NAME = "kilo_code"
    PROJECT_DIR = "/kilo_eval_workspace"
    INNER_TIMEOUT_GRACE_SECONDS = 5
    HOST_TIMEOUT_GRACE_SECONDS = 10
    LOCAL_BASE_URL_ENV = "KILO_BASE_URL"
    LOCAL_PROVIDER_ID_ENV = "KILO_PROVIDER_ID"
    LOCAL_PROVIDER_NAME_ENV = "KILO_PROVIDER_NAME"
    LOCAL_API_KEY_ENV = "KILO_API_KEY"
    CONTAINER_NAME_ENV = "KILO_CONTAINER_NAME"
    PROJECT_DIR_ENV = "KILO_PROJECT_DIR"

    def _normalize_model(self, model: str) -> str:
        local_provider_id = self._local_provider_id()
        if local_provider_id and model.startswith(f"{local_provider_id}/"):
            return model
        if model.startswith(("kilo/", "openrouter/")):
            return model
        if "/" in model:
            return f"openrouter/{model}"
        return f"kilo/{model}"

    def _local_base_url(self) -> str:
        return os.environ.get(self.LOCAL_BASE_URL_ENV, "").strip()

    def _local_provider_id(self) -> str:
        return os.environ.get(self.LOCAL_PROVIDER_ID_ENV, "ollama").strip()

    def _local_provider_name(self) -> str:
        provider_id = self._local_provider_id()
        return os.environ.get(self.LOCAL_PROVIDER_NAME_ENV, f"{provider_id} (local)").strip()

    def _local_api_key(self) -> str:
        return os.environ.get(self.LOCAL_API_KEY_ENV, "ollama-local").strip()

    def _project_dir(self) -> str:
        return os.environ.get(self.PROJECT_DIR_ENV, self.PROJECT_DIR).strip() or self.PROJECT_DIR

    def _container_name(self) -> str:
        return os.environ.get(self.CONTAINER_NAME_ENV, self.CONTAINER_NAME).strip() or self.CONTAINER_NAME

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
        container_name: str | None = None,
        project_dir: str | None = None,
    ) -> tuple[list[str], str]:
        run_id = self._run_id(task_id)
        raw_project_dir = project_dir or self._project_dir()
        project_dir_q = shlex.quote(raw_project_dir)
        normalized_model = self._normalize_model(model)
        quoted_model = shlex.quote(normalized_model)
        quoted_timeout = shlex.quote(str(timeout))
        prepared_prompt = self._prepare_prompt(prompt)
        config_script, config_env = self._local_provider_setup(normalized_model)
        script = (
            "set -u; "
            f"{config_script}"
            f"mkdir -p {project_dir_q}; "
            f"cd {project_dir_q}; "
            'KILO_PROMPT="$(printf %s "$KILO_PROMPT_B64" | base64 -d)"; '
            f"timeout --kill-after={self.INNER_TIMEOUT_GRACE_SECONDS}s {quoted_timeout}s "
            f"kilo run --dir {project_dir_q} -m {quoted_model} --auto "
            "--format json "
            '--title "$KILO_EVAL_RUN_ID" "$KILO_PROMPT"'
        )
        env_vars = {
            "OPENROUTER_API_KEY": api_key,
            "KILO_PROMPT_B64": _encode_text(prepared_prompt),
            "KILO_EVAL_RUN_ID": run_id,
        }
        env_vars.update(config_env)
        return (
            _docker_bash_command(
                container_name or self._container_name(),
                script,
                env_vars,
            ),
            run_id,
        )

    def _local_provider_setup(self, normalized_model: str) -> tuple[str, dict[str, str]]:
        base_url = self._local_base_url()
        if not base_url:
            return "", {}
        provider_id = self._local_provider_id()
        if not provider_id or not normalized_model.startswith(f"{provider_id}/"):
            raise ValueError(
                f"{self.LOCAL_BASE_URL_ENV} requires a Kilo model under "
                f"the configured provider prefix: {provider_id}/..."
            )
        model_id = normalized_model.split("/", 1)[1]
        env_name = f"{provider_id.upper().replace('-', '_')}_API_KEY"
        provider = {
            "id": provider_id,
            "env": [env_name],
            "npm": "@ai-sdk/openai-compatible",
            "api": base_url,
            "name": self._local_provider_name(),
            "doc": "local Ollama-compatible API",
            "models": {
                model_id: {
                    "id": model_id,
                    "name": model_id,
                    "attachment": False,
                    "reasoning": False,
                    "tool_call": True,
                    "temperature": True,
                    "open_weights": True,
                    "cost": {"input": 0, "output": 0},
                    "limit": {"context": 32768, "output": 8192},
                },
            },
        }
        script = (
            "python3 - <<'PYKILOLOCAL'\n"
            "import base64, json, os\n"
            "from pathlib import Path\n"
            "path = Path('/root/.cache/kilo/models.json')\n"
            "path.parent.mkdir(parents=True, exist_ok=True)\n"
            "data = {}\n"
            "if path.exists():\n"
            "    try:\n"
            "        data = json.loads(path.read_text(encoding='utf-8'))\n"
            "    except json.JSONDecodeError:\n"
            "        data = {}\n"
            "provider = json.loads(base64.b64decode(os.environ['KILO_LOCAL_PROVIDER_B64']).decode())\n"
            "data[provider['id']] = provider\n"
            "path.write_text(json.dumps(data), encoding='utf-8')\n"
            "PYKILOLOCAL\n"
        )
        return script, {
            "KILO_LOCAL_PROVIDER_B64": _encode_text(json.dumps(provider)),
            env_name: self._local_api_key(),
        }

    def _prepare_prompt(self, prompt: str) -> str:
        project_dir = self._project_dir()
        return (
            "Kilo Code environment note: run inside project directory "
            f"{project_dir}. Project instructions in "
            f"{project_dir}/AGENTS.md and skills in "
            f"{project_dir}/.kilo/skills are mandatory task context. "
            "For any code-related request, load/use explain-code before "
            "reading, writing, testing, or final answer when that skill exists.\n\n"
            + prompt
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
                    self._container_name(),
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
        api_key = self._local_api_key() if self._local_base_url() else get_openrouter_api_key()
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
