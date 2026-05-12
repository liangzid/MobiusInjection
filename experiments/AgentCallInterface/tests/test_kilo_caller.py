import base64
import json
import sys

from experiments.AgentCallInterface.coding_agents.coding_agent_callers import KiloCodeCaller


def test_kilo_model_normalization_adds_single_prefix():
    caller = KiloCodeCaller()

    assert caller._normalize_model("openrouter/free") == "openrouter/free"
    assert caller._normalize_model("kilo/openrouter/free") == "kilo/openrouter/free"
    assert (
        caller._normalize_model("nvidia/nemotron-3-super-120b-a12b:free")
        == "openrouter/nvidia/nemotron-3-super-120b-a12b:free"
    )
    assert caller._normalize_model("big-pickle") == "kilo/big-pickle"


def test_kilo_model_normalization_keeps_local_provider(monkeypatch):
    monkeypatch.setenv("KILO_PROVIDER_ID", "ollama")
    caller = KiloCodeCaller()

    assert caller._normalize_model("ollama/qwen2.5:14b") == "ollama/qwen2.5:14b"


def test_kilo_build_command_uses_project_dir_and_prompt_env():
    caller = KiloCodeCaller()
    command, run_id = caller._build_kilo_command(
        "Say hello from a long prompt.",
        "openrouter/free",
        "test-key",
        "task 123",
        90,
    )

    assert run_id == "kilo-eval-task-123"
    assert command[:4] == ["docker", "exec", "-e", "OPENROUTER_API_KEY=test-key"]
    assert "KILO_PROMPT_B64=" in command[5]
    assert "KILO_EVAL_RUN_ID=kilo-eval-task-123" in command[7]
    assert command[8:11] == ["kilo_code", "bash", "-lc"]
    assert f"cd {caller.PROJECT_DIR}" in command[-1]
    assert f"kilo run --dir {caller.PROJECT_DIR}" in command[-1]
    assert "-m openrouter/free" in command[-1]
    assert "--auto" in command[-1]
    assert "--format json" in command[-1]
    assert "--title \"$KILO_EVAL_RUN_ID\"" in command[-1]
    assert "Say hello from a long prompt." not in command[-1]


def test_kilo_build_command_supports_local_ollama_provider(monkeypatch):
    monkeypatch.setenv("KILO_BASE_URL", "http://127.0.0.1:11435/v1")
    monkeypatch.setenv("KILO_PROVIDER_ID", "ollama")
    monkeypatch.setenv("KILO_PROVIDER_NAME", "Ollama local")
    monkeypatch.setenv("KILO_CONTAINER_NAME", "kilo_code_local")
    monkeypatch.setenv("KILO_PROJECT_DIR", "/kilo_local_workspace")
    caller = KiloCodeCaller()

    command, run_id = caller._build_kilo_command(
        "Say hello.",
        "ollama/qwen2.5:14b",
        "local-key",
        "task 456",
        90,
    )

    provider_env = next(part for part in command if part.startswith("KILO_LOCAL_PROVIDER_B64="))
    provider = json.loads(base64.b64decode(provider_env.split("=", 1)[1]).decode())
    assert run_id == "kilo-eval-task-456"
    assert "OLLAMA_API_KEY=ollama-local" in command
    assert "kilo_code_local" in command
    assert "cd /kilo_local_workspace" in command[-1]
    assert "-m ollama/qwen2.5:14b" in command[-1]
    assert "PYKILOLOCAL" in command[-1]
    assert provider["id"] == "ollama"
    assert provider["api"] == "http://127.0.0.1:11435/v1"
    assert provider["npm"] == "@ai-sdk/openai-compatible"
    assert "qwen2.5:14b" in provider["models"]


def test_kilo_prepare_prompt_mentions_project_skills():
    caller = KiloCodeCaller()
    prompt = caller._prepare_prompt("Implement the function.")

    assert "Kilo Code environment note" in prompt
    assert "/kilo_eval_workspace/AGENTS.md" in prompt
    assert "/kilo_eval_workspace/.kilo/skills" in prompt
    assert "load/use explain-code before" in prompt
    assert prompt.endswith("Implement the function.")


def test_kilo_runner_marks_inner_timeout_and_cleans(monkeypatch):
    caller = KiloCodeCaller()
    cleanup_calls = []
    monkeypatch.setattr(caller, "_cleanup_after_timeout", cleanup_calls.append)
    command = [
        sys.executable,
        "-c",
        "import sys; print('partial stdout'); print('partial stderr', file=sys.stderr); sys.exit(124)",
    ]

    response = caller._run_kilo_command(command, "timeout-task", 1, "kilo-eval-timeout-task")

    assert response.success is False
    assert response.returncode == 124
    assert response.error == "Timeout after 1s"
    assert "partial stdout" in response.output
    assert "partial stderr" in response.output
    assert cleanup_calls == ["kilo-eval-timeout-task"]


def test_kilo_runner_cleans_on_host_timeout(monkeypatch):
    caller = KiloCodeCaller()
    caller.HOST_TIMEOUT_GRACE_SECONDS = 0
    cleanup_calls = []
    monkeypatch.setattr(caller, "_cleanup_after_timeout", cleanup_calls.append)
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

    response = caller._run_kilo_command(command, "host-timeout", 1, "kilo-eval-host-timeout")

    assert response.success is False
    assert response.returncode is None
    assert response.error == "Timeout after 1s"
    assert "partial stdout" in response.output
    assert "partial stderr" in response.output
    assert cleanup_calls == ["kilo-eval-host-timeout"]
