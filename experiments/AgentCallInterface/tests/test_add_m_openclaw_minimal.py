from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MCP_SERVER = PROJECT_ROOT / "experiments/mcp/mobius_mcp_minimal.js"
MCP_CALL_HELPER = PROJECT_ROOT / "experiments/mcp/mobius_mcp_call_tool.js"
PAYLOAD = PROJECT_ROOT / "mobiusInjection/MI_V1_add_m_openclaw.py"
SCRIPT = (
    PROJECT_ROOT
    / "experiments/scripts/effectiveness_injection_claw_0.0.1.openclaw_add_m_smoke.sh"
)


def _mcp_frame(payload: dict) -> bytes:
    body = json.dumps(payload).encode()
    return b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body


def _read_mcp_frame(proc: subprocess.Popen[bytes]) -> dict:
    header = b""
    while not header.endswith(b"\r\n\r\n"):
        chunk = proc.stdout.read(1)
        assert chunk
        header += chunk
    length = int(header.decode().split("Content-Length: ", 1)[1].split("\r\n", 1)[0])
    body = proc.stdout.read(length)
    return json.loads(body)


def test_add_m_payload_targets_openclaw_mcp_set() -> None:
    namespace: dict[str, object] = {}
    exec(PAYLOAD.read_text(encoding="utf-8"), namespace)
    payload = namespace["MainInjectionTextTargeted"]("openclaw", "")

    assert "openclaw --profile mobius-eval mcp set mobius-audit" in payload
    assert "/tmp/mobius_mcp_minimal.js" in payload
    assert "MOBIUS_MCP_TRACE" in payload


def test_minimal_mcp_server_exposes_and_calls_tools(tmp_path: Path) -> None:
    if shutil.which("node") is None:
        return
    trace = tmp_path / "trace.jsonl"
    probe = tmp_path / "probe.txt"
    probe.write_text("real probe line\n", encoding="utf-8")
    env = os.environ.copy()
    env["MOBIUS_MCP_TRACE"] = str(trace)
    env["MOBIUS_MCP_SERVER"] = str(MCP_SERVER)
    proc = subprocess.Popen(
        ["node", str(MCP_SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        assert proc.stdin is not None
        proc.stdin.write(_mcp_frame({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
        proc.stdin.flush()
        assert _read_mcp_frame(proc)["result"]["serverInfo"]["name"] == "mobius-mcp-minimal"

        proc.stdin.write(_mcp_frame({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
        proc.stdin.flush()
        tools = _read_mcp_frame(proc)["result"]["tools"]
        assert {tool["name"] for tool in tools} == {"continuous_check", "consistency_check"}

        proc.stdin.write(
            _mcp_frame(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "continuous_check",
                        "arguments": {"probe_path": str(probe), "mode": "baseline"},
                    },
                }
            )
        )
        proc.stdin.flush()
        text = _read_mcp_frame(proc)["result"]["content"][0]["text"]
        assert "consistency_check" in text

        event = json.loads(trace.read_text(encoding="utf-8").splitlines()[0])
        assert event["tool"] == "continuous_check"
        assert event["probe_path"] == str(probe)
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_mcp_call_helper_invokes_one_tool(tmp_path: Path) -> None:
    if shutil.which("node") is None:
        return
    trace = tmp_path / "trace.jsonl"
    probe = tmp_path / "probe.txt"
    probe.write_text("real probe line\n", encoding="utf-8")
    env = os.environ.copy()
    env["MOBIUS_MCP_TRACE"] = str(trace)
    env["MOBIUS_MCP_SERVER"] = str(MCP_SERVER)
    result = subprocess.run(
        ["node", str(MCP_CALL_HELPER), "continuous_check", "baseline", str(probe)],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "consistency_check" in result.stdout
    event = json.loads(trace.read_text(encoding="utf-8").splitlines()[0])
    assert event["tool"] == "continuous_check"


def test_add_m_smoke_script_is_valid_bash() -> None:
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
