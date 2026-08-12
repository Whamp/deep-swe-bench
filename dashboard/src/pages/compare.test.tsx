import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Compare from "@/pages/compare";
import type { CompareResponse, ComparisonCell, ComparisonRun } from "@/lib/types";

const SUBSETS = {
  subsets: [
    { name: "36_v2", task_count: 2, tasks: ["task-a", "task-b"] },
    { name: "12_v2", task_count: 1, tasks: ["task-a"] },
  ],
};

function mockApi(response: CompareResponse | Error) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/subsets")) return jsonResponse(SUBSETS);
    if (response instanceof Error) throw response;
    return jsonResponse(response);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function jsonResponse(value: unknown) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(value),
  };
}

function renderCompare() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Compare />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function cell(
  task: string,
  rewardBinary: number,
  rewardPartial: number,
  overrides: Partial<ComparisonCell> = {},
): ComparisonCell {
  const config = overrides.config ?? "baseline";
  const rep = overrides.rep ?? 0;
  return {
    task,
    config,
    rep,
    result_path: `/results/${config}/${task}/rep${rep}/result.json`,
    reward_binary: rewardBinary,
    reward_partial: rewardPartial,
    total_tokens: 1_000_000,
    cost_usd: 1,
    agent_wall_s: 300,
    patch_bytes: 5000,
    difficulty: task === "task-a" ? "easy" : "hard",
    ...overrides,
  };
}

function makeRun(overrides: Partial<ComparisonRun> = {}): ComparisonRun {
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
    median_cost: 1.5,
    median_tokens: 1_000_000,
    median_wall_s: 300,
    total_cost: 3,
    cells: [cell("task-a", 1, 1), cell("task-b", 0, 0.4)],
    ...overrides,
  };
}

function completeResponse(): CompareResponse {
  return {
    subset: "36_v2",
    runs: [
      makeRun(),
      makeRun({
        run_id: "gpt-5.6-sol/low/pi-check",
        config: "pi-check",
        solved: 2,
        solve_rate: 100,
        mean_partial: 0.95,
        total_cost: 4,
        cells: [
          cell("task-a", 1, 1, { config: "pi-check" }),
          cell("task-b", 1, 0.9, { config: "pi-check" }),
        ],
      }),
      makeRun({
        run_id: "gpt-5.6-sol/low/regression",
        config: "regression",
        solved: 0,
        solve_rate: 0,
        mean_partial: 0.2,
        cells: [
          cell("task-a", 0, 0.2, { config: "regression" }),
          cell("task-b", 0, 0.2, { config: "regression" }),
        ],
      }),
      makeRun({
        run_id: "gpt-5.5/low/partial",
        model: "gpt-5.5",
        config: "partial",
        distinct_tasks: 1,
        total_cells: 1,
        cells: [cell("task-a", 1, 1)],
      }),
      makeRun({
        run_id: "gpt-5.5/low/partial-two",
        model: "gpt-5.5",
        config: "partial-two",
        distinct_tasks: 1,
        total_cells: 1,
        cells: [cell("task-a", 0, 0.4)],
      }),
    ],
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Compare page", () => {
  it("renders a bounded loading state", () => {
    mockApi(completeResponse());
    renderCompare();
    expect(screen.getByLabelText("Loading comparison")).toBeInTheDocument();
  });

  it("fetches a fixed subset and first-rep scope by default", async () => {
    const fetchMock = mockApi(completeResponse());
    renderCompare();

    await screen.findByText("Paired config evidence");
    expect(
      fetchMock.mock.calls.some(([url]) =>
        String(url).includes("/api/compare?subset=36_v2&reps=1"),
      ),
    ).toBe(true);
  });

  it("renders a paired decision workspace with separate task and rep evidence", async () => {
    mockApi(completeResponse());
    renderCompare();

    expect(await screen.findByText("B · pi-check: net +1 solved task")).toBeInTheDocument();
    expect(screen.getByLabelText("Comparison dataset")).toBeVisible();
    expect(screen.getByLabelText("Model and thinking group")).toBeVisible();
    expect(screen.getByLabelText("Reference config")).toBeVisible();
    expect(screen.getByLabelText("Reference config")).toHaveValue("gpt-5.6-sol/low/baseline");
    expect(screen.getByLabelText("Challenger config")).toHaveValue("gpt-5.6-sol/low/pi-check");
    expect(screen.getByText("Per-task partial reward")).toBeInTheDocument();
    expect(screen.getByText(/above diagonal favors B · first rep per task/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Zoom to variation" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByText("View all 1 discordant task")).toBeInTheDocument();
    const trajectoryLinks = screen.getAllByRole("link", {
      name: "Compare trajectories for task-b rep 0",
    });
    expect(trajectoryLinks.length).toBeGreaterThan(0);
    for (const trajectoryLink of trajectoryLinks) {
      expect(trajectoryLink).toHaveAttribute(
        "href",
        "/trajectory?left=%2Fresults%2Fbaseline%2Ftask-b%2Frep0%2Fresult.json&right=%2Fresults%2Fpi-check%2Ftask-b%2Frep0%2Fresult.json",
      );
    }
    expect(screen.getAllByText("Task solve · shared").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Rep solve · scoped").length).toBeGreaterThan(0);
    expect(screen.getAllByText("B-only 1").length).toBeGreaterThan(0);
    expect(screen.getByText(/no significance claim is made/i)).toBeInTheDocument();
  });

  it("changes the challenger and recomputes the paired verdict", async () => {
    mockApi(completeResponse());
    renderCompare();
    await screen.findByText("B · pi-check: net +1 solved task");

    fireEvent.change(screen.getByLabelText("Challenger config"), {
      target: { value: "gpt-5.6-sol/low/regression" },
    });

    expect(await screen.findByText("B · regression: net −1 solved task")).toBeInTheDocument();
  });

  it("swaps reference and challenger direction", async () => {
    mockApi(completeResponse());
    renderCompare();
    await screen.findByText("B · pi-check: net +1 solved task");

    fireEvent.click(screen.getByRole("button", { name: "Swap A ↔ B" }));

    expect(await screen.findByText("B · baseline: net −1 solved task")).toBeInTheDocument();
  });

  it("refetches when rep scope changes", async () => {
    const fetchMock = mockApi(completeResponse());
    renderCompare();
    await screen.findByText("Paired config evidence");

    fireEvent.click(screen.getByRole("button", { name: "First 3" }));

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([url]) =>
          String(url).includes("/api/compare?subset=36_v2&reps=3"),
        ),
      ).toBe(true),
    );
  });

  it("keeps partial groups out until explicitly included", async () => {
    mockApi(completeResponse());
    renderCompare();
    await screen.findByText("Paired config evidence");

    expect(screen.queryByRole("option", { name: /gpt-5.5\/low/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Full coverage only" }));

    expect(await screen.findByRole("option", { name: /gpt-5.5\/low/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Partial included" })).toBeInTheDocument();
  });

  it("shows an honest empty intersection instead of crashing", async () => {
    mockApi({
      runs: [
        makeRun({ cells: [] }),
        makeRun({
          run_id: "gpt-5.6-sol/low/pi-check",
          config: "pi-check",
          cells: [],
        }),
      ],
    });
    renderCompare();

    expect(await screen.findByText("B · pi-check: net 0 solved tasks")).toBeInTheDocument();
    expect(screen.getByText(/across 0 shared tasks/i)).toBeInTheDocument();
    expect(screen.getByText("No one-sided task flips.")).toBeInTheDocument();
  });

  it("renders an empty state when no results overlap", async () => {
    mockApi({ runs: [] });
    renderCompare();
    expect(await screen.findByText("No comparable pair")).toBeInTheDocument();
    expect(screen.getByText(/No completed config results overlap/)).toBeInTheDocument();
  });

  it("renders fetch errors", async () => {
    mockApi(new Error("network error"));
    renderCompare();
    expect(await screen.findByText("Unable to load comparison data")).toBeInTheDocument();
  });
});
