
import {
	debugLog,
	withDebugLogContext,
	type DebugLogContext,
} from "../debug-log.js";
import type { Runtime } from "../runtime.js";
import {
	buildCompactionProjection,
	compactionAuthority,
	renderSummary,
	type Entry,
	type MemoryDetails,
} from "../session-ledger/index.js";

const DEFAULT_OBSERVATIONS_POOL_MAX_TOKENS = 20_000;

interface CompactionHookEvent {
	preparation: {
		firstKeptEntryId: string;
		tokensBefore: number;
	};
	branchEntries: Entry[];
}

interface CompactionHookContext {
	cwd: string;
	hasUI: boolean;
	ui: {
		notify(message: string, type?: "warning" | "info" | "error"): void;
	};
	sessionManager: {
		getSessionId(): string;
		getSessionFile(): string | undefined;
	};
}

interface CompactionHookResult {
	cancel?: boolean;
	compaction?: {
		summary: string;
		firstKeptEntryId: string;
		tokensBefore: number;
		details: MemoryDetails;
	};
}

interface CompactionHookApi {
	on(
		event: "session_before_compact",
		handler: (
			event: CompactionHookEvent,
			ctx: CompactionHookContext,
		) => Promise<CompactionHookResult>,
	): void;
}

function observationsPoolMaxTokens(runtime: Runtime): number {
	const value = (runtime.config as { observationsPoolMaxTokens?: unknown }).observationsPoolMaxTokens;
	return typeof value === "number" && Number.isFinite(value) && value > 0
		? value
		: DEFAULT_OBSERVATIONS_POOL_MAX_TOKENS;
}

function compactionDebugContext(runtime: Runtime, ctx: CompactionHookContext): DebugLogContext {
	const context: DebugLogContext = {
		enabled: runtime.config.debugLog === true,
		cwd: ctx.cwd,
	};
	if (!context.enabled) {
		return context;
	}
	try {
		return {
			...context,
			sessionId: ctx.sessionManager.getSessionId(),
			sessionFile: ctx.sessionManager.getSessionFile(),
		};
	} catch {
		// Debug metadata is best-effort and must never prevent compaction.
		return context;
	}
}

/** Registers coverage-gated ownership for Pi compaction summaries. */
export function registerCompactionHook(pi: CompactionHookApi, runtime: Runtime): void {
	pi.on("session_before_compact", async (event, ctx) => {
		if (runtime.compactHookInFlight) {
			if (ctx.hasUI) {
				ctx.ui.notify(
					"Observational memory: another compaction is already in progress; cancelling duplicate",
					"warning",
				);
			}
			return { cancel: true };
		}

		runtime.compactHookInFlight = true;
		try {
			runtime.ensureConfig(ctx.cwd);
			const { preparation, branchEntries } = event;
			const { firstKeptEntryId, tokensBefore } = preparation;
			const entries = branchEntries;
			const authority = withDebugLogContext(
				compactionDebugContext(runtime, ctx),
				() => {
					const decision = compactionAuthority(entries, firstKeptEntryId);
					debugLog("compaction.authority", {
						owner: decision.owner,
						reason: decision.reason,
						coverageBoundaryId: decision.coverageBoundaryId,
						pruneBoundaryId: decision.pruneBoundaryId,
					});
					return decision;
				},
			);
			if (authority.owner === "host") {
				return {};
			}
			const projection = buildCompactionProjection(
				entries,
				firstKeptEntryId,
				{ observationsPoolMaxTokens: observationsPoolMaxTokens(runtime) },
			);
			const summary = renderSummary(projection.reflections, projection.observations);

			return {
				compaction: {
					summary,
					firstKeptEntryId,
					tokensBefore,
					details: projection.details,
				},
			};
		} finally {
			runtime.compactHookInFlight = false;
		}
	});
}
