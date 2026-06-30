import { ModelRegistry } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/model-registry.js';
import { AuthStorage, FileAuthStorageBackend } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/auth-storage.js';

const JWT_CLAIM_PATH = 'https://api.openai.com/auth';
const endpoint = 'https://chatgpt.com/backend-api/codex/responses';
const prompt = 'Compute exactly: Let a_1=7 and a_{n+1}=(3*a_n+11) mod 1009. What is a_37? Reply with only the integer.';
const models = ['gpt-5.4', 'gpt-5.4-mini'];
const cases = [
  {case: 'omit_reasoning_pi_off', reasoning: undefined},
  {case: 'explicit_none', reasoning: {effort: 'none', summary: 'auto'}},
  {case: 'explicit_low', reasoning: {effort: 'low', summary: 'auto'}},
  {case: 'explicit_xhigh', reasoning: {effort: 'xhigh', summary: 'auto'}},
];
const reps = 3;

function accountIdFromJwt(token) {
  const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString('utf8'));
  const accountId = payload?.[JWT_CLAIM_PATH]?.chatgpt_account_id;
  if (!accountId) throw new Error('missing chatgpt account id');
  return accountId;
}
function makeBody(model, reasoning) {
  const body = {
    model,
    store: false,
    stream: true,
    instructions: 'You are a controlled API probe. Answer exactly as requested.',
    input: [{role: 'user', content: [{type: 'input_text', text: prompt}]}],
    text: {verbosity: 'low'},
    include: ['reasoning.encrypted_content'],
    tool_choice: 'auto',
    parallel_tool_calls: true,
  };
  if (reasoning !== undefined) body.reasoning = reasoning;
  return body;
}
async function readSse(res) {
  const text = await res.text();
  const events = [];
  for (const chunk of text.split('\n\n')) {
    const lines = chunk.split('\n').filter(l => l.startsWith('data:'));
    if (!lines.length) continue;
    const data = lines.map(l => l.slice(5).trim()).join('\n').trim();
    if (!data || data === '[DONE]') continue;
    try { events.push(JSON.parse(data)); } catch (e) { events.push({parse_error: String(e), raw: data}); }
  }
  return events;
}
const registry = ModelRegistry.create(new AuthStorage(new FileAuthStorageBackend()));
const auth = await registry.getApiKeyAndHeaders(registry.find('openai-codex', 'gpt-5.4'));
if (!auth.ok || !auth.apiKey) throw new Error(auth.ok ? 'missing openai-codex api key' : auth.error);
const accountId = accountIdFromJwt(auth.apiKey);
for (const model of models) {
  for (const c of cases) {
    for (let rep = 0; rep < reps; rep++) {
      const body = makeBody(model, c.reasoning);
      const started = Date.now();
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          ...(auth.headers || {}),
          'Authorization': `Bearer ${auth.apiKey}`,
          'chatgpt-account-id': accountId,
          'originator': 'pi',
          'User-Agent': 'pi controlled-probe',
          'OpenAI-Beta': 'responses=experimental',
          'accept': 'text/event-stream',
          'content-type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      const elapsedMs = Date.now() - started;
      const events = await readSse(res);
      const completed = [...events].reverse().find(e => e.type === 'response.completed' || e.type === 'response.done' || e.type === 'response.incomplete');
      const response = completed?.response;
      const usage = response?.usage ?? null;
      console.log(JSON.stringify({
        model,
        case: c.case,
        rep,
        requestReasoning: body.reasoning ?? null,
        httpStatus: res.status,
        ok: res.ok && !!completed,
        responseStatus: response?.status ?? null,
        responseModel: response?.model ?? null,
        usage,
        elapsedMs,
      }));
    }
  }
}
