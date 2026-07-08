import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const SCHEMA_VERSION = 1;
const DEFAULT_MAX_CONTEXTS = 2;
const DEFAULT_MAX_PROVIDER_REQUESTS = 2;
const SENSITIVE_KEY = /(authorization|api[-_]?key|access[-_]?token|refresh[-_]?token|secret|cookie|password)/i;

function envInt(name, fallback) {
  const raw = process.env[name];
  if (!raw) return fallback;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n >= 0 ? n : fallback;
}

function captureDir(ctx) {
  return process.env.PI_INITIAL_CONTEXT_DIR || join(ctx?.cwd || process.cwd(), ".pi-initial-context");
}

function redactingReplacer() {
  const seen = new WeakSet();
  return (key, value) => {
    if (key && SENSITIVE_KEY.test(key)) return "[redacted]";
    if (typeof value === "bigint") return value.toString();
    if (typeof value === "function") return `[function ${value.name || "anonymous"}]`;
    if (value && typeof value === "object") {
      if (seen.has(value)) return "[circular]";
      seen.add(value);
    }
    return value;
  };
}

function writeText(ctx, name, content) {
  const dir = captureDir(ctx);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, name), String(content ?? ""), "utf8");
}

function writeJson(ctx, name, value) {
  writeText(ctx, name, `${JSON.stringify(value, redactingReplacer(), 2)}\n`);
}

function maybeGetSystemPrompt(event, ctx) {
  try {
    if (typeof event?.systemPrompt === "string") return event.systemPrompt;
    if (typeof ctx?.getSystemPrompt === "function") return String(ctx.getSystemPrompt() ?? "");
  } catch (error) {
    return `[initial-context-capture: getSystemPrompt failed: ${error instanceof Error ? error.message : String(error)}]`;
  }
  return "";
}

function maybeGetSystemPromptOptions(event, ctx) {
  try {
    if (event?.systemPromptOptions) return event.systemPromptOptions;
    if (typeof ctx?.getSystemPromptOptions === "function") return ctx.getSystemPromptOptions();
  } catch (error) {
    return { error: `getSystemPromptOptions failed: ${error instanceof Error ? error.message : String(error)}` };
  }
  return null;
}

function stopAfter() {
  const raw = (process.env.PI_INITIAL_CONTEXT_STOP_AFTER || "").trim();
  if (raw === "before_agent_start" || raw === "before_provider_request") return raw;
  return "";
}

function requestStop(ctx, phase) {
  writeJson(ctx, "capture_stop.json", {
    phase,
    requestedAt: new Date().toISOString(),
    mechanism: "ctx.abort+ctx.shutdown",
  });
  if (typeof ctx?.abort === "function") ctx.abort();
  if (typeof ctx?.shutdown === "function") ctx.shutdown();
}

export default function initialContextCapture(pi) {
  const maxContexts = envInt("PI_INITIAL_CONTEXT_MAX_CONTEXTS", DEFAULT_MAX_CONTEXTS);
  const maxProviderRequests = envInt("PI_INITIAL_CONTEXT_MAX_PROVIDER_REQUESTS", DEFAULT_MAX_PROVIDER_REQUESTS);
  const stop = stopAfter();
  let contextCount = 0;
  let providerRequestCount = 0;

  pi.on("before_agent_start", (event, ctx) => {
    writeJson(ctx, "capture_meta.json", {
      schemaVersion: SCHEMA_VERSION,
      maxContexts,
      maxProviderRequests,
      stopAfter: stop || null,
      cwd: ctx?.cwd,
      capturedAt: new Date().toISOString(),
    });
    try {
      writeText(ctx, "system_prompt.txt", maybeGetSystemPrompt(event, ctx));
      writeJson(ctx, "system_prompt_options.json", maybeGetSystemPromptOptions(event, ctx));
      writeJson(ctx, "before_agent_start_event_keys.json", Object.keys(event ?? {}));
      writeJson(ctx, "before_agent_start_ctx_keys.json", Object.keys(ctx ?? {}));
      writeText(ctx, "user_prompt.txt", typeof event?.prompt === "string" ? event.prompt : "");
    } catch (error) {
      writeJson(ctx, "capture_error.json", {
        phase: "before_agent_start",
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
    }
    if (stop === "before_agent_start") requestStop(ctx, stop);
  });

  try {
    pi.on("context", (event, ctx) => {
      contextCount += 1;
      if (contextCount > maxContexts) return;
      writeJson(ctx, `context_${String(contextCount).padStart(4, "0")}_messages.json`, event?.messages ?? null);
    });
  } catch {
    // Some Pi-compatible harnesses may not expose the context event. The core
    // before_agent_start/provider payload artifacts still capture the initial surface.
  }

  pi.on("before_provider_request", (event, ctx) => {
    providerRequestCount += 1;
    if (providerRequestCount > maxProviderRequests) return;
    writeJson(ctx, `provider_request_${String(providerRequestCount).padStart(4, "0")}.json`, event?.payload ?? null);
    if (providerRequestCount === 1 && stop === "before_provider_request") requestStop(ctx, stop);
  });
}
