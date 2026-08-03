import { appendFile } from "node:fs/promises";

export const QWEN_AGENTWORLD_DEFAULT_BASH_TIMEOUT_SECONDS = 360;
export const QWEN_AGENTWORLD_BASH_TIMEOUT_AUDIT_PATH = "/out/qwen-agentworld-bash-timeout.ndjson";

type QwenAgentWorldBashTimeoutAction = "defaulted" | "preserved";
type BashToolInput = {
  command: string;
  timeout?: number;
};

/** Default a missing Qwen-AgentWorld Bash timeout while preserving model-chosen values. */
export function applyQwenAgentWorldDefaultBashTimeout(
  input: BashToolInput,
): QwenAgentWorldBashTimeoutAction {
  if (typeof input.timeout === "number") {
    return "preserved";
  }

  input.timeout = QWEN_AGENTWORLD_DEFAULT_BASH_TIMEOUT_SECONDS;
  return "defaulted";
}

/** Enforce and audit the Qwen-AgentWorld Bash timeout policy before execution. */
export default function registerQwenAgentWorldBashTimeout(
  pi,
  auditPath = QWEN_AGENTWORLD_BASH_TIMEOUT_AUDIT_PATH,
): void {
  pi.on("tool_call", async (event) => {
    if (event.toolName !== "bash") {
      return;
    }

    const input = event.input as BashToolInput;
    const action = applyQwenAgentWorldDefaultBashTimeout(input);
    const record = {
      action,
      effectiveTimeout: input.timeout,
      event: "qwen_agentworld_bash_timeout",
      toolCallId: event.toolCallId,
      toolName: "bash",
    };
    await appendFile(auditPath, `${JSON.stringify(record)}\n`, "utf8");
  });
}
