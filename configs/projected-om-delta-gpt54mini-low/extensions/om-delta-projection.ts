import { mkdirSync, appendFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { getAgentDir } from "@earendil-works/pi-coding-agent";
import {
	OM_OBSERVATIONS_DROPPED,
	OM_OBSERVATIONS_RECORDED,
	OM_REFLECTIONS_RECORDED,
	isObservationsDroppedEntry,
	isObservationsRecordedEntry,
	isReflectionsRecordedEntry,
	observationToSummaryLine,
	reflectionToSummaryLine,
	type Entry,
	type Observation,
	type Reflection,
} from "./pi-observational-memory/src/session-ledger/index.js";

const CUSTOM_TYPE = "om.delta_projection";
const MAX_UPDATE_CHARS = 12000;

type Published = {
	observationIds: Set<string>;
	reflectionIds: Set<string>;
	droppedObservationIds: Set<string>;
};

type Delta = {
	observations: Observation[];
	reflections: Reflection[];
	droppedObservationIds: string[];
};

function sha256(text: string): string {
	return createHash("sha256").update(text).digest("hex");
}

function stringArray(value: unknown): string[] {
	return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function log(row: Record<string, unknown>): void {
	const dir = join(getAgentDir(), "observational-memory", "projection");
	mkdirSync(dir, { recursive: true });
	appendFileSync(join(dir, "projection.ndjson"), JSON.stringify(row) + "\n");
}

function publishedFrom(entries: Entry[]): Published {
	const published: Published = {
		observationIds: new Set(),
		reflectionIds: new Set(),
		droppedObservationIds: new Set(),
	};

	for (const entry of entries) {
		if (entry.type !== "custom_message" || entry.customType !== CUSTOM_TYPE) continue;
		const details = entry.details as Record<string, unknown> | undefined;
		for (const id of stringArray(details?.observationIds)) published.observationIds.add(id);
		for (const id of stringArray(details?.reflectionIds)) published.reflectionIds.add(id);
		for (const id of stringArray(details?.droppedObservationIds)) published.droppedObservationIds.add(id);
	}

	return published;
}

function collectDelta(entries: Entry[], published: Published): Delta {
	const observations: Observation[] = [];
	const reflections: Reflection[] = [];
	const droppedObservationIds: string[] = [];

	for (const entry of entries) {
		if (isObservationsRecordedEntry(entry)) {
			for (const observation of entry.data.observations) {
				if (published.observationIds.has(observation.id)) continue;
				published.observationIds.add(observation.id);
				observations.push(observation);
			}
			continue;
		}

		if (isReflectionsRecordedEntry(entry)) {
			for (const reflection of entry.data.reflections) {
				if (published.reflectionIds.has(reflection.id)) continue;
				published.reflectionIds.add(reflection.id);
				reflections.push(reflection);
			}
			continue;
		}

		if (isObservationsDroppedEntry(entry)) {
			for (const observationId of entry.data.observationIds) {
				if (published.droppedObservationIds.has(observationId)) continue;
				published.droppedObservationIds.add(observationId);
				droppedObservationIds.push(observationId);
			}
		}
	}

	return { observations, reflections, droppedObservationIds };
}

function renderDelta(delta: Delta): string {
	const parts: string[] = [
		`<observational-memory-update>\nNew condensed memories from earlier in this same task trajectory. Treat these as append-only context; later updates supersede older conflicting records. Use recall(<id>) only if exact source context is needed.`,
	];

	if (delta.reflections.length > 0) {
		parts.push(`## New reflections\n${delta.reflections.map(reflectionToSummaryLine).join("\n")}`);
	}
	if (delta.observations.length > 0) {
		parts.push(`## New observations\n${delta.observations.map(observationToSummaryLine).join("\n")}`);
	}
	if (delta.droppedObservationIds.length > 0) {
		parts.push(
			`## Superseded observations\nThe following observation ids were dropped by observational memory and should be treated as superseded unless recalled for audit: ${delta.droppedObservationIds.map((id) => `[${id}]`).join(", ")}`,
		);
	}

	let content = `${parts.join("\n\n")}\n</observational-memory-update>`;
	if (content.length <= MAX_UPDATE_CHARS) return content;

	const keep = Math.max(0, MAX_UPDATE_CHARS - 220);
	content = `${parts[0]}\n\n[This memory update was truncated to keep the benchmark projection bounded; newest records are retained.]\n\n${content.slice(-keep)}`;
	return content;
}

function hasDelta(delta: Delta): boolean {
	return delta.observations.length > 0 || delta.reflections.length > 0 || delta.droppedObservationIds.length > 0;
}

export default function omDeltaProjection(pi: any) {
	pi.on("context", (event: any, ctx: any) => {
		const entries = (ctx?.sessionManager?.getBranch?.() ?? []) as Entry[];
		const published = publishedFrom(entries);
		const delta = collectDelta(entries, published);
		const injected = hasDelta(delta);

		if (!injected) {
			log({
				event: "om-delta-projection.context",
				injected: false,
				observations: 0,
				reflections: 0,
				droppedObservations: 0,
			});
			return undefined;
		}

		const content = renderDelta(delta);
		const details = {
			version: 1,
			mode: "append-only-delta",
			observationIds: delta.observations.map((observation) => observation.id),
			reflectionIds: delta.reflections.map((reflection) => reflection.id),
			droppedObservationIds: delta.droppedObservationIds,
			contentSha256: sha256(content),
			contentChars: content.length,
		};

		const entryId = ctx.sessionManager.appendCustomMessageEntry(CUSTOM_TYPE, content, false, details);
		log({
			event: "om-delta-projection.context",
			injected: true,
			customMessageEntryId: entryId,
			observations: delta.observations.length,
			reflections: delta.reflections.length,
			droppedObservations: delta.droppedObservationIds.length,
			contentChars: content.length,
			contentSha256: details.contentSha256,
		});

		return {
			messages: [
				...event.messages,
				{
					role: "custom",
					customType: CUSTOM_TYPE,
					content,
					display: false,
					details,
					timestamp: Date.now(),
				},
			],
		};
	});
}
