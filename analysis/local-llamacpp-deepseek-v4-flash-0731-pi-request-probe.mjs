import http from "node:http";
import { streamSimple } from "/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js";
import pinDeepSeekV4FlashRequest from "../configs/baseline-deepseek-v4-flash-0731@1.0.0/extensions/local-llamacpp-deepseek-v4-request.ts";

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
  provider: "local-llamacpp",
  id: "deepseek-v4-flash-0731",
  name: "DeepSeek V4 Flash 0731",
  api: "openai-completions",
  baseUrl: `http://127.0.0.1:${server.address().port}/v1`,
  apiKey: "local",
  reasoning: true,
  input: ["text"],
  contextWindow: 200192,
  maxTokens: 81920,
  thinkingLevelMap: { max: "max" },
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  compat: {
    supportsDeveloperRole: false,
    supportsStore: false,
    supportsReasoningEffort: false,
    supportsUsageInStreaming: true,
    supportsStrictMode: false,
    maxTokensField: "max_tokens",
    thinkingFormat: "chat-template",
    chatTemplateKwargs: {
      thinking: { $var: "thinking.enabled" },
      reasoning_effort: { $var: "thinking.effort" },
    },
  },
};

for await (const _event of streamSimple(
  model,
  {
    systemPrompt: "request-shape probe",
    messages: [{ role: "user", content: [{ type: "text", text: "probe" }] }],
  },
  {
    apiKey: "local",
    reasoning: "max",
    maxTokens: 8,
  },
)) {
  // Drain the mock response so pi-ai completes the request lifecycle.
}

let requestHook;
pinDeepSeekV4FlashRequest({
  on(eventName, handler) {
    if (eventName === "before_provider_request") requestHook = handler;
  },
});
const piRequest = requests[0];
const finalRequest = requestHook(
  { payload: piRequest },
  { model: { provider: model.provider, id: model.id } },
);
console.log(
  JSON.stringify({
    artifact: "LOCAL_LLAMACPP_DEEPSEEK_V4_FLASH_0731_PI_REQUEST_PROBE",
    api: model.api,
    endpointPath: "/v1/chat/completions",
    model: finalRequest.model,
    requestedThinking: "max",
    sentChatTemplateKwargs: finalRequest.chat_template_kwargs ?? null,
    sentSampling: {
      temperature: finalRequest.temperature,
      top_p: finalRequest.top_p,
      top_k: finalRequest.top_k,
      min_p: finalRequest.min_p,
      repeat_penalty: finalRequest.repeat_penalty,
    },
    sentReasoningEffort: finalRequest.reasoning_effort ?? null,
    generatedAgainstLiveModel: false,
  }),
);
server.close();
