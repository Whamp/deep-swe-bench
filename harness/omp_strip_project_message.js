import { appendFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const PROJECT_HEADER = "PROJECT\n===================================";
const REQUIRED_MARKERS = [
  "<workstation>",
  "Each response MUST advance the task",
  "There is no stopping condition other than completion",
  "You MUST verify the effect of significant behavioral changes before yielding",
];

function allowedTools() {
  const raw = process.env.OMP_ALLOWED_TOOLS || "";
  const names = raw.split(",").map((name) => name.trim()).filter(Boolean);
  return names.length > 0 ? new Set(names) : null;
}

function toolName(tool) {
  if (!tool || typeof tool !== "object") return "";
  return String(tool?.function?.name || tool?.name || tool?.type || "");
}

function filterTools(tools, allowed) {
  if (!Array.isArray(tools) || !allowed) return { tools, strippedToolNames: [] };
  const kept = [];
  const strippedToolNames = [];
  for (const tool of tools) {
    const name = toolName(tool);
    if (name && !allowed.has(name)) {
      strippedToolNames.push(name);
      continue;
    }
    kept.push(tool);
  }
  return { tools: strippedToolNames.length > 0 ? kept : tools, strippedToolNames };
}

function textPart(part) {
  if (typeof part === "string") return part;
  if (!part || typeof part !== "object") return "";
  if (typeof part.text === "string") return part.text;
  if (typeof part.content === "string") return part.content;
  return "";
}

function messageText(message) {
  const content = message?.content;
  if (typeof content === "string") return content;
  if (Array.isArray(content)) return content.map(textPart).join("\n");
  return "";
}

function isOmpProjectDeveloperMessage(message) {
  if (!message || typeof message !== "object") return false;
  if (message.role !== "developer") return false;
  const text = messageText(message);
  if (!text.startsWith(PROJECT_HEADER)) return false;
  return REQUIRED_MARKERS.every((marker) => text.includes(marker));
}

function stripMessages(messages) {
  if (!Array.isArray(messages)) return { messages, stripped: 0 };
  const kept = [];
  let stripped = 0;
  for (const message of messages) {
    if (isOmpProjectDeveloperMessage(message)) {
      stripped += 1;
      continue;
    }
    kept.push(message);
  }
  return { messages: stripped > 0 ? kept : messages, stripped };
}

function log(row) {
  const dir = process.env.OMP_PROJECT_MESSAGE_STRIP_DIR;
  if (!dir) return;
  mkdirSync(dir, { recursive: true });
  appendFileSync(join(dir, "strip.ndjson"), `${JSON.stringify(row)}\n`);
}

export default function stripOmpProjectMessage(pi) {
  pi.on("before_provider_request", (event) => {
    const payload = event?.payload;
    if (!payload || typeof payload !== "object") return;

    const input = stripMessages(payload.input);
    const messages = stripMessages(payload.messages);
    const tools = filterTools(payload.tools, allowedTools());
    const strippedMessages = input.stripped + messages.stripped;
    const strippedToolNames = tools.strippedToolNames;

    log({
      event: "omp-project-message-strip.before_provider_request",
      stripped: strippedMessages,
      strippedToolNames,
      inputMessagesBefore: Array.isArray(payload.input) ? payload.input.length : null,
      inputMessagesAfter: Array.isArray(input.messages) ? input.messages.length : null,
      messagesBefore: Array.isArray(payload.messages) ? payload.messages.length : null,
      messagesAfter: Array.isArray(messages.messages) ? messages.messages.length : null,
      toolsBefore: Array.isArray(payload.tools) ? payload.tools.map(toolName) : null,
      toolsAfter: Array.isArray(tools.tools) ? tools.tools.map(toolName) : null,
      timestamp: new Date().toISOString(),
    });

    if (strippedMessages === 0 && strippedToolNames.length === 0) return;
    return {
      ...payload,
      ...(Array.isArray(payload.input) ? { input: input.messages } : {}),
      ...(Array.isArray(payload.messages) ? { messages: messages.messages } : {}),
      ...(Array.isArray(payload.tools) ? { tools: tools.tools } : {}),
    };
  });
}
