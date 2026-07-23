// local-vllm-thinkingcap-sampling.ts
//
// Appends the sampling parameters recommended for bottlecapai/ThinkingCap-Qwen3.6-27B
// to the final local-vLLM OpenAI-compatible provider payload.
//
// Pi exposes the final request body in `before_provider_request`, so vLLM
// extra-body keys are appended directly to that payload. The OpenAI-client
// example is used only for the `chat_template_kwargs: { preserve_thinking: true }`
// shape; sampling values below come from the benchmark config requirement.
// `temperature` and `top_p` are normal top-level OpenAI-compatible payload fields;
// `top_k` and `min_p` are vLLM extra-body fields.
//
// Required parameters:
//   temperature = 1.0
//   top_p       = 0.95
//   top_k       = 20
//   min_p       = 0.0
//
// Set PI_SAMPLING_DEBUG=1 to log the applied values to stderr.
export default function (pi) {
	const TARGET_PROVIDER = "local-vllm";
	const TARGET_MODEL = "bottlecapai/ThinkingCap-Qwen3.6-27B";
	const SAMPLING = {
		temperature: 1.0,
		top_p: 0.95,
		top_k: 20,
		min_p: 0.0,
	};

	pi.on("before_provider_request", (event, ctx) => {
		if (!ctx.model) return;
		if (ctx.model.provider !== TARGET_PROVIDER) return;
		if (ctx.model.id !== TARGET_MODEL) return;
		const payload = event.payload;
		if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;

		const next = { ...payload, ...SAMPLING };

		if (process.env.PI_SAMPLING_DEBUG) {
			console.error(
				JSON.stringify({
					dbg: "thinkingcap-sampling",
					model: ctx.model.id,
					temperature: next.temperature,
					top_p: next.top_p,
					top_k: next.top_k,
					min_p: next.min_p,
				}),
			);
		}

		return next;
	});
}
