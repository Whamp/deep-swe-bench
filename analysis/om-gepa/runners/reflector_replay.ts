import { join } from "node:path";
import { parseArgs, plainModel, readJson, readPrompt, requireString, resolvePiModelAuth, sha256, withIsolatedExtension, mockStreamFromTool, openAICompatibleAgentLoop } from "./common.ts";

async function main() {
  const args = parseArgs();
  const casePath = requireString(args, "case");
  const mockMode = typeof args["mock-mode"] === "string" ? args["mock-mode"] : "gold";
  if (!["gold", "empty", "live"].includes(mockMode)) throw new Error("--mock-mode must be gold, empty, or live");
  const backend = typeof args.backend === "string" ? args.backend : process.env.OM_GEPA_BACKEND ?? "openai-compatible";
  if (!["openai-compatible", "pi-codex"].includes(backend)) throw new Error("--backend must be openai-compatible or pi-codex");
  const workerModel = String(args.model || process.env.OM_GEPA_MODEL || (backend === "pi-codex" ? "openai-codex/gpt-5.4-mini" : "gpt-4o-mini"));
  const thinkingLevel = String(args["thinking-level"] || process.env.OM_GEPA_THINKING || (backend === "pi-codex" ? "low" : "off"));
  const testCase = readJson(casePath);
  if (testCase.role !== "reflector") throw new Error(`case role must be reflector, got ${testCase.role}`);
  const candidatePrompt = readPrompt(args["candidate-prompt"]);
  const extensionSrc = typeof args["extension-src"] === "string" ? args["extension-src"] : undefined;

  const result = await withIsolatedExtension("reflector", candidatePrompt, extensionSrc, async (dir) => {
    const mod = await import(join(dir, "src", "agents", "reflector", "agent.ts"));
    const promptMod = await import(join(dir, "src", "agents", "reflector", "prompts.ts"));
    const payload = mockMode === "gold" ? { reflections: testCase.goldReflections ?? [] } : { reflections: [] };
    let model: any = plainModel(workerModel);
    let apiKey = "om-gepa-mock";
    let headers: Record<string, string> | undefined;
    let agentLoop: any = mockMode === "live"
      ? openAICompatibleAgentLoop({
          model: workerModel,
          apiKey: process.env.OM_GEPA_API_KEY || process.env.OPENAI_API_KEY || "",
          baseUrl: process.env.OM_GEPA_BASE_URL || process.env.OPENAI_BASE_URL || "https://api.openai.com/v1",
          thinkingLevel,
        })
      : (_prompts: any[], context: any) => mockStreamFromTool(
          async () => {
            if (payload.reflections.length > 0) {
              await context.tools[0].execute("om-gepa-mock", payload);
            }
          },
          { promptSha256: sha256(context.systemPrompt ?? "") },
        );
    if (mockMode === "live" && backend === "pi-codex") {
      const resolved = await resolvePiModelAuth(workerModel);
      model = resolved.model;
      apiKey = resolved.apiKey ?? "";
      headers = resolved.headers;
      agentLoop = undefined;
    } else if (mockMode === "live" && !(process.env.OM_GEPA_API_KEY || process.env.OPENAI_API_KEY)) {
      throw new Error("live mode with openai-compatible backend requires OM_GEPA_API_KEY or OPENAI_API_KEY");
    }
    const reflections = await mod.runReflector({
      model,
      apiKey,
      headers,
      reflections: testCase.reflections ?? [],
      observations: testCase.observations ?? [],
      ...(agentLoop ? { agentLoop } : {}),
      maxTurns: 4,
      thinkingLevel,
    });
    return {
      role: "reflector",
      case_id: testCase.case_id,
      reflections: reflections ?? [],
      prompt_sha256: sha256(promptMod.REFLECTOR_SYSTEM),
      candidate_prompt_used: candidatePrompt !== undefined,
      mock_mode: mockMode,
      backend,
      model: workerModel,
      thinking_level: thinkingLevel,
    };
  });
  process.stdout.write(JSON.stringify(result, null, 2) + "\n");
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exit(1);
});
