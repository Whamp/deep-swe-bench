import assert from "node:assert/strict";
import test from "node:test";

import registerLocalVllmDeepSeekV4Wna16Request from "../configs/baseline-vllm-deepseek-v4-flash-0731-wna16@1.1.0/extensions/local-vllm-deepseek-v4-wna16-request.ts";

function captureQualityCandidateRequestHandler() {
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

test("pins sampling only for the projection-sensitive quality candidate", () => {
  const handler = captureQualityCandidateRequestHandler();
  const payload = {
    model: "deepseek-v4-flash-0731-wna16-quality-12035985",
    temperature: 0.8,
    top_p: 1.0,
    untouched: "value",
  };

  assert.deepEqual(
    handler(
      { payload },
      {
        model: {
          provider: "local-vllm",
          id: "deepseek-v4-flash-0731-wna16-quality-12035985",
        },
      },
    ),
    {
      model: "deepseek-v4-flash-0731-wna16-quality-12035985",
      temperature: 1.0,
      top_p: 0.95,
      untouched: "value",
    },
  );

  assert.equal(
    handler(
      { payload },
      {
        model: {
          provider: "local-vllm",
          id: "deepseek-v4-flash-0731-wna16",
        },
      },
    ),
    undefined,
  );
});
