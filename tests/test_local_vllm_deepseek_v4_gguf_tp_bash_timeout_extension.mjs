import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import registerLocalVllmDeepSeekV4GgufTpBashTimeout, {
  LOCAL_VLLM_DEEPSEEK_V4_GGUF_TP_DEFAULT_BASH_TIMEOUT_SECONDS,
  applyLocalVllmDeepSeekV4GgufTpDefaultBashTimeout,
} from "../configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/extensions/local-vllm-deepseek-v4-gguf-tp-bash-timeout.ts";

function captureLocalVllmDeepSeekV4GgufTpToolCallHandler(auditPath) {
  let handler;
  registerLocalVllmDeepSeekV4GgufTpBashTimeout(
    {
      on(eventName, candidate) {
        assert.equal(eventName, "tool_call");
        handler = candidate;
      },
    },
    auditPath,
  );
  assert.equal(typeof handler, "function");
  return handler;
}

test("defaults a missing GGUF-TP bash timeout to 360 seconds", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "gguf-tp-bash-timeout-"));
  const auditPath = path.join(directory, "audit.ndjson");
  const handler = captureLocalVllmDeepSeekV4GgufTpToolCallHandler(auditPath);
  const event = {
    toolName: "bash",
    toolCallId: "bash-defaulted",
    input: { command: "pytest tests/" },
  };

  await handler(event);

  assert.equal(LOCAL_VLLM_DEEPSEEK_V4_GGUF_TP_DEFAULT_BASH_TIMEOUT_SECONDS, 360);
  assert.equal(event.input.timeout, 360);
  const records = (await readFile(auditPath, "utf8"))
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line));
  assert.deepEqual(records, [
    {
      action: "defaulted",
      effectiveTimeout: 360,
      event: "local_vllm_deepseek_v4_gguf_tp_bash_timeout",
      toolCallId: "bash-defaulted",
      toolName: "bash",
    },
  ]);
});

test("preserves model-selected GGUF-TP bash timeouts", () => {
  for (const timeout of [1, 15, 30, 120, 360, 600, 3600]) {
    const input = { command: "pytest tests/", timeout };
    assert.equal(applyLocalVllmDeepSeekV4GgufTpDefaultBashTimeout(input), "preserved");
    assert.equal(input.timeout, timeout);
  }
});

test("does not mutate or audit non-bash tools", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "gguf-tp-bash-timeout-"));
  const auditPath = path.join(directory, "audit.ndjson");
  const handler = captureLocalVllmDeepSeekV4GgufTpToolCallHandler(auditPath);
  const event = {
    toolName: "read",
    toolCallId: "read-1",
    input: { path: "README.md" },
  };

  await handler(event);

  assert.deepEqual(event.input, { path: "README.md" });
  await assert.rejects(readFile(auditPath, "utf8"), { code: "ENOENT" });
});
