// local-vllm-preserve-thinking.ts
//
// For local vLLM Qwen3.6 reasoning models this extension:
//   1. Injects `chat_template_kwargs.preserve_thinking = true` (needed for multi-turn
//      reasoning replay) for every model in `preserveThinkingModels`.
//   2. Maps pi's thinking level (off/minimal/low/medium/high/xhigh) to a hard per-request
//      `thinking_token_budget` for every model in `BUDGETS_BY_MODEL`. vLLM enforces this
//      server-side by force-injecting `</think>` once the budget is exceeded
//      (ThinkingBudgetStateHolder in vllm/v1/sample). Without it, `enable_thinking=true`
//      runs uncapped and the model spends ~100% of its budget on <think> and emits empty
//      output.
//
// Only add a model to BUDGETS_BY_MODEL once its vLLM instance is on a build that supports
// `thinking_token_budget` (vLLM >= 0.23.x with the V1 model runner). Old vLLM ignores the
// field, but scoping here keeps the behavior explicit per model.
//
// Set PI_BUDGET_DEBUG=1 to log the resolved payload to stderr.
//
// Notes:
// - getThinkingLevel() lives on the ExtensionAPI (pi), NOT on the event ctx.
// - "off" is represented in the payload as chat_template_kwargs.enable_thinking === false,
//   which we gate on (no budget when thinking is off).
// - xhigh requires `thinkingLevelMap: { "xhigh": "xhigh" }` on the model in models.json,
//   otherwise pi clamps xhigh down to high (getSupportedThinkingLevels in pi-ai/models.js).
export default function (pi) {
	const preserveThinkingModels = new Set([
		"cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit",
		"Qwen/Qwen3.6-35B-A3B",
		"cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4",
	]);

	// Per-model thinking-token budgets by pi level (Qwen3.6-27B; aligned to the reasoning-
	// budget study — avoid tiny budgets for hard tasks; 32k is the accuracy default).
	const BUDGETS_BY_MODEL = {
		"cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4": {
			minimal: 4096,
			low: 8192,
			medium: 16384,
			high: 32768,
			xhigh: 65536,
		},
	};

	pi.on("before_provider_request", (event, ctx) => {
		if (!ctx.model) return;
		if (ctx.model.provider !== "local-vllm") return;
		if (!preserveThinkingModels.has(ctx.model.id)) return;
		const payload = event.payload;
		if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;

		// 1) preserve_thinking for multi-turn reasoning
		const existing = payload.chat_template_kwargs;
		const chatTemplateKwargs =
			existing && typeof existing === "object" && !Array.isArray(existing)
				? { ...existing, preserve_thinking: true }
				: { preserve_thinking: true };

		const next = { ...payload, chat_template_kwargs: chatTemplateKwargs };

		// 2) hard thinking budget — only when thinking is on
		// Prefer thinkingBudgets from model config (models.json), fall back to hardcoded map.
		let level;
		const modelBudgets = ctx.model.thinkingBudgets;
		const budgets =
			(modelBudgets && typeof modelBudgets === "object")
				? modelBudgets
				: BUDGETS_BY_MODEL[ctx.model.id];
		if (budgets && ctx.model.reasoning && chatTemplateKwargs.enable_thinking) {
			level = typeof pi.getThinkingLevel === "function" ? pi.getThinkingLevel() : undefined;
			if (level) {
				const budget = budgets[level];
				if (typeof budget === "number") next.thinking_token_budget = budget;
			}
		}

		if (process.env.PI_BUDGET_DEBUG) {
			console.error(
				JSON.stringify({
					dbg: "vllm-budget",
					model: ctx.model.id,
					level: level ?? "off",
					enable_thinking: chatTemplateKwargs.enable_thinking,
					thinking_token_budget: next.thinking_token_budget ?? null,
				}),
			);
		}

		return next;
	});
}
