// Apply Poolside's recommended Laguna S 2.1 sampling tuple.
export default function (pi) {
	const targetProvider = "local-vllm";
	const targetModel = "poolside/Laguna-S-2.1-INT4";
	const sampling = { temperature: 0.7, top_p: 0.95 };

	pi.on("before_provider_request", (event, ctx) => {
		if (ctx.model?.provider !== targetProvider || ctx.model.id !== targetModel) return;
		const payload = event.payload;
		if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;

		const next = { ...payload, ...sampling };
		if (process.env.PI_SAMPLING_DEBUG) {
			console.error(
				JSON.stringify({
					dbg: "laguna-sampling",
					model: ctx.model.id,
					temperature: next.temperature,
					top_p: next.top_p,
				}),
			);
		}

		return next;
	});
}
