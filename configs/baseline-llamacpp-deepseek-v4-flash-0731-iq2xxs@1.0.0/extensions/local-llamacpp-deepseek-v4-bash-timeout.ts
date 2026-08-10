import { appendFile } from "node:fs/promises";

export const LLAMACPP_DEEPSEEK_V4_DEFAULT_BASH_TIMEOUT_SECONDS = 360;
export const LLAMACPP_DEEPSEEK_V4_BASH_TIMEOUT_AUDIT_PATH =
  "/out/llamacpp-deepseek-v4-bash-timeout.ndjson";

type LlamacppDeepSeekV4BashTimeoutAction = "defaulted" | "preserved";
type BashToolInput = {
  command: string;
  timeout?: number;
};

/**
 * Default a missing Bash timeout while preserving model-chosen values. Local
 * models (e.g. agentworld, gemma-4, thinking-cap) have been observed to omit the
 * timeout argument and get permanently blocked; this guarantees one is present.
 */
export function applyLlamacppDeepSeekV4DefaultBashTimeout(
  input: BashToolInput,
): LlamacppDeepSeekV4BashTimeoutAction {
  if (typeof input.timeout === "number") {
    return "preserved";
  }

  input.timeout = LLAMACPP_DEEPSEEK_V4_DEFAULT_BASH_TIMEOUT_SECONDS;
  return "defaulted";
}

/** Enforce and audit the Bash timeout policy before each Bash execution. */
export default function registerLlamacppDeepSeekV4BashTimeout(
  pi,
  auditPath = LLAMACPP_DEEPSEEK_V4_BASH_TIMEOUT_AUDIT_PATH,
): void {
  pi.on("tool_call", async (event) => {
    if (event.toolName !== "bash") {
      return;
    }

    const input = event.input as BashToolInput;
    const action = applyLlamacppDeepSeekV4DefaultBashTimeout(input);
    const record = {
      action,
      effectiveTimeout: input.timeout,
      event: "llamacpp_deepseek_v4_bash_timeout",
      toolCallId: event.toolCallId,
      toolName: "bash",
    };
    await appendFile(auditPath, `${JSON.stringify(record)}\n`, "utf8");
  });
}
