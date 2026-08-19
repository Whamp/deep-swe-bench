/** Pins the DeepSeek V4 Flash GGUF-TP agentic sampling profile. */
export default function registerLocalVllmDeepSeekV4GgufTpRequest(pi): void {
  const targetProvider = "local-vllm";
  const targetModel = "deepseek-v4-flash-0731-gguf-tp";

  pi.on("before_provider_request", (event, ctx) => {
    if (ctx.model?.provider !== targetProvider || ctx.model.id !== targetModel) {
      return;
    }

    const payload = event.payload;
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return;
    }

    return {
      ...payload,
      temperature: 1.0,
      top_p: 0.95,
    };
  });
}
