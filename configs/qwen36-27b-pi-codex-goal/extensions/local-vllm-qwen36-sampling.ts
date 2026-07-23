// Apply the requested Qwen3.6 sampling tuple to the final vLLM request body.
export default function (pi) {
	const targetProvider = "local-vllm";
	const targetModel = "cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4";
	const sampling = {
		temperature: 1.0,
		top_p: 0.95,
		top_k: 20,
		min_p: 0.0,
		presence_penalty: 0.0,
		repetition_penalty: 1.0,
	};

	pi.on("before_provider_request", (event, ctx) => {
		if (ctx.model?.provider !== targetProvider || ctx.model.id !== targetModel) return;
		const payload = event.payload;
		if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;

		const next = { ...payload, ...sampling };
		if (process.env.PI_SAMPLING_DEBUG) {
			console.error(
				JSON.stringify({
					dbg: "qwen36-sampling",
					model: ctx.model.id,
					temperature: next.temperature,
					top_p: next.top_p,
					top_k: next.top_k,
					min_p: next.min_p,
					presence_penalty: next.presence_penalty,
					repetition_penalty: next.repetition_penalty,
				}),
			);
		}

		return next;
	});
}
