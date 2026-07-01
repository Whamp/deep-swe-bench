import { completeWithPiCodex, parseArgs, requireString } from "./common.ts";

async function readStdin(): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  return Buffer.concat(chunks).toString("utf8");
}

async function main() {
  const args = parseArgs();
  const modelSpec = requireString(args, "model");
  const thinking = typeof args.thinking === "string" ? args.thinking : "xhigh";
  const maxTokens = typeof args["max-tokens"] === "string" ? Number(args["max-tokens"]) : 4096;
  const raw = await readStdin();
  const payload = raw.trim() ? JSON.parse(raw) : {};
  const prompt = typeof payload.prompt === "string"
    ? payload.prompt
    : Array.isArray(payload.messages)
      ? payload.messages.map((m: any) => `${m.role ?? "message"}: ${typeof m.content === "string" ? m.content : JSON.stringify(m.content)}`).join("\n\n")
      : "";
  if (!prompt.trim()) throw new Error("codex_lm requires prompt text on stdin");
  const result = await completeWithPiCodex({
    modelSpec,
    thinking,
    prompt,
    maxTokens,
    systemPrompt: typeof payload.systemPrompt === "string" ? payload.systemPrompt : undefined,
  });
  process.stdout.write(JSON.stringify(result, null, 2) + "\n");
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exit(1);
});
