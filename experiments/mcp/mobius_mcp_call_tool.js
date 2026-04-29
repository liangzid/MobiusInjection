#!/usr/bin/env node
"use strict";

const { spawn } = require("child_process");

const [, , toolName, mode = "baseline", probePath = "/tmp/mobius_mcp_probe.txt"] = process.argv;
if (!toolName) {
  console.error("usage: mobius_mcp_call_tool.js <tool> [mode] [probe_path]");
  process.exit(2);
}

const serverPath = process.env.MOBIUS_MCP_SERVER || "/tmp/mobius_mcp_minimal.js";
const nodeBinary = process.env.MOBIUS_NODE || process.execPath || "node";
const child = spawn(nodeBinary, [serverPath], {
  env: {
    ...process.env,
    MOBIUS_MCP_TRACE: process.env.MOBIUS_MCP_TRACE || "/tmp/mobius_mcp_trace.jsonl",
  },
});

let inputBuffer = Buffer.alloc(0);
const pending = new Map();

function sendMessage(message) {
  const body = JSON.stringify(message);
  child.stdin.write(`Content-Length: ${Buffer.byteLength(body, "utf8")}\r\n\r\n${body}`);
}

function readNextMessage() {
  const headerEnd = inputBuffer.indexOf("\r\n\r\n");
  if (headerEnd === -1) {
    return null;
  }
  const header = inputBuffer.slice(0, headerEnd).toString("utf8");
  const match = header.match(/Content-Length:\s*(\d+)/i);
  if (!match) {
    throw new Error(`Missing Content-Length header: ${header}`);
  }
  const length = Number(match[1]);
  const bodyStart = headerEnd + 4;
  const bodyEnd = bodyStart + length;
  if (inputBuffer.length < bodyEnd) {
    return null;
  }
  const raw = inputBuffer.slice(bodyStart, bodyEnd).toString("utf8");
  inputBuffer = inputBuffer.slice(bodyEnd);
  return JSON.parse(raw);
}

child.stdout.on("data", (chunk) => {
  inputBuffer = Buffer.concat([inputBuffer, chunk]);
  for (;;) {
    const message = readNextMessage();
    if (message === null) {
      break;
    }
    const waiter = pending.get(message.id);
    if (waiter) {
      pending.delete(message.id);
      waiter.resolve(message);
    }
  }
});

child.stderr.on("data", (chunk) => {
  process.stderr.write(chunk);
});

function request(method, params) {
  return new Promise((resolve, reject) => {
    const id = pending.size + 1;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`MCP request timed out: ${method}`));
    }, 10000);
    pending.set(id, {
      resolve: (message) => {
        clearTimeout(timer);
        resolve(message);
      },
    });
    sendMessage({ jsonrpc: "2.0", id, method, params });
  });
}

async function main() {
  await request("initialize", {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "mobius-mcp-call-tool", version: "0.1.0" },
  });
  const response = await request("tools/call", {
    name: toolName,
    arguments: { probe_path: probePath, mode },
  });
  if (response.error) {
    throw new Error(response.error.message || JSON.stringify(response.error));
  }
  const text = response.result?.content?.[0]?.text || JSON.stringify(response.result);
  console.log(text);
  child.stdin.end();
}

main()
  .then(() => {
    child.kill();
  })
  .catch((error) => {
    child.kill();
    console.error(error.message);
    process.exit(1);
  });
