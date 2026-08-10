const DEEPSEEK_V4_PROVIDER = "local-llamacpp";
const DEEPSEEK_V4_MODEL = "deepseek-v4-flash-0731-q8-fast-prefill";

/**
 * Agentic sampling profile per the official DeepSeek-V4-Flash-0731 model card
 * ("temperature = 1.0, top_p = 0.95 for agentic scenarios"). top_k/min_p/
 * repeat_penalty are disabled so only temperature + top_p apply, matching the
 * OpenRouter API baseline and overriding the server's non-agentic defaults.
 */
const DEEPSEEK_V4_SAMPLING = {
  temperature: 1.0,
  top_p: 0.95,
  top_k: 0,
  min_p: 0.0,
  repeat_penalty: 1.0,
};

/** Pins the live llama.cpp DeepSeek V4 Flash 0731 agentic sampling profile. */
export default function pinLlamacppDeepSeekV4Request(pi) {
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
