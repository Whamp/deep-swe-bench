import assert from "node:assert/strict";
import test from "node:test";

import registerLocalVllmDeepSeekV4Wna16Request from "../configs/baseline-vllm-deepseek-v4-flash-0731-wna16@1.0.0/extensions/local-vllm-deepseek-v4-wna16-request.ts";

function captureLocalVllmDeepSeekV4Wna16RequestHandler() {
  let handler;
  registerLocalVllmDeepSeekV4Wna16Request({
    on(eventName, candidate) {
      assert.equal(eventName, "before_provider_request");
      handler = candidate;
    },
  });
  assert.equal(typeof handler, "function");
  return handler;
}

test("pins the DeepSeek V4 Flash WNA16 agentic sampling profile", () => {
  const handler = captureLocalVllmDeepSeekV4Wna16RequestHandler();
  const payload = {
    model: "deepseek-v4-flash-0731-wna16",
    temperature: 0.8,
    top_p: 1.0,
    untouched: "value",
  };

  const result = handler(
    { payload },
    {
      model: {
        provider: "local-vllm",
        id: "deepseek-v4-flash-0731-wna16",
      },
    },
  );

  assert.deepEqual(result, {
    model: "deepseek-v4-flash-0731-wna16",
    temperature: 1.0,
    top_p: 0.95,
    untouched: "value",
  });
});

test("does not alter another model or provider", () => {
  const handler = captureLocalVllmDeepSeekV4Wna16RequestHandler();
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
          id: "deepseek-v4-flash-0731-wna16",
        },
      },
    ),
    undefined,
  );
  assert.deepEqual(payload, { temperature: 0.8 });
});
