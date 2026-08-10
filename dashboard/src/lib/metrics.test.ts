import { describe, it, expect } from "vitest";
import fc from "fast-check";
import {
  paretoFrontier,
  median,
  mean,
  sum,
  solveRate,
  pickBaseline,
  fmtSeconds,
  fmtTokens,
  fmtCost,
  fmtPercent,
  difficultyBucket,
  cellAgeS,
  type ParetoPoint,
} from "@/lib/metrics";

describe("paretoFrontier", () => {
  it("marks all points on frontier when none dominate each other", () => {
    const points: ParetoPoint[] = [
      { id: "a", cost: 1, value: 1 },
      { id: "b", cost: 2, value: 3 },
      { id: "c", cost: 3, value: 5 },
    ];
    const result = paretoFrontier(points);
    expect(result.every((p) => p.isPareto)).toBe(true);
  });

  it("excludes dominated points", () => {
    const points: ParetoPoint[] = [
      { id: "cheap-good", cost: 1, value: 5 },
      { id: "expensive-bad", cost: 5, value: 1 },
      { id: "middle", cost: 3, value: 3 },
    ];
    const result = paretoFrontier(points);
    // cheap-good dominates all; expensive-bad is dominated
    expect(result.find((p) => p.id === "cheap-good")?.isPareto).toBe(true);
    expect(result.find((p) => p.id === "expensive-bad")?.isPareto).toBe(false);
  });

  it("is idempotent", () => {
    const arb = pointArb();
    fc.assert(
      fc.property(fc.array(arb, { maxLength: 20 }), (points: ParetoPoint[]) => {
        const once = paretoFrontier(points);
        const stripped = once.map(({ isPareto: _, ...rest }) => rest as ParetoPoint);
        const twice = paretoFrontier(stripped);
        expect(twice.map((p) => p.isPareto)).toEqual(once.map((p) => p.isPareto));
      }),
    );
  });

  it("every frontier point is non-dominated by any other valid point", () => {
    const arb = pointArb();
    fc.assert(
      fc.property(fc.array(arb, { minLength: 1, maxLength: 30 }), (points: ParetoPoint[]) => {
        const result = paretoFrontier(points);
        const valid = points.filter(
          (p) => Number.isFinite(p.cost) && Number.isFinite(p.value) && p.cost >= 0,
        );
        for (const p of result) {
          if (!p.isPareto) continue;
          for (const other of valid) {
            if (other.id === p.id) continue;
            const dominated =
              other.cost <= p.cost &&
              other.value >= p.value &&
              (other.cost < p.cost || other.value > p.value);
            expect(dominated).toBe(false);
          }
        }
      }),
    );
  });

  it("handles empty input", () => {
    expect(paretoFrontier([])).toEqual([]);
  });

  it("excludes NaN, negative cost, and invalid values from frontier", () => {
    const points: ParetoPoint[] = [
      { id: "good", cost: 1, value: 1 },
      { id: "nan-cost", cost: NaN, value: 1 },
      { id: "neg-cost", cost: -1, value: 1 },
      { id: "nan-value", cost: 1, value: NaN },
    ];
    const result = paretoFrontier(points);
    expect(result.find((p) => p.id === "good")?.isPareto).toBe(true);
    expect(result.find((p) => p.id === "nan-cost")?.isPareto).toBe(false);
    expect(result.find((p) => p.id === "neg-cost")?.isPareto).toBe(false);
    expect(result.find((p) => p.id === "nan-value")?.isPareto).toBe(false);
  });

  it("equal cost + equal value does not dominate (needs strict inequality)", () => {
    const points: ParetoPoint[] = [
      { id: "dup-a", cost: 1, value: 5 },
      { id: "dup-b", cost: 1, value: 5 },
    ];
    const result = paretoFrontier(points);
    expect(result.every((p) => p.isPareto)).toBe(true);
  });
});

describe("median", () => {
  it("returns 0 for empty input", () => {
    expect(median([])).toBe(0);
  });

  it("computes odd-length median", () => {
    expect(median([3, 1, 2])).toBe(2);
  });

  it("computes even-length median", () => {
    expect(median([1, 2, 3, 4])).toBe(2.5);
  });

  it("filters NaN and null", () => {
    expect(median([1, NaN, 3, null as unknown as number, 2])).toBe(2);
  });

  it("handles single element", () => {
    expect(median([42])).toBe(42);
  });

  it("is monotone under additive constant", () => {
    fc.assert(
      fc.property(fc.array(fc.integer({ min: -100, max: 100 }), { maxLength: 20 }), (arr) => {
        if (arr.length === 0) return;
        const m = median(arr);
        const m2 = median(arr.map((v) => v + 100));
        expect(m2).toBeCloseTo(m + 100, 5);
      }),
    );
  });
});

describe("mean", () => {
  it("returns 0 for empty input", () => {
    expect(mean([])).toBe(0);
  });

  it("computes mean", () => {
    expect(mean([1, 2, 3])).toBe(2);
  });

  it("filters NaN", () => {
    expect(mean([1, NaN, 3])).toBe(2);
  });

  it("sum = mean * count for finite values", () => {
    fc.assert(
      fc.property(fc.array(fc.integer({ min: -1000, max: 1000 }), { maxLength: 20 }), (arr) => {
        const valid = arr.filter(Number.isFinite);
        if (valid.length === 0) return;
        expect(mean(arr) * valid.length).toBeCloseTo(sum(arr), 5);
      }),
    );
  });
});

describe("sum", () => {
  it("returns 0 for empty input", () => {
    expect(sum([])).toBe(0);
  });

  it("computes sum", () => {
    expect(sum([1, 2, 3, 4])).toBe(10);
  });

  it("treats NaN as 0", () => {
    expect(sum([1, NaN, 3])).toBe(4);
  });
});

describe("solveRate", () => {
  it("returns 0 for empty input", () => {
    expect(solveRate([])).toBe(0);
  });

  it("computes fraction of values >= 1", () => {
    expect(solveRate([1, 0, 1, 0])).toBe(0.5);
  });

  it("returns 1 when all solve", () => {
    expect(solveRate([1, 1, 1])).toBe(1);
  });

  it("handles values > 1", () => {
    expect(solveRate([2, 0])).toBe(0.5);
  });
});

describe("formatting", () => {
  it("fmtSeconds handles ranges", () => {
    expect(fmtSeconds(0)).toBe("0s");
    expect(fmtSeconds(59)).toBe("59s");
    expect(fmtSeconds(60)).toBe("1m");
    expect(fmtSeconds(3600)).toBe("1.0h");
    expect(fmtSeconds(null)).toBe("—");
    expect(fmtSeconds(NaN)).toBe("—");
  });

  it("fmtTokens handles ranges", () => {
    expect(fmtTokens(500)).toBe("500");
    expect(fmtTokens(1500)).toBe("1.5k");
    expect(fmtTokens(1_500_000)).toBe("1.50M");
    expect(fmtTokens(null)).toBe("—");
  });

  it("fmtCost handles ranges", () => {
    expect(fmtCost(0)).toBe("$0");
    expect(fmtCost(0.005)).toBe("$0.0050");
    expect(fmtCost(0.5)).toBe("$0.500");
    expect(fmtCost(1.5)).toBe("$1.50");
    expect(fmtCost(null)).toBe("—");
  });

  it("fmtPercent handles ranges", () => {
    expect(fmtPercent(0.5)).toBe("50.0%");
    expect(fmtPercent(1)).toBe("100.0%");
    expect(fmtPercent(null)).toBe("—");
  });
});

describe("difficultyBucket", () => {
  it("classifies correctly", () => {
    expect(difficultyBucket(10)).toBe("hard");
    expect(difficultyBucket(33)).toBe("medium");
    expect(difficultyBucket(50)).toBe("medium");
    expect(difficultyBucket(66)).toBe("easy");
    expect(difficultyBucket(90)).toBe("easy");
    expect(difficultyBucket(NaN)).toBe("unknown");
  });

  it("boundaries: <33 is hard, 33-65 is medium, >=66 is easy", () => {
    expect(difficultyBucket(32.9)).toBe("hard");
    expect(difficultyBucket(65.9)).toBe("medium");
    expect(difficultyBucket(66)).toBe("easy");
  });
});

describe("cellAgeS", () => {
  it("returns null for invalid input", () => {
    expect(cellAgeS(null)).toBeNull();
    expect(cellAgeS(undefined)).toBeNull();
    expect(cellAgeS("")).toBeNull();
    expect(cellAgeS("not-a-date")).toBeNull();
  });

  it("returns null for future timestamps", () => {
    expect(cellAgeS("2099-01-01T00:00:00Z", Date.now())).toBeNull();
  });

  it("returns non-negative age for past timestamps", () => {
    const age = cellAgeS("2020-01-01T00:00:00Z", new Date("2020-01-01T01:00:00Z").getTime());
    expect(age).toBe(3600);
  });

  it("is monotone non-decreasing with increasing started_at distance", () => {
    const now = new Date("2025-01-01T12:00:00Z").getTime();
    const a1 = cellAgeS("2025-01-01T11:00:00Z", now)!;
    const a2 = cellAgeS("2025-01-01T10:00:00Z", now)!;
    expect(a2).toBeGreaterThan(a1);
    expect(a1).toBeGreaterThanOrEqual(0);
    expect(a2).toBeGreaterThanOrEqual(0);
  });
});

// --- Arbitraries ---

function pointArb(): fc.Arbitrary<ParetoPoint> {
  return fc.record({
    id: fc.string({ minLength: 1, maxLength: 5 }),
    cost: fc.float({ min: 0, max: 1000, noNaN: true }),
    value: fc.float({ min: 0, max: 100, noNaN: true }),
  });
}

describe("pickBaseline", () => {
  const groups = (
    cfg: string,
    tasks: Array<[string, number]>,
    model = "gpt-5.5",
    thinking = "low",
  ) => ({
    run_id: `${model}/${thinking}/${cfg}`,
    model,
    thinking,
    config: cfg,
    cells: tasks.map(([task, rb]) => ({ task, reward_binary: rb })),
  });

  it("picks a same-model different-config group covering the task set", () => {
    const runTasks = ["task-a", "task-b", "task-c"];
    const gs = [
      groups("baseline", [
        ["task-a", 1],
        ["task-b", 0],
        ["task-c", 1],
      ]), // 66.7%
      groups("experimental", [
        ["task-a", 0],
        ["task-b", 0],
        ["task-c", 0],
      ]), // 0%
    ];
    const choice = pickBaseline(gs, "gpt-5.5", "low", "myconfig", runTasks);
    expect(choice).not.toBeNull();
    expect(choice!.label).toBe("baseline");
    expect(choice!.solveRate).toBeCloseTo(66.67, 1);
    expect(choice!.solvedSet.has("task-a")).toBe(true);
    expect(choice!.solvedSet.has("task-b")).toBe(false);
  });

  it("excludes the run's own config", () => {
    const runTasks = ["task-a", "task-b"];
    const gs = [
      groups("myconfig", [
        ["task-a", 1],
        ["task-b", 1],
      ]),
      groups("baseline", [
        ["task-a", 0],
        ["task-b", 0],
      ]),
    ];
    const choice = pickBaseline(gs, "gpt-5.5", "low", "myconfig", runTasks);
    expect(choice!.label).toBe("baseline");
  });

  it("returns null when no group covers >=50% of the task set", () => {
    const runTasks = ["task-a", "task-b", "task-c", "task-d"];
    const gs = [groups("baseline", [["task-a", 1]])]; // 25% coverage
    expect(pickBaseline(gs, "gpt-5.5", "low", "x", runTasks)).toBeNull();
  });

  it("returns null for an empty task set", () => {
    expect(pickBaseline([], "gpt-5.5", "low", "x", [])).toBeNull();
  });

  it("requires matching model and thinking", () => {
    const runTasks = ["task-a", "task-b"];
    const gs = [
      groups(
        "baseline",
        [
          ["task-a", 1],
          ["task-b", 1],
        ],
        "other-model",
        "low",
      ),
    ];
    expect(pickBaseline(gs, "gpt-5.5", "low", "x", runTasks)).toBeNull();
  });

  it("matches a provider-qualified run model to the results-directory group name", () => {
    // run model 'openai-codex/gpt-5.6-sol' must match group model 'gpt-5.6-sol'.
    const runTasks = ["task-a", "task-b"];
    const gs = [
      groups(
        "baseline",
        [
          ["task-a", 1],
          ["task-b", 0],
        ],
        "gpt-5.6-sol",
        "low",
      ),
    ];
    const choice = pickBaseline(gs, "openai-codex/gpt-5.6-sol", "low", "myconfig", runTasks);
    expect(choice).not.toBeNull();
    expect(choice!.label).toBe("baseline");
  });
});
