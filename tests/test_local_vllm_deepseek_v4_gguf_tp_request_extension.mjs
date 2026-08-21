import assert from "node:assert/strict";
import test from "node:test";

import registerLocalVllmDeepSeekV4GgufTpRequest from "../configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/extensions/local-vllm-deepseek-v4-gguf-tp-request.ts";

function captureLocalVllmDeepSeekV4GgufTpRequestHandler() {
  let handler;
  registerLocalVllmDeepSeekV4GgufTpRequest({
    on(eventName, candidate) {
      assert.equal(eventName, "before_provider_request");
      handler = candidate;
    },
  });
  assert.equal(typeof handler, "function");
  return handler;
}

test("pins the DeepSeek V4 Flash GGUF-TP agentic sampling profile", () => {
  const handler = captureLocalVllmDeepSeekV4GgufTpRequestHandler();
  const payload = {
    model: "deepseek-v4-flash-0731-gguf-tp",
    temperature: 0.8,
    top_p: 1.0,
    untouched: "value",
  };

  const result = handler(
    { payload },
    {
      model: {
        provider: "local-vllm",
        id: "deepseek-v4-flash-0731-gguf-tp",
      },
    },
  );

  assert.deepEqual(result, {
    model: "deepseek-v4-flash-0731-gguf-tp",
    temperature: 1.0,
    top_p: 0.95,
    untouched: "value",
  });
});

test("does not alter another model or provider", () => {
  const handler = captureLocalVllmDeepSeekV4GgufTpRequestHandler();
  const payload = { temperature: 0.8 };

  assert.equal(
    handler({ payload }, { model: { provider: "local-vllm", id: "another-model" } }),
    undefined,
  );
  assert.equal(
    handler(
      { payload },
      {
        model: {
          provider: "openrouter",
          id: "deepseek-v4-flash-0731-gguf-tp",
        },
      },
    ),
    undefined,
  );
  assert.deepEqual(payload, { temperature: 0.8 });
});
