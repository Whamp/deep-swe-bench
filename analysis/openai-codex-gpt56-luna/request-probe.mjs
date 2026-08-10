import { readFile } from "node:fs/promises";
import http from "node:http";
import { pathToFileURL } from "node:url";
import zlib from "node:zlib";

const packageRoot = process.env.PI_CODING_AGENT_PACKAGE_ROOT;
if (!packageRoot) {
  throw new Error("GPT-5.6-Luna request probe missing PI_CODING_AGENT_PACKAGE_ROOT");
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
const baseModel = registry.find("openai-codex", "gpt-5.6-luna");
if (!baseModel) {
  throw new Error(`GPT-5.6-Luna request probe model missing in Pi ${packageJson.version}`);
}

const jwtPayload = Buffer.from(
  JSON.stringify({
    "https://api.openai.com/auth": { chatgpt_account_id: "acct_test" },
  }),
).toString("base64url");
const fakeJwt = ["x", jwtPayload, "x"].join(".");
const capturedRequests = [];

function decodeCodexRequestBody(chunks, contentEncoding) {
  let body = Buffer.concat(chunks);
  const isZstd = body.subarray(0, 4).equals(Buffer.from([0x28, 0xb5, 0x2f, 0xfd]));
  if (contentEncoding === "gzip") body = zlib.gunzipSync(body);
  else if (contentEncoding === "deflate") body = zlib.inflateSync(body);
  else if (contentEncoding === "br") body = zlib.brotliDecompressSync(body);
  else if (contentEncoding === "zstd" || isZstd) {
    body = zlib.zstdDecompressSync(body);
  }
  return JSON.parse(body.toString("utf8"));
}

const server = http.createServer((request, response) => {
  const chunks = [];
  request.on("data", (chunk) => chunks.push(chunk));
  request.on("end", () => {
    const requestBody = decodeCodexRequestBody(chunks, request.headers["content-encoding"]);
    capturedRequests.push(requestBody);
    response.writeHead(200, { "content-type": "text/event-stream" });
    response.write(
      `data: ${JSON.stringify({
        type: "response.completed",
        response: {
          id: "resp_mock",
          status: "completed",
          model: requestBody.model,
          output: [],
          usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 },
        },
      })}\n\n`,
    );
    response.end();
  });
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));

try {
  const model = {
    ...baseModel,
    baseUrl: `http://127.0.0.1:${server.address().port}`,
  };
  const context = {
    systemPrompt: "Probe the request shape.",
    messages: [{ role: "user", content: [{ type: "text", text: "Reply OK" }] }],
    tools: [
      {
        name: "probe_tool",
        description: "Return a local probe marker.",
        parameters: {
          type: "object",
          properties: {},
          required: [],
          additionalProperties: false,
        },
      },
    ],
  };

  for (const requestedThinking of ["low", "high", "max"]) {
    const requestIndex = capturedRequests.length;
    for await (const _event of streamSimple(model, context, {
      apiKey: fakeJwt,
      maxTokens: 16,
      reasoning: requestedThinking,
      transport: "sse",
    })) {
      // The mock response is intentionally consumed through Pi's real stream path.
    }
    const requestBody = capturedRequests[requestIndex];
    console.log(
      JSON.stringify({
        probe: "openai-codex-gpt56-luna-thinking-request",
        piVersion: packageJson.version,
        provider: baseModel.provider,
        model: baseModel.id,
        api: baseModel.api,
        contextWindow: baseModel.contextWindow,
        maxTokens: baseModel.maxTokens,
        availableThinkingLevels: getSupportedThinkingLevels(baseModel),
        thinkingLevelMap: baseModel.thinkingLevelMap ?? null,
        requestedThinking,
        clampedThinking: clampThinkingLevel(baseModel, requestedThinking),
        reasoning: requestBody.reasoning ?? null,
        stream: requestBody.stream,
        store: requestBody.store,
        toolCount: requestBody.tools?.length ?? 0,
        endpointPath: "/codex/responses",
        baseUrl: "mock://local",
      }),
    );
  }
} finally {
  server.close();
}
