import type { ComparisonRun } from "@/lib/types";
import { paretoFrontier } from "@/lib/metrics";

/** Decision-ready comparison row with explicit rep/task, cost, and token semantics. */
export interface LeaderboardRow extends ComparisonRun {
  group_key: string;
  task_solved: number;
  task_total: number;
  task_solve_rate: number;
  cost_per_successful_rep: number | null;
  cost_tracked: boolean;
  full_coverage: boolean;
  is_baseline: boolean;
  baseline_run_id: string | null;
  baseline_delta: number | null;
  sample_label: string;
}

/** Four measured leaderboard callouts; no statistical significance is implied. */
export interface LeaderboardHighlights {
  balanced_pick: LeaderboardRow | null;
  best_solve: LeaderboardRow | null;
  best_value: LeaderboardRow | null;
  biggest_lift: LeaderboardRow | null;
}

function leaderboardGroupKey(run: Pick<ComparisonRun, "model" | "thinking">): string {
  return `${run.model ?? "unknown"}/${run.thinking ?? "unknown"}`;
}

function taskSolveSummary(run: ComparisonRun): {
  solved: number;
  total: number;
  rate: number;
} {
  const tasks = new Map<string, boolean>();
  for (const cell of run.cells) {
    tasks.set(cell.task, (tasks.get(cell.task) ?? false) || Number(cell.reward_binary) >= 1);
  }
  const solved = [...tasks.values()].filter(Boolean).length;
  const total = tasks.size;
  return {
    solved,
    total,
    rate: total > 0 ? (solved / total) * 100 : 0,
  };
}

function leaderboardSampleLabel(run: ComparisonRun): string {
  const tasks = run.distinct_tasks;
  if (tasks > 0 && run.total_cells % tasks === 0) {
    const reps = run.total_cells / tasks;
    return `${tasks} tasks × ${reps} ${reps === 1 ? "rep" : "reps"}`;
  }
  return `${tasks} tasks · ${run.total_cells} reps`;
}

/**
 * Derive task-level coverage, cost efficiency, and same-group baseline deltas.
 * The canonical baseline is the exact `baseline` config within model+thinking.
 */
export function deriveLeaderboardRows(runs: ComparisonRun[], subsetSize: number): LeaderboardRow[] {
  const canonicalBaselines = new Map<string, ComparisonRun>();
  for (const run of runs) {
    if (run.config !== "baseline") continue;
    const key = leaderboardGroupKey(run);
    const current = canonicalBaselines.get(key);
    if (
      !current ||
      run.distinct_tasks > current.distinct_tasks ||
      (run.distinct_tasks === current.distinct_tasks && run.total_cells > current.total_cells)
    ) {
      canonicalBaselines.set(key, run);
    }
  }

  return runs.map((run) => {
    const groupKey = leaderboardGroupKey(run);
    const baseline = canonicalBaselines.get(groupKey);
    const taskSummary = taskSolveSummary(run);
    const costTracked = Number.isFinite(run.median_cost) && run.median_cost > 0;
    return {
      ...run,
      group_key: groupKey,
      task_solved: taskSummary.solved,
      task_total: taskSummary.total,
      task_solve_rate: taskSummary.rate,
      cost_per_successful_rep: costTracked && run.solved > 0 ? run.total_cost / run.solved : null,
      cost_tracked: costTracked,
      full_coverage: subsetSize <= 0 || run.distinct_tasks >= subsetSize,
      is_baseline: run.config === "baseline",
      baseline_run_id: baseline?.run_id ?? null,
      baseline_delta: baseline ? run.solve_rate - baseline.solve_rate : null,
      sample_label: leaderboardSampleLabel(run),
    };
  });
}

export type LeaderboardCostMetric = "cost_per_successful_rep" | "median_cost";

/** Full-coverage, cost-tracked Pareto frontier for the named cost axis. */
export function leaderboardCostFrontier(
  rows: LeaderboardRow[],
  costMetric: LeaderboardCostMetric,
): LeaderboardRow[] {
  const eligible = rows.filter((row) => {
    const cost = row[costMetric];
    return row.full_coverage && row.cost_tracked && cost != null && cost > 0;
  });
  const frontier = paretoFrontier(
    eligible.map((row) => ({
      id: row.run_id,
      cost: row[costMetric]!,
      value: row.solve_rate,
      row,
    })),
  );
  return frontier.filter((point) => point.isPareto).map((point) => point.row);
}

/** Frontier used by the balanced/value cards: rep solve rate vs cost per successful rep. */
export function leaderboardValueFrontier(rows: LeaderboardRow[]): LeaderboardRow[] {
  return leaderboardCostFrontier(rows, "cost_per_successful_rep");
}

/** Select explicit measured highlights from full-coverage comparison rows. */
export function selectLeaderboardHighlights(rows: LeaderboardRow[]): LeaderboardHighlights {
  const eligible = rows.filter((row) => row.full_coverage);
  const valueFrontier = leaderboardValueFrontier(eligible);
  const bestSolve =
    [...eligible].sort((a, b) => b.solve_rate - a.solve_rate || a.median_cost - b.median_cost)[0] ??
    null;
  const bestValue =
    [...valueFrontier].sort(
      (a, b) =>
        (a.cost_per_successful_rep ?? Number.POSITIVE_INFINITY) -
          (b.cost_per_successful_rep ?? Number.POSITIVE_INFINITY) || b.solve_rate - a.solve_rate,
    )[0] ?? null;
  const biggestLift =
    [...eligible]
      .filter((row) => !row.is_baseline && row.baseline_delta != null)
      .sort(
        (a, b) =>
          (b.baseline_delta ?? Number.NEGATIVE_INFINITY) -
            (a.baseline_delta ?? Number.NEGATIVE_INFINITY) || b.solve_rate - a.solve_rate,
      )[0] ?? null;

  let balancedPick: LeaderboardRow | null = null;
  if (valueFrontier.length > 0) {
    const costs = valueFrontier.map((row) => row.cost_per_successful_rep!);
    const solves = valueFrontier.map((row) => row.solve_rate);
    const minCost = Math.min(...costs);
    const maxCost = Math.max(...costs);
    const minSolve = Math.min(...solves);
    const maxSolve = Math.max(...solves);
    const costRange = maxCost - minCost || 1;
    const solveRange = maxSolve - minSolve || 1;
    balancedPick = [...valueFrontier].sort((a, b) => {
      const distance = (row: LeaderboardRow) => {
        const costDistance = (row.cost_per_successful_rep! - minCost) / costRange;
        const solveDistance = (maxSolve - row.solve_rate) / solveRange;
        return Math.hypot(costDistance, solveDistance);
      };
      return (
        distance(a) - distance(b) ||
        b.solve_rate - a.solve_rate ||
        a.cost_per_successful_rep! - b.cost_per_successful_rep!
      );
    })[0]!;
  }

  return {
    balanced_pick: balancedPick,
    best_solve: bestSolve,
    best_value: bestValue,
    biggest_lift: biggestLift,
  };
}
