import { appendFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { getAgentDir } from "@earendil-works/pi-coding-agent";

function writeAudit(record: Record<string, unknown>): void {
	const path = join(getAgentDir(), "openai-codex-thinking", "requests.ndjson");
	mkdirSync(dirname(path), { recursive: true });
	appendFileSync(path, JSON.stringify({ timestamp: new Date().toISOString(), event: "codex_reasoning_forced_none", ...record }) + "\n", "utf8");
}

export default function (_pi: ExtensionAPI) {
	(globalThis as any).__PI_OPENAI_CODEX_OFF_NONE_AUDIT = {
		record(record: Record<string, unknown>) {
			writeAudit(record);
		},
	};
}
