import { appendFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const MODEL = "cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4";
const AUDIT_PATH = join(homedir(), ".pi", "workflows", "qwen-request-guard.ndjson");
const MARKER = "__QWEN_WORKFLOW_REQUEST_GUARD__";
let sequence = 0;
let completedTurns = 0;
let toolsRemoved = false;

function workflowIsActive(): boolean {
  return process.env.PI_QWEN_WORKFLOW_ACTIVE === "1";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function appendAudit(value: unknown): void {
  mkdirSync(dirname(AUDIT_PATH), { recursive: true });
  appendFileSync(AUDIT_PATH, `${JSON.stringify(value)}\n`, "utf8");
}

export default function workflowRequestAudit(pi: ExtensionAPI): void {
  pi.on("before_provider_request", (event) => {
    if (!isRecord(event.payload) || event.payload.model !== MODEL) {
      return;
    }

    const existingTemplate = isRecord(event.payload.chat_template_kwargs)
      ? event.payload.chat_template_kwargs
      : {};
    event.payload.chat_template_kwargs = {
      ...existingTemplate,
      enable_thinking: true,
      preserve_thinking: true,
    };
    event.payload.temperature = 1.0;
    event.payload.top_p = 0.95;
    event.payload.top_k = 20;
    event.payload.min_p = 0.0;
    event.payload.presence_penalty = 0.0;
    event.payload.repetition_penalty = 1.0;

    sequence += 1;
    const audit = {
      marker: MARKER,
      sequence,
      scope: workflowIsActive() ? "workflow" : "main",
      provider: "local-vllm",
      model: `local-vllm/${MODEL}`,
      enable_thinking: true,
      preserve_thinking: true,
      temperature: 1.0,
      top_p: 0.95,
      top_k: 20,
      min_p: 0.0,
      presence_penalty: 0.0,
      repetition_penalty: 1.0,
    };
    appendAudit(audit);
    process.stderr.write(`${JSON.stringify(audit)}\n`);
  });

  pi.on("turn_end", async (_event, ctx) => {
    if (!workflowIsActive() || toolsRemoved) {
      return;
    }
    completedTurns += 1;
    const writer = !ctx.cwd.includes("/.pi/worktrees/");
    const limit = writer ? 30 : 12;
    if (completedTurns < limit) {
      return;
    }
    toolsRemoved = true;
    pi.setActiveTools([]);
    process.stderr.write(`${JSON.stringify({
      marker: "__QWEN_WORKFLOW_TURN_CAP__",
      completedTurns,
      limit,
      writer,
    })}\n`);
  });
}
