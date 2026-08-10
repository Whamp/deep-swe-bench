import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import registerLlamacppDeepSeekV4BashTimeout, {
  LLAMACPP_DEEPSEEK_V4_DEFAULT_BASH_TIMEOUT_SECONDS,
  applyLlamacppDeepSeekV4DefaultBashTimeout,
} from "../configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0/extensions/local-llamacpp-deepseek-v4-bash-timeout.ts";

function captureLlamacppDeepSeekV4ToolCallHandler(auditPath) {
  let handler;
  const pi = {
    on(eventName, candidate) {
      assert.equal(eventName, "tool_call");
      handler = candidate;
    },
  };
  registerLlamacppDeepSeekV4BashTimeout(pi, auditPath);
  assert.equal(typeof handler, "function");
  return handler;
}

async function readLlamacppDeepSeekV4TimeoutAuditRecords(auditPath) {
  return (await readFile(auditPath, "utf8"))
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line));
}

test("defaults a missing llama.cpp DeepSeek V4 Bash timeout to 360 seconds", async () => {
  const directory = await mkdtemp(
    path.join(os.tmpdir(), "llamacpp-deepseek-v4-bash-timeout-"),
  );
  const auditPath = path.join(directory, "audit.ndjson");
  const handler = captureLlamacppDeepSeekV4ToolCallHandler(auditPath);
  const event = {
    toolName: "bash",
    toolCallId: "bash-defaulted",
    input: { command: "pytest tests/" },
  };

  await handler(event);

  assert.equal(LLAMACPP_DEEPSEEK_V4_DEFAULT_BASH_TIMEOUT_SECONDS, 360);
  assert.equal(event.input.timeout, 360);
  assert.deepEqual(await readLlamacppDeepSeekV4TimeoutAuditRecords(auditPath), [
    {
      action: "defaulted",
      effectiveTimeout: 360,
      event: "llamacpp_deepseek_v4_bash_timeout",
      toolCallId: "bash-defaulted",
      toolName: "bash",
    },
  ]);
});

test("preserves every model-chosen llama.cpp DeepSeek V4 Bash timeout", () => {
  for (const timeout of [1, 15, 30, 120, 360, 600, 3600]) {
    const input = { command: "pytest tests/", timeout };
    assert.equal(applyLlamacppDeepSeekV4DefaultBashTimeout(input), "preserved");
    assert.equal(input.timeout, timeout);
  }
});

test("does not mutate or audit non-Bash tools", async () => {
  const directory = await mkdtemp(
    path.join(os.tmpdir(), "llamacpp-deepseek-v4-bash-timeout-"),
  );
  const auditPath = path.join(directory, "audit.ndjson");
  const handler = captureLlamacppDeepSeekV4ToolCallHandler(auditPath);
  const event = {
    toolName: "read",
    toolCallId: "read-1",
    input: { path: "README.md" },
  };

  await handler(event);

  assert.deepEqual(event.input, { path: "README.md" });
  await assert.rejects(readFile(auditPath, "utf8"), { code: "ENOENT" });
});
