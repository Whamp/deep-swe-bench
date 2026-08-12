import { useState, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchRun, ApiError } from "@/lib/api";
import type { RunDetail as RunDetailData, Cell, DetailLevel } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StateBadge, OutcomeBadge, Badge } from "@/components/ui/badge";
import { ErrorState } from "@/components/error-state";
import { LiveScore } from "@/components/live-score";
import { cellTrajectoryHref } from "@/lib/trajectory-links";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { fmtSeconds, fmtTokens, fmtCost, fmtPercent } from "@/lib/metrics";

const DETAIL_OPTIONS: DetailLevel[] = ["summary", "operational", "diagnostic"];

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>();
  const [detail, setDetail] = useState<DetailLevel>("operational");

  const {
    data: run,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["run", runId, detail],
    queryFn: () => fetchRun(runId!, detail),
    enabled: !!runId,
    refetchInterval: 5000,
  });

  if (!runId) return <p className="text-muted-foreground">No run selected.</p>;
  if (isLoading) return <p className="text-muted-foreground">Loading…</p>;
  if (error) {
    const isNotFound = error instanceof ApiError && error.status === 404;
    return (
      <ErrorState
        title={isNotFound ? "Run not found" : "Unable to load run"}
        message={isNotFound ? "This run does not exist or has been removed." : String(error)}
        runId={runId}
      />
    );
  }
  if (!run) return <ErrorState runId={runId} />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
          ← Overview
        </Link>
        <h2 className="text-xl font-bold break-all">{run.run_id}</h2>
        <StateBadge state={run.state} />
        <div className="ml-auto flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Detail</span>
          <select
            aria-label="Run detail level"
            name="detail-level"
            value={detail}
            onChange={(e) => setDetail(e.target.value as DetailLevel)}
            className="rounded-md border border-border bg-card px-2 py-1 text-sm"
          >
            {DETAIL_OPTIONS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
      </div>

      <LiveScore run={run} />
      <RunSummary run={run} />

      <ActiveCells cells={run.active_cells || []} />
      <PreflightSmokeResults cells={Object.values(run.preflight || {})} />
      <FinishedRepResults cells={run.finished_cells || run.recent_finished || []} />

      {detail === "diagnostic" && <DiagnosticPanels run={run} />}
    </div>
  );
}

function RunSummary({ run }: { run: RunDetailData }) {
  const c = run.counts || {};
  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>
            {run.model || run.kind} {run.thinking || ""}
          </Badge>
          <Badge>
            {run.launch_plan_identity
              ? `plan ${run.launch_plan_identity.slice(0, 19)}`
              : run.launch_metadata}
          </Badge>
          <Badge variant={run.preflight_state === "failed" ? "failed" : "default"}>
            preflight {run.preflight_state}
          </Badge>
          {(run.configs || []).map((cfg) => (
            <Badge key={cfg}>{cfg}</Badge>
          ))}
        </div>
        <div>
          <Progress value={c.batch_done || 0} max={c.batch_total || 1} />
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            <span>
              {c.batch_done || 0}/{c.batch_total || 0} done
            </span>
            <span>updated {fmtSeconds(run.heartbeat_age_s)} ago</span>
            {run.stale_cell_count > 0 && (
              <Badge variant="stale">{run.stale_cell_count} stale</Badge>
            )}
            {run.max_cell_age_s != null && run.max_cell_age_s > 0 && (
              <span>oldest active {fmtSeconds(run.max_cell_age_s)}</span>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-4 text-xs">
          <FileLink path={run.paths?.manifest} label="manifest" />
          <FileLink path={run.paths?.status} label="status" />
          <FileLink path={run.paths?.events} label="events" />
          <span className="text-muted-foreground">
            workspace <code className="break-all">{run.workspace || "—"}</code>
          </span>
        </div>
        {run.failure_buckets && Object.keys(run.failure_buckets).length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground">Failures:</span>
            {Object.entries(run.failure_buckets).map(([k, v]) => (
              <Badge key={k} variant="failed">
                {k}: {v}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/** Active cells, sorted anomaly-first (stale, then oldest). */
function ActiveCells({ cells }: { cells: Cell[] }) {
  const sorted = useMemo(
    () =>
      [...cells].sort((a, b) => {
        const sa = a.potentially_stale ? 1 : 0;
        const sb = b.potentially_stale ? 1 : 0;
        if (sa !== sb) return sb - sa; // stale first
        return (b.cell_age_s ?? 0) - (a.cell_age_s ?? 0); // then oldest
      }),
    [cells],
  );
  if (sorted.length === 0) return null;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Active cells · {sorted.length}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Task</TableHead>
              <TableHead>Rep</TableHead>
              <TableHead>Age</TableHead>
              <TableHead>Activity</TableHead>
              <TableHead>Files</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((cell, i) => {
              const s = cell.summary || {};
              return (
                <TableRow key={`${cell.cell_id || "cell"}-${i}`}>
                  <TableCell className="font-medium">{cell.task || "—"}</TableCell>
                  <TableCell>{cell.rep ?? "—"}</TableCell>
                  <TableCell>
                    {cell.potentially_stale ? (
                      <Badge variant="stale">{fmtSeconds(cell.cell_age_s)}</Badge>
                    ) : cell.cell_age_s != null ? (
                      fmtSeconds(cell.cell_age_s)
                    ) : (
                      "—"
                    )}
                  </TableCell>
                  <TableCell>
                    <TrajectoryLink cell={cell} />
                  </TableCell>
                  <TableCell className="text-xs">
                    <CellFiles cell={cell} summary={s} />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

/** Finished reps remain individually inspectable after leaving the active set. */
function FinishedRepResults({ cells }: { cells: Cell[] }) {
  const sorted = useMemo(
    () =>
      [...cells].sort((a, b) => {
        const aNeedsAttention = a.outcome !== "ok" && a.outcome !== "skipped" ? 1 : 0;
        const bNeedsAttention = b.outcome !== "ok" && b.outcome !== "skipped" ? 1 : 0;
        if (aNeedsAttention !== bNeedsAttention) return bNeedsAttention - aNeedsAttention;
        return String(b.finished_at || "").localeCompare(String(a.finished_at || ""));
      }),
    [cells],
  );
  if (sorted.length === 0) return null;
  const solved = sorted.filter((cell) => Number(cell.summary?.reward_binary) >= 1).length;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Finished reps · {sorted.length} · {solved} solved
        </CardTitle>
      </CardHeader>
      <CardContent className="max-h-[36rem] overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Task</TableHead>
              <TableHead>Rep</TableHead>
              <TableHead>Outcome</TableHead>
              <TableHead>Result</TableHead>
              <TableHead>Partial</TableHead>
              <TableHead>F2P</TableHead>
              <TableHead>P2P</TableHead>
              <TableHead>Output tokens</TableHead>
              <TableHead>Wall time</TableHead>
              <TableHead>Tool errors</TableHead>
              <TableHead>Files</TableHead>
              <TableHead>Inspect</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((cell, i) => {
              const summary = cell.summary || {};
              const rewardBinary = summary.reward_binary;
              return (
                <TableRow key={`${cell.cell_id || "cell"}-${i}`}>
                  <TableCell className="font-medium">{cell.task || "—"}</TableCell>
                  <TableCell>{cell.rep ?? "—"}</TableCell>
                  <TableCell>
                    <OutcomeBadge outcome={cell.outcome} />
                  </TableCell>
                  <TableCell>
                    {rewardBinary === undefined ? (
                      "—"
                    ) : Number(rewardBinary) >= 1 ? (
                      <Badge variant="ok">solved</Badge>
                    ) : (
                      <Badge variant="empty">not solved</Badge>
                    )}
                  </TableCell>
                  <TableCell>{fmtPercent(summary.reward_partial as number | undefined)}</TableCell>
                  <TableCell>{fmtPercent(summary.f2p as number | undefined)}</TableCell>
                  <TableCell>{fmtPercent(summary.p2p as number | undefined)}</TableCell>
                  <TableCell>{fmtTokens(summary.output_tokens as number | undefined)}</TableCell>
                  <TableCell>{fmtSeconds(summary.agent_wall_s as number | undefined)}</TableCell>
                  <TableCell className="whitespace-nowrap text-xs">
                    <FinishedCellToolErrors summary={summary} />
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                    <CellFiles cell={cell} summary={summary} />
                  </TableCell>
                  <TableCell className="text-xs">
                    <TrajectoryLink cell={cell} />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function FinishedCellToolErrors({
  summary,
}: {
  summary: Record<string, number | boolean | string | null | undefined>;
}) {
  const calls = summary.tool_calls;
  if (typeof calls !== "number" || calls <= 0) return "—";
  const errors = typeof summary.tool_call_errors === "number" ? summary.tool_call_errors : 0;
  const rate =
    typeof summary.tool_call_error_rate === "number" ? summary.tool_call_error_rate : null;
  return `${errors}/${calls} · ${fmtPercent(rate)}`;
}

function CellFiles({
  cell,
  summary,
  metrics,
}: {
  cell: Cell;
  summary: Record<string, number | boolean | string | null | undefined>;
  metrics?: boolean;
}) {
  const bits: string[] = [];
  if (metrics) {
    if (summary.total_tokens !== undefined)
      bits.push(`tok ${fmtTokens(summary.total_tokens as number)}`);
    if (summary.cost_usd !== undefined) bits.push(`${fmtCost(summary.cost_usd as number)}`);
    if (summary.agent_wall_s !== undefined)
      bits.push(`${fmtSeconds(summary.agent_wall_s as number)}`);
  }
  return (
    <span className="text-muted-foreground">
      {bits.length > 0 && <span>{bits.join(" · ")} </span>}
      {cell.result_path && (
        <a
          href={`/api/file?path=${encodeURIComponent(cell.result_path)}&tail=50`}
          target="_blank"
          rel="noreferrer"
          className="text-primary hover:underline"
        >
          result
        </a>
      )}
      {cell.result_path && cell.log_path && " · "}
      {cell.log_path && (
        <a
          href={`/api/file?path=${encodeURIComponent(cell.log_path)}&tail=200`}
          target="_blank"
          rel="noreferrer"
          className="text-primary hover:underline"
        >
          log
        </a>
      )}
    </span>
  );
}

function TrajectoryLink({ cell }: { cell: Cell }) {
  if (!cell.result_path) return <span className="text-muted-foreground">unavailable</span>;
  return (
    <Link
      to={cellTrajectoryHref(cell.result_path)}
      className="rounded-md border border-border bg-background/60 px-2 py-1 text-xs text-primary hover:bg-accent hover:text-foreground"
    >
      view trajectory →
    </Link>
  );
}

/** Preflight smoke reps expose both agent execution and smoke-contract evidence. */
function PreflightSmokeResults({ cells }: { cells: Cell[] }) {
  if (cells.length === 0) return null;
  const passed = cells.filter((cell) => cell.state === "passed").length;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Preflight / smoke · {cells.length} · {passed} passed
        </CardTitle>
      </CardHeader>
      <CardContent className="max-h-[36rem] overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Task</TableHead>
              <TableHead>Config</TableHead>
              <TableHead>Rep</TableHead>
              <TableHead>Contract verdict</TableHead>
              <TableHead>Execution outcome</TableHead>
              <TableHead>Task result</TableHead>
              <TableHead>Partial pass</TableHead>
              <TableHead>Usage / evidence</TableHead>
              <TableHead>Contract diagnostics</TableHead>
              <TableHead>Inspect</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {cells.map((cell, i) => {
              const summary = cell.summary || {};
              const rewardBinary = summary.reward_binary;
              return (
                <TableRow key={`${cell.cell_id || "preflight"}-${i}`}>
                  <TableCell className="font-medium">{cell.task || "—"}</TableCell>
                  <TableCell>{cell.config || "—"}</TableCell>
                  <TableCell>{cell.rep ?? "—"}</TableCell>
                  <TableCell>
                    <StateBadge state={cell.state} />
                  </TableCell>
                  <TableCell>
                    <OutcomeBadge outcome={cell.outcome} />
                  </TableCell>
                  <TableCell>
                    {rewardBinary === undefined ? (
                      "—"
                    ) : Number(rewardBinary) >= 1 ? (
                      <Badge variant="ok">solved</Badge>
                    ) : (
                      <Badge variant="empty">not solved</Badge>
                    )}
                  </TableCell>
                  <TableCell>{fmtPercent(summary.reward_partial as number | undefined)}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    <div className="space-y-1">
                      <CellFiles cell={cell} summary={summary} metrics />
                      <FileLink path={cell.contract_path} label="contract" />
                    </div>
                  </TableCell>
                  <TableCell className="min-w-64 text-xs">
                    <PreflightContractDiagnostics diagnostics={cell.diagnostics || []} />
                  </TableCell>
                  <TableCell className="text-xs">
                    <TrajectoryLink cell={cell} />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function PreflightContractDiagnostics({
  diagnostics,
}: {
  diagnostics: NonNullable<Cell["diagnostics"]>;
}) {
  if (diagnostics.length === 0) return <span className="text-muted-foreground">none</span>;
  return (
    <details>
      <summary className="cursor-pointer text-red-400">
        {diagnostics.length} contract {diagnostics.length === 1 ? "failure" : "failures"}
      </summary>
      <ul className="mt-2 space-y-2">
        {diagnostics.map((diagnostic, index) => (
          <li key={`${diagnostic.requirement || "diagnostic"}-${diagnostic.target || index}`}>
            <div className="font-medium">
              {diagnostic.requirement || "unknown requirement"} ·{" "}
              {diagnostic.target || "unknown target"}
            </div>
            <div className="text-muted-foreground">{diagnostic.reason || "no reason recorded"}</div>
          </li>
        ))}
      </ul>
    </details>
  );
}

function FileLink({ path, label }: { path?: string; label: string }) {
  if (!path) return <span className="text-muted-foreground">{label}: —</span>;
  return (
    <a
      href={`/api/file?path=${encodeURIComponent(path)}&tail=200`}
      target="_blank"
      rel="noreferrer"
      className="text-primary hover:underline"
    >
      {label}
    </a>
  );
}

function DiagnosticPanels({ run }: { run: RunDetailData }) {
  return (
    <>
      {run.events_tail && run.events_tail.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Recent events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-96 overflow-auto rounded-md border border-border bg-background/80 p-3 text-xs">
              {run.events_tail.map((e) => JSON.stringify(e)).join("\n")}
            </pre>
          </CardContent>
        </Card>
      )}
      {run.status && (
        <Card>
          <CardHeader>
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              status.json
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-96 overflow-auto rounded-md border border-border bg-background/80 p-3 text-xs">
              {JSON.stringify(run.status, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
      {run.manifest && (
        <Card>
          <CardHeader>
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              manifest.json
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-96 overflow-auto rounded-md border border-border bg-background/80 p-3 text-xs">
              {JSON.stringify(run.manifest, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </>
  );
}
