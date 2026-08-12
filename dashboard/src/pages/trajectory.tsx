import { useEffect, useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { fetchCellTrajectory } from "@/lib/api";
import type {
  CellTrajectory,
  CellTrajectoryArtifact,
  CellTrajectoryCell,
  CellTrajectoryMetric,
} from "@/lib/types";
import { fmtCost, fmtPercent, fmtSeconds, fmtTokens } from "@/lib/metrics";
import { Sparkline } from "@/components/sparkline";
import { CellTrajectoryTurnCard, type TrajectoryDensity } from "@/components/trajectory-turn";
import { CellTrajectoryArtifactViewer } from "@/components/trajectory-artifact-viewer";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const TRAJECTORY_PAGE_SIZE = 20;
const TRAJECTORY_TABS = ["trace", "tests", "prompt", "patch", "logs"] as const;
const PATCH_KINDS: CellTrajectoryArtifact["kind"][] = ["patch"];
const TEST_KINDS: CellTrajectoryArtifact["kind"][] = ["tests"];
const LOG_KINDS: CellTrajectoryArtifact["kind"][] = ["log"];

type TrajectoryTab = (typeof TRAJECTORY_TABS)[number];

/** Deep-linkable single or paired benchmark trajectory workspace. */
export default function Trajectory() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<TrajectoryTab>("trace");
  const [density, setDensity] = useState<TrajectoryDensity>("focus");
  const paths = trajectoryPaths(searchParams);
  const requestedTurn = parseRequestedTurn(searchParams.get("turn"));
  const offset = Math.floor((requestedTurn - 1) / TRAJECTORY_PAGE_SIZE) * TRAJECTORY_PAGE_SIZE;
  const queries = useQueries({
    queries: paths.map((path) => ({
      queryKey: ["cell-trajectory", path, offset, TRAJECTORY_PAGE_SIZE],
      queryFn: () => fetchCellTrajectory(path, offset, TRAJECTORY_PAGE_SIZE),
      refetchInterval: (query: { state: { data?: CellTrajectory } }) =>
        query.state.data?.session?.is_live ? 4_000 : false,
    })),
  });
  const trajectories = queries.map((query) => query.data).filter(Boolean) as CellTrajectory[];
  const isPaired = paths.length === 2;
  const isLoading = queries.some((query) => query.isLoading);
  const error = queries.find((query) => query.error)?.error;
  const maxTurns = Math.max(0, ...trajectories.map((trajectory) => trajectory.total_turns ?? 0));
  const hasPrevious = offset > 0;
  const hasNext = trajectories.some((trajectory) => trajectory.has_next);

  const chooseTurn = (turn: number) => {
    const next = new URLSearchParams(searchParams);
    if (turn <= 1) next.delete("turn");
    else next.set("turn", String(turn));
    setSearchParams(next);
  };

  useEffect(() => {
    if (maxTurns <= 0 || requestedTurn <= maxTurns) return;
    const next = new URLSearchParams(searchParams);
    next.set("turn", String(maxTurns));
    setSearchParams(next, { replace: true });
  }, [maxTurns, requestedTurn, searchParams, setSearchParams]);

  if (paths.length === 0) {
    return (
      <TrajectoryEmptyState message="Open a result from a run or comparison to inspect its trajectory." />
    );
  }
  if (isLoading) {
    return <TrajectoryLoading />;
  }
  if (error) {
    return <TrajectoryEmptyState message={`Unable to load trajectory: ${String(error)}`} />;
  }
  if (trajectories.some((trajectory) => !trajectory.found)) {
    const missing = trajectories.find((trajectory) => !trajectory.found);
    return (
      <TrajectoryEmptyState
        message={missing?.error ?? "No native Pi session transcript exists for this cell."}
      />
    );
  }

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end gap-3">
        <div>
          <div className="flex items-center gap-3 text-sm">
            <Link to="/compare" className="text-muted-foreground hover:text-foreground">
              ← Compare
            </Link>
            <span className="text-xs font-medium uppercase tracking-[0.18em] text-primary">
              {isPaired ? "Paired trajectories" : "Cell trajectory"}
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            {isPaired ? "Trajectory comparison" : "Trajectory"}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Native session evidence. Focus collapses long reasoning and output; Full expands all
            recorded content.
          </p>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <DensitySelector density={density} onChange={setDensity} />
          {maxTurns > 0 && (
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              Jump to turn
              <select
                aria-label="Jump to turn"
                name="trajectory-turn"
                value={Math.min(requestedTurn, maxTurns)}
                onChange={(event) => chooseTurn(Number(event.target.value))}
                className="rounded-md border border-border bg-card px-2 py-1.5 text-foreground"
              >
                {Array.from({ length: maxTurns }, (_, index) => index + 1).map((turn) => (
                  <option key={turn} value={turn}>
                    {turn}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
      </header>

      <TrajectoryTabList activeTab={activeTab} onChange={setActiveTab} />

      <div className={cn("grid gap-4", isPaired && "xl:grid-cols-2")}>
        {trajectories.map((trajectory, index) => (
          <CellTrajectoryPane
            key={trajectory.cell?.result_path ?? paths[index]}
            trajectory={trajectory}
            activeTab={activeTab}
            density={density}
            sideLabel={isPaired ? (index === 0 ? "A · Reference" : "B · Challenger") : undefined}
          />
        ))}
      </div>

      {activeTab === "trace" && maxTurns > 0 && (
        <TrajectoryPagination
          offset={offset}
          trajectories={trajectories}
          hasPrevious={hasPrevious}
          hasNext={hasNext}
          onPrevious={() => chooseTurn(Math.max(1, offset - TRAJECTORY_PAGE_SIZE + 1))}
          onNext={() => chooseTurn(offset + TRAJECTORY_PAGE_SIZE + 1)}
        />
      )}
    </div>
  );
}

function CellTrajectoryPane({
  trajectory,
  activeTab,
  density,
  sideLabel,
}: {
  trajectory: CellTrajectory;
  activeTab: TrajectoryTab;
  density: TrajectoryDensity;
  sideLabel?: string;
}) {
  const cell = trajectory.cell!;
  const artifacts = trajectory.artifacts ?? [];
  return (
    <section className="min-w-0 space-y-3">
      <TrajectoryCellHeader cell={cell} trajectory={trajectory} sideLabel={sideLabel} />
      {activeTab === "trace" && (
        <>
          <TrajectoryMetricCharts metrics={trajectory.metrics ?? []} paired={Boolean(sideLabel)} />
          <div className="space-y-3">
            {(trajectory.turns ?? []).map((turn) => (
              <CellTrajectoryTurnCard key={turn.idx} turn={turn} density={density} />
            ))}
            {(trajectory.turns ?? []).length === 0 && (
              <p className="rounded-md border border-border p-6 text-sm text-muted-foreground">
                This page contains no assistant turns.
              </p>
            )}
          </div>
        </>
      )}
      {activeTab === "tests" && (
        <TrajectoryTestEvidence trajectory={trajectory} artifacts={artifacts} />
      )}
      {activeTab === "prompt" && (
        <pre className="max-h-[75vh] overflow-auto whitespace-pre-wrap break-words rounded-lg border border-border bg-card p-4 text-sm leading-6">
          {trajectory.prompt || "No user prompt was recorded in this session."}
        </pre>
      )}
      {activeTab === "patch" && (
        <CellTrajectoryArtifactViewer
          artifacts={artifacts}
          kinds={PATCH_KINDS}
          emptyMessage="No model patch was stored for this cell."
        />
      )}
      {activeTab === "logs" && (
        <CellTrajectoryArtifactViewer
          artifacts={artifacts}
          kinds={LOG_KINDS}
          emptyMessage="No text logs were stored for this cell."
        />
      )}
    </section>
  );
}

function TrajectoryCellHeader({
  cell,
  trajectory,
  sideLabel,
}: {
  cell: CellTrajectoryCell;
  trajectory: CellTrajectory;
  sideLabel?: string;
}) {
  const solved = Number(cell.reward_binary ?? 0) >= 1;
  return (
    <section className="rounded-lg border border-border bg-card p-4">
      {sideLabel && (
        <div className="mb-1 text-[10px] font-medium uppercase tracking-[0.16em] text-primary">
          {sideLabel}
        </div>
      )}
      <div className="flex flex-wrap items-start gap-2">
        <div className="min-w-0">
          <h2 className="break-all text-lg font-semibold">{cell.task ?? "Unknown task"}</h2>
          <p className="text-xs text-muted-foreground">
            {cell.config ?? "unknown config"} · rep {cell.rep ?? "—"}
          </p>
        </div>
        <div className="ml-auto flex flex-wrap gap-1.5">
          <Badge variant={solved ? "ok" : "empty"}>{solved ? "solved" : "not solved"}</Badge>
          <Badge>{cell.model ?? trajectory.session?.model ?? "unknown model"}</Badge>
          <Badge>
            {cell.thinking_level ?? trajectory.session?.thinking_level ?? "thinking unknown"}
          </Badge>
          {trajectory.session?.is_live && <Badge variant="ok">live</Badge>}
        </div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
        <TrajectoryHeaderStat
          label="Partial"
          value={fmtPercent(numberValue(cell.reward_partial))}
        />
        <TrajectoryHeaderStat label="F2P" value={fmtPercent(numberValue(cell.f2p))} />
        <TrajectoryHeaderStat label="P2P" value={fmtPercent(numberValue(cell.p2p))} />
        <TrajectoryHeaderStat
          label="Wall time"
          value={fmtSeconds(numberValue(cell.agent_wall_s))}
        />
      </div>
    </section>
  );
}

function TrajectoryHeaderStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-background/50 p-2">
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-0.5 font-medium tabular-nums">{value}</div>
    </div>
  );
}

function TrajectoryMetricCharts({
  metrics,
  paired,
}: {
  metrics: CellTrajectoryMetric[];
  paired: boolean;
}) {
  const latest = metrics.at(-1);
  const charts = [
    {
      label: "Cumulative cost",
      ariaLabel: "Cumulative cost per turn",
      data: metrics.map((metric) => metric.cumulative_cost),
      value: fmtCost(latest?.cumulative_cost),
    },
    {
      label: "Context size",
      ariaLabel: "Context size per turn",
      data: metrics.map((metric) => metric.context_tokens),
      value: fmtTokens(Math.max(0, ...metrics.map((metric) => metric.context_tokens))),
    },
    {
      label: "Output tokens",
      ariaLabel: "Output tokens per turn",
      data: metrics.map((metric) => metric.output_tokens),
      value: fmtTokens(metrics.reduce((total, metric) => total + metric.output_tokens, 0)),
    },
    {
      label: "Observation size",
      ariaLabel: "Observation size per turn",
      data: metrics.map((metric) => metric.observation_chars),
      value: formatCompactCount(
        metrics.reduce((total, metric) => total + metric.observation_chars, 0),
        "chars",
      ),
    },
    {
      label: "Command time",
      ariaLabel: "Command time per turn",
      data: metrics.map((metric) => metric.command_time_ms),
      value: fmtSeconds(
        metrics.reduce((total, metric) => total + metric.command_time_ms, 0) / 1_000,
      ),
    },
  ];

  return (
    <section
      className={cn("grid gap-2 sm:grid-cols-2", paired ? "xl:grid-cols-2" : "xl:grid-cols-5")}
    >
      {charts.map((chart) => (
        <div key={chart.label} className="min-w-0 rounded-lg border border-border bg-card p-3">
          <div className="flex items-baseline justify-between gap-2 text-xs">
            <span className="text-muted-foreground">{chart.label}</span>
            <span className="font-medium tabular-nums">{chart.value}</span>
          </div>
          <div className="mt-2 overflow-hidden">
            <Sparkline data={chart.data} width={240} height={42} ariaLabel={chart.ariaLabel} />
          </div>
        </div>
      ))}
    </section>
  );
}

function TrajectoryTestEvidence({
  trajectory,
  artifacts,
}: {
  trajectory: CellTrajectory;
  artifacts: CellTrajectoryArtifact[];
}) {
  const summary = trajectory.test_summary;
  const cell = trajectory.cell!;
  return (
    <section className="space-y-4 rounded-lg border border-border bg-card p-4">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <TrajectoryHeaderStat
          label="Reward"
          value={Number(cell.reward_binary ?? 0) >= 1 ? "solved" : "not solved"}
        />
        <TrajectoryHeaderStat label="F2P" value={fmtPercent(numberValue(cell.f2p))} />
        <TrajectoryHeaderStat label="P2P" value={fmtPercent(numberValue(cell.p2p))} />
        <TrajectoryHeaderStat label="Verifier exit" value={String(cell.verifier_exit ?? "—")} />
      </div>
      {summary ? (
        <div className="flex flex-wrap gap-2 text-xs">
          <Badge variant="ok">{summary.passed} passed</Badge>
          <Badge variant={summary.failed > 0 ? "failed" : "default"}>{summary.failed} failed</Badge>
          <Badge>{summary.skipped} skipped</Badge>
          <Badge>{summary.tests} total</Badge>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No CTRF summary was stored.</p>
      )}
      <CellTrajectoryArtifactViewer
        artifacts={artifacts}
        kinds={TEST_KINDS}
        emptyMessage="No verifier or test report files were stored for this cell."
      />
    </section>
  );
}

function TrajectoryTabList({
  activeTab,
  onChange,
}: {
  activeTab: TrajectoryTab;
  onChange: (tab: TrajectoryTab) => void;
}) {
  return (
    <div
      role="tablist"
      aria-label="Trajectory evidence"
      className="flex overflow-x-auto border-b border-border"
    >
      {TRAJECTORY_TABS.map((tab) => (
        <button
          key={tab}
          role="tab"
          aria-selected={activeTab === tab}
          onClick={() => onChange(tab)}
          className={cn(
            "border-b-2 px-4 py-2 text-sm capitalize",
            activeTab === tab
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground",
          )}
        >
          {capitalizeTrajectoryLabel(tab)}
        </button>
      ))}
    </div>
  );
}

function DensitySelector({
  density,
  onChange,
}: {
  density: TrajectoryDensity;
  onChange: (density: TrajectoryDensity) => void;
}) {
  return (
    <div className="flex rounded-md border border-border bg-card p-0.5">
      {(["focus", "full"] as const).map((choice) => (
        <button
          key={choice}
          aria-pressed={density === choice}
          onClick={() => onChange(choice)}
          className={cn(
            "rounded px-2.5 py-1 text-xs capitalize",
            density === choice ? "bg-accent text-foreground" : "text-muted-foreground",
          )}
        >
          {capitalizeTrajectoryLabel(choice)}
        </button>
      ))}
    </div>
  );
}

function TrajectoryPagination({
  offset,
  trajectories,
  hasPrevious,
  hasNext,
  onPrevious,
  onNext,
}: {
  offset: number;
  trajectories: CellTrajectory[];
  hasPrevious: boolean;
  hasNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
}) {
  const maxVisible = Math.max(
    0,
    ...trajectories.map((trajectory) => trajectory.turns?.length ?? 0),
  );
  const maxTurns = Math.max(0, ...trajectories.map((trajectory) => trajectory.total_turns ?? 0));
  return (
    <nav
      className="flex items-center justify-center gap-3 text-xs text-muted-foreground"
      aria-label="Trajectory pages"
    >
      <button
        onClick={onPrevious}
        disabled={!hasPrevious}
        className="rounded-md border border-border px-3 py-1.5 text-foreground disabled:cursor-not-allowed disabled:opacity-40"
      >
        Previous turns
      </button>
      <span className="tabular-nums">
        {offset + 1}–{Math.min(maxTurns, offset + maxVisible)} of {maxTurns}
      </span>
      <button
        onClick={onNext}
        disabled={!hasNext}
        className="rounded-md border border-border px-3 py-1.5 text-foreground disabled:cursor-not-allowed disabled:opacity-40"
      >
        Next turns
      </button>
    </nav>
  );
}

function TrajectoryLoading() {
  return (
    <div aria-label="Loading trajectory" className="space-y-3">
      <div className="h-24 animate-pulse rounded-lg border border-border bg-card" />
      <div className="h-48 animate-pulse rounded-lg border border-border bg-card" />
    </div>
  );
}

function TrajectoryEmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-10 text-center">
      <h1 className="text-lg font-semibold">Trajectory unavailable</h1>
      <p className="mt-1 text-sm text-muted-foreground">{message}</p>
      <Link to="/compare" className="mt-4 inline-block text-sm text-primary hover:underline">
        Open Compare
      </Link>
    </div>
  );
}

function trajectoryPaths(searchParams: URLSearchParams): string[] {
  const left = searchParams.get("left");
  const right = searchParams.get("right");
  if (left && right) return [left, right];
  const path = searchParams.get("path") ?? left ?? right;
  return path ? [path] : [];
}

function parseRequestedTurn(raw: string | null): number {
  const turn = Number(raw ?? 1);
  return Number.isInteger(turn) && turn > 0 ? turn : 1;
}

function numberValue(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function capitalizeTrajectoryLabel(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatCompactCount(value: number, unit: string): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M ${unit}`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}k ${unit}`;
  return `${value} ${unit}`;
}
