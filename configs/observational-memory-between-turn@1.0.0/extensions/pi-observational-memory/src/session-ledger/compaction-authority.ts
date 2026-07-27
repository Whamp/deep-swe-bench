import {
	entryIndexById,
	findLastCompactionIndex,
	isSourceEntry,
} from "./progress.js";
import {
	isObserverCompletedEntry,
	isObservationsRecordedEntry,
	type Entry,
} from "./types.js";

/** The participant allowed to provide one prepared compaction summary. */
export interface CompactionAuthorityDecision {
	owner: "observational-memory" | "host";
	reason: "covered" | "uncovered" | "boundary-unresolved" | "no-pruned-source";
	coverageBoundaryId?: string;
	pruneBoundaryId?: string;
}

/**
 * Decides whether trustworthy source coverage reaches the current prune boundary.
 * Authority validation is intentionally stricter than scheduling progress: every
 * marker must point backward to an existing source entry.
 */
export function compactionAuthority(
	entries: Entry[],
	firstKeptEntryId: string,
): CompactionAuthorityDecision {
	const indexes = entryIndexById(entries);
	const firstKeptIndex = indexes.get(firstKeptEntryId);
	if (firstKeptIndex === undefined) {
		return { owner: "host", reason: "boundary-unresolved" };
	}

	const previousCompactionIndex = findLastCompactionIndex(entries);
	const previousFirstKeptIndex = previousCompactionIndex === -1
		? -1
		: indexes.get(entries[previousCompactionIndex].firstKeptEntryId ?? "") ?? -1;
	const pruneRangeStart = previousCompactionIndex === -1
		? 0
		: previousFirstKeptIndex >= 0
			? previousFirstKeptIndex
			: previousCompactionIndex + 1;

	let pruneBoundaryIndex = -1;
	for (let i = firstKeptIndex - 1; i >= pruneRangeStart; i--) {
		if (isSourceEntry(entries[i])) {
			pruneBoundaryIndex = i;
			break;
		}
	}
	if (pruneBoundaryIndex === -1) {
		return { owner: "host", reason: "no-pruned-source" };
	}

	let coverageBoundaryIndex = -1;
	for (let i = 0; i < entries.length; i++) {
		const entry = entries[i];
		if (!isObservationsRecordedEntry(entry) && !isObserverCompletedEntry(entry)) {
			continue;
		}
		const coveredIndex = indexes.get(entry.data.coversUpToId);
		if (
			coveredIndex !== undefined &&
			coveredIndex < i &&
			isSourceEntry(entries[coveredIndex]) &&
			coveredIndex > coverageBoundaryIndex
		) {
			coverageBoundaryIndex = coveredIndex;
		}
	}

	const coverageBoundaryId = entries[coverageBoundaryIndex]?.id;
	const pruneBoundaryId = entries[pruneBoundaryIndex].id;
	if (coverageBoundaryIndex >= pruneBoundaryIndex) {
		return {
			owner: "observational-memory",
			reason: "covered",
			coverageBoundaryId,
			pruneBoundaryId,
		};
	}
	return {
		owner: "host",
		reason: "uncovered",
		coverageBoundaryId,
		pruneBoundaryId,
	};
}
