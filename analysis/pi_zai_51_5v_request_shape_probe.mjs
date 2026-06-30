#!/usr/bin/env node
import http from 'node:http';
import { streamSimple } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js';

const captured = [];
const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', c => { body += c; });
  req.on('end', () => {
    const parsed = JSON.parse(body || '{}');
    captured.push(parsed);
    res.writeHead(200, {'Content-Type': 'text/event-stream'});
    res.write(`data: ${JSON.stringify({id:'mock', object:'chat.completion.chunk', created:1, model:parsed.model, choices:[{index:0, delta:{content:'OK'}, finish_reason:null}]})}\n\n`);
    res.write(`data: ${JSON.stringify({id:'mock', object:'chat.completion.chunk', created:1, model:parsed.model, choices:[{index:0, delta:{}, finish_reason:'stop'}], usage:{prompt_tokens:1, completion_tokens:1, total_tokens:2}})}\n\n`);
    res.write('data: [DONE]\n\n');
    res.end();
  });
});
const port = await new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server.address().port)));
async function drain(s) { for await (const _ of s) {} }
function model(id, input = ['text']) {
  return {
    provider: 'zai', id, name: id, api: 'openai-completions', baseUrl: `http://127.0.0.1:${port}/v1`, headers: {},
    input, reasoning: true, contextWindow: 200000, maxTokens: 131072,
    cost: { input:0, output:0, cacheRead:0, cacheWrite:0 },
    compat: { maxTokensField:'max_tokens', supportsDeveloperRole:false, supportsReasoningEffort:false, supportsStore:false, thinkingFormat:'zai', zaiToolStream:true },
  };
}
const textContext = { systemPrompt: 'system', messages: [{ role:'user', content:[{type:'text', text:'Return OK'}] }] };
const imageContext = { systemPrompt: 'system', messages: [{ role:'user', content:[{type:'text', text:'Describe this image briefly'}, {type:'image', mimeType:'image/png', data:'iVBORw0KGgo='}] }] };
const cases = [
  ['glm51_off', model('glm-5.1'), textContext, 'off'],
  ['glm51_low', model('glm-5.1'), textContext, 'low'],
  ['glm51_high', model('glm-5.1'), textContext, 'high'],
  ['glm51_xhigh', model('glm-5.1'), textContext, 'xhigh'],
  ['glm5v_off_text', model('glm-5v-turbo', ['text','image']), textContext, 'off'],
  ['glm5v_high_text', model('glm-5v-turbo', ['text','image']), textContext, 'high'],
  ['glm5v_high_image', model('glm-5v-turbo', ['text','image']), imageContext, 'high'],
  ['glm5v_xhigh_image', model('glm-5v-turbo', ['text','image']), imageContext, 'xhigh'],
];
try {
  for (const [name, m, ctx, thinking] of cases) {
    const before = captured.length;
    await drain(streamSimple(m, ctx, { apiKey:'dummy', reasoning: thinking, maxTokens: 128, temperature: 0 }));
    const b = captured[before];
    console.log(JSON.stringify({
      case:name, model:b.model, requestedThinking:thinking, thinking:b.thinking, reasoning_effort:b.reasoning_effort ?? null,
      max_tokens:b.max_tokens, messageContent:b.messages?.at(-1)?.content,
    }));
  }
} finally { server.close(); }
