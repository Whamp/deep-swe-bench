import { mkdirSync, renameSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";

const SCHEMA_VERSION = 1;
const DEFAULT_MAX_CONTEXTS = 2;
const DEFAULT_MAX_PROVIDER_REQUESTS = 2;
const SENSITIVE_KEY = /(authorization|api[-_]?key|access[-_]?token|refresh[-_]?token|secret|cookie|password)/i;
type StopAfter = "" | "before_agent_start" | "before_provider_request";

function envInt(name: string, fallback: number): number {
  const raw = process.env[name];
  if (!raw) return fallback;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n >= 0 ? n : fallback;
}

function envEnabled(name: string): boolean {
  return ["1", "true", "yes"].includes((process.env[name] || "").toLowerCase());
}

function captureDir(ctx: { cwd?: string }): string {
  return process.env.PI_INITIAL_CONTEXT_DIR || join(ctx.cwd || process.cwd(), ".pi-initial-context");
}

function redactingReplacer() {
  const seen = new WeakSet<object>();
  return (key: string, value: unknown) => {
    if (key && SENSITIVE_KEY.test(key)) return "[redacted]";
    if (typeof value === "bigint") return value.toString();
    if (typeof value === "function") return `[function ${value.name || "anonymous"}]`;
    if (value && typeof value === "object") {
      if (seen.has(value as object)) return "[circular]";
      seen.add(value as object);
    }
    return value;
  };
}

function writeText(ctx: { cwd?: string }, name: string, content: string): void {
  const dir = captureDir(ctx);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, name), content, "utf8");
}

function writeJson(ctx: { cwd?: string }, name: string, value: unknown): void {
  writeText(ctx, name, `${JSON.stringify(value, redactingReplacer(), 2)}\n`);
}

function writeAtomicText(
  ctx: { cwd?: string },
  name: string,
  content: string,
): void {
  const dir = captureDir(ctx);
  mkdirSync(dir, { recursive: true });
  const path = join(dir, name);
  const temporaryPath = join(dir, `.${name}.tmp`);
  writeFileSync(temporaryPath, content, { encoding: "utf8", mode: 0o600 });
  renameSync(temporaryPath, path);
}

function writeLatestProviderRequest(
  ctx: { cwd?: string },
  requestCount: number,
  payload: unknown,
): void {
  const encoded = `${JSON.stringify(payload, redactingReplacer(), 2)}\n`;
  writeAtomicText(ctx, "provider_request_latest.json", encoded);
  const metadata = {
    schemaVersion: SCHEMA_VERSION,
    providerRequestCount: requestCount,
    payloadBytes: Buffer.byteLength(encoded),
    payloadSha256: createHash("sha256").update(encoded).digest("hex"),
  };
  writeAtomicText(
    ctx,
    "provider_request_latest_meta.json",
    `${JSON.stringify(metadata, null, 2)}\n`,
  );
}

function maybeGetSystemPrompt(event: any, ctx: any): string {
  if (typeof event?.systemPrompt === "string") return event.systemPrompt;
  if (typeof ctx?.getSystemPrompt === "function") return ctx.getSystemPrompt();
  return "";
}

function maybeGetSystemPromptOptions(event: any, ctx: any): unknown {
  if (event?.systemPromptOptions) return event.systemPromptOptions;
  if (typeof ctx?.getSystemPromptOptions === "function") return ctx.getSystemPromptOptions();
  return null;
}

function stopAfter(): StopAfter {
  const raw = (process.env.PI_INITIAL_CONTEXT_STOP_AFTER || "").trim();
  if (raw === "before_agent_start" || raw === "before_provider_request") return raw;
  return "";
}

function requestStop(ctx: any, phase: StopAfter): void {
  writeJson(ctx, "capture_stop.json", {
    phase,
    requestedAt: new Date().toISOString(),
    mechanism: "ctx.abort+ctx.shutdown",
  });
  if (typeof ctx?.abort === "function") ctx.abort();
  if (typeof ctx?.shutdown === "function") ctx.shutdown();
}

export default function initialContextCapture(pi: any): void {
  const maxContexts = envInt("PI_INITIAL_CONTEXT_MAX_CONTEXTS", DEFAULT_MAX_CONTEXTS);
  const maxProviderRequests = envInt("PI_INITIAL_CONTEXT_MAX_PROVIDER_REQUESTS", DEFAULT_MAX_PROVIDER_REQUESTS);
  const captureLatestProviderRequest = envEnabled(
    "PI_INITIAL_CONTEXT_CAPTURE_LATEST_PROVIDER_REQUEST",
  );
  const stop = stopAfter();
  let contextCount = 0;
  let providerRequestCount = 0;

  pi.on("before_agent_start", (event: any, ctx: any) => {
    writeJson(ctx, "capture_meta.json", {
      schemaVersion: SCHEMA_VERSION,
      maxContexts,
      maxProviderRequests,
      captureLatestProviderRequest,
      stopAfter: stop || null,
      cwd: ctx?.cwd,
      capturedAt: new Date().toISOString(),
    });
    writeText(ctx, "system_prompt.txt", maybeGetSystemPrompt(event, ctx));
    writeJson(ctx, "system_prompt_options.json", maybeGetSystemPromptOptions(event, ctx));
    writeText(ctx, "user_prompt.txt", typeof event?.prompt === "string" ? event.prompt : "");
    if (stop === "before_agent_start") requestStop(ctx, stop);
  });

  try {
    pi.on("context", (event: any, ctx: any) => {
      contextCount += 1;
      if (contextCount > maxContexts) return;
      writeJson(ctx, `context_${String(contextCount).padStart(4, "0")}_messages.json`, event?.messages ?? null);
    });
  } catch {
    // Some Pi-compatible harnesses may not expose the context event. The core
    // before_agent_start/provider payload artifacts still capture the initial surface.
  }

  pi.on("before_provider_request", (event: any, ctx: any) => {
    providerRequestCount += 1;
    if (captureLatestProviderRequest) {
      writeLatestProviderRequest(ctx, providerRequestCount, event?.payload ?? null);
    }
    if (providerRequestCount > maxProviderRequests) return;
    writeJson(ctx, `provider_request_${String(providerRequestCount).padStart(4, "0")}.json`, event?.payload ?? null);
    if (providerRequestCount === 1 && stop === "before_provider_request") requestStop(ctx, stop);
  });
}
