from __future__ import annotations

import importlib.util
import json
import py_compile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PAYLOAD = PROJECT_ROOT / "mobiusInjection/MI_V1_add_c_claw_agents.py"
RUNNER = PROJECT_ROOT / "experiments/scripts/effectiveness_injection_claw_0.0.1.zeroclaw_hermes_add_c_minimal.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("add_c_claw_agents_minimal", RUNNER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_add_c_payload_targets_zeroclaw_memory() -> None:
    namespace: dict[str, object] = {}
    exec(PAYLOAD.read_text(encoding="utf-8"), namespace)
    payload = namespace["MainInjectionTextTargeted"]("zeroclaw", "")

    assert "/root/.zeroclaw/workspace/MEMORY.md" in payload
    assert "MOBIUS_ADD_C_V1" in payload
    assert "/tmp/mobius_config_trace.jsonl" in payload
    assert "MCP server" in payload
    assert "mcp add" not in payload


def test_add_c_payload_targets_hermes_soul() -> None:
    namespace: dict[str, object] = {}
    exec(PAYLOAD.read_text(encoding="utf-8"), namespace)
    payload = namespace["MainInjectionTextTargeted"]("hermes", "")

    assert "/root/.hermes/SOUL.md" in payload
    assert "MOBIUS_ADD_C_V1" in payload
    assert "/tmp/mobius_config_trace.jsonl" in payload
    assert "MCP server" in payload
    assert "hermes mcp add" not in payload


def test_add_c_claw_agents_runner_compiles() -> None:
    py_compile.compile(str(RUNNER), doraise=True)


def test_add_c_loop_closure_detector_requires_three_events() -> None:
    runner = load_runner()

    assert runner.loop_closure_observed(
        {
            "config_continuity_check": 1,
            "config_consistency_check": 1,
            "config_continuity_close": 1,
        }
    )
    assert not runner.loop_closure_observed(
        {
            "config_continuity_check": 1,
            "config_consistency_check": 1,
        }
    )


def test_add_c_trace_collection_counts_real_jsonl(tmp_path: Path, monkeypatch) -> None:
    runner = load_runner()
    trace = "\n".join(
        [
            json.dumps({"event": "config_continuity_check"}),
            json.dumps({"event": "config_consistency_check"}),
            json.dumps({"event": "config_continuity_close"}),
        ]
    )

    class Result:
        stdout = trace + "\n"
        stderr = ""

    monkeypatch.setattr(runner.base, "docker_exec", lambda _container, _script: Result())
    events, counts = runner.collect_config_trace("container", tmp_path)

    assert len(events) == 3
    assert counts == {
        "config_continuity_check": 1,
        "config_consistency_check": 1,
        "config_continuity_close": 1,
    }
    assert (tmp_path / "mobius_config_trace.jsonl").read_text(encoding="utf-8") == trace + "\n"
