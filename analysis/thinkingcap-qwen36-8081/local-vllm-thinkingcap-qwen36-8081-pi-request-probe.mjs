import http from "node:http";
import { streamSimple } from "/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js";
import registerThinkingCapQwen36ProviderRequest from "../../configs/baseline-thinkingcap-qwen36@1.1.0/extensions/local-vllm-thinkingcap-qwen36-request.ts";

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
  id: "thinkingcap-qwen3.6-27b-awq-int4",
  name: "ThinkingCap Qwen3.6 27B AWQ INT4",
  api: "openai-completions",
  baseUrl: `http://127.0.0.1:${server.address().port}/v1`,
  apiKey: "local",
  reasoning: true,
  input: ["text"],
  contextWindow: 262144,
  maxTokens: 98304,
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  compat: {
    supportsDeveloperRole: false,
    supportsStore: false,
    supportsReasoningEffort: false,
    supportsUsageInStreaming: true,
    maxTokensField: "max_tokens",
    thinkingFormat: "qwen-chat-template",
    chatTemplateKwargs: {
      enable_thinking: { $var: "thinking.enabled" },
    },
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
  {
    apiKey: "local",
    reasoning: "high",
    maxTokens: 98304,
  },
)) {
  // Drain the mock response so pi-ai completes the request lifecycle.
}

let requestHook;
registerThinkingCapQwen36ProviderRequest({
  on(eventName, handler) {
    if (eventName === "before_provider_request") requestHook = handler;
  },
});
const piRequest = requests[0];
const finalRequest = requestHook(
  { payload: piRequest },
  { model: { provider: model.provider, id: model.id } },
);
process.stdout.write(
  `${JSON.stringify({
    artifact: "LOCAL_VLLM_THINKINGCAP_QWEN36_8081_PI_REQUEST_PROBE",
    api: model.api,
    endpointPath: "/v1/chat/completions",
    model: finalRequest.model,
    requestedThinking: "high",
    sentMaxTokens: finalRequest.max_tokens,
    sentChatTemplateKwargs: finalRequest.chat_template_kwargs ?? null,
    sentSampling: {
      temperature: finalRequest.temperature,
      top_p: finalRequest.top_p,
      top_k: finalRequest.top_k,
      min_p: finalRequest.min_p,
      repetition_penalty: finalRequest.repetition_penalty,
    },
    sentThinkingTokenBudget: finalRequest.thinking_token_budget ?? null,
    sentReasoningEffort: finalRequest.reasoning_effort ?? null,
    sentToolChoice: finalRequest.tool_choice ?? null,
    sentToolCount: finalRequest.tools?.length ?? 0,
    generatedAgainstLiveModel: false,
  })}\n`,
);
server.close();
