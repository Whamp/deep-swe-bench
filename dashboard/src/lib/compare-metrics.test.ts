import { describe, expect, it } from "vitest";
import fc from "fast-check";
import type { ComparisonCell, ComparisonRun } from "@/lib/types";
import {
  compareConfigPair,
  defaultComparePair,
  difficultySolveSummary,
  matchedTaskTrajectoryPair,
  type ComparePairOutcome,
} from "@/lib/compare-metrics";

function cell(
  task: string,
  rewardBinary: number,
  rewardPartial: number,
  overrides: Partial<ComparisonCell> = {},
): ComparisonCell {
  return {
    task,
    config: "baseline",
    rep: 0,
    result_path: `/results/baseline/${task}/rep0/result.json`,
    reward_binary: rewardBinary,
    reward_partial: rewardPartial,
    total_tokens: 100,
    reported_total_tokens: 100,
    cache_read_tokens: 80,
    adjusted_tokens: 28,
    cost_usd: 1,
    agent_wall_s: 10,
    patch_bytes: 10,
    difficulty: "medium",
    ...overrides,
  };
}

function run(overrides: Partial<ComparisonRun> = {}): ComparisonRun {
  return {
    run_id: "gpt-5.6-sol/low/baseline",
    model: "gpt-5.6-sol",
    thinking: "low",
    config: "baseline",
    state: "completed",
    total_cells: 2,
    distinct_tasks: 2,
    solved: 1,
    solve_rate: 50,
    mean_partial: 0.7,
    median_cost: 1,
    median_tokens: 100,
    median_wall_s: 10,
    total_cost: 2,
    total_reported_tokens: 200,
    total_cache_read_tokens: 160,
    total_adjusted_tokens: 56,
    cache_read_share: 0.8,
    solves_per_million_adjusted_tokens: 17_857.142857,
    token_policy: "cache-read-10pct-v1",
    cache_read_weight: 0.1,
    cells: [cell("task-a", 1, 1), cell("task-b", 0, 0.4)],
    ...overrides,
  };
}

function outcomeRun(prefix: string, outcomes: boolean[]): ComparisonRun {
  const cells = outcomes.map((solved, index) =>
    cell(`task-${index}`, solved ? 1 : 0, solved ? 1 : 0, { config: prefix }),
  );
  return run({
    run_id: `model/low/${prefix}`,
    config: prefix,
    cells,
    total_cells: cells.length,
    distinct_tasks: cells.length,
    solved: outcomes.filter(Boolean).length,
    solve_rate: outcomes.length ? (outcomes.filter(Boolean).length / outcomes.length) * 100 : 0,
  });
}

describe("compareConfigPair", () => {
  it("compares only shared tasks and reports directional flips", () => {
    const reference = run({
      cells: [cell("task-a", 1, 1), cell("task-b", 0, 0.4), cell("reference-only", 1, 1)],
    });
    const challenger = run({
      run_id: "gpt-5.6-sol/low/pi-check",
      config: "pi-check",
      cells: [
        cell("task-a", 1, 0.8, { config: "pi-check" }),
        cell("task-b", 1, 0.9, { config: "pi-check" }),
        cell("challenger-only", 1, 1, { config: "pi-check" }),
      ],
    });

    const result = compareConfigPair(reference, challenger);

    expect(result.shared_tasks).toBe(2);
    expect(result.both_solved).toBe(1);
    expect(result.reference_only).toBe(0);
    expect(result.challenger_only).toBe(1);
    expect(result.neither_solved).toBe(0);
    expect(result.net_flips).toBe(1);
    expect(result.reference_task_solve_rate).toBe(50);
    expect(result.challenger_task_solve_rate).toBe(100);
    expect(result.reference_mean_partial).toBeCloseTo(0.7);
    expect(result.challenger_mean_partial).toBeCloseTo(0.85);
    expect(result.partial_delta).toBeCloseTo(0.15);
    expect(result.tasks.map((task) => task.task)).toEqual(["task-b", "task-a"]);
  });

  it("uses the best observed rep for per-task outcome and partial reward", () => {
    const reference = run({
      cells: [cell("task-a", 0, 0.2, { rep: 0 }), cell("task-a", 1, 0.9, { rep: 1 })],
    });
    const challenger = run({
      run_id: "model/low/challenger",
      config: "challenger",
      cells: [cell("task-a", 0, 0.5, { rep: 0 }), cell("task-a", 0, 0.7, { rep: 1 })],
    });

    const result = compareConfigPair(reference, challenger);

    expect(result.reference_only).toBe(1);
    expect(result.tasks[0]?.reference_partial).toBe(0.9);
    expect(result.tasks[0]?.challenger_partial).toBe(0.7);
  });

  it("marks cost as untracked from total cost rather than a zero median", () => {
    const reference = run({ total_cost: 2, median_cost: 0 });
    const challenger = run({ total_cost: 0, median_cost: 0 });

    const result = compareConfigPair(reference, challenger);

    expect(result.reference_cost_tracked).toBe(true);
    expect(result.challenger_cost_tracked).toBe(false);
    expect(result.cost_per_successful_rep_delta).toBeNull();
  });

  it("is symmetric when reference and challenger are swapped", () => {
    fc.assert(
      fc.property(
        fc.array(fc.boolean(), { maxLength: 30 }),
        fc.array(fc.boolean(), { maxLength: 30 }),
        (a, b) => {
          const forward = compareConfigPair(outcomeRun("a", a), outcomeRun("b", b));
          const reverse = compareConfigPair(outcomeRun("b", b), outcomeRun("a", a));
          expect(reverse.shared_tasks).toBe(forward.shared_tasks);
          expect(reverse.both_solved).toBe(forward.both_solved);
          expect(reverse.neither_solved).toBe(forward.neither_solved);
          expect(reverse.reference_only).toBe(forward.challenger_only);
          expect(reverse.challenger_only).toBe(forward.reference_only);
          expect(reverse.net_flips + forward.net_flips).toBe(0);
        },
      ),
    );
  });
});

describe("matchedTaskTrajectoryPair", () => {
  it("selects the shared rep that demonstrates a directional task flip", () => {
    const reference = run({
      cells: [
        cell("task-a", 0, 0.2, { rep: 0, result_path: "/reference/rep0/result.json" }),
        cell("task-a", 0, 0.3, { rep: 1, result_path: "/reference/rep1/result.json" }),
      ],
    });
    const challenger = run({
      run_id: "model/low/challenger",
      config: "challenger",
      cells: [
        cell("task-a", 0, 0.4, { rep: 0, result_path: "/challenger/rep0/result.json" }),
        cell("task-a", 1, 1, { rep: 1, result_path: "/challenger/rep1/result.json" }),
      ],
    });

    expect(matchedTaskTrajectoryPair(reference, challenger, "task-a")).toEqual({
      task: "task-a",
      rep: 1,
      reference_path: "/reference/rep1/result.json",
      challenger_path: "/challenger/rep1/result.json",
    });
  });
});

describe("defaultComparePair", () => {
  it("prefers the largest full-coverage group with a canonical baseline", () => {
    const rows = [
      run({ run_id: "gpt-5.5/low/baseline", model: "gpt-5.5", config: "baseline" }),
      run({
        run_id: "gpt-5.5/low/challenger-a",
        model: "gpt-5.5",
        config: "challenger-a",
        solve_rate: 60,
      }),
      run({
        run_id: "gpt-5.5/low/challenger-b",
        model: "gpt-5.5",
        config: "challenger-b",
        solve_rate: 70,
      }),
      run({ run_id: "gpt-5.6-sol/low/baseline", config: "baseline", solve_rate: 80 }),
      run({ run_id: "gpt-5.6-sol/low/pi-check", config: "pi-check", solve_rate: 90 }),
    ];

    expect(defaultComparePair(rows, 2)).toEqual({
      group_key: "gpt-5.5/low",
      reference_id: "gpt-5.5/low/baseline",
      challenger_id: "gpt-5.5/low/challenger-b",
    });
  });

  it("falls back to the two strongest configs when no baseline exists", () => {
    const rows = [
      run({
        run_id: "model/high/a",
        model: "model",
        thinking: "high",
        config: "a",
        solve_rate: 10,
      }),
      run({
        run_id: "model/high/b",
        model: "model",
        thinking: "high",
        config: "b",
        solve_rate: 30,
      }),
      run({
        run_id: "model/high/c",
        model: "model",
        thinking: "high",
        config: "c",
        solve_rate: 20,
      }),
    ];

    expect(defaultComparePair(rows, 2)).toEqual({
      group_key: "model/high",
      reference_id: "model/high/b",
      challenger_id: "model/high/c",
    });
  });
});

describe("difficultySolveSummary", () => {
  it("returns null instead of fake zero for an empty bucket", () => {
    const summary = difficultySolveSummary(run().cells, new Set(["task-a", "task-b"]));
    expect(summary.easy).toEqual({ solved: 0, total: 0, solve_rate: null });
    expect(summary.medium).toEqual({ solved: 1, total: 2, solve_rate: 50 });
  });
});

const _outcomeTypeCheck: ComparePairOutcome = "challenger_only";
void _outcomeTypeCheck;
