// Free mocked request-shape probe for the OpenRouter DeepSeek V4 Flash 0731 baseline leaf.
//
// Proves what Pi's built-in `openrouter` provider sends for `deepseek/deepseek-v4-flash-0731`
// at each requested thinking level, both (A) with pi-ai's shipped thinkingLevelMap and
// (B) with the leaf models.json `modelOverrides` thinkingLevelMap applied. No live model
// generation or tool loop is used: a local mock returns a fixed non-reasoning SSE reply.
//
// Mirrors the methodology of analysis/local-llamacpp-deepseek-v4-flash-0731-pi-request-probe.mjs
// but targets the openrouter thinkingFormat branch (sends `reasoning: { effort }`, not a
// chat_template_kwargs hook).
import http from "node:http";
import { streamSimple } from "/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js";

// pi-ai's shipped openrouter.json entry for deepseek/deepseek-v4-flash-0731 (as of the
// subject image's pi-ai). max maps to null -> not a directly supported level.
const BUILTIN_THINKING_LEVEL_MAP = {
  minimal: null,
  low: null,
  medium: null,
  high: "high",
  max: null,
  xhigh: "xhigh",
};

// Leaf models.json modelOverrides.deepseek/deepseek-v4-flash-0731.thinkingLevelMap.
// Maps the DeepSeek-native efforts {low, high, max} so requested levels are genuinely
// sent, matching the local llama.cpp run (which sends reasoning_effort: "max").
const LEAF_OVERRIDE = {
  low: "low",
  high: "high",
  xhigh: "max",
  max: "max",
};

function makeModel(thinkingLevelMap, baseUrl, samplingParams) {
  return {
    id: "deepseek/deepseek-v4-flash-0731",
    name: "DeepSeek: DeepSeek V4 Flash 0731",
    api: "openai-completions",
    baseUrl,
    provider: "openrouter",
    reasoning: true,
    input: ["text"],
    cost: { input: 0.09, output: 0.18, cacheRead: 0.018, cacheWrite: 0 },
    contextWindow: 1048576,
    maxTokens: 65536,
    compat: {
      supportsDeveloperRole: false,
      thinkingFormat: "openrouter",
      requiresReasoningContentOnAssistantMessages: true,
    },
    thinkingLevelMap,
    samplingParams,
  };
}

async function probeOne(label, thinkingLevelMap, samplingParams) {
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
  const baseUrl = `http://127.0.0.1:${server.address().port}/v1`;
  const model = makeModel(thinkingLevelMap, baseUrl, samplingParams);

  const levels = ["max", "high", "low"];
  for (const level of levels) {
    for await (const _event of streamSimple(
      model,
      {
        systemPrompt: "request-shape probe",
        messages: [{ role: "user", content: [{ type: "text", text: "probe" }] }],
      },
      { apiKey: "probe", reasoning: level, maxTokens: 8 },
    )) {
      // Drain the mock response so pi-ai completes the request lifecycle.
    }
  }
  server.close();

  const records = levels.map((level, i) => {
    const r = requests[i] ?? {};
    return {
      requestedThinking: level,
      sentReasoning: r.reasoning ?? null,
      sentSampling: {
        temperature: r.temperature ?? null,
        top_p: r.top_p ?? null,
      },
    };
  });
  return { label, thinkingLevelMap, samplingParams: samplingParams ?? null, records };
}

// The model card's canonical coding-eval sampling (matches the local llama.cpp run's
// pinned tuple for the params the DeepSeek OpenRouter endpoint accepts). The endpoint
// supports temperature + top_p but not top_k/min_p/repeat_penalty.
const LEAF_SAMPLING_PARAMS = { temperature: 1.0, top_p: 0.95 };

const builtin = await probeOne("BUILTIN_SHIPPED_MAP", BUILTIN_THINKING_LEVEL_MAP);
const overridden = await probeOne(
  "LEAF_OVERRIDE_MAP",
  { ...BUILTIN_THINKING_LEVEL_MAP, ...LEAF_OVERRIDE },
  LEAF_SAMPLING_PARAMS,
);

console.log(
  JSON.stringify({
    artifact: "OPENROUTER_DEEPSEEK_V4_FLASH_0731_PI_REQUEST_PROBE",
    api: "openai-completions",
    endpointPath: "/v1/chat/completions",
    provider: "openrouter",
    model: "deepseek/deepseek-v4-flash-0731",
    thinkingFormat: "openrouter",
    sentParamShape: "reasoning.effort",
    generatedAgainstLiveModel: false,
    results: [
      {
        ...builtin,
        note:
          "pi-ai shipped map: supported levels are {off, high, xhigh}. max=null is not supported, so clampThinkingLevel promotes max -> xhigh and Pi sends reasoning.effort='xhigh'. low=null is not supported either, so low clamps UP to high and Pi sends reasoning.effort='high'. high sends 'high' directly.",
      },
      {
        ...overridden,
        note:
          "Leaf models.json modelOverrides merge {max:'max', xhigh:'max', high:'high', low:'low'} into the shipped map (provider-composer applyModelOverride). Now max sends DeepSeek-native reasoning.effort='max' (matches the local llama.cpp run's reasoning_effort='max'); high sends 'high'; low sends 'low'.",
      },
    ],
  }),
);
