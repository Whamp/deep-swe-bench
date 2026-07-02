import { constants, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { accessSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const LOCK_RETRY_MS = 10;
const LOCK_RETRIES = 500;

function sleep(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseNumber(value: string | undefined): number | undefined {
	if (!value) return undefined;
	const parsed = Number.parseFloat(value);
	return Number.isFinite(parsed) ? parsed : undefined;
}

function readCounter(filePath: string): number {
	if (!existsSync(filePath)) {
		return Number.parseInt(process.env.RLM_CALL_COUNT || "0", 10) || 0;
	}
	const raw = readFileSync(filePath, "utf8").trim();
	return Number.parseInt(raw || "0", 10) || 0;
}

export async function allocateCallCount(): Promise<number> {
	const counterFile = process.env.RLM_CALL_COUNTER_FILE || path.join(tmpdir(), "rlm_calls_default.counter");
	process.env.RLM_CALL_COUNTER_FILE = counterFile;
	const lockDir = `${counterFile}.lock`;
	mkdirSync(path.dirname(counterFile), { recursive: true });

	for (let attempt = 0; attempt < LOCK_RETRIES; attempt++) {
		try {
			mkdirSync(lockDir);
			try {
				const next = readCounter(counterFile) + 1;
				writeFileSync(counterFile, `${next}\n`);
				process.env.RLM_CALL_COUNT = String(next);
				return next;
			} finally {
				rmSync(lockDir, { recursive: true, force: true });
			}
		} catch (error) {
			const code = (error as NodeJS.ErrnoException).code;
			if (code !== "EEXIST") throw error;
			await sleep(LOCK_RETRY_MS);
		}
	}

	throw new Error(`Timed out waiting for call counter lock: ${lockDir}`);
}

export function assertWithinMaxCalls(callCount: number): void {
	const maxCalls = Number.parseInt(process.env.RLM_MAX_CALLS || "", 10);
	// callCount is the 1-based number of the call being allocated, so RLM_MAX_CALLS=N
	// must permit calls 1..N and only reject call N+1.
	if (Number.isFinite(maxCalls) && callCount > maxCalls) {
		throw new Error(`Max calls exceeded: ${maxCalls} of ${maxCalls} calls already used. Increase RLM_MAX_CALLS or reduce recursion depth.`);
	}
}

export function remainingTimeoutSeconds(): number | undefined {
	const timeout = Number.parseInt(process.env.RLM_TIMEOUT || "", 10);
	if (!Number.isFinite(timeout)) {
		return undefined;
	}
	const start = Number.parseInt(process.env.RLM_START_TIME || `${Math.floor(Date.now() / 1000)}`, 10);
	const elapsed = Math.floor(Date.now() / 1000) - start;
	return timeout - elapsed;
}

export function assertTimeoutAvailable(): number | undefined {
	const remaining = remainingTimeoutSeconds();
	if (remaining !== undefined && remaining <= 0) {
		const timeout = process.env.RLM_TIMEOUT || "0";
		throw new Error(`Timeout exceeded: no time remains from RLM_TIMEOUT=${timeout}. Increase RLM_TIMEOUT or simplify the task.`);
	}
	return remaining;
}

export interface CostSummary {
	cost: number;
	tokens: number;
}

export function readCostSummary(costFile = process.env.RLM_COST_FILE): CostSummary {
	if (!costFile || !existsSync(costFile)) {
		return { cost: 0, tokens: 0 };
	}

	let cost = 0;
	let tokens = 0;
	for (const line of readFileSync(costFile, "utf8").split(/\r?\n/)) {
		if (!line.trim()) continue;
		try {
			const parsed = JSON.parse(line);
			cost += Number(parsed.cost || 0);
			tokens += Number(parsed.tokens || 0);
		} catch {
			// Ignore malformed cost lines; this matches rlm_cost's tolerant parser.
		}
	}
	return { cost, tokens };
}

// Best-effort: the tool runs in parallel executionMode and cost is recorded only after a
// child finishes, so concurrent calls can each pass this check before any cost lands and a
// tree may slightly overshoot RLM_BUDGET. The race-free hard ceiling is RLM_MAX_CALLS.
export function assertBudgetAvailable(): void {
	const budget = parseNumber(process.env.RLM_BUDGET);
	if (budget === undefined) {
		return;
	}
	if (process.env.RLM_JSON === "0") {
		throw new Error("RLM_BUDGET requires RLM_JSON=1 in native extension mode so child Pi cost can be measured.");
	}
	const current = readCostSummary();
	if (current.cost >= budget) {
		throw new Error(`Budget exceeded: spent $${current.cost.toFixed(6)} of $${budget.toFixed(6)} budget. Increase RLM_BUDGET or simplify the task.`);
	}
}

export function appendCostSummary(summary: CostSummary): void {
	if (!process.env.RLM_COST_FILE) {
		return;
	}
	writeFileSync(process.env.RLM_COST_FILE, `${JSON.stringify(summary)}\n`, { flag: "a" });
}

export function canExecute(filePath: string): boolean {
	try {
		accessSync(filePath, constants.X_OK);
		return true;
	} catch {
		return false;
	}
}
