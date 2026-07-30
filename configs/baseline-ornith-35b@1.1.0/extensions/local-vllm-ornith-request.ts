// Pin the live Ornith serving profile's sampling settings.
export default function (pi) {
  const targetProvider = "local-vllm";
  const targetModel = "ornith-1.0-35b";
  const sampling = {
    temperature: 1.0,
    top_p: 0.95,
    top_k: 20,
    min_p: 0.0,
    repetition_penalty: 1.0,
  };

  pi.on("before_provider_request", (event, ctx) => {
    if (ctx.model?.provider !== targetProvider || ctx.model.id !== targetModel) return;
    const payload = event.payload;
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;

    return { ...payload, ...sampling };
  });
}
