#!/usr/bin/env node
// Capture Prime Agent 0.7.0's built-in zai/glm-5.2 max-thinking request locally.
// This probe contacts only a localhost mock server and uses a dummy API key.
import http from 'node:http';

const PRIME_AI = '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/prime-agent/node_modules/@earendil-works/pi-ai/dist';
const { getModel } = await import(`${PRIME_AI}/models.js`);
const { streamSimpleOpenAICompletions } = await import(`${PRIME_AI}/providers/openai-completions.js`);

let captured;
const server = http.createServer((request, response) => {
  let raw = '';
  request.on('data', chunk => { raw += chunk; });
  request.on('end', () => {
    captured = JSON.parse(raw);
    response.writeHead(200, { 'Content-Type': 'text/event-stream' });
    response.write(`data: ${JSON.stringify({
      id: 'mock', object: 'chat.completion.chunk', created: 1,
      model: 'glm-5.2', choices: [{ index: 0, delta: { content: 'OK' }, finish_reason: null }],
    })}\n\n`);
    response.write(`data: ${JSON.stringify({
      id: 'mock', object: 'chat.completion.chunk', created: 1,
      model: 'glm-5.2', choices: [{ index: 0, delta: {}, finish_reason: 'stop' }],
      usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
    })}\n\n`);
    response.end('data: [DONE]\n\n');
  });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));

try {
  const catalogModel = getModel('zai', 'glm-5.2');
  if (!catalogModel) throw new Error('Prime Agent catalog has no zai/glm-5.2');
  const model = {
    ...catalogModel,
    baseUrl: `http://127.0.0.1:${server.address().port}/v1`,
  };
  const context = {
    systemPrompt: 'system',
    messages: [{ role: 'user', content: [{ type: 'text', text: 'Return OK' }] }],
  };
  for await (const _event of streamSimpleOpenAICompletions(model, context, {
    apiKey: 'dummy',
    reasoning: 'max',
    maxTokens: 128,
    temperature: 0,
  })) {
    // Drain the provider stream.
  }
  console.log(JSON.stringify({
    subject: 'prime-agent@0.7.0',
    provider: catalogModel.provider,
    model: catalogModel.id,
    api: catalogModel.api,
    catalogBaseUrl: catalogModel.baseUrl,
    catalogThinkingLevelMap: catalogModel.thinkingLevelMap,
    requestedThinking: 'max',
    enable_thinking: captured.enable_thinking ?? null,
    thinking: captured.thinking ?? null,
    reasoning_effort: captured.reasoning_effort ?? null,
    tool_stream: captured.tool_stream ?? null,
    max_tokens: captured.max_tokens ?? null,
    max_completion_tokens: captured.max_completion_tokens ?? null,
  }));
} finally {
  server.close();
}
