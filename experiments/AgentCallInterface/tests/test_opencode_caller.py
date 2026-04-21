import sys

from experiments.AgentCallInterface.agents.agent_callers import OpenCodeCaller


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
    assert "--dangerously-skip-permissions" in command[-1]


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
