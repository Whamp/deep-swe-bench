import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CellSessionPanel } from "@/components/cell-session";
import type { Cell, RunDetail as RunDetailData } from "@/lib/types";
import RunDetail from "@/pages/run-detail";
import { mockDashboardJson, renderDashboardRoute } from "@/test/dashboard-test-harness";

function renderRunDetail(run: RunDetailData) {
  mockDashboardJson(run);
  return renderDashboardRoute(<RunDetail />, "/run/:runId", "/run/confirmed-run");
}

describe("Run detail confirmed-launch summary", () => {
  it("shows approval identity, workspace, progress, and preflight verdict", async () => {
    renderRunDetail({
      active_count: 0,
      configs: ["pi-check@1.0.1"],
      counts: {
        batch_done: 1,
        batch_skipped: 1,
        batch_total: 1,
        preflight_done: 1,
        preflight_failed: 0,
      },
      kind: "structured",
      launch_metadata: "confirmed_plan",
      launch_plan_identity: "sha256:4489b49b",
      preflight_state: "passed",
      run_id: "confirmed-run",
      stage: "done",
      stale_cell_count: 0,
      state: "completed",
      workspace: "/repo/.worktrees/confirmed-launch",
    });

    expect(await screen.findByText("confirmed-run")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Run detail level" })).toBeInTheDocument();
    expect(screen.getByText("plan sha256:4489b49b")).toBeInTheDocument();
    expect(screen.getByText("preflight passed")).toBeInTheDocument();
    expect(screen.getByText("/repo/.worktrees/confirmed-launch")).toBeInTheDocument();
    expect(screen.getByText("1/1 done")).toBeInTheDocument();
  });
});

describe("Run detail preflight smoke inspection", () => {
  it("shows passed and failed smoke evidence, diagnostics, and session access", async () => {
    renderRunDetail({
      active_count: 0,
      counts: { batch_done: 0, batch_total: 0, preflight_done: 2, preflight_failed: 1 },
      kind: "structured",
      launch_metadata: "confirmed_plan",
      preflight_state: "failed",
      run_id: "confirmed-run",
      stale_cell_count: 0,
      state: "failed",
      preflight: {
        "task/pi-check/rep0": {
          cell_id: "task/pi-check/rep0",
          task: "smoke-task",
          config: "pi-check@1.3.0",
          rep: 0,
          state: "passed",
          outcome: "ok",
          result_path: "/repo/results/pi-check/smoke-task/rep0/result.json",
          log_path: "/repo/results/_runs/confirmed-run/logs/pi-check.log",
          contract_path: "/repo/configs/pi-check/smoke.json",
          summary: {
            reward_binary: 0,
            reward_partial: 0.8010204081632653,
            total_tokens: 6_784_328,
            cost_usd: 0,
            agent_wall_s: 413,
          },
          diagnostics: [],
        },
        "task/baseline/rep0": {
          cell_id: "task/baseline/rep0",
          task: "smoke-task",
          config: "baseline@1.0.0",
          rep: 0,
          state: "failed",
          outcome: "empty",
          result_path: "/repo/results/baseline/smoke-task/rep0/result.json",
          log_path: "/repo/results/_runs/confirmed-run/logs/baseline.log",
          contract_path: "/repo/configs/baseline/smoke.json",
          summary: { reward_binary: -1, reward_partial: 0, total_tokens: 0 },
          diagnostics: [
            {
              requirement: "usage_evidence",
              target: "result.total_tokens",
              reason: "expected a positive number, got 0",
            },
          ],
        },
      },
    });

    expect(await screen.findByText("Preflight / smoke · 2 · 1 passed")).toBeInTheDocument();
    expect(screen.getByText("pi-check@1.3.0")).toBeInTheDocument();
    expect(screen.getByText("baseline@1.0.0")).toBeInTheDocument();
    expect(screen.getByText("80.1%")).toBeInTheDocument();
    expect(screen.getByText("usage_evidence · result.total_tokens")).toBeInTheDocument();
    expect(screen.getByText("expected a positive number, got 0")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "contract" })).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: /view session/i })).toHaveLength(2);
  });
});

describe("Run detail completed rep inspection", () => {
  const finishedCell: Cell = {
    task: "task-success",
    config: "cfg@1.0.0",
    rep: 0,
    state: "done",
    result_path: "/repo/results/model/high/cfg/task-success/rep_0/result.json",
    summary: { reward_binary: 1, reward_partial: 0.875 },
  };

  it("keeps a successful finished rep visible with outcome, partial score, and session access", async () => {
    renderRunDetail({
      run_id: "confirmed-run",
      state: "completed",
      kind: "structured",
      counts: { batch_done: 1, batch_total: 1, ok: 1 },
      active_count: 0,
      stale_cell_count: 0,
      launch_metadata: "confirmed_plan",
      preflight_state: "passed",
      recent_finished: [
        {
          cell_id: "task-success--cfg--rep0",
          task: "task-success",
          config: "cfg@1.0.0",
          rep: 0,
          state: "done",
          outcome: "ok",
          result_path: "/repo/results/model/high/cfg/task-success/rep_0/result.json",
          log_path: "/repo/results/model/high/cfg/task-success/rep_0/logs/agent.log",
          summary: {
            reward_binary: 1,
            reward_partial: 0.875,
            f2p: 0.1363636364,
            p2p: 0.938276114,
            output_tokens: 56_527,
            agent_wall_s: 1_261,
            tool_calls: 107,
            tool_call_errors: 5,
            tool_call_error_rate: 0.0467,
          },
        },
      ],
    });

    expect(await screen.findByText("task-success")).toBeInTheDocument();
    expect(screen.getByText("87.5%")).toBeInTheDocument();
    expect(screen.getByText("13.6%")).toBeInTheDocument();
    expect(screen.getByText("93.8%")).toBeInTheDocument();
    expect(screen.getByText("56.5k")).toBeInTheDocument();
    expect(screen.getByText("21m")).toBeInTheDocument();
    expect(screen.getByText("5/107 · 4.7%")).toBeInTheDocument();
    expect(screen.getByText("ok")).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: "Config" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /view session/i })).toBeInTheDocument();
    expect(screen.queryByText(/all ok/i)).not.toBeInTheDocument();
  });

  it("shows a finished rep's parsed tool-call error count and rate", async () => {
    mockDashboardJson({
      session: {
        found: true,
        turns: 1,
        total_tokens: 100,
        total_cost: 0.01,
        tool_calls: 4,
        tool_call_errors: 1,
        tool_call_error_rate: 0.25,
        is_live: false,
        turns_list: [],
      },
    });
    renderDashboardRoute(<CellSessionPanel cell={finishedCell} onClose={vi.fn()} />, "/", "/");

    expect(await screen.findByText("1/4 tool calls · 25.0% error rate")).toBeInTheDocument();
  });
});
