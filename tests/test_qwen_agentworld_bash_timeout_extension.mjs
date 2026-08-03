import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import registerQwenAgentWorldBashTimeout, {
  QWEN_AGENTWORLD_DEFAULT_BASH_TIMEOUT_SECONDS,
  applyQwenAgentWorldDefaultBashTimeout,
} from "../configs/pi-check@1.3.0/extensions/qwen-agentworld-bash-timeout.ts";

function captureQwenAgentWorldToolCallHandler(auditPath) {
  let handler;
  const pi = {
    on(eventName, candidate) {
      assert.equal(eventName, "tool_call");
      handler = candidate;
    },
  };
  registerQwenAgentWorldBashTimeout(pi, auditPath);
  assert.equal(typeof handler, "function");
  return handler;
}

async function readQwenAgentWorldTimeoutAuditRecords(auditPath) {
  return (await readFile(auditPath, "utf8"))
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line));
}

test("defaults a missing Qwen-AgentWorld Bash timeout to 360 seconds", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "qwen-agentworld-bash-timeout-"));
  const auditPath = path.join(directory, "audit.ndjson");
  const handler = captureQwenAgentWorldToolCallHandler(auditPath);
  const event = {
    toolName: "bash",
    toolCallId: "bash-defaulted",
    input: { command: "pytest tests/" },
  };

  await handler(event);

  assert.equal(QWEN_AGENTWORLD_DEFAULT_BASH_TIMEOUT_SECONDS, 360);
  assert.equal(event.input.timeout, 360);
  assert.deepEqual(await readQwenAgentWorldTimeoutAuditRecords(auditPath), [
    {
      action: "defaulted",
      effectiveTimeout: 360,
      event: "qwen_agentworld_bash_timeout",
      toolCallId: "bash-defaulted",
      toolName: "bash",
    },
  ]);
});

test("preserves every model-chosen Qwen-AgentWorld Bash timeout", () => {
  for (const timeout of [1, 15, 30, 120, 360, 600, 3600]) {
    const input = { command: "pytest tests/", timeout };
    assert.equal(applyQwenAgentWorldDefaultBashTimeout(input), "preserved");
    assert.equal(input.timeout, timeout);
  }
});

test("does not mutate or audit non-Bash tools", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "qwen-agentworld-bash-timeout-"));
  const auditPath = path.join(directory, "audit.ndjson");
  const handler = captureQwenAgentWorldToolCallHandler(auditPath);
  const event = {
    toolName: "read",
    toolCallId: "read-1",
    input: { path: "README.md" },
  };

  await handler(event);

  assert.deepEqual(event.input, { path: "README.md" });
  await assert.rejects(readFile(auditPath, "utf8"), { code: "ENOENT" });
});
