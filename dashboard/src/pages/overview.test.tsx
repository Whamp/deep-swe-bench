import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { RunSummary } from "@/lib/types";
import Overview from "@/pages/overview";
import { mockDashboardJson, renderDashboardRoute } from "@/test/dashboard-test-harness";

describe("Overview page", () => {
  it("renders a bounded loading state initially", () => {
    mockDashboardJson({ runs: [] });
    renderDashboardRoute(<Overview />, "/", "/");
    expect(screen.getByText(/Loading active runs/i)).toBeInTheDocument();
  });

  it("keeps completed runs in compact History, not the default view", async () => {
    const runs: RunSummary[] = [
      {
        run_id: "test-run-1",
        state: "completed",
        kind: "structured",
        counts: { batch_done: 10, batch_total: 10, ok: 8 },
        active_count: 0,
        stale_cell_count: 0,
        model: "test-model",
        thinking: "low",
        configs: ["baseline@1.0.0"],
        launch_metadata: "confirmed_plan",
        preflight_state: "passed",
      },
    ];
    mockDashboardJson({ runs });
    renderDashboardRoute(<Overview />, "/", "/");

    expect(await screen.findByText("No runs are running")).toBeInTheDocument();
    expect(screen.queryByText("test-run-1")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /^History/i }));
    expect(screen.getByText("test-run-1")).toBeInTheDocument();
    expect(screen.getByText("baseline@1.0.0")).toBeInTheDocument();
    expect(screen.getAllByText(/test-model/i).length).toBeGreaterThan(0);
  });

  it("renders empty state when no runs", async () => {
    mockDashboardJson({ runs: [] });
    renderDashboardRoute(<Overview />, "/", "/");
    expect(await screen.findByText(/No structured state/i)).toBeInTheDocument();
  });
});

describe("Overview active health", () => {
  it("shows stale badge on a genuinely running card", async () => {
    const runs: RunSummary[] = [
      {
        run_id: "stale-cell-run",
        state: "running",
        kind: "structured",
        counts: { batch_done: 5, batch_total: 10 },
        active_count: 3,
        stale_cell_count: 2,
        max_cell_age_s: 2400,
        launch_metadata: "legacy_structured",
        preflight_state: "running",
      },
    ];
    mockDashboardJson({ runs });
    renderDashboardRoute(<Overview />, "/", "/");
    expect(await screen.findByText("2 stale")).toBeInTheDocument();
  });

  it("labels preflight honestly instead of showing green zero active", async () => {
    const runs: RunSummary[] = [
      {
        run_id: "preflight-run",
        state: "running",
        stage: "preflight",
        kind: "structured",
        counts: { batch_done: 0, batch_total: 36 },
        active_count: 0,
        stale_cell_count: 0,
        launch_metadata: "confirmed_plan",
        preflight_state: "running",
      },
    ];
    mockDashboardJson({ runs });
    renderDashboardRoute(<Overview />, "/", "/");
    expect(await screen.findByText("preflight in progress")).toBeInTheDocument();
    expect(screen.queryByText("0 active")).not.toBeInTheDocument();
  });
});

describe("Overview views and filtering", () => {
  const mixedRuns: RunSummary[] = [
    {
      run_id: "live-run",
      state: "running",
      kind: "structured",
      counts: { batch_done: 1, batch_total: 10 },
      active_count: 2,
      stale_cell_count: 0,
      launch_metadata: "confirmed_plan",
      preflight_state: "passed",
      model: "gpt-5.5",
      thinking: "low",
      configs: ["pi-check"],
      heartbeat_age_s: 5,
    },
    {
      run_id: "dead-run",
      state: "stalled",
      kind: "structured",
      counts: { batch_done: 3, batch_total: 10 },
      active_count: 0,
      stale_cell_count: 0,
      launch_metadata: "legacy_structured",
      preflight_state: "passed",
      model: "gpt-5.5",
      thinking: "low",
      configs: ["old"],
      heartbeat_age_s: 90000,
      updated_at: "2026-08-10T00:00:00Z",
    },
    {
      run_id: "failed-run",
      state: "failed",
      kind: "structured",
      counts: { batch_done: 6, batch_total: 10 },
      active_count: 0,
      stale_cell_count: 0,
      launch_metadata: "confirmed_plan",
      preflight_state: "passed",
      model: "gpt-5.5",
      thinking: "low",
      configs: ["retired-attempt"],
      heartbeat_age_s: 12000,
      updated_at: "2026-08-12T00:00:00Z",
    },
    {
      run_id: "finished-run",
      state: "completed",
      kind: "structured",
      counts: { batch_done: 10, batch_total: 10 },
      active_count: 0,
      stale_cell_count: 0,
      launch_metadata: "confirmed_plan",
      preflight_state: "passed",
      model: "qwen",
      thinking: "high",
      configs: ["baseline"],
      heartbeat_age_s: 200000,
      updated_at: "2026-08-11T00:00:00Z",
      score_snapshot: { solved: 8, finished: 10, solve_rate: 80 },
    },
  ];

  it("defaults to ongoing: live card plus actionable stalled rows, no terminal history", async () => {
    mockDashboardJson({ runs: mixedRuns });
    renderDashboardRoute(<Overview />, "/", "/");
    expect(await screen.findByText("live-run")).toBeInTheDocument();
    expect(screen.getByText("dead-run")).toBeInTheDocument();
    expect(screen.queryByText("failed-run")).not.toBeInTheDocument();
    expect(screen.queryByText("finished-run")).not.toBeInTheDocument();
  });

  it("reserves Needs attention for stalled runs and states the next action", async () => {
    mockDashboardJson({ runs: mixedRuns });
    renderDashboardRoute(<Overview />, "/", "/");
    await screen.findByText("live-run");
    await userEvent.click(screen.getByRole("button", { name: "Needs attention 1" }));
    expect(screen.getByText("dead-run")).toBeInTheDocument();
    expect(screen.getByText("No heartbeat for 25.0h")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Inspect stalled run dead-run" })).toBeInTheDocument();
    expect(screen.queryByText("failed-run")).not.toBeInTheDocument();
    expect(screen.queryByText("live-run")).not.toBeInTheDocument();
    expect(screen.queryByText("finished-run")).not.toBeInTheDocument();
  });

  it("keeps terminal failures and completed runs in History without duplicating attention", async () => {
    mockDashboardJson({ runs: mixedRuns });
    renderDashboardRoute(<Overview />, "/", "/");
    await screen.findByText("live-run");
    await userEvent.click(screen.getByRole("button", { name: "History 2" }));
    expect(screen.getByText("failed-run")).toBeInTheDocument();
    expect(screen.getByText("finished-run")).toBeInTheDocument();
    expect(screen.getAllByRole("link").map((link) => link.getAttribute("aria-label"))).toEqual([
      "View run failed-run",
      "View run finished-run",
    ]);
    expect(screen.queryByText("dead-run")).not.toBeInTheDocument();
    expect(screen.queryByText("live-run")).not.toBeInTheDocument();
  });

  it("search filters by text within the selected view", async () => {
    mockDashboardJson({ runs: mixedRuns });
    renderDashboardRoute(<Overview />, "/", "/");
    await screen.findByText("live-run");
    await userEvent.click(screen.getByRole("button", { name: /^History/i }));
    const search = screen.getByLabelText("Filter runs");
    await userEvent.type(search, "qwen");
    expect(screen.getByText("finished-run")).toBeInTheDocument();
    expect(screen.queryByText("dead-run")).not.toBeInTheDocument();
  });

  it("renders stalled state honestly instead of running", async () => {
    mockDashboardJson({ runs: mixedRuns });
    renderDashboardRoute(<Overview />, "/", "/");
    await screen.findByText("dead-run");
    expect(screen.getByText("stalled")).toBeInTheDocument();
  });
});
