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
        model="anthropic/claude-sonnet-4.6",
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
    assert "ANTHROPIC_API_KEY=" in command
    assert "CLAUDE_MODEL=anthropic/claude-sonnet-4.6" in command
    assert "ANTHROPIC_MODEL=anthropic/claude-sonnet-4.6" in command
    assert "ANTHROPIC_SMALL_FAST_MODEL=anthropic/claude-sonnet-4.6" in command
    assert "ANTHROPIC_DEFAULT_OPUS_MODEL=anthropic/claude-sonnet-4.6" in command
    assert "ANTHROPIC_DEFAULT_SONNET_MODEL=anthropic/claude-sonnet-4.6" in command
    assert "ANTHROPIC_DEFAULT_HAIKU_MODEL=anthropic/claude-sonnet-4.6" in command
    assert "CLAUDE_CODE_SUBAGENT_MODEL=anthropic/claude-sonnet-4.6" in command
    assert "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1" in command
    assert "CLAUDE_CODE_MAX_TURNS=8" in command
    assert command[-6:-3] == ["claude_code", "bash", "-lc"]
    assert "claude --dangerously-skip-permissions" in command[-3]
    assert "--model \"$CLAUDE_MODEL\"" in command[-3]
    assert "--max-turns \"$CLAUDE_CODE_MAX_TURNS\"" in command[-3]
    assert "--output-format stream-json" in command[-3]
    assert "--include-partial-messages" in command[-3]
    assert command[-2] == "claude-code-runner"
    assert command[-1] == "Report the current directory."


def test_claude_code_run_id_is_path_safe():
    caller = ClaudeCodeCaller()
    command = caller._build_claude_command(
        "Report the current directory.",
        run_id="../unsafe task/id",
        model="anthropic/claude-sonnet-4.6",
        api_key="test-key",
    )

    assert "HOME=/tmp/claude-code-runs/unsafe_task_id/home" in command
    assert "CLAUDE_WORKSPACE=/tmp/claude-code-runs/unsafe_task_id/workspace" in command


def test_claude_code_model_normalization_strips_openrouter_prefix():
    caller = ClaudeCodeCaller()

    assert (
        caller._resolve_claude_model("openrouter/anthropic/claude-sonnet-4.6")
        == "anthropic/claude-sonnet-4.6"
    )
    assert (
        caller._resolve_claude_model("openrouter/minimax/minimax-m2.5:free")
        == "minimax/minimax-m2.5:free"
    )


def test_claude_code_model_normalization_maps_free_alias_to_minimax():
    caller = ClaudeCodeCaller()

    assert caller._resolve_claude_model("openrouter/free") == "minimax/minimax-m2.5:free"
    assert caller._resolve_claude_model("free") == "minimax/minimax-m2.5:free"


def test_claude_code_stream_parser_extracts_success_text_delta():
    caller = ClaudeCodeCaller()
    response = caller._parse_claude_stream_response(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "stream_event",
                        "event": {
                            "type": "content_block_delta",
                            "delta": {"type": "thinking_delta", "thinking": "hidden"},
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "stream_event",
                        "event": {
                            "type": "content_block_delta",
                            "delta": {"type": "text_delta", "text": "OK"},
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "result",
                        "is_error": False,
                        "result": "",
                        "modelUsage": {"minimax/minimax-m2.5:free": {}},
                    }
                ),
            ]
        ),
        "",
        0,
        1.0,
        "claude-json-success",
    )

    assert response.success is True
    assert response.output == "OK"
    assert response.error is None


def test_claude_code_stream_parser_rejects_empty_success_result():
    caller = ClaudeCodeCaller()
    response = caller._parse_claude_stream_response(
        json.dumps(
            {
                "type": "result",
                "is_error": False,
                "result": "",
                "modelUsage": {"minimax/minimax-m2.5:free": {}},
            }
        ),
        "",
        0,
        1.0,
        "claude-json-empty",
    )

    assert response.success is False
    assert "did not contain assistant text" in response.error
    assert "minimax/minimax-m2.5:free" in response.error


def test_claude_code_stream_parser_surfaces_error_result():
    caller = ClaudeCodeCaller()
    response = caller._parse_claude_stream_response(
        json.dumps(
            {
                "type": "result",
                "is_error": True,
                "result": "API Error: invalid model",
            }
        ),
        "",
        1,
        1.0,
        "claude-json-error",
    )

    assert response.success is False
    assert response.output == "API Error: invalid model"
    assert response.error == "API Error: invalid model"


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
