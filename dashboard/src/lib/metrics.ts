// Pure utility functions for metrics, formatting, and Pareto frontier computation.
// These are heavily unit + property tested.

export interface ParetoPoint {
  id: string;
  cost: number; // lower is better
  value: number; // higher is better
  [key: string]: unknown;
}

/**
 * Compute the Pareto frontier: the set of points where no other point is both
 * cheaper AND higher-value. A point A dominates point B if A.cost <= B.cost AND
 * A.value >= B.value, with at least one strict inequality.
 *
 * Points with NaN/null/undefined cost or value are excluded from the frontier
 * but kept in the output (isPareto=false).
 */
export function paretoFrontier<T extends ParetoPoint>(
  points: T[],
): Array<T & { isPareto: boolean }> {
  const valid = points.filter(
    (p) => Number.isFinite(p.cost) && Number.isFinite(p.value) && p.cost >= 0,
  );

  return points.map((p) => {
    const isValid = Number.isFinite(p.cost) && Number.isFinite(p.value) && p.cost >= 0;
    if (!isValid) return { ...p, isPareto: false };
    const dominated = valid.some(
      (other) =>
        other.id !== p.id &&
        other.cost <= p.cost &&
        other.value >= p.value &&
        (other.cost < p.cost || other.value > p.value),
    );
    return { ...p, isPareto: !dominated };
  });
}

/**
 * Compute median of an array of numbers. Returns 0 for empty input.
 * NaN/null/undefined values are filtered out.
 */
export function median(values: number[]): number {
  const valid = values.filter((v) => Number.isFinite(v));
  if (valid.length === 0) return 0;
  const sorted = [...valid].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1]! + sorted[mid]!) / 2 : sorted[mid]!;
}

/**
 * Compute mean of an array of numbers. Returns 0 for empty input.
 * NaN/null/undefined values are filtered out.
 */
export function mean(values: number[]): number {
  const valid = values.filter((v) => Number.isFinite(v));
  if (valid.length === 0) return 0;
  return valid.reduce((sum, v) => sum + v, 0) / valid.length;
}

/**
 * Compute sum of an array of numbers. Returns 0 for empty input.
 * NaN/null/undefined values are treated as 0.
 */
export function sum(values: number[]): number {
  return values.reduce((acc, v) => acc + (Number.isFinite(v) ? v : 0), 0);
}

/**
 * Compute solve rate: fraction of cells with reward_binary >= 1.
 * Returns 0 for empty input.
 */
export function solveRate(binaries: number[]): number {
  const valid = binaries.filter((v) => Number.isFinite(v));
  if (valid.length === 0) return 0;
  return valid.filter((v) => v >= 1).length / valid.length;
}

/**
 * Pick a baseline comparison group from cross-run data for a live run.
 *
 * Matches a DIFFERENT config on the same model+thinking with the best task
 * coverage of the live run's task set (>=50% coverage to qualify). The model
 * is matched on its basename so a provider-qualified manifest model (e.g.
 * `openai-codex/gpt-5.6-sol`) still matches the results-directory group name
 * (`gpt-5.6-sol`). Returns the baseline's solve rate over the shared task set
 * and the per-task flip set so the UI can show a live delta. Returns null when
 * no confident match exists.
 */
export interface BaselineChoice {
  label: string;
  solveRate: number; // 0-100 over shared tasks
  sharedTasks: number;
  coverage: number; // 0-1 fraction of the live run's tasks the baseline covers
  solvedSet: Set<string>;
}

function modelBasename(model: string | null): string | null {
  if (!model) return null;
  const slash = model.lastIndexOf("/");
  return slash >= 0 ? model.slice(slash + 1) : model;
}

export function pickBaseline(
  groups: Array<{
    run_id: string;
    model: string | null;
    thinking: string | null;
    config: string;
    cells: Array<{ task: string; reward_binary: number }>;
  }>,
  runModel: string | null,
  runThinking: string | null,
  runConfig: string | null,
  runTasks: string[],
): BaselineChoice | null {
  if (!runTasks.length) return null;
  const taskSet = new Set(runTasks);
  const wantModel = modelBasename(runModel);
  let best: BaselineChoice | null = null;
  for (const g of groups) {
    if (runConfig && g.config === runConfig) continue;
    if (wantModel && modelBasename(g.model) !== wantModel) continue;
    if (runThinking && g.thinking !== runThinking) continue;
    const shared = g.cells.filter((c) => taskSet.has(c.task));
    const coverage = shared.length / runTasks.length;
    if (coverage < 0.5) continue;
    // Per-task solve = any rep solved.
    const solved = new Set<string>();
    const seen = new Set<string>();
    for (const c of shared) {
      seen.add(c.task);
      if (c.reward_binary >= 1) solved.add(c.task);
    }
    const rate = (solved.size / seen.size) * 100;
    const choice: BaselineChoice = {
      label: g.config,
      solveRate: Number.isFinite(rate) ? rate : 0,
      sharedTasks: seen.size,
      coverage,
      solvedSet: solved,
    };
    if (
      !best ||
      coverage > best.coverage ||
      (coverage === best.coverage && choice.sharedTasks > best.sharedTasks)
    ) {
      best = choice;
    }
  }
  return best;
}

/**
 * Colour band for a solve-rate glance: green/amber/red. Used by the live-score
 * hero and the overview cards so the colour language is consistent everywhere.
 */
export function rateColor(rate: number): string {
  if (rate >= 50) return "text-green-400";
  if (rate >= 25) return "text-amber-400";
  return "text-red-400";
}

export function fmtSeconds(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return "—";
  if (v < 60) return `${Math.round(v)}s`;
  if (v < 3600) return `${Math.round(v / 60)}m`;
  return `${(v / 3600).toFixed(1)}h`;
}

export function fmtTokens(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return "—";
  if (v < 1000) return `${Math.round(v)}`;
  if (v < 1_000_000) return `${(v / 1000).toFixed(1)}k`;
  return `${(v / 1_000_000).toFixed(2)}M`;
}

export function fmtCost(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return "—";
  if (v === 0) return "$0";
  if (v < 0.01) return `$${v.toFixed(4)}`;
  if (v < 1) return `$${v.toFixed(3)}`;
  return `$${v.toFixed(2)}`;
}

export function fmtPercent(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return "—";
  return `${(v * 100).toFixed(digits)}%`;
}

/**
 * Classify a pass rate (0-100) into a difficulty bucket.
 * hard: <33, medium: 33-66, easy: >=66
 */
export function difficultyBucket(passRate: number): "hard" | "medium" | "easy" | "unknown" {
  if (!Number.isFinite(passRate)) return "unknown";
  if (passRate < 33) return "hard";
  if (passRate < 66) return "medium";
  return "easy";
}

/**
 * Compute cell age in seconds from a started_at ISO timestamp.
 * Returns null if the timestamp is invalid or in the future.
 */
export function cellAgeS(
  startedAt: string | null | undefined,
  now: number = Date.now(),
): number | null {
  if (!startedAt) return null;
  const started = new Date(startedAt).getTime();
  if (!Number.isFinite(started)) return null;
  const age = (now - started) / 1000;
  return age >= 0 ? age : null;
}
