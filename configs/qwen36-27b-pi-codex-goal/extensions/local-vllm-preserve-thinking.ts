// Preserve Qwen reasoning across tool turns without changing its thinking budget.
export default function (pi) {
	const targetProvider = "local-vllm";
	const targetModel = "cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4";

	pi.on("before_provider_request", (event, ctx) => {
		if (ctx.model?.provider !== targetProvider || ctx.model.id !== targetModel) return;
		const payload = event.payload;
		if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;

		const existing = payload.chat_template_kwargs;
		const chatTemplateKwargs =
			existing && typeof existing === "object" && !Array.isArray(existing)
				? { ...existing, preserve_thinking: true }
				: { preserve_thinking: true };
		const next = { ...payload, chat_template_kwargs: chatTemplateKwargs };

		if (process.env.PI_PRESERVE_THINKING_DEBUG) {
			console.error(
				JSON.stringify({
					dbg: "qwen-preserve-thinking",
					model: ctx.model.id,
					enable_thinking: chatTemplateKwargs.enable_thinking,
					preserve_thinking: chatTemplateKwargs.preserve_thinking,
					thinking_token_budget: next.thinking_token_budget ?? null,
				}),
			);
		}

		return next;
	});
}
