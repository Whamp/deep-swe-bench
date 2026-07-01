#!/usr/bin/env node
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const REPO = path.resolve(new URL("../..", import.meta.url).pathname);
const PI_BIN = process.env.PI_BIN || "pi";
const SENTINEL = `OM_VISIBILITY_SENTINEL_${Math.random().toString(16).slice(2)}_do_not_ignore`;
const OM_INDEX = path.join(REPO, "configs/observational-memory/extensions/pi-observational-memory/src/index.ts");
const CAPTURE_EXT = path.join(REPO, "analysis/om-visibility-smoke/extensions/payload-capture.ts");
const SEED_EXT = path.join(REPO, "analysis/om-visibility-smoke/extensions/seed-om-memory.ts");

function mkdirp(p) { fs.mkdirSync(p, { recursive: true }); }
function readJsonl(file) {
  if (!fs.existsSync(file)) return [];
  return fs.readFileSync(file, "utf8").trim().split("\n").filter(Boolean).map((line) => JSON.parse(line));
}

function makeServer() {
  const requests = [];
  const server = http.createServer((req, res) => {
    let body = "";
    req.on("data", (chunk) => { body += chunk; });
    req.on("end", () => {
      let json = {};
      try { json = body ? JSON.parse(body) : {}; } catch {}
      requests.push({ url: req.url, body: json });
      if (!req.url?.includes("/chat/completions")) {
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ object: "list", data: [] }));
        return;
      }
      const content = "SMOKE_PROVIDER_ACK";
      const promptTokens = Math.ceil(JSON.stringify(json.messages ?? []).length / 4);
      const completionTokens = 3;
      if (json.stream) {
        res.writeHead(200, {
          "content-type": "text/event-stream",
          "cache-control": "no-cache",
          connection: "keep-alive",
        });
        const id = `chatcmpl-smoke-${requests.length}`;
        res.write(`data: ${JSON.stringify({ id, object: "chat.completion.chunk", model: json.model, choices: [{ index: 0, delta: { role: "assistant" }, finish_reason: null }] })}\n\n`);
        res.write(`data: ${JSON.stringify({ id, object: "chat.completion.chunk", model: json.model, choices: [{ index: 0, delta: { content }, finish_reason: null }] })}\n\n`);
        res.write(`data: ${JSON.stringify({ id, object: "chat.completion.chunk", model: json.model, choices: [{ index: 0, delta: {}, finish_reason: "stop" }], usage: { prompt_tokens: promptTokens, completion_tokens: completionTokens, total_tokens: promptTokens + completionTokens } })}\n\n`);
        res.write("data: [DONE]\n\n");
        res.end();
        return;
      }
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({
        id: `chatcmpl-smoke-${requests.length}`,
        object: "chat.completion",
        model: json.model,
        choices: [{ index: 0, message: { role: "assistant", content }, finish_reason: "stop" }],
        usage: { prompt_tokens: promptTokens, completion_tokens: completionTokens, total_tokens: promptTokens + completionTokens },
      }));
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve({ server, port: server.address().port, requests }));
  });
}

function writeAgentConfig(root, port, omSettings = {}) {
  const agent = path.join(root, "agent");
  mkdirp(agent);
  fs.writeFileSync(path.join(agent, "models.json"), JSON.stringify({
    providers: {
      smoke: {
        baseUrl: `http://127.0.0.1:${port}/v1`,
        api: "openai-completions",
        apiKey: "smoke-key",
        compat: { supportsDeveloperRole: false, supportsReasoningEffort: false },
        models: [{
          id: "echo",
          name: "Smoke Echo",
          reasoning: false,
          contextWindow: 20000,
          maxTokens: 1024,
          cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        }],
      },
    },
  }, null, 2));
  fs.writeFileSync(path.join(agent, "settings.json"), JSON.stringify({
    defaultProjectTrust: "always",
    compaction: { enabled: false, reserveTokens: 1024, keepRecentTokens: 1 },
    "observational-memory": {
      observeAfterTokens: 1,
      reflectAfterTokens: 999999,
      compactAfterTokens: 1,
      observationsPoolMaxTokens: 20000,
      observationsPoolTargetTokens: 10000,
      agentMaxTurns: 2,
      model: { provider: "smoke", id: "echo", thinking: "off" },
      passive: false,
      debugLog: true,
      ...omSettings,
    },
  }, null, 2));
  return agent;
}

function startPi({ root, port, payloadLog, extensions = [], appendSystemPrompt = "" }) {
  const cwd = path.join(root, "work");
  mkdirp(cwd);
  writeAgentConfig(root, port);
  const args = [
    "--mode", "rpc",
    "--model", "smoke/echo",
    "--thinking", "off",
    "--no-skills",
    "--no-context-files",
    "-a",
  ];
  if (appendSystemPrompt) args.push("--append-system-prompt", appendSystemPrompt);
  for (const ext of extensions) args.push("-e", ext);
  const child = spawn(PI_BIN, args, {
    cwd,
    env: {
      ...process.env,
      PI_CODING_AGENT_DIR: path.join(root, "agent"),
      OM_VISIBILITY_SENTINEL: SENTINEL,
      OM_VISIBILITY_PAYLOAD_LOG: payloadLog,
    },
    stdio: ["pipe", "pipe", "pipe"],
  });
  const events = [];
  let buffer = "";
  child.stdout.on("data", (chunk) => {
    buffer += chunk.toString();
    for (;;) {
      const i = buffer.indexOf("\n");
      if (i < 0) break;
      const line = buffer.slice(0, i).trim();
      buffer = buffer.slice(i + 1);
      if (!line) continue;
      try { events.push(JSON.parse(line)); } catch { events.push({ type: "raw", line }); }
    }
  });
  let stderr = "";
  child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
  function send(obj) { child.stdin.write(JSON.stringify(obj) + "\n"); }
  async function waitFor(pred, label, timeoutMs = 20000) {
    const start = Date.now();
    let idx = 0;
    while (Date.now() - start < timeoutMs) {
      while (idx < events.length) {
        const ev = events[idx++];
        if (pred(ev)) return ev;
      }
      if (child.exitCode !== null) throw new Error(`pi exited while waiting for ${label}; stderr=${stderr}`);
      await new Promise((r) => setTimeout(r, 25));
    }
    throw new Error(`timeout waiting for ${label}; lastEvents=${JSON.stringify(events.slice(-5))}; stderr=${stderr}`);
  }
  async function stop() {
    child.kill("SIGTERM");
    await new Promise((r) => setTimeout(r, 100));
    if (child.exitCode === null) child.kill("SIGKILL");
  }
  return { child, send, waitFor, stop, events, get stderr() { return stderr; } };
}

async function promptAndWait(rpc, id, message) {
  rpc.send({ id, type: "prompt", message });
  await rpc.waitFor((ev) => ev.type === "response" && ev.id === id && ev.success === true, `${id} accepted`);
  await rpc.waitFor((ev) => ev.type === "agent_end", `${id} agent_end`, 30000);
}

async function getSessionStats(rpc) {
  rpc.send({ id: "stats-1", type: "get_session_stats" });
  const res = await rpc.waitFor((ev) => ev.type === "response" && ev.id === "stats-1", "session stats", 10000);
  if (!res.success) throw new Error(`get_session_stats failed: ${JSON.stringify(res)}`);
  return res.data;
}

async function compactAndWait(rpc) {
  const stats = await getSessionStats(rpc);
  rpc.send({ id: "compact-1", type: "compact" });
  const res = await rpc.waitFor((ev) => ev.type === "response" && ev.id === "compact-1", "compact response", 30000);
  if (!res.success) {
    if (String(res.error ?? "").includes("Already compacted")) return { compact: null, statsBefore: stats, alreadyCompacted: true };
    throw new Error(`compact failed: ${JSON.stringify(res)} stats=${JSON.stringify(stats)}`);
  }
  return { compact: res.data, statsBefore: stats, alreadyCompacted: false };
}

async function seedAndWait(rpc) {
  rpc.send({ id: "seed-om", type: "prompt", message: "/seedom" });
  const res = await rpc.waitFor((ev) => ev.type === "response" && ev.id === "seed-om", "seed command response", 10000);
  if (!res.success) throw new Error(`seed command failed: ${JSON.stringify(res)}`);
}

async function positiveControl(port) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "om-vis-positive-"));
  const payloadLog = path.join(root, "payloads.jsonl");
  const rpc = startPi({
    root,
    port,
    payloadLog,
    extensions: [CAPTURE_EXT],
    appendSystemPrompt: `Positive-control sentinel: ${SENTINEL}`,
  });
  try {
    await promptAndWait(rpc, "positive-prompt", "Say ACK for the positive control.");
  } finally {
    await rpc.stop();
  }
  const rows = readJsonl(payloadLog).filter((r) => r.role === "executor");
  return { root, payloadLog, ok: rows.some((r) => r.containsSentinel), rows };
}

async function compactionProjection(port) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "om-vis-compaction-"));
  const payloadLog = path.join(root, "payloads.jsonl");
  const rpc = startPi({
    root,
    port,
    payloadLog,
    extensions: [CAPTURE_EXT, SEED_EXT, OM_INDEX],
  });
  const filler = "compact-me ".repeat(30000);
  let compactData;
  try {
    await promptAndWait(rpc, "phase-one", `PHASE_ONE_PROMPT. Say ACK only.\n${filler}`);
    await seedAndWait(rpc);
    await promptAndWait(rpc, "pre-compact", "PRE_COMPACT_PROMPT. Say ACK only.");
    compactData = await compactAndWait(rpc);
    await promptAndWait(rpc, "phase-two", "PHASE_TWO_PROMPT. Say ACK only.");
  } finally {
    await rpc.stop();
  }
  const rows = readJsonl(payloadLog).filter((r) => r.role === "executor");
  const phaseOne = rows.filter((r) => JSON.stringify(r.payload).includes("PHASE_ONE_PROMPT"));
  const phaseTwo = rows.filter((r) => JSON.stringify(r.payload).includes("PHASE_TWO_PROMPT"));
  return {
    root,
    payloadLog,
    compactData,
    phaseOneHasSentinel: phaseOne.some((r) => r.containsSentinel),
    phaseTwoHasSentinel: phaseTwo.some((r) => r.containsSentinel),
    phaseTwoHasSummaryHeader: phaseTwo.some((r) => r.containsOmSummaryHeader),
    phaseTwoHasObservationId: phaseTwo.some((r) => r.containsObservationId),
    rows,
  };
}

const { server, port, requests } = await makeServer();
try {
  const positive = await positiveControl(port);
  const compaction = await compactionProjection(port);
  const summary = {
    sentinel: SENTINEL,
    positiveControl: {
      ok: positive.ok,
      payloadLog: positive.payloadLog,
      executorRequests: positive.rows.length,
    },
    compactionProjection: {
      ok: !compaction.phaseOneHasSentinel && compaction.phaseTwoHasSentinel && compaction.phaseTwoHasSummaryHeader && compaction.phaseTwoHasObservationId,
      payloadLog: compaction.payloadLog,
      compactData: compaction.compactData,
      executorRequests: compaction.rows.length,
      phaseOneHasSentinel: compaction.phaseOneHasSentinel,
      phaseTwoHasSentinel: compaction.phaseTwoHasSentinel,
      phaseTwoHasSummaryHeader: compaction.phaseTwoHasSummaryHeader,
      phaseTwoHasObservationId: compaction.phaseTwoHasObservationId,
    },
    fakeProviderRequests: requests.length,
  };
  console.log(JSON.stringify(summary, null, 2));
  if (!summary.positiveControl.ok || !summary.compactionProjection.ok) process.exitCode = 1;
} finally {
  server.close();
}
