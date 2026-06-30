import http from 'node:http';
import { ModelRegistry } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/model-registry.js';
import { AuthStorage, FileAuthStorageBackend } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/auth-storage.js';
import { streamSimple } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-codex-responses.js';
import { clampThinkingLevel, getSupportedThinkingLevels } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/models.js';

const levels = ['off','minimal','low','medium','high','xhigh'];
const models = ['gpt-5.5','gpt-5.4','gpt-5.4-mini'];
const auth = new AuthStorage(new FileAuthStorageBackend());
const registry = ModelRegistry.create(auth);
const jwtPayload = Buffer.from(JSON.stringify({'https://api.openai.com/auth': {chatgpt_account_id: 'acct_test'}})).toString('base64url');
const fakeJwt = ['x', jwtPayload, 'x'].join('.');

const rows = [];
const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', c => body += c);
  req.on('end', () => {
    const parsed = JSON.parse(body || '{}');
    rows.push({headers: {'chatgpt-account-id': req.headers['chatgpt-account-id']}, body: parsed});
    res.writeHead(200, {'content-type':'text/event-stream'});
    res.write('data: '+JSON.stringify({type:'response.completed', response:{id:'resp_mock', status:'completed', model:parsed.model, output:[], usage:{input_tokens:1, output_tokens:1, total_tokens:2}}})+'\n\n');
    res.end();
  });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const baseUrl = `http://127.0.0.1:${server.address().port}`;

for (const modelId of models) {
  const baseModel = registry.find('openai-codex', modelId);
  const model = {...baseModel, baseUrl};
  for (const requestedThinking of levels) {
    const before = rows.length;
    for await (const _ of streamSimple(model, {systemPrompt:'s', messages:[{role:'user', content:[{type:'text', text:'hello'}]}]}, {apiKey: fakeJwt, reasoning: requestedThinking, maxTokens: 8, transport: 'sse'})) {}
    const sent = rows[before].body;
    console.log(JSON.stringify({
      provider: 'openai-codex',
      model: modelId,
      api: model.api,
      availableThinkingLevels: getSupportedThinkingLevels(baseModel),
      thinkingLevelMap: baseModel.thinkingLevelMap ?? null,
      requestedThinking,
      clampedThinking: clampThinkingLevel(baseModel, requestedThinking),
      sentReasoning: sent.reasoning ?? null,
      endpointPath: '/codex/responses',
      baseUrl: 'mock://local',
    }));
  }
}
server.close();
