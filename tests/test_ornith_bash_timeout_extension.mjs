import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import registerOrnithBashTimeout, {
  ORNITH_DEFAULT_BASH_TIMEOUT_SECONDS,
  applyOrnithDefaultBashTimeout,
} from "../configs/baseline-ornith-35b@1.1.0/extensions/ornith-bash-timeout.ts";

function captureToolCallHandler(auditPath) {
  let handler;
  const pi = {
    on(eventName, candidate) {
      assert.equal(eventName, "tool_call");
      handler = candidate;
    },
  };
  registerOrnithBashTimeout(pi, auditPath);
  assert.equal(typeof handler, "function");
  return handler;
}

async function readAuditRecords(auditPath) {
  return (await readFile(auditPath, "utf8"))
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line));
}

test("defaults a missing Bash timeout to 360 seconds and audits it", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "ornith-bash-timeout-"));
  const auditPath = path.join(directory, "audit.ndjson");
  const handler = captureToolCallHandler(auditPath);
  const event = {
    toolName: "bash",
    toolCallId: "bash-defaulted",
    input: { command: "pytest tests/" },
  };

  await handler(event);

  assert.equal(ORNITH_DEFAULT_BASH_TIMEOUT_SECONDS, 360);
  assert.equal(event.input.timeout, 360);
  assert.deepEqual(await readAuditRecords(auditPath), [
    {
      action: "defaulted",
      effectiveTimeout: 360,
      event: "ornith_bash_timeout",
      toolCallId: "bash-defaulted",
      toolName: "bash",
    },
  ]);
});

test("preserves every model-chosen Bash timeout", async () => {
  for (const timeout of [1, 15, 30, 120, 360, 600, 3600]) {
    const input = { command: "pytest tests/", timeout };
    assert.equal(applyOrnithDefaultBashTimeout(input), "preserved");
    assert.equal(input.timeout, timeout);
  }
});

test("audits a preserved model-chosen Bash timeout", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "ornith-bash-timeout-"));
  const auditPath = path.join(directory, "audit.ndjson");
  const handler = captureToolCallHandler(auditPath);
  const event = {
    toolName: "bash",
    toolCallId: "bash-preserved",
    input: { command: "pytest tests/", timeout: 120 },
  };

  await handler(event);

  assert.equal(event.input.timeout, 120);
  assert.deepEqual(await readAuditRecords(auditPath), [
    {
      action: "preserved",
      effectiveTimeout: 120,
      event: "ornith_bash_timeout",
      toolCallId: "bash-preserved",
      toolName: "bash",
    },
  ]);
});

test("does not mutate or audit non-Bash tools", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "ornith-bash-timeout-"));
  const auditPath = path.join(directory, "audit.ndjson");
  const handler = captureToolCallHandler(auditPath);
  const event = {
    toolName: "read",
    toolCallId: "read-1",
    input: { path: "README.md" },
  };

  await handler(event);

  assert.deepEqual(event.input, { path: "README.md" });
  await assert.rejects(readFile(auditPath, "utf8"), { code: "ENOENT" });
});
