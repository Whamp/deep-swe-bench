import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Leaderboard from "@/pages/leaderboard";
import type { CompareResponse, ComparisonCell, ComparisonRun, SubsetsResponse } from "@/lib/types";

function makeCells(taskCount: number, reps: number, solvedCells: number): ComparisonCell[] {
  return Array.from({ length: taskCount * reps }, (_, index) => ({
    task: `task-${Math.floor(index / reps)}`,
    config: "config",
    rep: index % reps,
    result_path: `/results/config/task-${Math.floor(index / reps)}/rep${index % reps}/result.json`,
    reward_binary: index < solvedCells ? 1 : 0,
    reward_partial: index < solvedCells ? 1 : 0.2,
    total_tokens: 100_000,
    reported_total_tokens: 100_000,
    cache_read_tokens: 90_000,
    adjusted_tokens: 19_000,
    cost_usd: 1,
    agent_wall_s: 100,
    patch_bytes: 100,
  }));
}

function makeRun(overrides: Partial<ComparisonRun> = {}): ComparisonRun {
  const runId = overrides.run_id ?? "gpt-5.5/low/baseline";
  const [parsedModel, parsedThinking, ...configParts] = runId.split("/");
  const totalCells = overrides.total_cells ?? 108;
  const distinctTasks = overrides.distinct_tasks ?? 36;
  const solved = overrides.solved ?? 33;
  const reps =
    distinctTasks > 0 && totalCells % distinctTasks === 0 ? totalCells / distinctTasks : 1;
  return {
    run_id: runId,
    model: overrides.model ?? parsedModel ?? "gpt-5.5",
    thinking: overrides.thinking ?? parsedThinking ?? "low",
    config: overrides.config ?? configParts.join("/") ?? "baseline",
    state: "completed",
    total_cells: totalCells,
    distinct_tasks: distinctTasks,
    solved,
    solve_rate: overrides.solve_rate ?? (solved / totalCells) * 100,
    mean_partial: 0.967,
    median_cost: 0.86,
    median_tokens: 610_000,
    median_wall_s: 206,
    total_cost: 100,
    total_reported_tokens: totalCells * 100_000,
    total_cache_read_tokens: totalCells * 90_000,
    total_adjusted_tokens: totalCells * 19_000,
    cache_read_share: 0.9,
    solves_per_million_adjusted_tokens: solved / ((totalCells * 19_000) / 1_000_000),
    token_policy: "cache-read-10pct-v1",
    cache_read_weight: 0.1,
    cells: overrides.cells ?? makeCells(distinctTasks, reps, solved),
    ...overrides,
  };
}

const SUBSETS: SubsetsResponse = {
  subsets: [
    {
      name: "36_v2",
      task_count: 36,
      tasks: Array.from({ length: 36 }, (_, index) => `task-${index}`),
    },
    {
      name: "12_v0",
      task_count: 12,
      tasks: Array.from({ length: 12 }, (_, index) => `task-${index}`),
    },
  ],
};

function mockFetch(options: { subsets?: SubsetsResponse; compare?: CompareResponse | Error }) {
  globalThis.fetch = vi.fn().mockImplementation((url: string) => {
    const parsed = String(url);
    if (parsed.includes("/api/subsets")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(options.subsets ?? SUBSETS),
      });
    }
    if (parsed.includes("/api/compare")) {
      if (options.compare instanceof Error) return Promise.reject(options.compare);
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(options.compare),
      });
    }
    return Promise.reject(new Error(`unexpected fetch: ${parsed}`));
  });
}

function renderLeaderboard() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Leaderboard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const COMPLETE_RUNS: ComparisonRun[] = [
  makeRun({
    run_id: "gpt-5.5/low/baseline",
    solved: 33,
    solve_rate: 30.6,
    total_cost: 100,
  }),
  makeRun({
    run_id: "gpt-5.5/low/pi-check",
    solved: 53,
    solve_rate: 49.1,
    median_cost: 1.2,
    total_cost: 130,
  }),
  makeRun({
    run_id: "gpt-5.6-sol/medium/baseline",
    solved: 81,
    solve_rate: 75,
    median_cost: 1.52,
    total_cost: 178,
  }),
];

describe("Leaderboard page", () => {
  it("renders a bounded loading state initially", () => {
    mockFetch({ compare: { runs: [], subset: "36_v2" } });
    renderLeaderboard();
    expect(screen.getByLabelText("Loading leaderboard")).toBeInTheDocument();
  });

  it("renders measured decision cards, value frontier, and ranked evidence", async () => {
    mockFetch({ compare: { runs: COMPLETE_RUNS, subset: "36_v2" } });
    renderLeaderboard();

    expect(await screen.findByText("Measured standouts")).toBeInTheDocument();
    expect(screen.getByText("Balanced pick")).toBeInTheDocument();
    expect(screen.getByText("Highest solve")).toBeInTheDocument();
    expect(screen.getByText("Best value")).toBeInTheDocument();
    expect(screen.getByText("Biggest baseline lift")).toBeInTheDocument();
    expect(screen.getByText("Value frontier")).toBeInTheDocument();
    expect(screen.getByText("Ranked evidence")).toBeInTheDocument();
    expect(screen.getByText(/Start here · balanced pick/i)).toBeInTheDocument();
    expect(
      screen.getByText("View: 36_v2 · all reps · all model + thinking groups"),
    ).toBeInTheDocument();
    expect(screen.getByText("Dataset, reps, model + thinking")).toBeInTheDocument();
    expect(screen.getAllByText(/Equal-weight 0–1 normalization/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Cost / successful rep").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Solves / 1M adjusted tokens").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/cache reads × 0.10 · cache-read-10pct-v1/).length).toBeGreaterThan(
      0,
    );
    expect(screen.getByText("colored ring = Pareto")).toBeInTheDocument();
    expect(screen.getByText("white ring = selected")).toBeInTheDocument();
    expect(screen.getAllByText("+18.5pp").length).toBeGreaterThan(0);
  });

  it("shows task and rep success as separate denominators", async () => {
    const oneOfThreeCells = makeCells(36, 3, 0).map((item) => ({
      ...item,
      reward_binary: item.rep === 0 ? 1 : 0,
    }));
    const oneOfThreePerTask = makeRun({
      run_id: "gpt-5.5/low/one-of-three",
      solved: 36,
      solve_rate: 33.3,
      cells: oneOfThreeCells,
    });
    mockFetch({ compare: { runs: [oneOfThreePerTask], subset: "36_v2" } });
    const { container } = renderLeaderboard();

    await screen.findByText("Ranked evidence");
    expect(container.textContent).toContain("33.3% reps · 100.0% tasks");
    expect(container.textContent).toContain("36/108 reps · 36/36 tasks (100.0%)");
  });

  it("hides partial coverage by default and includes it on request", async () => {
    const partial = makeRun({
      run_id: "gpt-5.5/low/pilot",
      total_cells: 9,
      distinct_tasks: 9,
      solved: 9,
      solve_rate: 100,
      cells: makeCells(9, 1, 9),
    });
    mockFetch({ compare: { runs: [COMPLETE_RUNS[0]!, partial], subset: "36_v2" } });
    const { container } = renderLeaderboard();

    await screen.findByText("Ranked evidence");
    expect(container.textContent).not.toContain("pilot");
    fireEvent.click(screen.getByRole("button", { name: "Include partial" }));
    await waitFor(() => expect(container.textContent).toContain("pilot"));
    expect(container.textContent).toContain("Partial");
  });

  it("filters by config search and model-thinking scope", async () => {
    mockFetch({ compare: { runs: COMPLETE_RUNS, subset: "36_v2" } });
    const { container } = renderLeaderboard();
    await screen.findByText("Ranked evidence");

    fireEvent.change(screen.getByLabelText("Search configs"), {
      target: { value: "pi-check" },
    });
    await waitFor(() => {
      expect(container.textContent).toContain("pi-check");
      expect(container.textContent).not.toContain("gpt-5.6-sol · medium");
    });

    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    fireEvent.change(screen.getByLabelText("Search configs"), {
      target: { value: "gpt-5.6-sol" },
    });
    await waitFor(() => {
      expect(container.textContent).toContain("gpt-5.6-sol · medium");
      expect(container.textContent).not.toContain("pi-check");
      expect(container.textContent).toContain("1 full coverage");
    });

    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    fireEvent.change(screen.getByLabelText("Model and thinking"), {
      target: { value: "gpt-5.6-sol/medium" },
    });
    await waitFor(() => {
      expect(container.textContent).toContain("gpt-5.6-sol · medium");
      expect(container.textContent).not.toContain("pi-check");
    });
  });

  it("sorts lower-is-better metrics ascending on first click", async () => {
    mockFetch({ compare: { runs: COMPLETE_RUNS, subset: "36_v2" } });
    const { container } = renderLeaderboard();
    await screen.findByText("Ranked evidence");

    fireEvent.click(screen.getByRole("button", { name: /^Med cost/ }));
    const firstDesktopRow = container.querySelector("tbody tr");
    expect(firstDesktopRow?.textContent).toContain("baseline");
    expect(firstDesktopRow?.textContent).toContain("gpt-5.5 · low");
  });

  it("sorts adjusted token efficiency higher first", async () => {
    mockFetch({ compare: { runs: COMPLETE_RUNS, subset: "36_v2" } });
    const { container } = renderLeaderboard();
    await screen.findByText("Ranked evidence");

    fireEvent.click(screen.getByRole("button", { name: /^Solves \/ 1M adjusted tokens/ }));
    const firstDesktopRow = container.querySelector("tbody tr");
    expect(firstDesktopRow?.textContent).toContain("baseline");
    expect(firstDesktopRow?.textContent).toContain("gpt-5.6-sol · medium");
  });

  it("reveals diagnostic columns behind More metrics", async () => {
    mockFetch({ compare: { runs: COMPLETE_RUNS, subset: "36_v2" } });
    renderLeaderboard();
    await screen.findByText("Ranked evidence");

    expect(screen.queryByRole("button", { name: /^Mean partial/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "More metrics" }));
    expect(screen.getByRole("button", { name: /^Mean partial/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Med tokens/ })).toBeInTheDocument();
  });

  it("renders legacy API rows without adjusted token fields", async () => {
    const legacy = makeRun();
    delete legacy.total_reported_tokens;
    delete legacy.total_cache_read_tokens;
    delete legacy.total_adjusted_tokens;
    delete legacy.cache_read_share;
    delete legacy.solves_per_million_adjusted_tokens;
    delete legacy.token_policy;
    delete legacy.cache_read_weight;
    mockFetch({ compare: { runs: [legacy], subset: "36_v2" } });
    const { container } = renderLeaderboard();

    await screen.findByText("Ranked evidence");
    expect(container.textContent).toContain("cache-read share unavailable");
  });

  it("labels zero cost as untracked instead of treating it as free", async () => {
    const untracked = makeRun({
      run_id: "local-model/high/baseline",
      median_cost: 0,
      total_cost: 0,
      solved: 90,
      solve_rate: 83.3,
    });
    mockFetch({ compare: { runs: [untracked], subset: "36_v2" } });
    const { container } = renderLeaderboard();
    await screen.findByText("Ranked evidence");

    expect(container.textContent).toContain("Cost untracked");
    expect(container.textContent).toContain("No eligible config");
  });

  it("renders an actionable empty state", async () => {
    mockFetch({ compare: { runs: [], subset: "36_v2" } });
    renderLeaderboard();
    expect(
      await screen.findByText("No comparable configs match these filters."),
    ).toBeInTheDocument();
  });

  it("renders error state on fetch failure", async () => {
    mockFetch({ compare: new Error("network error") });
    renderLeaderboard();
    expect(await screen.findByText("Unable to load leaderboard")).toBeInTheDocument();
  });
});
