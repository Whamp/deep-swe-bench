import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const packageRoot = process.env.PI_CODING_AGENT_PACKAGE_ROOT;
if (!packageRoot) {
  throw new Error("GPT-5.6-Luna live probe missing PI_CODING_AGENT_PACKAGE_ROOT");
}

const packageJson = JSON.parse(await readFile(`${packageRoot}/package.json`, "utf8"));
const importFromPackage = (relativePath) =>
  import(pathToFileURL(`${packageRoot}/${relativePath}`).href);
const { ModelRegistry } = await importFromPackage("dist/core/model-registry.js");
const { ModelRuntime } = await importFromPackage("dist/core/model-runtime.js");
const { streamSimple } = await importFromPackage(
  "node_modules/@earendil-works/pi-ai/dist/api/openai-codex-responses.js",
);
const { clampThinkingLevel, getSupportedThinkingLevels } = await importFromPackage(
  "node_modules/@earendil-works/pi-ai/dist/models.js",
);

const runtime = await ModelRuntime.create({
  allowModelNetwork: false,
  modelsPath: null,
});
const registry = new ModelRegistry(runtime);
const model = registry.find("openai-codex", "gpt-5.6-luna");
if (!model) {
  throw new Error(`GPT-5.6-Luna live probe model missing in Pi ${packageJson.version}`);
}
const auth = await registry.getApiKeyAndHeaders(model);
if (!auth.ok || !auth.apiKey) {
  throw new Error(`GPT-5.6-Luna live probe auth unavailable: ${auth.error ?? "missing API key"}`);
}

for (const requestedThinking of ["low", "high", "max"]) {
  const row = {
    capturedAt: new Date().toISOString(),
    probe: "openai-codex-gpt56-luna-live",
    piVersion: packageJson.version,
    provider: model.provider,
    model: model.id,
    api: model.api,
    availableThinkingLevels: getSupportedThinkingLevels(model),
    thinkingLevelMap: model.thinkingLevelMap ?? null,
    requestedThinking,
    clampedThinking: clampThinkingLevel(model, requestedThinking),
    ok: false,
    stopReason: null,
    responseText: null,
    usage: null,
    errorMessage: null,
  };

  try {
    let finalMessage = null;
    const stream = streamSimple(
      model,
      {
        systemPrompt: "You are a terse model-path probe. Reply with exactly OK.",
        messages: [{ role: "user", content: [{ type: "text", text: "Reply OK." }] }],
      },
      {
        apiKey: auth.apiKey,
        env: auth.env,
        headers: auth.headers,
        maxTokens: 16,
        reasoning: requestedThinking,
        timeoutMs: 60_000,
        transport: "sse",
      },
    );
    for await (const event of stream) {
      if (event.type === "done") finalMessage = event.message;
      if (event.type === "error") {
        throw new Error(event.error?.errorMessage ?? JSON.stringify(event.error));
      }
    }
    row.ok = true;
    row.stopReason = finalMessage?.stopReason ?? null;
    row.responseText =
      finalMessage?.content
        ?.filter((content) => content.type === "text")
        .map((content) => content.text)
        .join("") ?? null;
    row.usage = finalMessage?.usage ?? null;
  } catch (error) {
    row.errorMessage = error instanceof Error ? error.message : String(error);
  }

  console.log(JSON.stringify(row));
}
