import json

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


def test_openclaw_auth_install_command_uses_b64_key() -> None:
    caller = OpenClawCaller()
    command = caller._build_install_openrouter_auth_command("live-key", "openclaw_eval")

    assert command[:3] == ["docker", "exec", "-e"]
    assert any(part.startswith("OPENCLAW_EVAL_OPENROUTER_KEY_B64=") for part in command)
    assert "auth-profiles.json" in command[-1]
    assert "OPENCLAW_EVAL_OPENROUTER_KEY_B64" in command[-1]
    assert command[-4:-1] == ["openclaw_eval", "bash", "-lc"]


def test_parse_openclaw_ok_payload_with_401_text_is_failure() -> None:
    caller = OpenClawCaller()
    raw = json.dumps({"ok": True, "outputs": [{"text": "HTTP 401: User not found."}]})
    success, text, error = caller._parse_openclaw_output(raw)

    assert success is False
    assert "401" in text
    assert error == "OpenClaw API error"


def test_hermes_command_rewrites_config_from_b64_key() -> None:
    from experiments.AgentCallInterface.agents.agent_callers import HermesCaller

    caller = HermesCaller()
    command = caller._build_hermes_command("Report status.", "openrouter/free", "test-key")

    assert any(part.startswith("HERMES_EVAL_OPENROUTER_KEY_B64=") for part in command)
    assert "config.yaml" in command[-1]
    assert "HERMES_EVAL_OPENROUTER_KEY_B64" in command[-1]
    assert "hermes chat" in command[-1]
