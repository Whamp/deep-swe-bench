import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Preserve ThinkingCap reasoning, cap high thinking, and pin official sampling.
export default function registerThinkingCapProviderRequest(pi: ExtensionAPI): void {
  const targetProvider = "local-vllm";
  const targetModel = "bottlecapai/ThinkingCap-Qwen3.6-27B";
  const highThinkingTokenBudget = 32768;
  const sampling = {
    temperature: 1.0,
    top_p: 0.95,
    top_k: 20,
    min_p: 0.0,
  };

  pi.on("before_provider_request", (event, ctx) => {
    if (ctx.model?.provider !== targetProvider || ctx.model.id !== targetModel) return;
    const payload = event.payload;
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;

    const existing = payload.chat_template_kwargs;
    const chatTemplateKwargs =
      existing && typeof existing === "object" && !Array.isArray(existing)
        ? { ...existing, preserve_thinking: true }
        : { preserve_thinking: true };

    return {
      ...payload,
      ...sampling,
      chat_template_kwargs: chatTemplateKwargs,
      ...(chatTemplateKwargs.enable_thinking
        ? { thinking_token_budget: highThinkingTokenBudget }
        : {}),
    };
  });
}
