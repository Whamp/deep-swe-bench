import http from 'node:http';
import { streamSimple } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js';
import { clampThinkingLevel, getSupportedThinkingLevels } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/models.js';

const modelBase = {
  provider: 'local-vllm',
  id: 'cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4',
  name: 'Qwen3.6 27B AWQ BF16 INT4 (server60 vLLM)',
  api: 'openai-completions',
  baseUrl: 'mock://local',
  apiKey: 'local',
  reasoning: true,
  input: ['text'],
  contextWindow: 262144,
  maxTokens: 16384,
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  compat: {
    supportsDeveloperRole: false,
    supportsReasoningEffort: false,
    thinkingFormat: 'qwen-chat-template',
  },
};

const requestedLevels = ['off', 'low'];
const rows = [];

const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', c => body += c);
  req.on('end', () => {
    const parsed = JSON.parse(body || '{}');
    rows.push({ headers: req.headers, body: parsed });
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    res.write('data: ' + JSON.stringify({
      id: 'chatcmpl_mock',
      object: 'chat.completion.chunk',
      created: 0,
      model: parsed.model,
      choices: [{ index: 0, delta: { content: 'ok' }, finish_reason: null }],
    }) + '\n\n');
    res.write('data: ' + JSON.stringify({
      id: 'chatcmpl_mock',
      object: 'chat.completion.chunk',
      created: 0,
      model: parsed.model,
      choices: [{ index: 0, delta: {}, finish_reason: 'stop' }],
      usage: { prompt_tokens: 3, completion_tokens: 1, total_tokens: 4 },
    }) + '\n\n');
    res.write('data: [DONE]\n\n');
    res.end();
  });
});

await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const baseUrl = `http://127.0.0.1:${server.address().port}/v1`;

for (const requestedThinking of requestedLevels) {
  const before = rows.length;
  const model = { ...modelBase, baseUrl };
  for await (const _ of streamSimple(model, {
    systemPrompt: 'You are a test assistant.',
    messages: [{ role: 'user', content: [{ type: 'text', text: 'Reply ok.' }] }],
  }, {
    apiKey: 'local',
    reasoning: requestedThinking,
    maxTokens: 8,
  })) {}
  const sent = rows[before].body;
  console.log(JSON.stringify({
    provider: model.provider,
    model: model.id,
    api: model.api,
    compat: model.compat,
    requestedThinking,
    availableThinkingLevels: getSupportedThinkingLevels(model),
    clampedThinking: clampThinkingLevel(model, requestedThinking),
    sentChatTemplateKwargs: sent.chat_template_kwargs ?? null,
    sentEnableThinkingTopLevel: sent.enable_thinking ?? null,
    sentReasoningEffort: sent.reasoning_effort ?? null,
    endpointPath: '/v1/chat/completions',
    baseUrl: 'mock://local',
  }));
}

server.close();
