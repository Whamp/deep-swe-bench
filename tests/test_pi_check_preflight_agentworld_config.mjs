import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import registerQwenAgentWorldBashTimeout, {
  QWEN_AGENTWORLD_DEFAULT_BASH_TIMEOUT_SECONDS,
  applyQwenAgentWorldDefaultBashTimeout,
} from "../configs/pi-check@1.6.0/extensions/qwen-agentworld-bash-timeout.ts";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const configRoot = path.join(repositoryRoot, "configs/pi-check@1.6.0");
const expectedPiCheckSourceHashes = {
  LICENSE: "3d4e9090aa3b4e96cf2ca7ecacfa58432cd655949ea79f5b20371429a9419189",
  "README.md": "830080ca277b22b5098cfdb0ba3381898bb28cc505e29e59afd906ef33dce1a5",
  "package.json": "fed82105efa37da1c0af99f1dbe5d96e3602e6a99dfff009c02b11ecde53c9fb",
  "extensions/checkExtension.ts":
    "18831af527441a53ddcdc6485a117ee99ae39d2208b64d30f73bd8b8043441b7",
  "extensions/isBashFileMutation.ts":
    "3882f5086970f9c2dea470b994ac3097e8bd6b8d4467cc6a6093abfc13f22f24",
  "extensions/preflightController.ts":
    "a36802950067781934cb58c4e71bd5221e6923480b22281f1c7784412da22808",
};

async function sha256(filePath) {
  return createHash("sha256")
    .update(await readFile(filePath))
    .digest("hex");
}

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

test("vendors the reviewed pi-check PreFlight source from commit 57d5013", async () => {
  for (const [relativePath, expectedHash] of Object.entries(expectedPiCheckSourceHashes)) {
    assert.equal(
      await sha256(path.join(configRoot, "extensions/pi-check", relativePath)),
      expectedHash,
      relativePath,
    );
  }
});

test("enables PreFlight, exact-model final check, and AgentWorld timeout in order", async () => {
  const flags = (await readFile(path.join(configRoot, "pi-flags"), "utf8")).trim().split("\n");
  assert.deepEqual(flags, [
    "-e",
    "/arm/extensions/local-vllm-qwen-agentworld-request.ts",
    "-e",
    "/arm/extensions/qwen-agentworld-bash-timeout.ts",
    "-e",
    "/arm/extensions/pi-check/extensions/checkExtension.ts",
    "--check-preflight",
    "--check",
    "local-vllm/qwen-agentworld-35b-a3b:high",
  ]);
});

test("defaults missing Bash timeouts to 360 seconds and preserves numeric choices", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "agentworld-preflight-timeout-"));
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
  for (const timeout of [1, 120, 360, 600, 3600]) {
    const input = { command: "pytest tests/", timeout };
    assert.equal(applyQwenAgentWorldDefaultBashTimeout(input), "preserved");
    assert.equal(input.timeout, timeout);
  }
});
