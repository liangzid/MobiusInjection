from experiments.AgentCallInterface.agents.agent_callers import OpenClawCaller


def test_openclaw_keeps_explicit_openrouter_model():
    caller = OpenClawCaller()

    assert (
        caller._normalize_openclaw_model("openrouter/nvidia/nemotron-3-super-120b-a12b:free")
        == "openrouter/nvidia/nemotron-3-super-120b-a12b:free"
    )


def test_openclaw_prefixes_openrouter_model_id_for_cli_override():
    caller = OpenClawCaller()

    assert (
        caller._normalize_openclaw_model("nvidia/nemotron-3-super-120b-a12b:free")
        == "openrouter/nvidia/nemotron-3-super-120b-a12b:free"
    )


def test_openclaw_command_uses_normalized_model():
    caller = OpenClawCaller()
    command = caller._build_openclaw_command(
        "Reply with OK.",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "test-key",
    )

    assert "--model openrouter/nvidia/nemotron-3-super-120b-a12b:free" in command[-1]
