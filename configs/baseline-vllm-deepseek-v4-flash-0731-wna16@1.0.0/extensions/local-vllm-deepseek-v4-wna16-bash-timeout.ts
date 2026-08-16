import { appendFile } from "node:fs/promises";

export const LOCAL_VLLM_DEEPSEEK_V4_WNA16_DEFAULT_BASH_TIMEOUT_SECONDS = 360;
export const LOCAL_VLLM_DEEPSEEK_V4_WNA16_BASH_TIMEOUT_AUDIT_PATH =
  "/out/local-vllm-deepseek-v4-wna16-bash-timeout.ndjson";

type LocalVllmDeepSeekV4Wna16BashTimeoutAction = "defaulted" | "preserved";
type BashToolInput = {
  command: string;
  timeout?: number;
};

/** Defaults a missing bash timeout while preserving model-selected values. */
export function applyLocalVllmDeepSeekV4Wna16DefaultBashTimeout(
  input: BashToolInput,
): LocalVllmDeepSeekV4Wna16BashTimeoutAction {
  if (typeof input.timeout === "number") {
    return "preserved";
  }

  input.timeout = LOCAL_VLLM_DEEPSEEK_V4_WNA16_DEFAULT_BASH_TIMEOUT_SECONDS;
  return "defaulted";
}

/** Enforces and audits the bash timeout policy before each bash execution. */
export default function registerLocalVllmDeepSeekV4Wna16BashTimeout(
  pi,
  auditPath = LOCAL_VLLM_DEEPSEEK_V4_WNA16_BASH_TIMEOUT_AUDIT_PATH,
): void {
  pi.on("tool_call", async (event) => {
    if (event.toolName !== "bash") {
      return;
    }

    const input = event.input as BashToolInput;
    const action = applyLocalVllmDeepSeekV4Wna16DefaultBashTimeout(input);
    const record = {
      action,
      effectiveTimeout: input.timeout,
      event: "local_vllm_deepseek_v4_wna16_bash_timeout",
      toolCallId: event.toolCallId,
      toolName: "bash",
    };
    await appendFile(auditPath, `${JSON.stringify(record)}\n`, "utf8");
  });
}
