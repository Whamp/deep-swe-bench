import { mkdirSync, appendFileSync } from "node:fs";
import { join } from "node:path";
import { getAgentDir } from "@earendil-works/pi-coding-agent";
import { fullProjection, renderSummary } from "./pi-observational-memory/src/session-ledger/index.js";

const MAX_SUMMARY_CHARS = 16000;
const HEADER = "These are condensed memories from earlier in this session.";

function toolNames(payload: any): string[] {
	const tools = payload?.tools;
	if (!Array.isArray(tools)) return [];
	return tools.map((tool: any) => tool?.function?.name ?? tool?.name).filter(Boolean).map(String);
}

function isExecutorPayload(payload: any): boolean {
	const names = toolNames(payload);
	if (names.some((name) => name.startsWith("record_") || name === "drop_observations")) return false;
	return names.some((name) => ["read", "write", "edit", "bash", "recall"].includes(name));
}

function bounded(summary: string): string {
	if (summary.length <= MAX_SUMMARY_CHARS) return summary;
	return `${HEADER}\n\n[Earlier memory summary truncated to fit this benchmark projection.]\n\n${summary.slice(-MAX_SUMMARY_CHARS)}`;
}

function log(row: Record<string, unknown>): void {
	const dir = join(getAgentDir(), "observational-memory", "projection");
	mkdirSync(dir, { recursive: true });
	appendFileSync(join(dir, "projection.ndjson"), JSON.stringify(row) + "\n");
}

export default function omLiveProjection(pi: any) {
	pi.on("before_provider_request", (event: any, ctx: any) => {
		const payload = event.payload;
		if (!payload || typeof payload !== "object" || !Array.isArray(payload.messages)) return;
		if (!isExecutorPayload(payload)) return;
		if (JSON.stringify(payload.messages).includes(HEADER)) return;

		const entries = ctx?.sessionManager?.getBranch?.() ?? [];
		const projection = fullProjection(entries);
		const summary = bounded(renderSummary(projection.reflections, projection.observations));
		const injected = summary.length > 0;
		log({
			event: "projected-om.before_provider_request",
			injected,
			observations: projection.observations.length,
			reflections: projection.reflections.length,
			summaryChars: summary.length,
		});
		if (!injected) return;

		return {
			...payload,
			messages: [{ role: "system", content: summary }, ...payload.messages],
		};
	});
}
