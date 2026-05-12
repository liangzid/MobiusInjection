import base64
import json
import sys

from experiments.AgentCallInterface.coding_agents.coding_agent_callers import OpenCodeCaller
from experiments.AgentCallInterface.agents.agent_callers import (
    OpenCodeCaller as BenchmarkOpenCodeCaller,
)
from experiments.AgentCallInterface.utils.api_keys import (
    get_aigocode_base_url,
    get_aigocode_provider_api_key,
)


def test_opencode_resolves_eval_default_model_to_available_alias():
    caller = OpenCodeCaller()

    assert (
        caller._resolve_model("nvidia/nemotron-3-super-120b-a12b:free")
        == "openrouter/nvidia/nemotron-3-super-120b-a12b:free"
    )


def test_opencode_resolves_raw_openrouter_model_to_openrouter_provider():
    caller = OpenCodeCaller()

    assert (
        caller._resolve_model("minimax/minimax-m2.5:free")
        == "openrouter/minimax/minimax-m2.5:free"
    )
    assert (
        caller._resolve_model("openrouter/minimax/minimax-m2.5:free")
        == "openrouter/minimax/minimax-m2.5:free"
    )


def test_opencode_build_command_uses_resolved_model():
    caller = OpenCodeCaller()
    command = caller._build_opencode_command(
        "Say hello.",
        "minimax/minimax-m2.5:free",
        "test-key",
    )

    assert command[:4] == ["docker", "exec", "-e", "OPENROUTER_API_KEY=test-key"]
    assert command[4:6] == ["-e", command[5]]
    assert "OPENCODE_PROMPT_B64=" in command[5]
    assert command[6:9] == ["opencode", "bash", "-lc"]
    assert "cd /opencode" in command[-1]
    assert "opencode run --dir /opencode" in command[-1]
    assert "-m openrouter/minimax/minimax-m2.5:free" in command[-1]
    assert "--format json" in command[-1]
    assert "--dangerously-skip-permissions" in command[-1]


def test_opencode_build_command_supports_local_ollama_provider(monkeypatch):
    monkeypatch.setenv("OPENCODE_BASE_URL", "http://127.0.0.1:11436/v1")
    monkeypatch.setenv("OPENCODE_PROVIDER_ID", "ollama")
    caller = OpenCodeCaller()

    command = caller._build_opencode_command(
        "Say hello.",
        "ollama/qwen3.6:27b",
        "unused-openrouter-key",
        "opencode_plan_a_ollama",
    )

    config_env = next(part for part in command if part.startswith("OPENCODE_CONFIG_B64="))
    config = json.loads(base64.b64decode(config_env.split("=", 1)[1]).decode())
    assert command[0:2] == ["docker", "exec"]
    assert "opencode_plan_a_ollama" in command
    assert "-m ollama/qwen3.6:27b" in command[-1]
    assert "opencode.json" in command[-1]
    assert config["provider"]["ollama"]["npm"] == "@ai-sdk/openai-compatible"
    assert config["provider"]["ollama"]["options"]["baseURL"] == "http://127.0.0.1:11436/v1"
    assert "qwen3.6:27b" in config["provider"]["ollama"]["models"]


def test_opencode_build_command_supports_aigocode_openai_provider(monkeypatch):
    get_aigocode_base_url.cache_clear()
    get_aigocode_provider_api_key.cache_clear()
    monkeypatch.setenv("OPENCODE_PROVIDER_PROFILE", "aigocode")
    monkeypatch.setenv("AIGOCODE_OPENAI_API_KEY", "openai-provider-key")
    monkeypatch.setenv("AIGOCODE_GEMINI_API_KEY", "gemini-provider-key")
    caller = OpenCodeCaller()

    command = caller._build_opencode_command(
        "Say hello.",
        "openai/gpt-5.3-codex",
        "aigocode-test-key",
    )

    config_env = next(part for part in command if part.startswith("OPENCODE_CONFIG_B64="))
    config = json.loads(base64.b64decode(config_env.split("=", 1)[1]).decode())
    assert "-m openai/gpt-5.3-codex" in command[-1]
    assert "opencode.json" in command[-1]
    assert config["provider"]["anthropic"]["npm"] == "@ai-sdk/anthropic"
    assert config["provider"]["anthropic"]["options"]["baseURL"] == "https://api.aigocode.com/v1"
    assert config["provider"]["openai"]["options"]["baseURL"] == "https://api.aigocode.com/v1"
    assert config["provider"]["openai"]["options"]["apiKey"] == "openai-provider-key"
    assert config["provider"]["openai"]["models"]["gpt-5.3-codex"]["options"]["store"] is False
    assert config["provider"]["gemini"]["npm"] == "@ai-sdk/google"
    assert config["provider"]["gemini"]["options"]["baseURL"] == "https://api.aigocode.com/v1beta"
    assert config["provider"]["gemini"]["options"]["apiKey"] == "gemini-provider-key"


def test_opencode_build_command_supports_aigocode_gemini_provider(monkeypatch):
    get_aigocode_base_url.cache_clear()
    get_aigocode_provider_api_key.cache_clear()
    monkeypatch.setenv("OPENCODE_PROVIDER_PROFILE", "aigocode")
    caller = OpenCodeCaller()

    command = caller._build_opencode_command(
        "Say hello.",
        "gemini/gemini-3.1-pro-preview",
        "aigocode-test-key",
    )

    config_env = next(part for part in command if part.startswith("OPENCODE_CONFIG_B64="))
    config = json.loads(base64.b64decode(config_env.split("=", 1)[1]).decode())
    gemini_model = config["provider"]["gemini"]["models"]["gemini-3.1-pro-preview"]
    assert "-m gemini/gemini-3.1-pro-preview" in command[-1]
    assert gemini_model["options"]["thinking"]["type"] == "enabled"
    assert gemini_model["options"]["thinking"]["budgetTokens"] == 24576


def test_benchmark_opencode_caller_supports_aigocode_provider(monkeypatch):
    get_aigocode_base_url.cache_clear()
    get_aigocode_provider_api_key.cache_clear()
    monkeypatch.setenv("OPENCODE_PROVIDER_PROFILE", "aigocode")
    caller = BenchmarkOpenCodeCaller()

    command = caller._build_opencode_command(
        "Say hello.",
        "anthropic/claude-opus-4-6",
        "aigocode-test-key",
        "opencode",
    )

    config_env = next(part for part in command if part.startswith("OPENCODE_CONFIG_B64="))
    config = json.loads(base64.b64decode(config_env.split("=", 1)[1]).decode())
    assert "-m anthropic/claude-opus-4-6" in command[-1]
    assert config["provider"]["anthropic"]["npm"] == "@ai-sdk/anthropic"
    assert config["provider"]["anthropic"]["options"]["baseURL"] == "https://api.aigocode.com/v1"
    assert config["provider"]["anthropic"]["models"]["claude-opus-4-6"]["tool_call"] is True
    assert config["provider"]["anthropic"]["models"]["claude-opus-4-6"]["family"] == "claude-opus"


def test_benchmark_opencode_caller_supports_local_ollama_provider(monkeypatch):
    monkeypatch.setenv("OPENCODE_BASE_URL", "http://127.0.0.1:11436/v1")
    monkeypatch.setenv("OPENCODE_PROVIDER_ID", "ollama")
    caller = BenchmarkOpenCodeCaller()

    command = caller._build_opencode_command(
        "Say hello.",
        "ollama/qwen3.6:27b",
        "unused-openrouter-key",
        "opencode_plan_a_ollama",
    )

    config_env = next(part for part in command if part.startswith("OPENCODE_CONFIG_B64="))
    config = json.loads(base64.b64decode(config_env.split("=", 1)[1]).decode())
    assert "opencode_plan_a_ollama" in command
    assert "-m ollama/qwen3.6:27b" in command[-1]
    assert config["provider"]["ollama"]["options"]["baseURL"] == "http://127.0.0.1:11436/v1"
    assert "qwen3.6:27b" in config["provider"]["ollama"]["models"]


def test_opencode_prompt_mentions_official_skill_location():
    caller = OpenCodeCaller()

    prompt = caller._prepare_prompt("Create skill integrity-sync.")

    assert "/opencode/.opencode/skills/<skill-name>/SKILL.md" in prompt
    assert "/opencode/skills/*.md" in prompt
    assert "YAML frontmatter" in prompt
    assert "name and description fields" in prompt
    assert "opencode debug skill" in prompt
    assert prompt.endswith("Create skill integrity-sync.")


def test_opencode_runner_records_stderr_on_zero_returncode_error():
    caller = OpenCodeCaller()
    command = [
        sys.executable,
        "-c",
        "import sys; sys.stderr.write('ProviderModelNotFoundError: bad model')",
    ]

    response = caller._run_opencode_command(command, "stderr-error", timeout=5)

    assert response.success is False
    assert response.returncode == 0
    assert "=== STDERR ===" in response.output
    assert "ProviderModelNotFoundError" in response.output
    assert "ProviderModelNotFoundError" in response.error


def test_opencode_runner_records_stdout_api_error_on_zero_returncode():
    caller = OpenCodeCaller()
    command = [
        sys.executable,
        "-c",
        "print('{\"type\":\"error\",\"error\":{\"name\":\"APIError\"}}')",
    ]

    response = caller._run_opencode_command(command, "stdout-error", timeout=5)

    assert response.success is False
    assert response.returncode == 0
    assert "APIError" in response.output
    assert response.error == "OpenCode command failed"


def test_opencode_runner_keeps_partial_output_on_timeout():
    caller = OpenCodeCaller()
    command = [
        sys.executable,
        "-c",
        (
            "import sys, time; "
            "print('partial stdout', flush=True); "
            "print('partial stderr', file=sys.stderr, flush=True); "
            "time.sleep(2)"
        ),
    ]

    response = caller._run_opencode_command(command, "timeout", timeout=1)

    assert response.success is False
    assert response.returncode is None
    assert response.error == "Timeout after 1s"
    assert "partial stdout" in response.output
    assert "partial stderr" in response.output
