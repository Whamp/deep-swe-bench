import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LiveScore } from "@/components/live-score";
import type { RunScore, RunSummary } from "@/lib/types";
import { renderDashboardRoute } from "@/test/dashboard-test-harness";

const run: RunSummary = {
  run_id: "live-score-run",
  state: "running",
  kind: "structured",
  model: "openai-codex/gpt-5.6-sol",
  thinking: "low",
  configs: ["pi-fabric@1.0.0"],
  launch_metadata: "confirmed_plan",
  preflight_state: "passed",
  counts: {},
  active_count: 1,
  stale_cell_count: 0,
};

const score: RunScore = {
  finished: 2,
  processed: 2,
  solved: 1,
  tasks_total: 2,
  tasks_solved: 1,
  solve_rate: 50,
  mean_partial: 0.6,
  tool_calls: 4,
  tool_call_errors: 1,
  tool_call_error_rate: 0.25,
  active: 1,
  cumulative_cost: 1,
  cost_per_solve: 1,
  projected_total_cost: 2,
  throughput_cells_per_hr: 10,
  eta_s: 360,
  failure_breakdown: {},
  timeline: [
    {
      ts: "2026-01-01T00:00:01Z",
      finished: 1,
      solved: 0,
      cost: 0.4,
      mean_partial: 0.4,
      tool_calls: 2,
      tool_call_errors: 0,
      tool_call_error_rate: 0,
    },
    {
      ts: "2026-01-01T00:00:02Z",
      finished: 2,
      solved: 1,
      cost: 1,
      mean_partial: 0.6,
      tool_calls: 4,
      tool_call_errors: 1,
      tool_call_error_rate: 0.25,
    },
  ],
  tasks: [
    {
      task: "task-a",
      best_reward_binary: 1,
      best_reward_partial: 1,
      reps: 1,
      solved: true,
      last_outcome: "ok",
    },
    {
      task: "task-b",
      best_reward_binary: 0,
      best_reward_partial: 0.2,
      reps: 1,
      solved: false,
      last_outcome: "ok",
    },
  ],
};

describe("LiveScore rate plots", () => {
  it("does not fabricate a baseline delta for a multi-config run", async () => {
    const fetchMock = vi.fn(async (input) => {
      const url = String(input);
      const body = url.includes("/score") ? { score } : { runs: [] };
      return {
        ok: true,
        status: 200,
        json: async () => body,
      } as Response;
    });
    globalThis.fetch = fetchMock;

    renderDashboardRoute(
      <LiveScore run={{ ...run, configs: ["baseline@1.0.0", "pi-check@1.0.1"] }} />,
      "/",
      "/",
    );

    expect(await screen.findByText(/configs combined/)).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes("/api/compare"))).toBe(
      false,
    );
  });

  it("plots cumulative mean partial and tool-call error rate", async () => {
    globalThis.fetch = vi.fn(async (input) => {
      const url = String(input);
      const body = url.includes("/score") ? { score } : { runs: [] };
      return {
        ok: true,
        status: 200,
        json: async () => body,
      } as Response;
    });

    renderDashboardRoute(<LiveScore run={run} />, "/", "/");

    expect(
      await screen.findByRole("img", { name: "Cumulative mean partial reward over time" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Cumulative tool-call error rate over time" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Mean partial · 60.0%")).toBeInTheDocument();
    expect(screen.getByText("Tool errors · 25.0%")).toBeInTheDocument();
    expect(screen.getByText("1/4 calls")).toBeInTheDocument();
  });
});
