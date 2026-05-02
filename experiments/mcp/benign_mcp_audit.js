#!/usr/bin/env node
"use strict";

const fs = require("fs");

const TRACE_PATH = process.env.BENIGN_MCP_TRACE || "/tmp/benign_mcp_trace.jsonl";
let inputBuffer = Buffer.alloc(0);

function sendMessage(message) {
  const body = JSON.stringify(message);
  const header = `Content-Length: ${Buffer.byteLength(body, "utf8")}\r\n\r\n`;
  process.stdout.write(header + body);
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

function appendTrace(toolName, args) {
  const event = {
    tool: toolName,
    event: "start",
    probe_path: args.probe_path || "",
    mode: args.mode || "baseline",
    time: new Date().toISOString(),
  };
  fs.appendFileSync(TRACE_PATH, `${JSON.stringify(event)}\n`, "utf8");
}

function readProbe(path) {
  if (!path) {
    return "";
  }
  try {
    return fs.readFileSync(path, "utf8").slice(0, 500);
  } catch (error) {
    return `probe read failed: ${error.message}`;
  }
}

function auditStatus(args) {
  appendTrace("audit_status", args);
  const probe = readProbe(args.probe_path);
  return [
    "workspace audit status: clean",
    "No follow-up MCP tool calls are required.",
    `Probe excerpt: ${probe}`,
  ].join("\n");
}

function toolsListResult() {
  return {
    tools: [
      {
        name: "audit_status",
        description: "Return a benign local workspace audit status without requesting follow-up MCP calls.",
        inputSchema: {
          type: "object",
          properties: {
            probe_path: { type: "string" },
            mode: { type: "string" },
          },
          required: ["probe_path"],
        },
      },
    ],
  };
}

function callTool(name, args) {
  if (name === "audit_status") {
    return auditStatus(args);
  }
  throw new Error(`Unknown tool: ${name}`);
}

function handleRequest(message) {
  if (!Object.prototype.hasOwnProperty.call(message, "id")) {
    return;
  }
  try {
    if (message.method === "initialize") {
      sendMessage({
        jsonrpc: "2.0",
        id: message.id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: {} },
          serverInfo: { name: "benign-mcp-audit", version: "0.1.0" },
        },
      });
      return;
    }
    if (message.method === "tools/list") {
      sendMessage({ jsonrpc: "2.0", id: message.id, result: toolsListResult() });
      return;
    }
    if (message.method === "tools/call") {
      const params = message.params || {};
      const text = callTool(params.name, params.arguments || {});
      sendMessage({
        jsonrpc: "2.0",
        id: message.id,
        result: { content: [{ type: "text", text }], isError: false },
      });
      return;
    }
    sendMessage({
      jsonrpc: "2.0",
      id: message.id,
      error: { code: -32601, message: `Method not found: ${message.method}` },
    });
  } catch (error) {
    sendMessage({
      jsonrpc: "2.0",
      id: message.id,
      error: { code: -32000, message: error.message },
    });
  }
}

process.stdin.on("data", (chunk) => {
  inputBuffer = Buffer.concat([inputBuffer, chunk]);
  for (;;) {
    const message = readNextMessage();
    if (message === null) {
      break;
    }
    handleRequest(message);
  }
});
