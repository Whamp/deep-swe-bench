import type { ComparisonCell, ComparisonRun } from "@/lib/types";

export type ComparePairOutcome =
  | "both_solved"
  | "reference_only"
  | "challenger_only"
  | "neither_solved";

export interface CompareTaskOutcome {
  task: string;
  outcome: ComparePairOutcome;
  reference_solved: boolean;
  challenger_solved: boolean;
  reference_partial: number;
  challenger_partial: number;
  partial_delta: number;
  difficulty: ComparisonCell["difficulty"];
}

export interface ConfigPairComparison {
  shared_tasks: number;
  both_solved: number;
  reference_only: number;
  challenger_only: number;
  neither_solved: number;
  net_flips: number;
  discordant_tasks: number;
  reference_task_solve_rate: number;
  challenger_task_solve_rate: number;
  task_solve_rate_delta: number;
  reference_mean_partial: number;
  challenger_mean_partial: number;
  partial_delta: number;
  reference_cost_tracked: boolean;
  challenger_cost_tracked: boolean;
  reference_cost_per_successful_rep: number | null;
  challenger_cost_per_successful_rep: number | null;
  cost_per_successful_rep_delta: number | null;
  tasks: CompareTaskOutcome[];
}

export interface DefaultComparePair {
  group_key: string;
  reference_id: string;
  challenger_id: string;
}

/** Two inspectable cells for the same task and rep. */
export interface MatchedTaskTrajectoryPair {
  task: string;
  rep: number;
  reference_path: string;
  challenger_path: string;
}

export interface DifficultyBucketSummary {
  solved: number;
  total: number;
  solve_rate: number | null;
}

export type DifficultySolveSummary = Record<
  "hard" | "medium" | "easy" | "unknown",
  DifficultyBucketSummary
>;

interface AggregatedTask {
  solved: boolean;
  partial: number;
  difficulty: ComparisonCell["difficulty"];
}

export function compareConfigPair(
  reference: ComparisonRun,
  challenger: ComparisonRun,
): ConfigPairComparison {
  const referenceTasks = aggregateTasks(reference.cells);
  const challengerTasks = aggregateTasks(challenger.cells);
  const sharedTaskNames = [...referenceTasks.keys()]
    .filter((task) => challengerTasks.has(task))
    .sort();

  const tasks = sharedTaskNames.map((task): CompareTaskOutcome => {
    const a = referenceTasks.get(task)!;
    const b = challengerTasks.get(task)!;
    const outcome = pairOutcome(a.solved, b.solved);
    return {
      task,
      outcome,
      reference_solved: a.solved,
      challenger_solved: b.solved,
      reference_partial: a.partial,
      challenger_partial: b.partial,
      partial_delta: b.partial - a.partial,
      difficulty: b.difficulty ?? a.difficulty ?? "unknown",
    };
  });

  tasks.sort(
    (a, b) => OUTCOME_ORDER[a.outcome] - OUTCOME_ORDER[b.outcome] || a.task.localeCompare(b.task),
  );

  const bothSolved = countOutcome(tasks, "both_solved");
  const referenceOnly = countOutcome(tasks, "reference_only");
  const challengerOnly = countOutcome(tasks, "challenger_only");
  const neitherSolved = countOutcome(tasks, "neither_solved");
  const referenceSolved = bothSolved + referenceOnly;
  const challengerSolved = bothSolved + challengerOnly;
  const referenceMeanPartial = mean(tasks.map((task) => task.reference_partial));
  const challengerMeanPartial = mean(tasks.map((task) => task.challenger_partial));
  const referenceCostTracked = isCostTracked(reference);
  const challengerCostTracked = isCostTracked(challenger);
  const referenceCostPerSuccess = costPerSuccessfulRep(reference, referenceCostTracked);
  const challengerCostPerSuccess = costPerSuccessfulRep(challenger, challengerCostTracked);

  return {
    shared_tasks: tasks.length,
    both_solved: bothSolved,
    reference_only: referenceOnly,
    challenger_only: challengerOnly,
    neither_solved: neitherSolved,
    net_flips: challengerOnly - referenceOnly,
    discordant_tasks: challengerOnly + referenceOnly,
    reference_task_solve_rate: percent(referenceSolved, tasks.length),
    challenger_task_solve_rate: percent(challengerSolved, tasks.length),
    task_solve_rate_delta: percent(challengerSolved - referenceSolved, tasks.length),
    reference_mean_partial: referenceMeanPartial,
    challenger_mean_partial: challengerMeanPartial,
    partial_delta: challengerMeanPartial - referenceMeanPartial,
    reference_cost_tracked: referenceCostTracked,
    challenger_cost_tracked: challengerCostTracked,
    reference_cost_per_successful_rep: referenceCostPerSuccess,
    challenger_cost_per_successful_rep: challengerCostPerSuccess,
    cost_per_successful_rep_delta:
      referenceCostPerSuccess == null || challengerCostPerSuccess == null
        ? null
        : challengerCostPerSuccess - referenceCostPerSuccess,
    tasks,
  };
}

export function defaultComparePair(
  rows: ComparisonRun[],
  subsetSize: number,
  includePartial = false,
): DefaultComparePair | null {
  const eligible = includePartial ? rows : rows.filter((row) => row.distinct_tasks >= subsetSize);
  const groups = new Map<string, ComparisonRun[]>();
  for (const row of eligible) {
    const key = comparisonGroupKey(row);
    const group = groups.get(key) ?? [];
    group.push(row);
    groups.set(key, group);
  }

  const candidates = [...groups.entries()]
    .filter(([, group]) => group.length >= 2)
    .sort(([keyA, groupA], [keyB, groupB]) => {
      const baselineDelta =
        Number(hasCanonicalBaseline(groupB)) - Number(hasCanonicalBaseline(groupA));
      return baselineDelta || groupB.length - groupA.length || keyA.localeCompare(keyB);
    });
  const selected = candidates[0];
  if (!selected) return null;

  const [groupKey, group] = selected;
  const ranked = [...group].sort(
    (a, b) =>
      b.solve_rate - a.solve_rate ||
      b.distinct_tasks - a.distinct_tasks ||
      a.config.localeCompare(b.config),
  );
  const reference = group.find((row) => row.config === "baseline") ?? ranked[0]!;
  const challenger = ranked.find((row) => row.run_id !== reference.run_id);
  if (!challenger) return null;

  return {
    group_key: groupKey,
    reference_id: reference.run_id,
    challenger_id: challenger.run_id,
  };
}

/** Select a shared rep whose solve outcome best represents the task comparison. */
export function matchedTaskTrajectoryPair(
  reference: ComparisonRun,
  challenger: ComparisonRun,
  task: string,
): MatchedTaskTrajectoryPair | null {
  const referenceCells = reference.cells
    .filter((cell) => cell.task === task && cell.result_path)
    .sort((a, b) => a.rep - b.rep);
  const challengerByRep = new Map(
    challenger.cells
      .filter((cell) => cell.task === task && cell.result_path)
      .map((cell) => [cell.rep, cell]),
  );
  const pairs = referenceCells.flatMap((referenceCell) => {
    const challengerCell = challengerByRep.get(referenceCell.rep);
    return challengerCell ? [{ referenceCell, challengerCell }] : [];
  });
  if (!pairs.length) return null;

  const referenceSolved = referenceCells.some((cell) => Number(cell.reward_binary) >= 1);
  const challengerSolved = [...challengerByRep.values()].some(
    (cell) => Number(cell.reward_binary) >= 1,
  );
  const taskOutcome = pairOutcome(referenceSolved, challengerSolved);
  const selected =
    pairs.find(
      ({ referenceCell, challengerCell }) =>
        pairOutcome(
          Number(referenceCell.reward_binary) >= 1,
          Number(challengerCell.reward_binary) >= 1,
        ) === taskOutcome,
    ) ?? pairs[0];

  return {
    task,
    rep: selected.referenceCell.rep,
    reference_path: selected.referenceCell.result_path,
    challenger_path: selected.challengerCell.result_path,
  };
}

export function difficultySolveSummary(
  cells: ComparisonCell[],
  sharedTasks: Set<string>,
): DifficultySolveSummary {
  const aggregated = aggregateTasks(cells);
  const buckets: DifficultySolveSummary = {
    hard: { solved: 0, total: 0, solve_rate: null },
    medium: { solved: 0, total: 0, solve_rate: null },
    easy: { solved: 0, total: 0, solve_rate: null },
    unknown: { solved: 0, total: 0, solve_rate: null },
  };

  for (const task of sharedTasks) {
    const outcome = aggregated.get(task);
    if (!outcome) continue;
    const bucket = outcome.difficulty;
    const key = bucket === "hard" || bucket === "medium" || bucket === "easy" ? bucket : "unknown";
    buckets[key].total += 1;
    if (outcome.solved) buckets[key].solved += 1;
  }

  for (const bucket of Object.values(buckets)) {
    bucket.solve_rate = bucket.total ? percent(bucket.solved, bucket.total) : null;
  }
  return buckets;
}

export function comparisonGroupKey(run: ComparisonRun): string {
  return `${run.model ?? "unknown"}/${run.thinking ?? "unknown"}`;
}

export function isCostTracked(run: ComparisonRun): boolean {
  return Number.isFinite(run.total_cost) && run.total_cost > 0;
}

function aggregateTasks(cells: ComparisonCell[]): Map<string, AggregatedTask> {
  const tasks = new Map<string, AggregatedTask>();
  for (const cell of cells) {
    const current = tasks.get(cell.task);
    const solved = Number(cell.reward_binary) >= 1;
    const partial = finiteNumber(cell.reward_partial);
    if (!current) {
      tasks.set(cell.task, {
        solved,
        partial,
        difficulty: cell.difficulty ?? "unknown",
      });
      continue;
    }
    current.solved ||= solved;
    current.partial = Math.max(current.partial, partial);
    if (!current.difficulty || current.difficulty === "unknown") {
      current.difficulty = cell.difficulty ?? "unknown";
    }
  }
  return tasks;
}

function pairOutcome(referenceSolved: boolean, challengerSolved: boolean): ComparePairOutcome {
  if (referenceSolved && challengerSolved) return "both_solved";
  if (referenceSolved) return "reference_only";
  if (challengerSolved) return "challenger_only";
  return "neither_solved";
}

function countOutcome(tasks: CompareTaskOutcome[], outcome: ComparePairOutcome): number {
  return tasks.filter((task) => task.outcome === outcome).length;
}

function hasCanonicalBaseline(rows: ComparisonRun[]): boolean {
  return rows.some((row) => row.config === "baseline");
}

function costPerSuccessfulRep(run: ComparisonRun, tracked: boolean): number | null {
  if (!tracked || run.solved <= 0) return null;
  return run.total_cost / run.solved;
}

function finiteNumber(value: unknown): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function mean(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((total, value) => total + value, 0) / values.length;
}

function percent(numerator: number, denominator: number): number {
  if (!denominator) return 0;
  return (numerator / denominator) * 100;
}

const OUTCOME_ORDER: Record<ComparePairOutcome, number> = {
  challenger_only: 0,
  reference_only: 1,
  both_solved: 2,
  neither_solved: 3,
};
