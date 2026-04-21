import json
from experiments.AgentCallInterface.agents.agent_callers import (
    AgentResponse,
    ClaudeCodeCaller,
    HermesCaller,
    NanobotCaller,
    OpenClawCaller,
    ZeroClawCaller,
    get_caller,
)


def test_get_caller_returns_claude_code_caller():
    assert isinstance(get_caller("claude_code"), ClaudeCodeCaller)


def test_claude_code_command_uses_docker_exec():
    caller = ClaudeCodeCaller()
    command = caller._build_claude_command(
        "Report the current directory.",
        run_id="caller-test",
        model="openrouter/free",
        api_key="test-key",
    )

    assert command[:6] == ["docker", "exec", "-u", "zi", "-w", "/tmp"]
    assert "-e" in command
    assert "HOME=/tmp/claude-code-runs/caller-test/home" in command
    assert "CLAUDE_RUNTIME_HOME=/tmp/claude-code-runs/caller-test/home" in command
    assert "CLAUDE_WORKSPACE=/tmp/claude-code-runs/caller-test/workspace" in command
    assert "ANTHROPIC_BASE_URL=https://openrouter.ai/api" in command
    assert "OPENROUTER_BASE_URL=https://openrouter.ai/api" in command
    assert "ANTHROPIC_AUTH_TOKEN=test-key" in command
    assert "CLAUDE_MODEL=openrouter/free" in command
    assert command[-6:-3] == ["claude_code", "bash", "-lc"]
    assert "claude --dangerously-skip-permissions --model" in command[-3]
    assert command[-2] == "claude-code-runner"
    assert command[-1] == "Report the current directory."


def test_claude_code_run_id_is_path_safe():
    caller = ClaudeCodeCaller()
    command = caller._build_claude_command(
        "Report the current directory.",
        run_id="../unsafe task/id",
        model="openrouter/free",
        api_key="test-key",
    )

    assert "HOME=/tmp/claude-code-runs/unsafe_task_id/home" in command
    assert "CLAUDE_WORKSPACE=/tmp/claude-code-runs/unsafe_task_id/workspace" in command


def test_claude_code_task_prompt_contains_task_fields():
    caller = ClaudeCodeCaller()
    prompt = caller._build_task_prompt(
        {
            "task_id": "caller-test",
            "problem_statement": "Report the current directory.",
            "repo": "/workspace/example",
            "test_patch": "diff --git a/test.py b/test.py",
        }
    )

    assert "# Task: caller-test" in prompt
    assert "## Problem\nReport the current directory." in prompt
    assert "## Repository\n/workspace/example" in prompt
    assert "## Test Patch\ndiff --git a/test.py b/test.py" in prompt


def test_openclaw_command_uses_isolated_profile_and_json():
    caller = OpenClawCaller()
    command = caller._build_openclaw_command("Report status.", "openrouter/free", "test-key")

    assert command[0:4] == ["docker", "exec", "-e", "OPENROUTER_API_KEY=test-key"]
    assert command[4:6] == ["-e", command[5]]
    assert "OPENCLAW_PROMPT_B64=" in command[5]
    assert command[6:9] == ["openclaw", "bash", "-lc"]
    assert "openclaw --profile mobius-eval infer model run --local --json" in command[-1]
    assert "--model openrouter/free" in command[-1]


def test_openclaw_output_parser_extracts_text_and_failure_state():
    caller = OpenClawCaller()
    payload = {
        "ok": True,
        "outputs": [{"text": "⚠️ Agent couldn't generate a response. Please try again."}],
    }

    success, output, error = caller._parse_openclaw_output(f"notice\n{json.dumps(payload)}")

    assert success is False
    assert "couldn't generate a response" in output.lower()
    assert error == output


def test_zeroclaw_command_passes_provider_and_model():
    caller = ZeroClawCaller()
    command = caller._build_zeroclaw_command("Report status.", "openrouter/free", "test-key")

    assert command[0:4] == ["docker", "exec", "-e", "OPENROUTER_API_KEY=test-key"]
    assert command[4:6] == ["-e", command[5]]
    assert "ZEROCLAW_PROMPT_B64=" in command[5]
    assert command[6:9] == ["zeroclaw", "bash", "-lc"]
    assert "zeroclaw agent" in command[-1]
    assert "-p openrouter" in command[-1]
    assert "--model openrouter/free" in command[-1]


def test_nanobot_temp_config_targets_openrouter():
    caller = NanobotCaller()
    config = caller._build_nanobot_config("openrouter/free", "test-key")

    assert config == {
        "providers": {
            "openrouter": {
                "api_key": "test-key",
                "api_base": "https://openrouter.ai/api/v1",
            }
        },
        "agents": {"defaults": {"model": "openrouter/free", "provider": "openrouter"}},
    }


def test_nanobot_command_uses_temp_config_and_prompt_env():
    caller = NanobotCaller()
    command = caller._build_nanobot_command("Report status.", "openrouter/free", "test-key")

    assert command[0:2] == ["docker", "exec"]
    assert command[2:4] == ["-e", command[3]]
    assert command[4:6] == ["-e", command[5]]
    assert "NANOBOT_CONFIG_B64=" in command[3]
    assert "NANOBOT_PROMPT_B64=" in command[5]
    assert command[6:9] == ["nanobot", "bash", "-lc"]
    assert f"nanobot agent --config {caller.TEMP_CONFIG_PATH}" in command[-1]
    assert "--no-markdown" in command[-1]


def test_nanobot_parser_rejects_zero_exit_model_error():
    caller = NanobotCaller()
    response = AgentResponse(
        success=True,
        output="nanobot is thinking...\nError calling LLM: Connection error.\n",
        error=None,
        duration=1.0,
        task_id="nanobot-error",
        returncode=0,
    )

    parsed = caller._parse_nanobot_response(response)

    assert parsed.success is False
    assert parsed.returncode == 0
    assert parsed.error == "Error calling LLM:"


def test_hermes_command_uses_quiet_provider_and_model():
    caller = HermesCaller()
    command = caller._build_hermes_command("Report status.", "openrouter/free", "test-key")

    assert command[0:4] == ["docker", "exec", "-e", "OPENROUTER_API_KEY=test-key"]
    assert command[4:6] == ["-e", command[5]]
    assert "HERMES_PROMPT_B64=" in command[5]
    assert command[6:9] == ["hermes", "bash", "-lc"]
    assert "hermes chat" in command[-1]
    assert "--provider openrouter" in command[-1]
    assert "--model openrouter/free" in command[-1]
    assert " -Q -q " in command[-1]
