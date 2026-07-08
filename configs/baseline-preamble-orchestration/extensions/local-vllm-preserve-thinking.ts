export default function (pi) {
	const preserveThinkingModels = new Set([
		"cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit",
		"Qwen/Qwen3.6-35B-A3B",
		"cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4",
	]);

	pi.on("before_provider_request", (event, ctx) => {
		if (!ctx.model) return;
		if (ctx.model.provider !== "local-vllm") return;
		if (!preserveThinkingModels.has(ctx.model.id)) return;
		if (!event.payload || typeof event.payload !== "object" || Array.isArray(event.payload)) return;

		const payload = event.payload;
		const existing = payload.chat_template_kwargs;
		const chatTemplateKwargs =
			existing && typeof existing === "object" && !Array.isArray(existing)
				? { ...existing, preserve_thinking: true }
				: { preserve_thinking: true };

		return {
			...payload,
			chat_template_kwargs: chatTemplateKwargs,
		};
	});
}
