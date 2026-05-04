#!/usr/bin/env python3
"""Local Ollama-compatible proxy that records request metrics as JSONL."""

from __future__ import annotations

import argparse
import json
import socket
import time
from dataclasses import dataclass
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


@dataclass(frozen=True)
class Upstream:
    host: str
    port: int
    scheme: str


@dataclass(frozen=True)
class ProxyConfig:
    upstream: Upstream
    log_path: Path
    timeout_seconds: float


def parse_upstream(raw_url: str) -> Upstream:
    parsed = urlparse(raw_url)
    if parsed.scheme != "http":
        raise ValueError("Only http upstream URLs are supported for local experiments")
    if not parsed.hostname:
        raise ValueError("Upstream URL must include a host")
    return Upstream(host=parsed.hostname, port=parsed.port or 80, scheme=parsed.scheme)


def json_or_none(raw: bytes) -> Any | None:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def stream_json_objects(raw: bytes) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith(b"data:"):
            text = text.removeprefix(b"data:").strip()
            if text == b"[DONE]":
                continue
        try:
            parsed = json.loads(text.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(parsed, dict):
            objects.append(parsed)
    return objects


def response_payloads(response_json: Any | None, response_body: bytes) -> list[dict[str, Any]]:
    if isinstance(response_json, dict):
        return [response_json]
    return stream_json_objects(response_body)


def token_counts(response_json: Any | None) -> dict[str, int | None]:
    if not isinstance(response_json, dict):
        return {"prompt_eval_count": None, "eval_count": None, "total_tokens": None}
    prompt_count, eval_count, total = ollama_token_counts(response_json)
    if prompt_count is None and eval_count is None and total is None:
        prompt_count, eval_count, total = openai_token_counts(response_json)
    if prompt_count is None and eval_count is None and total is None:
        prompt_count, eval_count, total = anthropic_token_counts(response_json)
    return {
        "prompt_eval_count": prompt_count,
        "eval_count": eval_count,
        "total_tokens": total,
    }


def ollama_token_counts(response_json: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
    prompt_count = response_json.get("prompt_eval_count")
    eval_count = response_json.get("eval_count")
    total = None
    if isinstance(prompt_count, int) and isinstance(eval_count, int):
        total = prompt_count + eval_count
    return (
        prompt_count if isinstance(prompt_count, int) else None,
        eval_count if isinstance(eval_count, int) else None,
        total,
    )


def openai_token_counts(response_json: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
    usage = response_json.get("usage")
    if not isinstance(usage, dict):
        return None, None, None
    prompt_count = usage.get("prompt_tokens")
    eval_count = usage.get("completion_tokens")
    total = usage.get("total_tokens")
    return (
        prompt_count if isinstance(prompt_count, int) else None,
        eval_count if isinstance(eval_count, int) else None,
        total if isinstance(total, int) else None,
    )


def anthropic_token_counts(response_json: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
    usage = response_json.get("usage")
    if not isinstance(usage, dict):
        return None, None, None
    prompt_count = usage.get("input_tokens")
    eval_count = usage.get("output_tokens")
    prompt = prompt_count if isinstance(prompt_count, int) else None
    completion = eval_count if isinstance(eval_count, int) else None
    total = prompt + completion if prompt is not None and completion is not None else None
    return prompt, completion, total


def model_name(request_json: Any | None, response_json: Any | None) -> str | None:
    for payload in (request_json, response_json):
        if isinstance(payload, dict) and isinstance(payload.get("model"), str):
            return payload["model"]
    return None


def first_model_name(payloads: list[dict[str, Any]]) -> str | None:
    for payload in payloads:
        if isinstance(payload.get("model"), str):
            return payload["model"]
    return None


def best_token_counts(payloads: list[dict[str, Any]]) -> dict[str, int | None]:
    for payload in reversed(payloads):
        counts = token_counts(payload)
        if any(value is not None for value in counts.values()):
            return counts
    return {"prompt_eval_count": None, "eval_count": None, "total_tokens": None}


def filtered_headers(headers: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() not in HOP_BY_HOP_HEADERS:
            result[key] = value
    return result


def build_log_record(
    *,
    method: str,
    path: str,
    request_body: bytes,
    response_body: bytes,
    status_code: int,
    latency_ms: float,
    client_address: str,
) -> dict[str, Any]:
    request_json = json_or_none(request_body)
    response_json = json_or_none(response_body)
    payloads = response_payloads(response_json, response_body)
    counts = best_token_counts(payloads)
    return {
        "ts": time.time(),
        "client": client_address,
        "method": method,
        "path": path,
        "model": model_name(request_json, response_json) or first_model_name(payloads),
        "status_code": status_code,
        "latency_ms": round(latency_ms, 3),
        "request_bytes": len(request_body),
        "response_bytes": len(response_body),
        **counts,
    }


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


class OllamaProxyHandler(BaseHTTPRequestHandler):
    server: "OllamaProxyServer"

    def do_GET(self) -> None:
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def do_HEAD(self) -> None:
        self._proxy()

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _request_body(self) -> bytes:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0:
            return b""
        return self.rfile.read(content_length)

    def _proxy(self) -> None:
        body = self._request_body()
        start = time.perf_counter()
        status, headers, response_body = self._forward(body)
        latency_ms = (time.perf_counter() - start) * 1000.0
        self._log(body, response_body, status, latency_ms)
        self._send_response(status, headers, response_body)

    def _forward(self, body: bytes) -> tuple[int, dict[str, str], bytes]:
        config = self.server.config
        conn = HTTPConnection(config.upstream.host, config.upstream.port, timeout=config.timeout_seconds)
        headers = filtered_headers(self.headers)
        headers["Host"] = f"{config.upstream.host}:{config.upstream.port}"
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            response = conn.getresponse()
            response_body = read_response_body(response)
            return response.status, filtered_headers(response.headers), response_body
        finally:
            conn.close()

    def _send_response(self, status: int, headers: dict[str, str], response_body: bytes) -> None:
        self.send_response(status)
        for key, value in headers.items():
            if key.lower() != "content-length":
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(response_body)

    def _log(self, request_body: bytes, response_body: bytes, status: int, latency_ms: float) -> None:
        record = build_log_record(
            method=self.command,
            path=self.path,
            request_body=request_body,
            response_body=response_body,
            status_code=status,
            latency_ms=latency_ms,
            client_address=self.client_address[0],
        )
        append_jsonl(self.server.config.log_path, record)


class OllamaProxyServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], config: ProxyConfig):
        super().__init__(server_address, OllamaProxyHandler)
        self.config = config


def read_response_body(response: Any, chunk_size: int = 65536) -> bytes:
    chunks: list[bytes] = []
    while True:
        try:
            chunk = response.read(chunk_size)
        except (ConnectionResetError, socket.timeout):
            break
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11436)
    parser.add_argument("--upstream", default="http://127.0.0.1:11435")
    parser.add_argument("--log-path", default="localserver/ollama_proxy.jsonl")
    parser.add_argument("--timeout-seconds", type=float, default=600.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ProxyConfig(
        upstream=parse_upstream(args.upstream),
        log_path=Path(args.log_path),
        timeout_seconds=args.timeout_seconds,
    )
    server = OllamaProxyServer((args.host, args.port), config)
    print(
        f"proxy listening on http://{args.host}:{args.port}, "
        f"upstream={args.upstream}, log={config.log_path}",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
