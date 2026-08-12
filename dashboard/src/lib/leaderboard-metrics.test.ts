import { describe, expect, it } from "vitest";
import type { ComparisonCell, ComparisonRun } from "@/lib/types";
import {
  deriveLeaderboardRows,
  leaderboardCostFrontier,
  leaderboardValueFrontier,
  selectLeaderboardHighlights,
} from "@/lib/leaderboard-metrics";

function cell(task: string, rep: number, solved: number): ComparisonCell {
  return {
    task,
    config: "config",
    rep,
    result_path: `/results/config/${task}/rep${rep}/result.json`,
    reward_binary: solved,
    reward_partial: solved,
    total_tokens: 100,
    cost_usd: 1,
    agent_wall_s: 10,
    patch_bytes: 10,
  };
}

function comparisonRun(overrides: Partial<ComparisonRun> = {}): ComparisonRun {
  return {
    run_id: "model/low/config",
    model: "model",
    thinking: "low",
    config: "config",
    state: "completed",
    total_cells: 4,
    distinct_tasks: 2,
    solved: 2,
    solve_rate: 50,
    mean_partial: 0.5,
    median_cost: 1,
    median_tokens: 100,
    median_wall_s: 10,
    total_cost: 4,
    cells: [cell("task-a", 0, 1), cell("task-a", 1, 0), cell("task-b", 0, 1), cell("task-b", 1, 0)],
    ...overrides,
  };
}

describe("deriveLeaderboardRows", () => {
  it("separates per-rep solve from any-rep task coverage and derives efficiency", () => {
    const [row] = deriveLeaderboardRows([comparisonRun()], 2);
    expect(row.task_solved).toBe(2);
    expect(row.task_solve_rate).toBe(100);
    expect(row.cost_per_successful_rep).toBe(2);
    expect(row.cost_tracked).toBe(true);
    expect(row.full_coverage).toBe(true);
    expect(row.sample_label).toBe("2 tasks × 2 reps");
  });

  it("computes baseline delta only against canonical baseline in the same model and thinking", () => {
    const baseline = comparisonRun({
      run_id: "model/low/baseline",
      config: "baseline",
      solve_rate: 40,
    });
    const candidate = comparisonRun({ solve_rate: 55 });
    const otherThinking = comparisonRun({
      run_id: "model/high/config",
      thinking: "high",
      solve_rate: 80,
    });
    const historicalBaseline = comparisonRun({
      run_id: "other/low/baseline-preamble",
      model: "other",
      config: "baseline-preamble",
      solve_rate: 10,
    });

    const rows = deriveLeaderboardRows([baseline, candidate, otherThinking, historicalBaseline], 2);
    expect(rows.find((row) => row.run_id === candidate.run_id)?.baseline_delta).toBe(15);
    expect(rows.find((row) => row.run_id === otherThinking.run_id)?.baseline_delta).toBeNull();
    expect(rows.find((row) => row.run_id === historicalBaseline.run_id)?.baseline_delta).toBeNull();
  });

  it("marks zero median cost as untracked and identifies partial coverage", () => {
    const [row] = deriveLeaderboardRows(
      [comparisonRun({ median_cost: 0, total_cost: 0, distinct_tasks: 1 })],
      2,
    );
    expect(row.cost_tracked).toBe(false);
    expect(row.cost_per_successful_rep).toBeNull();
    expect(row.full_coverage).toBe(false);
  });
});

describe("leaderboard decisions", () => {
  const runs = [
    comparisonRun({
      run_id: "model/low/baseline",
      config: "baseline",
      solve_rate: 40,
      solved: 4,
      total_cost: 4,
      median_cost: 1,
    }),
    comparisonRun({
      run_id: "model/low/value",
      config: "value",
      solve_rate: 50,
      solved: 5,
      total_cost: 4,
      median_cost: 1,
    }),
    comparisonRun({
      run_id: "model/low/quality",
      config: "quality",
      solve_rate: 80,
      solved: 8,
      total_cost: 16,
      median_cost: 0.5,
    }),
    comparisonRun({
      run_id: "model/low/untracked",
      config: "untracked",
      solve_rate: 100,
      solved: 10,
      total_cost: 0,
      median_cost: 0,
    }),
  ];

  it("keeps cost-untracked runs out of the value frontier", () => {
    const rows = deriveLeaderboardRows(runs, 2);
    const frontier = leaderboardValueFrontier(rows);
    expect(frontier.map((row) => row.config)).toEqual(["value", "quality"]);
  });

  it("recomputes frontier membership for the active cost axis", () => {
    const rows = deriveLeaderboardRows(runs, 2);
    expect(leaderboardCostFrontier(rows, "median_cost").map((row) => row.config)).toEqual([
      "quality",
    ]);
  });

  it("selects measured highlights without inventing uncertainty", () => {
    const rows = deriveLeaderboardRows(runs, 2);
    const highlights = selectLeaderboardHighlights(rows);
    expect(highlights.best_solve?.config).toBe("untracked");
    expect(highlights.best_value?.config).toBe("value");
    expect(highlights.biggest_lift?.config).toBe("untracked");
    expect(highlights.balanced_pick?.config).toBe("quality");
  });
});
