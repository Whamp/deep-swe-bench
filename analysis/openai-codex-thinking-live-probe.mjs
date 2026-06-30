import { ModelRegistry } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/model-registry.js';
import { AuthStorage, FileAuthStorageBackend } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/auth-storage.js';
import { streamSimple } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/api/openai-codex-responses.js';
import { clampThinkingLevel, getSupportedThinkingLevels } from '/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/models.js';

const levels = ['off','minimal','low','medium','high','xhigh'];
const models = ['gpt-5.5','gpt-5.4','gpt-5.4-mini'];
const auth = new AuthStorage(new FileAuthStorageBackend());
const registry = ModelRegistry.create(auth);
for (const modelId of models) {
  const model = registry.find('openai-codex', modelId);
  const authResult = await registry.getApiKeyAndHeaders(model);
  for (const requestedThinking of levels) {
    const row = {
      provider:'openai-codex', model:modelId, api:model.api,
      requestedThinking, clampedThinking: clampThinkingLevel(model, requestedThinking),
      availableThinkingLevels: getSupportedThinkingLevels(model),
      thinkingLevelMap: model.thinkingLevelMap ?? null,
      ok:false, stopReason:null, usage:null, error:null,
    };
    try {
      if (!authResult.ok || !authResult.apiKey) throw new Error(authResult.ok ? 'missing apiKey' : authResult.error);
      let final = null;
      const stream = streamSimple(model, {
        systemPrompt: 'You are a terse probe. Reply with exactly OK.',
        messages: [{role:'user', content:[{type:'text', text:'Reply OK.'}]}],
      }, {
        apiKey: authResult.apiKey,
        headers: authResult.headers,
        env: authResult.env,
        reasoning: requestedThinking,
        transport: 'sse',
        timeoutMs: 60000,
      });
      for await (const ev of stream) {
        if (ev.type === 'done') final = ev.message;
        if (ev.type === 'error') throw new Error(ev.error?.errorMessage || JSON.stringify(ev.error));
      }
      row.ok = true;
      row.stopReason = final?.stopReason ?? null;
      row.usage = final?.usage ?? null;
      row.responseModel = final?.model ?? null;
    } catch (e) {
      row.error = e instanceof Error ? e.message : String(e);
    }
    console.log(JSON.stringify(row));
  }
}
