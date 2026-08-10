#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import http from "node:http";
import { dirname, join } from "node:path";
import { realpathSync } from "node:fs";
import { pathToFileURL } from "node:url";
import zlib from "node:zlib";

const piExecutable = execFileSync("which", ["pi"], { encoding: "utf8" }).trim();
const packageRoot = dirname(dirname(realpathSync(piExecutable)));
const packageJson = JSON.parse(await readFile(join(packageRoot, "package.json"), "utf8"));
const importFromPi = (relativePath) => import(pathToFileURL(join(packageRoot, relativePath)).href);

const { ModelRegistry } = await importFromPi("dist/core/model-registry.js");
const { ModelRuntime } = await importFromPi("dist/core/model-runtime.js");
const { streamSimple: streamCodex } = await importFromPi(
  "node_modules/@earendil-works/pi-ai/dist/api/openai-codex-responses.js",
);
const { streamSimple: streamCompletions } = await importFromPi(
  "node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js",
);
const { clampThinkingLevel, getSupportedThinkingLevels } = await importFromPi(
  "node_modules/@earendil-works/pi-ai/dist/models.js",
);

const runtime = await ModelRuntime.create({ allowModelNetwork: false, modelsPath: null });
const registry = new ModelRegistry(runtime);
const capturedRequests = [];

function decodeRequestBody(chunks, contentEncoding) {
  let body = Buffer.concat(chunks);
  const isZstd = body.subarray(0, 4).equals(Buffer.from([0x28, 0xb5, 0x2f, 0xfd]));
  if (contentEncoding === "gzip") body = zlib.gunzipSync(body);
  else if (contentEncoding === "deflate") body = zlib.inflateSync(body);
  else if (contentEncoding === "br") body = zlib.brotliDecompressSync(body);
  else if (contentEncoding === "zstd" || isZstd) body = zlib.zstdDecompressSync(body);
  return JSON.parse(body.toString("utf8"));
}

const server = http.createServer((request, response) => {
  const chunks = [];
  request.on("data", (chunk) => chunks.push(chunk));
  request.on("end", () => {
    const body = decodeRequestBody(chunks, request.headers["content-encoding"]);
    capturedRequests.push(body);
    response.writeHead(200, { "content-type": "text/event-stream" });
    if (Array.isArray(body.messages)) {
      response.write(
        `data: ${JSON.stringify({ choices: [{ index: 0, delta: { content: "OK" }, finish_reason: null }] })}\n\n`,
      );
      response.write(
        `data: ${JSON.stringify({ choices: [{ index: 0, delta: {}, finish_reason: "stop" }], usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 } })}\n\n`,
      );
      response.write("data: [DONE]\n\n");
    } else {
      response.write(
        `data: ${JSON.stringify({ type: "response.completed", response: { id: "resp_mock", status: "completed", model: body.model, output: [], usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 } } })}\n\n`,
      );
    }
    response.end();
  });
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const baseUrl = `http://127.0.0.1:${server.address().port}`;

const context = {
  systemPrompt: "Probe request shape.",
  messages: [{ role: "user", content: [{ type: "text", text: "Reply OK" }] }],
  tools: [
    {
      name: "probe_tool",
      description: "Return a local probe marker.",
      parameters: { type: "object", properties: {}, required: [], additionalProperties: false },
    },
  ],
};

function requireModel(provider, modelId) {
  const model = registry.find(provider, modelId);
  if (!model) throw new Error(`Pi ${packageJson.version} model missing: ${provider}/${modelId}`);
  return model;
}

async function probeCodexModel(modelId) {
  const baseModel = requireModel("openai-codex", modelId);
  const model = { ...baseModel, baseUrl };
  const jwtPayload = Buffer.from(
    JSON.stringify({ "https://api.openai.com/auth": { chatgpt_account_id: "acct_test" } }),
  ).toString("base64url");
  const fakeJwt = ["x", jwtPayload, "x"].join(".");
  const requestIndex = capturedRequests.length;
  for await (const _event of streamCodex(model, context, {
    apiKey: fakeJwt,
    maxTokens: 16,
    reasoning: "low",
    transport: "sse",
  })) {
    // Consume the fixed mock response through Pi's real Codex adapter.
  }
  const request = capturedRequests[requestIndex];
  return {
    piVersion: packageJson.version,
    provider: baseModel.provider,
    model: baseModel.id,
    api: baseModel.api,
    requestedThinking: "low",
    clampedThinking: clampThinkingLevel(baseModel, "low"),
    supportedThinkingLevels: getSupportedThinkingLevels(baseModel),
    request: {
      model: request.model,
      reasoning: request.reasoning ?? null,
      stream: request.stream,
      store: request.store,
      toolCount: request.tools?.length ?? 0,
    },
  };
}

async function probeCompletionModel(provider, modelId, requestedThinking, override = {}) {
  const baseModel = requireModel(provider, modelId);
  const model = { ...baseModel, ...override, baseUrl };
  const requestIndex = capturedRequests.length;
  for await (const _event of streamCompletions(model, context, {
    apiKey: "local-probe",
    maxTokens: 16,
    reasoning: requestedThinking,
  })) {
    // Consume the fixed mock response through Pi's real completions adapter.
  }
  const request = capturedRequests[requestIndex];
  return {
    piVersion: packageJson.version,
    provider: baseModel.provider,
    model: baseModel.id,
    api: baseModel.api,
    requestedThinking,
    clampedThinking: clampThinkingLevel(model, requestedThinking),
    supportedThinkingLevels: getSupportedThinkingLevels(model),
    request: {
      model: request.model,
      reasoning: request.reasoning ?? null,
      thinking: request.thinking ?? null,
      reasoning_effort: request.reasoning_effort ?? null,
      temperature: request.temperature ?? null,
      top_p: request.top_p ?? null,
      stream: request.stream,
      toolCount: request.tools?.length ?? 0,
    },
  };
}

try {
  for (const modelId of ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"]) {
    console.log(JSON.stringify(await probeCodexModel(modelId)));
  }

  console.log(
    JSON.stringify(
      await probeCompletionModel("openrouter", "deepseek/deepseek-v4-flash-0731", "low", {
        thinkingLevelMap: {
          minimal: null,
          low: "low",
          medium: null,
          high: "high",
          xhigh: "max",
          max: "max",
        },
        samplingParams: { temperature: 1.0, top_p: 0.95 },
      }),
    ),
  );

  console.log(JSON.stringify(await probeCompletionModel("zai", "glm-5.2", "max")));
} finally {
  server.close();
}
