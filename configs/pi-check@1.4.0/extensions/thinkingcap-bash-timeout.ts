import { appendFile } from "node:fs/promises";

export const THINKINGCAP_DEFAULT_BASH_TIMEOUT_SECONDS = 360;
export const THINKINGCAP_BASH_TIMEOUT_AUDIT_PATH = "/out/thinkingcap-bash-timeout.ndjson";

type ThinkingCapBashTimeoutAction = "defaulted" | "preserved";
type BashToolInput = {
  command: string;
  timeout?: number;
};

/** Default a missing ThinkingCap Bash timeout while preserving model-chosen values. */
export function applyThinkingCapDefaultBashTimeout(
  input: BashToolInput,
): ThinkingCapBashTimeoutAction {
  if (typeof input.timeout === "number") {
    return "preserved";
  }

  input.timeout = THINKINGCAP_DEFAULT_BASH_TIMEOUT_SECONDS;
  return "defaulted";
}

/** Enforce and audit the ThinkingCap Bash timeout policy before execution. */
export default function registerThinkingCapBashTimeout(
  pi,
  auditPath = THINKINGCAP_BASH_TIMEOUT_AUDIT_PATH,
): void {
  pi.on("tool_call", async (event) => {
    if (event.toolName !== "bash") {
      return;
    }

    const input = event.input as BashToolInput;
    const action = applyThinkingCapDefaultBashTimeout(input);
    const record = {
      action,
      effectiveTimeout: input.timeout,
      event: "thinkingcap_bash_timeout",
      toolCallId: event.toolCallId,
      toolName: "bash",
    };
    await appendFile(auditPath, `${JSON.stringify(record)}\n`, "utf8");
  });
}
