import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Trajectory from "@/pages/trajectory";
import { renderDashboardRoute } from "@/test/dashboard-test-harness";

const RESULT_PATH = "/repo/results/model/high/cfg/task-a/rep0/result.json";

function trajectoryResponse(offset: number | "latest", resultPath = RESULT_PATH) {
  const isFinalPage = offset === 20 || offset === "latest";
  const turns = isFinalPage
    ? [makeTurn(21, "Final verification"), makeTurn(22, "Most recent verification")]
    : [makeTurn(1, "Inspect code")];
  const config = resultPath.includes("challenger") ? "challenger@1.0.0" : "cfg@1.0.0";
  return {
    trajectory: {
      found: true,
      cell: {
        result_path: resultPath,
        cell_path: resultPath.replace("/result.json", ""),
        task: "task-a",
        config,
        rep: 0,
        model: "provider/model-a",
        thinking_level: "high",
        reward_binary: 1,
        reward_partial: 0.75,
        f2p: 0.5,
        p2p: 1,
        agent_wall_s: 125,
      },
      session: {
        id: "session-1",
        provider: "provider",
        model: "model-a",
        thinking_level: "high",
        path: "/repo/session.jsonl",
        updated_at: 1_700_000_000,
        is_live: false,
      },
      prompt: "Implement the requested behavior exactly.",
      artifacts: [
        {
          path: "/repo/cell/artifacts/model.patch",
          relative_path: "artifacts/model.patch",
          kind: "patch",
          size: 24,
        },
        {
          path: "/repo/cell/verifier/ctrf.json",
          relative_path: "verifier/ctrf.json",
          kind: "tests",
          size: 80,
        },
        {
          path: "/repo/cell/logs/pi.stderr.txt",
          relative_path: "logs/pi.stderr.txt",
          kind: "log",
          size: 0,
        },
        {
          path: "/repo/cell/logs/verifier.stdout.txt",
          relative_path: "logs/verifier.stdout.txt",
          kind: "log",
          size: 42,
        },
      ],
      test_summary: {
        tests: 3,
        passed: 2,
        failed: 1,
        skipped: 0,
        pending: 0,
        other: 0,
      },
      total_turns: 22,
      offset: isFinalPage ? 20 : offset,
      limit: 20,
      has_previous: isFinalPage || Number(offset) > 0,
      has_next: offset === 0,
      turns,
      metrics: Array.from({ length: 22 }, (_, index) => ({
        idx: index + 1,
        timestamp: `2026-01-01T00:00:${String(index).padStart(2, "0")}.000Z`,
        intent: `Turn ${index + 1}`,
        cumulative_cost: (index + 1) / 100,
        context_tokens: (index + 1) * 1_000,
        output_tokens: (index + 1) * 10,
        total_tokens: (index + 1) * 1_010,
        observation_chars: (index + 1) * 100,
        command_time_ms: (index + 1) * 50,
      })),
    },
  };
}

function makeTurn(idx: number, reasoning: string) {
  return {
    idx,
    id: `turn-${idx}`,
    timestamp: "2026-01-01T00:00:02.000Z",
    elapsed_s: idx * 2,
    stop_reason: "toolUse",
    error: null,
    usage: {
      input_tokens: 200,
      output_tokens: 40,
      cache_read_tokens: 100,
      cache_write_tokens: 0,
      reasoning_tokens: 10,
      total_tokens: 350,
      cost: 0.02,
    },
    cumulative_cost: idx * 0.02,
    observation_chars: 42,
    command_time_ms: 2_000,
    blocks: [
      { type: "thinking", text: reasoning },
      { type: "text", text: "I will run the focused test." },
      { type: "unknown", data: { provider_event: "retained exactly" } },
      {
        type: "tool_call",
        id: `call-${idx}`,
        name: "bash",
        arguments: { command: "pytest -q tests/test_feature.py" },
        result: {
          timestamp: "2026-01-01T00:00:04.000Z",
          text: "focused test output\ncomplete final line",
          is_error: false,
          details: { exitCode: 0 },
          duration_ms: 2_000,
        },
      },
      {
        type: "tool_result",
        id: "orphan-1",
        name: "provider_tool",
        timestamp: "2026-01-01T00:00:05.000Z",
        text: "orphan output byte for byte",
        is_error: false,
        details: { provider_trace: "orphan details retained" },
        duration_ms: 0,
      },
    ],
  };
}

function mockTrajectoryApi() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = new URL(String(input), "http://dashboard.test");
    if (url.pathname === "/api/cell-trajectory") {
      return jsonResponse(
        trajectoryResponse(
          url.searchParams.get("offset") === "latest"
            ? "latest"
            : Number(url.searchParams.get("offset") ?? 0),
          url.searchParams.get("path") ?? RESULT_PATH,
        ),
      );
    }
    if (url.pathname === "/api/file") {
      return {
        ok: true,
        status: 200,
        text: () => Promise.resolve("artifact preview"),
      };
    }
    throw new Error(`Unexpected dashboard request: ${url}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function jsonResponse(value: unknown) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(value),
    text: () => Promise.resolve(JSON.stringify(value)),
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Trajectory page", () => {
  it("opens the latest page and lists the most recent turn first by default", async () => {
    const fetchMock = mockTrajectoryApi();
    renderDashboardRoute(
      <Trajectory />,
      "/trajectory",
      `/trajectory?path=${encodeURIComponent(RESULT_PATH)}`,
    );

    expect(await screen.findByText("Most recent verification")).toBeInTheDocument();
    expect(screen.getAllByText(/^Turn (21|22)$/).map((turn) => turn.textContent)).toEqual([
      "Turn 22",
      "Turn 21",
    ]);
    expect(screen.getByRole("combobox", { name: "Jump to turn" })).toHaveValue("22");
    expect(screen.getByRole("button", { name: "Next turns" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Previous turns" })).toBeEnabled();
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes("offset=latest"))).toBe(
      true,
    );
  });

  it("renders a complete deep-linked turn page with charts and evidence tabs", async () => {
    const fetchMock = mockTrajectoryApi();
    renderDashboardRoute(
      <Trajectory />,
      "/trajectory",
      `/trajectory?path=${encodeURIComponent(RESULT_PATH)}&turn=1`,
    );

    expect(await screen.findByRole("heading", { name: "task-a" })).toBeInTheDocument();
    expect(screen.getByText("cfg@1.0.0 · rep 0")).toBeInTheDocument();
    expect(screen.getByText("Inspect code")).toBeInTheDocument();
    expect(screen.getByText("I will run the focused test.")).toBeInTheDocument();
    expect(screen.getByText(/pytest -q tests\/test_feature.py/)).toBeInTheDocument();
    expect(screen.getByText(/complete final line/)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Cumulative cost per turn" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Context size per turn" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Output tokens per turn" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Observation size per turn" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Command time per turn" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Full" }));
    expect(screen.getAllByText("Structured details")).toHaveLength(2);
    for (const summary of screen.getAllByText("Structured details")) {
      expect(summary.closest("details")).toHaveAttribute("open");
    }
    expect(screen.getByText("Unrecognized provider block").closest("details")).toHaveAttribute(
      "open",
    );
    expect(screen.getByText(/orphan details retained/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Prompt" }));
    expect(screen.getByText("Implement the requested behavior exactly.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Tests" }));
    expect(screen.getByText("2 passed")).toBeInTheDocument();
    expect(screen.getByText("1 failed")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Logs" }));
    expect(screen.getByRole("combobox", { name: "File" })).toHaveValue(
      "/repo/cell/logs/verifier.stdout.txt",
    );

    fireEvent.click(screen.getByRole("tab", { name: "Trace" }));
    fireEvent.click(screen.getByRole("button", { name: "Next turns" }));
    expect(await screen.findByText("Final verification")).toBeInTheDocument();
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([input]) => String(input).includes("offset=20"))).toBe(
        true,
      ),
    );
  });

  it("normalizes an out-of-range turn link to the final real page", async () => {
    const fetchMock = mockTrajectoryApi();
    renderDashboardRoute(
      <Trajectory />,
      "/trajectory",
      `/trajectory?path=${encodeURIComponent(RESULT_PATH)}&turn=999`,
    );

    expect(await screen.findByText("Final verification")).toBeInTheDocument();
    await waitFor(() => {
      const offsets = fetchMock.mock.calls
        .filter(([input]) => String(input).includes("/api/cell-trajectory"))
        .map(([input]) =>
          new URL(String(input), "http://dashboard.test").searchParams.get("offset"),
        );
      expect(offsets).toContain("980");
      expect(offsets).toContain("20");
    });
  });

  it("waits for both paired responses before assigning reference and challenger labels", async () => {
    const referencePath = "/repo/results/model/high/baseline/task-a/rep0/result.json";
    const challengerPath = "/repo/results/model/high/challenger/task-a/rep0/result.json";
    let releaseReference!: () => void;
    let markChallengerLoaded!: () => void;
    const challengerLoaded = new Promise<void>((resolve) => {
      markChallengerLoaded = resolve;
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), "http://dashboard.test");
      const resultPath = url.searchParams.get("path") ?? RESULT_PATH;
      if (resultPath === referencePath) {
        await new Promise<void>((resolve) => {
          releaseReference = resolve;
        });
      } else {
        markChallengerLoaded();
      }
      return jsonResponse(trajectoryResponse(0, resultPath));
    });
    vi.stubGlobal("fetch", fetchMock);
    renderDashboardRoute(
      <Trajectory />,
      "/trajectory",
      `/trajectory?left=${encodeURIComponent(referencePath)}&right=${encodeURIComponent(challengerPath)}`,
    );

    await act(async () => {
      await challengerLoaded;
      await new Promise((resolve) => setTimeout(resolve, 20));
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(screen.getByLabelText("Loading trajectory")).toBeInTheDocument();
    expect(screen.queryByText("A · Reference")).not.toBeInTheDocument();
    await act(async () => releaseReference());
    expect(await screen.findByText("A · Reference")).toBeInTheDocument();
    expect(screen.getByText("B · Challenger")).toBeInTheDocument();
  });

  it("renders two matched result paths as synchronized reference and challenger panes", async () => {
    const fetchMock = mockTrajectoryApi();
    const referencePath = "/repo/results/model/high/baseline/task-a/rep0/result.json";
    const challengerPath = "/repo/results/model/high/challenger/task-a/rep0/result.json";
    renderDashboardRoute(
      <Trajectory />,
      "/trajectory",
      `/trajectory?left=${encodeURIComponent(referencePath)}&right=${encodeURIComponent(challengerPath)}`,
    );

    expect(
      await screen.findByRole("heading", { name: "Trajectory comparison" }),
    ).toBeInTheDocument();
    expect(screen.getByText("A · Reference")).toBeInTheDocument();
    expect(screen.getByText("B · Challenger")).toBeInTheDocument();
    expect(screen.getByText("challenger@1.0.0 · rep 0")).toBeInTheDocument();
    expect(screen.getAllByRole("img", { name: "Cumulative cost per turn" })).toHaveLength(2);

    fireEvent.click(screen.getByRole("tab", { name: "Logs" }));
    const fileSelectors = screen.getAllByRole("combobox", { name: "File" });
    expect(fileSelectors).toHaveLength(2);
    expect(new Set(fileSelectors.map((select) => select.id)).size).toBe(2);

    const fetchedPaths = fetchMock.mock.calls
      .map(([input]) => new URL(String(input), "http://dashboard.test"))
      .filter((url) => url.pathname === "/api/cell-trajectory")
      .map((url) => url.searchParams.get("path"));
    expect(fetchedPaths).toEqual(expect.arrayContaining([referencePath, challengerPath]));
  });
});
