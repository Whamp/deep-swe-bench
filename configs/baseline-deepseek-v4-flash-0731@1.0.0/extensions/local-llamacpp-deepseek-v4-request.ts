const DEEPSEEK_V4_PROVIDER = "local-llamacpp";
const DEEPSEEK_V4_MODEL = "deepseek-v4-flash-0731";
const DEEPSEEK_V4_SAMPLING = {
  temperature: 1.0,
  top_p: 0.95,
  top_k: 0,
  min_p: 0.0,
  repeat_penalty: 1.0,
};

/** Pins the live llama.cpp DeepSeek V4 Flash 0731 sampling profile. */
export default function pinDeepSeekV4FlashRequest(pi) {
  pi.on("before_provider_request", (event, context) => {
    if (
      context.model?.provider !== DEEPSEEK_V4_PROVIDER ||
      context.model.id !== DEEPSEEK_V4_MODEL
    ) {
      return;
    }
    const payload = event.payload;
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return;
    }

    return { ...payload, ...DEEPSEEK_V4_SAMPLING };
  });
}
