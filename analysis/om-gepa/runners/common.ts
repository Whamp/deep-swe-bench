import { cpSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { createHash } from "node:crypto";

export type Args = Record<string, string | boolean>;

export function parseArgs(argv = process.argv.slice(2)): Args {
  const args: Args = {};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i++;
    }
  }
  return args;
}

export function requireString(args: Args, key: string): string {
  const value = args[key];
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`Missing required --${key}`);
  }
  return value;
}

export function repoRoot(): string {
  return process.cwd();
}

function piRoot(): string {
  return process.env.PI_CODING_AGENT_PACKAGE_DIR
    ?? "/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent";
}

export function sha256(text: string): string {
  return createHash("sha256").update(text).digest("hex");
}

export function readJson(path: string): any {
  return JSON.parse(readFileSync(path, "utf-8"));
}

export function readPrompt(path: string | boolean | undefined): string | undefined {
  if (typeof path !== "string") return undefined;
  return readFileSync(path, "utf-8");
}

export function makeIsolatedExtension(role: "observer" | "reflector", candidatePrompt?: string, extensionSrc?: string): string {
  const root = repoRoot();
  const source = resolve(extensionSrc ?? join(root, "configs/observational-memory/extensions/pi-observational-memory/src"));
  const dir = join(tmpdir(), `om-gepa-${role}-${process.pid}-${Date.now()}`);
  mkdirSync(dir, { recursive: true });
  cpSync(source, join(dir, "src"), { recursive: true });
  mkdirSync(join(dir, "node_modules", "@earendil-works"), { recursive: true });
  const pi = piRoot();
  symlinkSync(pi, join(dir, "node_modules", "@earendil-works", "pi-coding-agent"), "dir");
  symlinkSync(join(pi, "node_modules", "@earendil-works", "pi-agent-core"), join(dir, "node_modules", "@earendil-works", "pi-agent-core"), "dir");
  symlinkSync(join(pi, "node_modules", "@earendil-works", "pi-ai"), join(dir, "node_modules", "@earendil-works", "pi-ai"), "dir");
  symlinkSync(join(pi, "node_modules", "typebox"), join(dir, "node_modules", "typebox"), "dir");
  writeFileSync(join(dir, "package.json"), JSON.stringify({ type: "module" }));
  if (candidatePrompt !== undefined) {
    const constant = role === "observer" ? "OBSERVER_SYSTEM" : "REFLECTOR_SYSTEM";
    const promptPath = join(dir, "src", "agents", role, "prompts.ts");
    writeFileSync(promptPath, `export const ${constant} = ${JSON.stringify(candidatePrompt)};\n`);
  }
  return dir;
}

export async function withIsolatedExtension<T>(role: "observer" | "reflector", candidatePrompt: string | undefined, extensionSrc: string | undefined, fn: (dir: string) => Promise<T>): Promise<T> {
  const dir = makeIsolatedExtension(role, candidatePrompt, extensionSrc);
  try {
    return await fn(dir);
  } finally {
    if (process.env.OM_GEPA_KEEP_TMP !== "1") rmSync(dir, { recursive: true, force: true });
  }
}

export function mockStreamFromTool(toolCall: () => Promise<unknown>, event: Record<string, unknown> = {}) {
  async function* iter() {
    await toolCall();
    yield { type: "mock_tool_executed", ...event };
  }
  const stream: any = iter();
  stream.result = async () => ({ ok: true });
  return stream;
}

export function plainModel(modelId = "om-gepa-mock") {
  return { provider: "om-gepa", id: modelId, reasoning: false } as any;
}

export function parseModelSpec(spec: string): { provider: string; id: string } {
  const idx = spec.indexOf("/");
  if (idx <= 0 || idx === spec.length - 1) throw new Error(`Model must be provider/id, got ${spec}`);
  return { provider: spec.slice(0, idx), id: spec.slice(idx + 1) };
}

export async function resolvePiModelAuth(modelSpec: string): Promise<{ model: any; apiKey?: string; headers?: Record<string, string>; env?: Record<string, string> }> {
  const { provider, id } = parseModelSpec(modelSpec);
  const pi = piRoot();
  const { AuthStorage } = await import(join(pi, "dist", "core", "auth-storage.js"));
  const { ModelRegistry } = await import(join(pi, "dist", "core", "model-registry.js"));
  const authJson = process.env.OM_GEPA_AUTH_JSON ?? join(homedir(), ".pi", "agent", "auth.json");
  const modelsJson = process.env.OM_GEPA_MODELS_JSON ?? join(homedir(), ".pi", "agent", "models.json");
  const auth = AuthStorage.create(authJson);
  const registry = ModelRegistry.create(auth, modelsJson);
  const model = registry.find(provider, id);
  if (!model) throw new Error(`Pi model not found: ${modelSpec}`);
  const requestAuth = await registry.getApiKeyAndHeaders(model);
  if (!requestAuth.ok) throw new Error(`Pi auth unavailable for ${modelSpec}: ${requestAuth.error}`);
  return { model, apiKey: requestAuth.apiKey, headers: requestAuth.headers, env: requestAuth.env };
}

export function textFromAssistantMessage(message: any): string {
  const content = message?.content;
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";
  return content.map((block) => {
    if (block?.type === "text" && typeof block.text === "string") return block.text;
    return "";
  }).filter(Boolean).join("\n").trim();
}

export async function completeWithPiCodex(options: { modelSpec: string; thinking: string; prompt: string; systemPrompt?: string; maxTokens?: number }): Promise<{ text: string; usage?: unknown; stopReason?: string; model?: string }> {
  const pi = piRoot();
  const { completeSimple } = await import(join(pi, "node_modules", "@earendil-works", "pi-ai", "dist", "compat.js"));
  const resolved = await resolvePiModelAuth(options.modelSpec);
  const message = await completeSimple(
    resolved.model,
    {
      ...(options.systemPrompt ? { systemPrompt: options.systemPrompt } : {}),
      messages: [{ role: "user", content: [{ type: "text", text: options.prompt }], timestamp: Date.now() }],
    },
    {
      apiKey: resolved.apiKey,
      headers: resolved.headers,
      env: resolved.env,
      reasoning: options.thinking === "off" ? undefined : options.thinking,
      maxTokens: options.maxTokens ?? 4096,
      timeoutMs: Number(process.env.OM_GEPA_CODEX_TIMEOUT_MS ?? 600000),
      maxRetries: Number(process.env.OM_GEPA_CODEX_MAX_RETRIES ?? 2),
    },
  );
  if (message.stopReason === "error" || message.stopReason === "aborted") {
    throw new Error(`Pi Codex completion failed: ${message.errorMessage ?? message.stopReason}`);
  }
  return { text: textFromAssistantMessage(message), usage: message.usage, stopReason: message.stopReason, model: message.model };
}

function toolParameters(tool: any): any {
  const params = tool?.parameters;
  if (!params || typeof params !== "object") return { type: "object", properties: {} };
  return params;
}

function contentToText(content: any): string {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return JSON.stringify(content ?? "");
  return content.map((part) => {
    if (part?.type === "text") return part.text ?? "";
    return JSON.stringify(part);
  }).join("\n");
}

export function openAICompatibleAgentLoop(options: { model: string; apiKey: string; baseUrl: string; maxTurns?: number; thinkingLevel?: string }) {
  // Qwen3.x vLLM (and similar thinking-capable OpenAI-compatible servers) spend the whole
  // token budget on reasoning unless thinking is explicitly disabled. `chat_template_kwargs
  // .enable_thinking=false` is what this vLLM honors; `/no_think` prompt prefixes do not.
  const disableThinking = (options.thinkingLevel ?? "off") === "off";
  return (prompts: any[], context: any) => {
    async function* iter() {
      const messages: any[] = [
        { role: "system", content: context.systemPrompt ?? "" },
        ...prompts.map((message) => ({ role: message.role ?? "user", content: contentToText(message.content) })),
      ];
      const tools = (context.tools ?? []).map((tool: any) => ({
        type: "function",
        function: {
          name: tool.name,
          description: tool.description ?? tool.label ?? tool.name,
          parameters: toolParameters(tool),
        },
      }));
      const byName = new Map((context.tools ?? []).map((tool: any) => [tool.name, tool]));
      for (let turn = 0; turn < (options.maxTurns ?? 6); turn++) {
        const response = await fetch(`${options.baseUrl.replace(/\/$/, "")}/chat/completions`, {
          method: "POST",
          headers: {
            "content-type": "application/json",
            authorization: `Bearer ${options.apiKey}`,
          },
          body: JSON.stringify({
            model: options.model,
            messages,
            tools,
            tool_choice: tools.length ? "auto" : undefined,
            temperature: 0,
            ...(disableThinking ? { chat_template_kwargs: { enable_thinking: false } } : {}),
          }),
        });
        if (!response.ok) throw new Error(`LLM request failed ${response.status}: ${await response.text()}`);
        const body: any = await response.json();
        const message = body.choices?.[0]?.message;
        if (!message) throw new Error(`LLM response missing message: ${JSON.stringify(body).slice(0, 500)}`);
        yield { type: "llm_message", usage: body.usage, finish_reason: body.choices?.[0]?.finish_reason };
        const toolCalls = message.tool_calls ?? [];
        if (!toolCalls.length) break;
        messages.push({ role: "assistant", content: message.content ?? "", tool_calls: toolCalls });
        for (const call of toolCalls) {
          const name = call.function?.name;
          const tool = byName.get(name) as any;
          if (!tool) throw new Error(`Unknown tool requested by model: ${name}`);
          let parsed: any = {};
          try {
            parsed = JSON.parse(call.function?.arguments || "{}");
          } catch (error) {
            parsed = {};
          }
          const result = await tool.execute(call.id ?? `call-${turn}`, parsed);
          messages.push({ role: "tool", tool_call_id: call.id, content: JSON.stringify(result) });
          yield { type: "tool_executed", tool: name, tool_call_id: call.id };
        }
      }
    }
    const stream: any = iter();
    stream.result = async () => ({ ok: true });
    return stream;
  };
}
