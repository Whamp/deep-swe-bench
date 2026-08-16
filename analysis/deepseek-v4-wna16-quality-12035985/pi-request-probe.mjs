import http from "node:http";
import { streamSimple } from "/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js";
import registerLocalVllmDeepSeekV4Wna16Request from "../../configs/baseline-vllm-deepseek-v4-flash-0731-wna16@1.1.0/extensions/local-vllm-deepseek-v4-wna16-request.ts";

const requests = [];
const server = http.createServer((request, response) => {
  let body = "";
  request.on("data", (chunk) => (body += chunk));
  request.on("end", () => {
    requests.push(JSON.parse(body));
    response.writeHead(200, { "content-type": "text/event-stream" });
    response.write(
      'data: {"choices":[{"index":0,"delta":{"content":"ok"},"finish_reason":null}]}\n\n',
    );
    response.write(
      'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":3,"completion_tokens":1,"total_tokens":4}}\n\n',
    );
    response.write("data: [DONE]\n\n");
    response.end();
  });
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));

const model = {
  provider: "local-vllm",
  id: "deepseek-v4-flash-0731-wna16-quality-12035985",
  name: "DeepSeek V4 Flash 0731 WNA16 quality candidate",
  api: "openai-completions",
  baseUrl: `http://127.0.0.1:${server.address().port}/v1`,
  apiKey: "local",
  reasoning: true,
  input: ["text"],
  contextWindow: 131072,
  maxTokens: 65536,
  thinkingLevelMap: { off: null, low: "low", high: "high", max: "max" },
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  compat: {
    supportsDeveloperRole: false,
    supportsStore: false,
    supportsReasoningEffort: true,
    supportsUsageInStreaming: true,
    supportsStrictMode: false,
    maxTokensField: "max_tokens",
    thinkingFormat: "openai",
    requiresReasoningContentOnAssistantMessages: true,
  },
};

for await (const _event of streamSimple(
  model,
  {
    systemPrompt: "request-shape probe",
    messages: [{ role: "user", content: [{ type: "text", text: "probe" }] }],
    tools: [
      {
        name: "record_probe",
        description: "Record a request-shape probe.",
        parameters: {
          type: "object",
          properties: { value: { type: "string" } },
          required: ["value"],
        },
      },
    ],
  },
  { apiKey: "local", reasoning: "max", maxTokens: 65536 },
)) {
  // Drain the mock response so pi-ai completes the request lifecycle.
}

let requestHook;
registerLocalVllmDeepSeekV4Wna16Request({
  on(eventName, handler) {
    if (eventName === "before_provider_request") requestHook = handler;
  },
});
const finalRequest = requestHook(
  { payload: requests[0] },
  { model: { provider: model.provider, id: model.id } },
);
const artifact = {
  artifact: "LOCAL_VLLM_DEEPSEEK_V4_WNA16_QUALITY_PI_REQUEST_PROBE",
  api: model.api,
  endpointPath: "/v1/chat/completions",
  model: finalRequest.model,
  requestedThinking: "max",
  sentMaxTokens: finalRequest.max_tokens,
  sentReasoningEffort: finalRequest.reasoning_effort ?? null,
  sentThinking: finalRequest.thinking ?? null,
  sentSampling: {
    temperature: finalRequest.temperature,
    top_p: finalRequest.top_p,
  },
  sentToolChoice: finalRequest.tool_choice ?? null,
  sentToolCount: finalRequest.tools?.length ?? 0,
  generatedAgainstLiveModel: false,
};
if (
  artifact.sentReasoningEffort !== "max" ||
  artifact.sentMaxTokens !== 65536 ||
  artifact.sentThinking !== null ||
  artifact.sentSampling.temperature !== 1.0 ||
  artifact.sentSampling.top_p !== 0.95 ||
  artifact.sentToolCount !== 1
) {
  throw new Error(`Unexpected Pi request shape: ${JSON.stringify(artifact)}`);
}
process.stdout.write(`${JSON.stringify(artifact)}\n`);
server.close();
