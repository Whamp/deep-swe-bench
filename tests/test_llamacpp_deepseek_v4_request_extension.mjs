import assert from "node:assert/strict";
import test from "node:test";

import registerLlamacppDeepSeekV4Request from "../configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0/extensions/local-llamacpp-deepseek-v4-request.ts";

function captureLlamacppDeepSeekV4RequestHandler() {
  let handler;
  const pi = {
    on(eventName, candidate) {
      assert.equal(eventName, "before_provider_request");
      handler = candidate;
    },
  };
  registerLlamacppDeepSeekV4Request(pi);
  assert.equal(typeof handler, "function");
  return handler;
}

test("pins the DeepSeek V4 Flash agentic sampling profile", () => {
  const handler = captureLlamacppDeepSeekV4RequestHandler();
  const payload = {
    model: "deepseek-v4-flash-0731-q8-fast-prefill",
    temperature: 0.8,
    top_p: 1.0,
    untouched: "value",
  };

  const result = handler(
    { payload },
    {
      model: {
        provider: "local-llamacpp",
        id: "deepseek-v4-flash-0731-q8-fast-prefill",
      },
    },
  );

  assert.deepEqual(result, {
    model: "deepseek-v4-flash-0731-q8-fast-prefill",
    temperature: 1.0,
    top_p: 0.95,
    top_k: 0,
    min_p: 0.0,
    repeat_penalty: 1.0,
    untouched: "value",
  });
});

test("does not alter requests for another model or provider", () => {
  const handler = captureLlamacppDeepSeekV4RequestHandler();
  const payload = { temperature: 0.8 };

  assert.equal(
    handler(
      { payload },
      { model: { provider: "local-llamacpp", id: "another-model" } },
    ),
    undefined,
  );
  assert.equal(
    handler(
      { payload },
      {
        model: {
          provider: "openrouter",
          id: "deepseek-v4-flash-0731-q8-fast-prefill",
        },
      },
    ),
    undefined,
  );
  assert.deepEqual(payload, { temperature: 0.8 });
});
