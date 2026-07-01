import fs from "node:fs";

const SENTINEL = process.env.OM_VISIBILITY_SENTINEL ?? "OM_VISIBILITY_SENTINEL_UNSET";
const LOG_PATH = process.env.OM_VISIBILITY_PAYLOAD_LOG;

function namesFromPayload(payload: any): string[] {
  const tools = payload?.tools ?? [];
  if (!Array.isArray(tools)) return [];
  return tools.map((tool: any) => tool?.function?.name ?? tool?.name).filter(Boolean);
}

function textOf(value: unknown): string {
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

export default function payloadCapture(pi: any) {
  let seq = 0;
  pi.on("before_provider_request", (event: any, ctx: any) => {
    if (!LOG_PATH) return;
    const payload = event.payload;
    const serialized = textOf(payload);
    const toolNames = namesFromPayload(payload);
    const role = toolNames.some((name) => String(name).startsWith("record_") || name === "drop_observations")
      ? "om_worker"
      : "executor";
    const row = {
      seq: ++seq,
      role,
      mode: ctx?.mode,
      model: payload?.model,
      messageCount: Array.isArray(payload?.messages) ? payload.messages.length : undefined,
      toolNames,
      containsSentinel: serialized.includes(SENTINEL),
      containsObservationId: serialized.includes("abc123abc123"),
      containsOmSummaryHeader: serialized.includes("These are condensed memories from earlier in this session")
        || serialized.includes("## Observations")
        || serialized.includes("## Reflections"),
      payload,
    };
    fs.appendFileSync(LOG_PATH, JSON.stringify(row) + "\n");
  });
}
