#!/usr/bin/env node
// Validate Pi's OpenAI-compatible ZAI request body construction against a local mock server.
// This does not contact Z.ai or log secrets.
import http from 'node:http';
import { streamSimple } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js';

const captured = [];

const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    let parsed = null;
    try { parsed = JSON.parse(body || '{}'); } catch {}
    captured.push({ method: req.method, url: req.url, headers: req.headers, body: parsed });
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    });
    const chunk = {
      id: 'mock',
      object: 'chat.completion.chunk',
      created: 1,
      model: parsed?.model || 'glm-5.2',
      choices: [{ index: 0, delta: { content: 'OK' }, finish_reason: null }],
    };
    const done = {
      id: 'mock',
      object: 'chat.completion.chunk',
      created: 1,
      model: parsed?.model || 'glm-5.2',
      choices: [{ index: 0, delta: {}, finish_reason: 'stop' }],
      usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
    };
    res.write(`data: ${JSON.stringify(chunk)}\n\n`);
    res.write(`data: ${JSON.stringify(done)}\n\n`);
    res.write('data: [DONE]\n\n');
    res.end();
  });
});

function listen(server) {
  return new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server.address().port)));
}

async function drain(stream) {
  for await (const _event of stream) {
    // no-op
  }
}

const context = {
  systemPrompt: 'system',
  messages: [{ role: 'user', content: [{ type: 'text', text: 'Return OK' }] }],
};

function baseModel(port, compat, thinkingLevelMap) {
  return {
    provider: 'zai',
    id: 'glm-5.2',
    name: 'GLM-5.2 mock',
    api: 'openai-completions',
    baseUrl: `http://127.0.0.1:${port}/v1`,
    headers: {},
    input: ['text'],
    reasoning: true,
    contextWindow: 1000000,
    maxTokens: 131072,
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    compat,
    thinkingLevelMap,
  };
}

const oldCompat = {
  maxTokensField: 'max_tokens',
  supportsDeveloperRole: false,
  supportsReasoningEffort: false,
  supportsStore: false,
  thinkingFormat: 'zai',
  zaiToolStream: true,
};

const proposedCompat = {
  maxTokensField: 'max_tokens',
  supportsDeveloperRole: false,
  supportsReasoningEffort: true,
  supportsStore: false,
  thinkingFormat: 'zai',
  zaiToolStream: true,
};

const proposedMap = {
  minimal: null,
  low: 'high',
  medium: 'high',
  high: 'high',
  xhigh: 'max',
};

const cases = [
  ['old_off', oldCompat, undefined, 'off'],
  ['old_low', oldCompat, undefined, 'low'],
  ['old_high', oldCompat, undefined, 'high'],
  ['old_xhigh', oldCompat, undefined, 'xhigh'],
  ['proposed_off', proposedCompat, proposedMap, 'off'],
  ['proposed_low', proposedCompat, proposedMap, 'low'],
  ['proposed_high', proposedCompat, proposedMap, 'high'],
  ['proposed_xhigh', proposedCompat, proposedMap, 'xhigh'],
];

const port = await listen(server);
try {
  for (const [name, compat, map, thinking] of cases) {
    const before = captured.length;
    const model = baseModel(port, compat, map);
    await drain(streamSimple(model, context, {
      apiKey: 'dummy',
      reasoning: thinking,
      maxTokens: 128,
      temperature: 0,
    }));
    const req = captured[before];
    const b = req.body;
    const summary = {
      case: name,
      requestedThinking: thinking,
      thinking: b.thinking,
      reasoning_effort: b.reasoning_effort ?? null,
      max_tokens: b.max_tokens,
      max_completion_tokens: b.max_completion_tokens ?? null,
      stream_options: b.stream_options,
      tool_stream: b.tool_stream ?? null,
    };
    console.log(JSON.stringify(summary));
  }
} finally {
  server.close();
}
