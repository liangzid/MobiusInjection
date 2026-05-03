import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.client import HTTPConnection

from localserver.ollama_proxy_logger import (
    OllamaProxyServer,
    ProxyConfig,
    Upstream,
    build_log_record,
)


class UpstreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"models": [{"name": "real-local-model"}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        body = json.dumps(
            {
                "model": "real-local-model",
                "message": {"role": "assistant", "content": "OK"},
                "prompt_eval_count": 7,
                "eval_count": 3,
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def start_server(server):
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return thread


def test_build_log_record_extracts_ollama_token_counts():
    record = build_log_record(
        method="POST",
        path="/api/chat",
        request_body=b'{"model":"qwen2.5:14b"}',
        response_body=b'{"prompt_eval_count":4,"eval_count":6}',
        status_code=200,
        latency_ms=12.3456,
        client_address="127.0.0.1",
    )

    assert record["model"] == "qwen2.5:14b"
    assert record["prompt_eval_count"] == 4
    assert record["eval_count"] == 6
    assert record["total_tokens"] == 10
    assert record["latency_ms"] == 12.346


def test_build_log_record_extracts_openai_token_counts():
    record = build_log_record(
        method="POST",
        path="/v1/chat/completions",
        request_body=b'{"model":"qwen2.5:14b"}',
        response_body=(
            b'{"model":"qwen2.5:14b","usage":'
            b'{"prompt_tokens":11,"completion_tokens":5,"total_tokens":16}}'
        ),
        status_code=200,
        latency_ms=1.0,
        client_address="127.0.0.1",
    )

    assert record["model"] == "qwen2.5:14b"
    assert record["prompt_eval_count"] == 11
    assert record["eval_count"] == 5
    assert record["total_tokens"] == 16


def test_build_log_record_extracts_streaming_ollama_token_counts():
    response_body = b"\n".join(
        [
            b'{"model":"qwen2.5:14b","message":{"content":"OK"},"done":false}',
            b'{"model":"qwen2.5:14b","done":true,'
            b'"prompt_eval_count":21,"eval_count":4}',
        ]
    )
    record = build_log_record(
        method="POST",
        path="/api/chat",
        request_body=b'{"model":"qwen2.5:14b"}',
        response_body=response_body,
        status_code=200,
        latency_ms=1.0,
        client_address="127.0.0.1",
    )

    assert record["model"] == "qwen2.5:14b"
    assert record["prompt_eval_count"] == 21
    assert record["eval_count"] == 4
    assert record["total_tokens"] == 25


def test_proxy_forwards_local_requests_and_writes_jsonl(tmp_path):
    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    start_server(upstream)
    log_path = tmp_path / "proxy.jsonl"
    proxy = OllamaProxyServer(
        ("127.0.0.1", 0),
        ProxyConfig(
            upstream=Upstream("127.0.0.1", upstream.server_port, "http"),
            log_path=log_path,
            timeout_seconds=5,
        ),
    )
    start_server(proxy)

    try:
        conn = HTTPConnection("127.0.0.1", proxy.server_port, timeout=5)
        conn.request(
            "POST",
            "/api/chat",
            body=b'{"model":"real-local-model","stream":false}',
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        response_body = response.read()
        conn.close()

        assert response.status == 200
        assert json.loads(response_body)["message"]["content"] == "OK"

        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["path"] == "/api/chat"
        assert record["model"] == "real-local-model"
        assert record["prompt_eval_count"] == 7
        assert record["eval_count"] == 3
        assert record["total_tokens"] == 10
        assert record["status_code"] == 200
    finally:
        proxy.shutdown()
        upstream.shutdown()
