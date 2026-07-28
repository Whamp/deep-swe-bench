import http from "node:http";
import { streamSimple } from "/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js";

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
  id: "gemma-4-31b",
  name: "Gemma 4 31B Google QAT W4A16",
  api: "openai-completions",
  baseUrl: `http://127.0.0.1:${server.address().port}/v1`,
  apiKey: "local",
  reasoning: true,
  input: ["text", "image"],
  contextWindow: 262144,
  maxTokens: 81920,
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  compat: {
    supportsDeveloperRole: false,
    supportsReasoningEffort: false,
    thinkingFormat: "chat-template",
    chatTemplateKwargs: {
      enable_thinking: { $var: "thinking.enabled" },
    },
  },
};

for await (const _ of streamSimple(
  model,
  {
    systemPrompt: "request-shape probe",
    messages: [{ role: "user", content: [{ type: "text", text: "probe" }] }],
  },
  {
    apiKey: "local",
    reasoning: "high",
    maxTokens: 8,
  },
)) {
}

const sent = requests[0];
console.log(
  JSON.stringify({
    artifact: "LOCAL_VLLM_GEMMA4_31B_PI_REQUEST_PROBE",
    api: model.api,
    endpointPath: "/v1/chat/completions",
    model: sent.model,
    requestedThinking: "high",
    sentChatTemplateKwargs: sent.chat_template_kwargs ?? null,
    sentReasoningEffort: sent.reasoning_effort ?? null,
  }),
);
server.close();
