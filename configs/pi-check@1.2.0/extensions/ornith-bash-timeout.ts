import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { appendFile } from "node:fs/promises";

export const ORNITH_DEFAULT_BASH_TIMEOUT_SECONDS = 360;
export const ORNITH_BASH_TIMEOUT_AUDIT_PATH = "/out/ornith-bash-timeout.ndjson";

type OrnithBashTimeoutAction = "defaulted" | "preserved";
type BashToolInput = {
  command: string;
  timeout?: number;
};

/** Default a missing Bash timeout while preserving a model-chosen timeout. */
export function applyOrnithDefaultBashTimeout(input: BashToolInput): OrnithBashTimeoutAction {
  if (typeof input.timeout === "number") {
    return "preserved";
  }

  input.timeout = ORNITH_DEFAULT_BASH_TIMEOUT_SECONDS;
  return "defaulted";
}

/** Enforce and audit the Ornith Bash timeout policy before each Bash execution. */
export default function registerOrnithBashTimeout(
  pi: ExtensionAPI,
  auditPath = ORNITH_BASH_TIMEOUT_AUDIT_PATH,
): void {
  pi.on("tool_call", async (event) => {
    if (event.toolName !== "bash") {
      return;
    }

    const input = event.input as BashToolInput;
    const action = applyOrnithDefaultBashTimeout(input);
    const record = {
      action,
      effectiveTimeout: input.timeout,
      event: "ornith_bash_timeout",
      toolCallId: event.toolCallId,
      toolName: "bash",
    };
    await appendFile(auditPath, `${JSON.stringify(record)}\n`, "utf8");
  });
}
