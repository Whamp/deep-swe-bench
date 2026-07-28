// Preserve Gemma 4 tool-turn reasoning and pin the server's sampling profile.
export default function (pi) {
  const targetProvider = "local-vllm";
  const targetModel = "gemma-4-31b";
  const sampling = {
    temperature: 1.0,
    top_p: 0.95,
    top_k: 64,
    min_p: 0.0,
    repetition_penalty: 1.0,
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
    };
  });
}
