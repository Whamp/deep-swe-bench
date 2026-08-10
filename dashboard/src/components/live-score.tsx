import { useQuery } from "@tanstack/react-query";
import { fetchRunScore, fetchCompare } from "@/lib/api";
import type { RunSummary } from "@/lib/types";
import { pickBaseline, rateColor, fmtCost, fmtSeconds, fmtPercent } from "@/lib/metrics";
import { Sparkline } from "@/components/sparkline";
import { Badge } from "@/components/ui/badge";

interface LiveScoreProps {
  run: RunSummary;
}

/**
 * Live scoring hero for a run: one big solve-rate number, a baseline delta,
 * compact cost/throughput/ETA stats, a failure-mode breakdown (anomaly-first),
 * and a sparkline of solve rate + cumulative cost over finished cells.
 *
 * Renders nothing while there is no score data (e.g. legacy runs, or before the
 * first cell finishes), so it degrades cleanly.
 */
export function LiveScore({ run }: LiveScoreProps) {
  const runKey = run.run_key || run.run_id;
  const { data: score } = useQuery({
    queryKey: ["run-score", runKey],
    queryFn: () => fetchRunScore(runKey),
    refetchInterval: 5000,
  });

  // A baseline delta is attributable only when this run contains one config.
  const runTasks = (score?.tasks || []).map((t) => t.task);
  const configCount = run.configs?.length ?? 0;
  const comparisonConfig = configCount === 1 ? (run.configs?.[0] ?? null) : null;
  const { data: compare } = useQuery({
    queryKey: ["compare-all"],
    queryFn: () => fetchCompare(),
    enabled: !!score && runTasks.length > 0 && !!comparisonConfig,
    staleTime: 30_000,
  });

  if (!score || score.finished === 0) {
    // No finished cells yet — show a compact "warming up" state if active.
    if (score && score.active > 0) {
      return (
        <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-60" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-400" />
          </span>
          <span className="text-sm text-muted-foreground">
            {score.active} cell{score.active === 1 ? "" : "s"} running · waiting for first result
          </span>
        </div>
      );
    }
    return null;
  }

  const baseline = compare
    ? pickBaseline(
        compare.runs,
        run.model ?? null,
        run.thinking ?? null,
        comparisonConfig,
        runTasks,
      )
    : null;

  const flips: { gained: string[]; lost: string[] } | null = baseline
    ? (() => {
        const gained: string[] = [];
        const lost: string[] = [];
        for (const t of score.tasks || []) {
          const bSolved = baseline.solvedSet.has(t.task);
          if (t.solved && !bSolved) gained.push(t.task);
          else if (!t.solved && bSolved) lost.push(t.task);
        }
        return { gained, lost };
      })()
    : null;

  const deltaPp = baseline ? score.solve_rate - baseline.solveRate : null;
  const failures = Object.entries(score.failure_breakdown || {}).sort((a, b) => b[1] - a[1]);
  const tl = score.timeline || [];
  const solvedSeries = tl.map((p) => p.solved);
  const finishedSeries = tl.map((p) => p.finished);
  const costSeries = tl.map((p) => p.cost);
  const meanPartialSeries = tl.map((p) => p.mean_partial);
  const toolErrorRateSeries = tl.map((p) => p.tool_call_error_rate);

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-wrap items-end gap-x-8 gap-y-4">
        {/* Hero: solve rate */}
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Solve rate</div>
          <div className={`text-4xl font-bold leading-none ${rateColor(score.solve_rate)}`}>
            {score.solve_rate.toFixed(1)}
            <span className="text-xl font-semibold text-muted-foreground">%</span>
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            {score.tasks_solved} solved / {score.tasks_total} tasks
            {configCount > 1 && <> · {configCount} configs combined</>}
            {score.active > 0 && <> · {score.active} running</>}
          </div>
          {baseline && (
            <div className="mt-1.5 flex items-center gap-1.5 text-xs">
              <span className="text-muted-foreground">vs {baseline.label}</span>
              <span
                className={
                  deltaPp != null && deltaPp > 0
                    ? "font-semibold text-green-400"
                    : deltaPp != null && deltaPp < 0
                      ? "font-semibold text-red-400"
                      : "font-semibold text-muted-foreground"
                }
              >
                {deltaPp != null && deltaPp > 0 ? "+" : ""}
                {deltaPp != null ? `${deltaPp.toFixed(1)}pp` : "—"}
              </span>
              <span className="text-muted-foreground">
                ({baseline.solveRate.toFixed(1)}% over {baseline.sharedTasks})
              </span>
            </div>
          )}
        </div>

        {/* Secondary stats */}
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <Stat
            label="Cost so far"
            value={fmtCost(score.cumulative_cost)}
            hint={
              score.projected_total_cost
                ? `→ ${fmtCost(score.projected_total_cost)} proj.`
                : undefined
            }
          />
          <Stat
            label="Cost / solve"
            value={score.cost_per_solve > 0 ? fmtCost(score.cost_per_solve) : "—"}
          />
          <Stat
            label="Throughput"
            value={
              score.throughput_cells_per_hr > 0
                ? `${score.throughput_cells_per_hr.toFixed(1)}/hr`
                : "—"
            }
          />
          <Stat
            label="ETA"
            value={score.eta_s != null ? fmtSeconds(score.eta_s) : "—"}
            hint="throughput-based"
          />
          <Stat label="Mean partial" value={fmtPercent(score.mean_partial)} />
          <Stat
            label="Tool-call errors"
            value={
              score.tool_call_error_rate != null ? fmtPercent(score.tool_call_error_rate) : "—"
            }
            hint={
              score.tool_calls > 0
                ? `${score.tool_call_errors}/${score.tool_calls} calls`
                : undefined
            }
          />
        </div>

        {/* Trend sparklines */}
        <div className="flex flex-wrap gap-4">
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
              Solved / finished
            </div>
            <Sparkline
              data={solvedSeries}
              behind={finishedSeries}
              color="hsl(142 71% 45%)"
              behindColor="hsl(var(--muted-foreground))"
              width={140}
              height={36}
              ariaLabel="Cumulative solved vs finished over time"
            />
          </div>
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
              Cost
            </div>
            <Sparkline
              data={costSeries}
              color="hsl(var(--primary))"
              width={140}
              height={36}
              ariaLabel="Cumulative cost over time"
            />
          </div>
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
              Mean partial · {fmtPercent(score.mean_partial)}
            </div>
            <Sparkline
              data={meanPartialSeries}
              domain={[0, 1]}
              color="hsl(190 80% 55%)"
              width={140}
              height={36}
              ariaLabel="Cumulative mean partial reward over time"
            />
          </div>
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
              Tool errors ·{" "}
              {score.tool_call_error_rate != null ? fmtPercent(score.tool_call_error_rate) : "—"}
            </div>
            <Sparkline
              data={toolErrorRateSeries}
              domain={[0, 1]}
              color="hsl(var(--destructive))"
              width={140}
              height={36}
              ariaLabel="Cumulative tool-call error rate over time"
            />
          </div>
        </div>
      </div>

      {/* Failure breakdown + flips — anomaly first */}
      {(failures.length > 0 || flips) && (
        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border pt-3">
          {failures.length > 0 && (
            <>
              <span className="text-xs text-muted-foreground">Failures:</span>
              {failures.map(([k, v]) => (
                <Badge
                  key={k}
                  variant={
                    k === "timeout"
                      ? "timeout"
                      : k === "transient"
                        ? "transient"
                        : k === "empty"
                          ? "empty"
                          : "failed"
                  }
                >
                  {k} {v}
                </Badge>
              ))}
            </>
          )}
          {flips && (flips.gained.length > 0 || flips.lost.length > 0) && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-muted-foreground">vs baseline flips:</span>
              {flips.gained.length > 0 && (
                <span className="text-xs font-medium text-green-400">
                  +{flips.gained.length} new solves
                </span>
              )}
              {flips.lost.length > 0 && (
                <span className="text-xs font-medium text-red-400">
                  −{flips.lost.length} regressions
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-base font-semibold">{value}</div>
      {hint && <div className="text-[10px] text-muted-foreground">{hint}</div>}
    </div>
  );
}
