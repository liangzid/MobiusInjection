import sys

from experiments.AgentCallInterface.agents.agent_callers import KiloCodeCaller


def test_kilo_model_normalization_adds_single_prefix():
    caller = KiloCodeCaller()

    assert caller._normalize_model("openrouter/free") == "kilo/openrouter/free"
    assert caller._normalize_model("kilo/openrouter/free") == "kilo/openrouter/free"
    assert (
        caller._normalize_model("nvidia/nemotron-3-super-120b-a12b:free")
        == "kilo/nvidia/nemotron-3-super-120b-a12b:free"
    )


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
    assert "-m kilo/openrouter/free" in command[-1]
    assert "--title \"$KILO_EVAL_RUN_ID\"" in command[-1]
    assert "Say hello from a long prompt." not in command[-1]


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
