interface WorkerUsageTraceModel {
	provider: string;
	id: string;
	api?: string;
}

interface WorkerUsageTraceEvent {
	stage: "observer" | "reflector" | "dropper";
	model: WorkerUsageTraceModel;
	thinkingLevel: string;
	event: unknown;
}

interface WorkerUsageTraceRecorder {
	recordAgentEvent(input: WorkerUsageTraceEvent): void;
}

declare global {
	var __PI_OM_WORKER_USAGE_TRACE: WorkerUsageTraceRecorder | undefined;
}

/** Forwards one nested observational-memory worker event to config-owned usage accounting. */
export function recordObservationalMemoryWorkerUsage(input: WorkerUsageTraceEvent): void {
	globalThis.__PI_OM_WORKER_USAGE_TRACE?.recordAgentEvent(input);
}
