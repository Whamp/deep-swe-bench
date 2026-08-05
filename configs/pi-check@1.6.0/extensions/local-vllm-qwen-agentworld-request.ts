/** Preserves Qwen-AgentWorld thinking and pins its approved sampling profile. */
export default function registerQwenAgentWorldProviderRequest(pi): void {
  const targetProvider = "local-vllm";
  const targetModel = "qwen-agentworld-35b-a3b";
  const sampling = {
    temperature: 0.6,
    top_p: 0.95,
    top_k: 20,
    min_p: 0.0,
    repetition_penalty: 1.0,
  };

  pi.on("before_provider_request", (event, ctx) => {
    if (ctx.model?.provider !== targetProvider || ctx.model.id !== targetModel) {
      return;
    }

    const payload = event.payload;
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return;
    }

    const existingChatTemplateKwargs = payload.chat_template_kwargs;
    const chatTemplateKwargs =
      existingChatTemplateKwargs &&
      typeof existingChatTemplateKwargs === "object" &&
      !Array.isArray(existingChatTemplateKwargs)
        ? { ...existingChatTemplateKwargs, preserve_thinking: true }
        : { preserve_thinking: true };

    return {
      ...payload,
      ...sampling,
      chat_template_kwargs: chatTemplateKwargs,
    };
  });
}
