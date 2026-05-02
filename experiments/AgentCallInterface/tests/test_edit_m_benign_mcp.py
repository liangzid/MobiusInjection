from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BENIGN_MCP_SERVER = PROJECT_ROOT / "experiments/mcp/benign_mcp_audit.js"
MCP_CALL_HELPER = PROJECT_ROOT / "experiments/mcp/mobius_mcp_call_tool.js"


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


def test_benign_mcp_server_exposes_single_non_mobius_tool(tmp_path: Path) -> None:
    if shutil.which("node") is None:
        pytest.skip("node is required for MCP stdio fixture tests")
    trace = tmp_path / "benign_trace.jsonl"
    probe = tmp_path / "probe.txt"
    probe.write_text("real preconfigured MCP baseline probe\n", encoding="utf-8")
    env = os.environ.copy()
    env["BENIGN_MCP_TRACE"] = str(trace)
    proc = subprocess.Popen(
        ["node", str(BENIGN_MCP_SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        assert proc.stdin is not None
        proc.stdin.write(_mcp_frame({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
        proc.stdin.flush()
        assert _read_mcp_frame(proc)["result"]["serverInfo"]["name"] == "benign-mcp-audit"

        proc.stdin.write(_mcp_frame({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
        proc.stdin.flush()
        tools = _read_mcp_frame(proc)["result"]["tools"]
        assert [tool["name"] for tool in tools] == ["audit_status"]

        proc.stdin.write(
            _mcp_frame(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "audit_status",
                        "arguments": {"probe_path": str(probe), "mode": "baseline"},
                    },
                }
            )
        )
        proc.stdin.flush()
        text = _read_mcp_frame(proc)["result"]["content"][0]["text"]
        assert "workspace audit status: clean" in text
        assert "No follow-up MCP tool calls are required." in text
        assert "continuous_check" not in text
        assert "consistency_check" not in text

        event = json.loads(trace.read_text(encoding="utf-8").splitlines()[0])
        assert event["tool"] == "audit_status"
        assert event["probe_path"] == str(probe)
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_mcp_call_helper_can_call_benign_fixture(tmp_path: Path) -> None:
    if shutil.which("node") is None:
        pytest.skip("node is required for MCP stdio fixture tests")
    trace = tmp_path / "benign_trace.jsonl"
    probe = tmp_path / "probe.txt"
    probe.write_text("real helper probe\n", encoding="utf-8")
    env = os.environ.copy()
    env["BENIGN_MCP_TRACE"] = str(trace)
    env["MOBIUS_MCP_SERVER"] = str(BENIGN_MCP_SERVER)
    result = subprocess.run(
        ["node", str(MCP_CALL_HELPER), "audit_status", "baseline", str(probe)],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "workspace audit status: clean" in result.stdout
    assert "continuous_check" not in result.stdout
    assert "consistency_check" not in result.stdout
    event = json.loads(trace.read_text(encoding="utf-8").splitlines()[0])
    assert event["tool"] == "audit_status"
