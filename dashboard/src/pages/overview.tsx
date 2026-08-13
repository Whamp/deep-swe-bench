import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchRuns } from "@/lib/api";
import type { RunSummary, Counts } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StateBadge, Badge } from "@/components/ui/badge";
import { ErrorState } from "@/components/error-state";
import { fmtSeconds, rateColor } from "@/lib/metrics";

type View = "ongoing" | "attention" | "history";
const ATTENTION_WINDOW_S = 7 * 24 * 3600;

function isActionableStalledRun(run: RunSummary): boolean {
  return (
    run.state === "stalled" &&
    run.heartbeat_age_s != null &&
    run.heartbeat_age_s < ATTENTION_WINDOW_S
  );
}

export default function Overview() {
  const {
    data: runs,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["runs"],
    queryFn: () => fetchRuns("summary"),
    refetchInterval: 5000,
  });
  const [query, setQuery] = useState("");
  const [view, setView] = useState<View>("ongoing");

  const data = useMemo(() => {
    const q = query.trim().toLowerCase();
    const matching = (runs || []).filter((r) => {
      if (!q) return true;
      return [r.run_id, r.run_key || "", r.model || "", r.thinking || "", ...(r.configs || [])]
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
    const sort = (items: RunSummary[]) =>
      [...items].sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""));
    const ongoing = sort(matching.filter((r) => r.state === "running"));
    const attention = sort(matching.filter(isActionableStalledRun));
    const history = sort(
      matching.filter((r) => r.state !== "running" && !isActionableStalledRun(r)),
    );
    return { ongoing, attention, history };
  }, [runs, query]);

  if (isLoading) return <LoadingOverview />;
  if (error) return <ErrorState title="Unable to load runs" message={String(error)} />;
  if (!runs || runs.length === 0)
    return (
      <p className="text-muted-foreground">No structured state or legacy track files found.</p>
    );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="text-lg font-bold">Agent sessions</h1>
          <p className="text-xs text-muted-foreground">
            Live operational view · refreshes every 5s
          </p>
        </div>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter by run, config, model…"
          aria-label="Filter runs"
          className="ml-auto min-w-[16rem] rounded-md border border-border bg-card px-3 py-1.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none"
        />
      </div>

      <div className="flex items-center gap-1 border-b border-border">
        <ViewTab
          active={view === "ongoing"}
          onClick={() => setView("ongoing")}
          label="Ongoing"
          count={data.ongoing.length}
        />
        <ViewTab
          active={view === "attention"}
          onClick={() => setView("attention")}
          label="Needs attention"
          count={data.attention.length}
        />
        <ViewTab
          active={view === "history"}
          onClick={() => setView("history")}
          label="History"
          count={data.history.length}
        />
      </div>

      {view === "ongoing" && (
        <>
          {data.ongoing.length === 0 ? (
            <EmptyOngoing
              attentionCount={data.attention.length}
              historyCount={data.history.length}
              onAttention={() => setView("attention")}
              onHistory={() => setView("history")}
            />
          ) : (
            <section>
              <SectionHeading title="Ongoing sessions" count={data.ongoing.length} />
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {data.ongoing.map((run, idx) => (
                  <ActiveRunCard key={run.run_key || `${run.run_id}-${idx}`} run={run} />
                ))}
              </div>
            </section>
          )}

          {data.attention.length > 0 && (
            <section>
              <div className="mb-2 flex items-center justify-between">
                <SectionHeading title="Needs attention" count={data.attention.length} />
                <button
                  onClick={() => setView("attention")}
                  className="text-xs text-primary hover:underline"
                >
                  View all →
                </button>
              </div>
              <RunRows runs={data.attention.slice(0, 5)} purpose="attention" />
            </section>
          )}
        </>
      )}

      {view === "attention" && (
        <section>
          <div className="mb-3">
            <SectionHeading title="Needs attention" count={data.attention.length} />
            <p className="text-xs text-muted-foreground">
              A stalled run stopped reporting while still declared running. Inspect it to decide
              whether its unfinished work should be resumed.
            </p>
          </div>
          {data.attention.length > 0 ? (
            <RunRows runs={data.attention} purpose="attention" />
          ) : (
            <p className="rounded-lg border border-border bg-card p-6 text-sm text-muted-foreground">
              No stalled runs need action. Terminal failures are kept in History.
            </p>
          )}
        </section>
      )}

      {view === "history" && (
        <section>
          <SectionHeading title="Run history" count={data.history.length} />
          {data.history.length > 0 ? (
            <RunRows runs={data.history} />
          ) : (
            <p className="text-sm text-muted-foreground">No historical runs match this filter.</p>
          )}
        </section>
      )}
    </div>
  );
}

function ViewTab({
  active,
  onClick,
  label,
  count,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  count: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? "border-primary text-foreground"
          : "border-transparent text-muted-foreground hover:text-foreground"
      }`}
    >
      {label} <span className="ml-1 text-xs text-muted-foreground">{count}</span>
    </button>
  );
}

function SectionHeading({ title, count }: { title: string; count: number }) {
  return (
    <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
      {title} · {count}
    </h2>
  );
}

function EmptyOngoing({
  attentionCount,
  historyCount,
  onAttention,
  onHistory,
}: {
  attentionCount: number;
  historyCount: number;
  onAttention: () => void;
  onHistory: () => void;
}) {
  return (
    <div className="rounded-lg border border-border bg-card px-6 py-10 text-center">
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-green-500/10 text-green-400">
        ✓
      </div>
      <h2 className="text-lg font-semibold">No runs are running</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        The dashboard is healthy and will update automatically.
      </p>
      <div className="mt-4 flex justify-center gap-3">
        {attentionCount > 0 && (
          <button
            onClick={onAttention}
            className="rounded-md border border-amber-500/40 px-3 py-1.5 text-sm text-amber-400 hover:bg-amber-500/10"
          >
            Show needs attention ({attentionCount})
          </button>
        )}
        <button
          onClick={onHistory}
          className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          Browse history ({historyCount})
        </button>
      </div>
    </div>
  );
}

function LoadingOverview() {
  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="mb-3 h-4 w-36 animate-pulse rounded bg-muted" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-32 animate-pulse rounded-md bg-muted/60" />
        ))}
      </div>
      <p className="mt-3 text-xs text-muted-foreground">Loading active runs…</p>
    </div>
  );
}

function runHref(run: RunSummary): string {
  return `/run/${encodeURIComponent(run.run_key || run.run_id)}`;
}

function ActiveRunCard({ run }: { run: RunSummary }) {
  const c: Counts = run.counts || {};
  const done = c.batch_done || 0;
  const total = c.batch_total || 0;
  const active = run.active_count || c.batch_running || 0;
  const preflighting = run.stage === "preflight" || run.preflight_state === "running";
  const snap = run.score_snapshot;
  return (
    <Card className="border-green-500/40 transition-colors hover:border-primary">
      <CardContent className="p-4">
        <a
          href={runHref(run)}
          className="block space-y-3 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <div className="flex items-start justify-between gap-2">
            <span className="break-all text-sm font-semibold leading-tight">{run.run_id}</span>
            <StateBadge state={run.state} />
          </div>
          <div className="truncate text-xs text-muted-foreground">
            {run.model || run.kind} {run.thinking || ""}
            {(run.configs || []).length > 0 && ` · ${(run.configs || []).join(", ")}`}
          </div>
          <div>
            <Progress value={done} max={total || 1} />
            <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {done}/{total} done
              </span>
              {snap && snap.finished > 0 && (
                <span className={`font-semibold ${rateColor(snap.solve_rate)}`}>
                  {snap.solve_rate.toFixed(0)}% solve
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
            {active > 0 ? (
              <span className="flex items-center gap-1 text-green-400">
                <span className="h-1.5 w-1.5 rounded-full bg-green-400" />
                {active} active
              </span>
            ) : preflighting ? (
              <span className="flex items-center gap-1 text-primary">
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                preflight in progress
              </span>
            ) : (
              <span className="text-muted-foreground">starting workers</span>
            )}
            <span className="text-muted-foreground">
              heartbeat {fmtSeconds(run.heartbeat_age_s)} ago
            </span>
            {run.stage && !preflighting && (
              <span className="text-muted-foreground">phase {run.stage}</span>
            )}
            {run.stale_cell_count > 0 && (
              <Badge variant="stale">{run.stale_cell_count} stale</Badge>
            )}
          </div>
        </a>
      </CardContent>
    </Card>
  );
}

function RunRows({
  runs,
  purpose = "history",
}: {
  runs: RunSummary[];
  purpose?: "attention" | "history";
}) {
  const needsAction = purpose === "attention";
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
      {runs.map((run, idx) => {
        const done = run.counts?.batch_done || 0;
        const total = run.counts?.batch_total || 0;
        return (
          <a
            key={run.run_key || `${run.run_id}-${idx}`}
            href={runHref(run)}
            aria-label={
              needsAction ? `Inspect stalled run ${run.run_id}` : `View run ${run.run_id}`
            }
            className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-start gap-3 border-t border-border px-3 py-3 first:border-t-0 hover:bg-accent/50"
          >
            <StateBadge state={run.state} />
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{run.run_id}</div>
              <div className="truncate text-xs text-muted-foreground">
                {(run.configs || []).join(", ") || run.model || run.kind}
              </div>
              <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
                <span>
                  {run.model || run.kind} {run.thinking || ""}
                </span>
                <span>
                  {done}/{total} done
                  {run.score_snapshot &&
                    run.score_snapshot.finished > 0 &&
                    ` · ${run.score_snapshot.solve_rate.toFixed(0)}% solve`}
                </span>
                <span className={needsAction ? "text-amber-400" : undefined}>
                  {needsAction ? "No heartbeat for" : "Updated"} {fmtSeconds(run.heartbeat_age_s)}
                  {!needsAction && " ago"}
                </span>
              </div>
            </div>
            <span className="self-center whitespace-nowrap text-xs font-medium text-primary">
              {needsAction ? "Inspect →" : "View →"}
            </span>
          </a>
        );
      })}
    </div>
  );
}
