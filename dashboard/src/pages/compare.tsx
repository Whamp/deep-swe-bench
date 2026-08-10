import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Cell as RechartsCell,
  ReferenceLine,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchCompare, fetchSubsets } from "@/lib/api";
import type { ComparisonRun } from "@/lib/types";
import {
  compareConfigPair,
  comparisonGroupKey,
  defaultComparePair,
  difficultySolveSummary,
  type ComparePairOutcome,
  type CompareTaskOutcome,
  type ConfigPairComparison,
} from "@/lib/compare-metrics";
import { fmtCost, fmtSeconds, fmtTokens } from "@/lib/metrics";
import { useIsMobile } from "@/lib/use-mobile";
import { MeasuredContainer } from "@/components/measured-container";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState } from "@/components/error-state";
import { cn } from "@/lib/utils";

const DEFAULT_SUBSET = "36_v2";
const REFERENCE_COLOR = "#58a6ff";
const CHALLENGER_COLOR = "#3fb950";

export default function Compare() {
  const [subset, setSubset] = useState(DEFAULT_SUBSET);
  const [reps, setReps] = useState(1);
  const [includePartial, setIncludePartial] = useState(false);
  const [groupScope, setGroupScope] = useState<string | null>(null);
  const [referenceId, setReferenceId] = useState<string | null>(null);
  const [challengerId, setChallengerId] = useState<string | null>(null);

  const subsetsQuery = useQuery({
    queryKey: ["subsets"],
    queryFn: fetchSubsets,
    staleTime: 60_000,
  });
  const compareQuery = useQuery({
    queryKey: ["compare", subset, reps],
    queryFn: () => fetchCompare({ subset, reps }),
    refetchInterval: 30_000,
  });

  const subsets = useMemo(() => subsetsQuery.data?.subsets ?? [], [subsetsQuery.data]);
  const rows = useMemo(() => compareQuery.data?.runs ?? [], [compareQuery.data]);
  const subsetSize = subsets.find((item) => item.name === subset)?.task_count ?? 0;
  const selectableRows = useMemo(
    () => rows.filter((row) => includePartial || row.distinct_tasks >= subsetSize),
    [includePartial, rows, subsetSize],
  );
  const groupOptions = useMemo(() => {
    const groups = new Map<string, ComparisonRun[]>();
    for (const row of selectableRows) {
      const key = comparisonGroupKey(row);
      const group = groups.get(key) ?? [];
      group.push(row);
      groups.set(key, group);
    }
    return [...groups.entries()]
      .filter(([, group]) => group.length >= 2)
      .map(([key, group]) => ({ key, count: group.length }))
      .sort((a, b) => b.count - a.count || a.key.localeCompare(b.key));
  }, [selectableRows]);
  const defaultFrame = useMemo(
    () => defaultComparePair(rows, subsetSize, includePartial),
    [includePartial, rows, subsetSize],
  );

  useEffect(() => {
    if (!rows.length || !subsetSize) return;
    const validGroups = new Set(groupOptions.map((group) => group.key));
    const nextGroup =
      groupScope && validGroups.has(groupScope) ? groupScope : defaultFrame?.group_key;
    if (!nextGroup) return;

    const scopedRows = rows.filter((row) => comparisonGroupKey(row) === nextGroup);
    const pair = defaultComparePair(scopedRows, subsetSize, includePartial);
    if (!pair) return;

    if (groupScope !== nextGroup) setGroupScope(nextGroup);
    const validIds = new Set(
      scopedRows
        .filter((row) => includePartial || row.distinct_tasks >= subsetSize)
        .map((row) => row.run_id),
    );
    if (
      !referenceId ||
      !challengerId ||
      referenceId === challengerId ||
      !validIds.has(referenceId) ||
      !validIds.has(challengerId)
    ) {
      setReferenceId(pair.reference_id);
      setChallengerId(pair.challenger_id);
    }
  }, [
    challengerId,
    defaultFrame,
    groupOptions,
    groupScope,
    includePartial,
    referenceId,
    rows,
    subsetSize,
  ]);

  const groupRows = useMemo(
    () =>
      selectableRows
        .filter((row) => comparisonGroupKey(row) === groupScope)
        .sort((a, b) => b.solve_rate - a.solve_rate || a.config.localeCompare(b.config)),
    [groupScope, selectableRows],
  );
  const reference = rows.find((row) => row.run_id === referenceId) ?? null;
  const challenger = rows.find((row) => row.run_id === challengerId) ?? null;
  const comparison = useMemo(
    () => (reference && challenger ? compareConfigPair(reference, challenger) : null),
    [challenger, reference],
  );

  const resetFrame = (nextSubset = subset) => {
    setSubset(nextSubset);
    setGroupScope(null);
    setReferenceId(null);
    setChallengerId(null);
  };

  if (subsetsQuery.isLoading || compareQuery.isLoading) return <CompareLoading />;
  if (subsetsQuery.error || compareQuery.error) {
    return (
      <ErrorState
        title="Unable to load comparison data"
        message={String(subsetsQuery.error ?? compareQuery.error)}
      />
    );
  }
  if (!rows.length) {
    return <EmptyCompare message="No completed config results overlap this subset." />;
  }

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-primary">
            Paired config evidence
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Compare</h1>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            Interrogate two configs on the same tasks, model, thinking level, and rep scope. Results
            are descriptive; no significance claim is made.
          </p>
        </div>
        <div className="text-right text-xs text-muted-foreground">
          <div className="text-lg font-semibold text-foreground">{subsetSize || "—"} tasks</div>
          <div>{formatRepScope(reps)}</div>
        </div>
      </header>

      <ComparisonScope
        subsets={subsets}
        subset={subset}
        reps={reps}
        includePartial={includePartial}
        groupScope={groupScope}
        groupOptions={groupOptions}
        onSubsetChange={resetFrame}
        onRepsChange={(value) => {
          setReps(value);
          setReferenceId(null);
          setChallengerId(null);
        }}
        onIncludePartialChange={(value) => {
          setIncludePartial(value);
          setGroupScope(null);
          setReferenceId(null);
          setChallengerId(null);
        }}
        onGroupScopeChange={(value) => {
          setGroupScope(value);
          setReferenceId(null);
          setChallengerId(null);
        }}
      />

      {groupRows.length < 2 || !reference || !challenger || !comparison ? (
        <EmptyCompare
          message={
            includePartial
              ? "Choose a model + thinking group with at least two configs."
              : "No model + thinking group has two full-coverage configs. Include partial coverage to inspect incomplete evidence."
          }
        />
      ) : (
        <>
          <PairSelector
            rows={groupRows}
            reference={reference}
            challenger={challenger}
            subsetSize={subsetSize}
            onReferenceChange={setReferenceId}
            onChallengerChange={setChallengerId}
            onSwap={() => {
              setReferenceId(challenger.run_id);
              setChallengerId(reference.run_id);
            }}
          />
          <ComparisonVerdict
            reference={reference}
            challenger={challenger}
            comparison={comparison}
            reps={reps}
          />
          <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.65fr)_minmax(300px,0.85fr)]">
            <PairedPartialScatter
              reference={reference}
              challenger={challenger}
              comparison={comparison}
              reps={reps}
            />
            <FlipEvidence comparison={comparison} />
          </div>
          <SideBySideEvidence
            reference={reference}
            challenger={challenger}
            comparison={comparison}
            subsetSize={subsetSize}
          />
          <TaskEvidenceDetails
            reference={reference}
            challenger={challenger}
            comparison={comparison}
          />
        </>
      )}
    </div>
  );
}

function ComparisonScope({
  subsets,
  subset,
  reps,
  includePartial,
  groupScope,
  groupOptions,
  onSubsetChange,
  onRepsChange,
  onIncludePartialChange,
  onGroupScopeChange,
}: {
  subsets: Array<{ name: string; task_count: number }>;
  subset: string;
  reps: number;
  includePartial: boolean;
  groupScope: string | null;
  groupOptions: Array<{ key: string; count: number }>;
  onSubsetChange: (value: string) => void;
  onRepsChange: (value: number) => void;
  onIncludePartialChange: (value: boolean) => void;
  onGroupScopeChange: (value: string) => void;
}) {
  const isMobile = useIsMobile();
  return (
    <Card>
      <CardContent className="p-3">
        <details className="group" open={!isMobile}>
          <summary className="cursor-pointer list-none text-sm font-medium md:hidden">
            Scope · {subset} · {formatRepScope(reps)} · {groupScope ?? "choosing group…"}
            <span className="float-right text-muted-foreground group-open:rotate-180">⌄</span>
          </summary>
          <div className="mt-3 grid gap-3 md:!mt-0 md:!grid md:grid-cols-[180px_260px_minmax(220px,1fr)_auto] md:items-end">
            <label className="space-y-1 text-xs text-muted-foreground">
              <span>Dataset</span>
              <select
                aria-label="Comparison dataset"
                value={subset}
                onChange={(event) => onSubsetChange(event.target.value)}
                className="h-9 w-full rounded-md border border-border bg-background px-2 text-sm text-foreground"
              >
                {subsets.map((item) => (
                  <option key={item.name} value={item.name}>
                    {item.name} · {item.task_count} tasks
                  </option>
                ))}
              </select>
            </label>
            <div className="space-y-1 text-xs text-muted-foreground">
              <span>Rep scope</span>
              <div className="flex rounded-md border border-border bg-background p-0.5">
                {[
                  [1, "First rep"],
                  [3, "First 3"],
                  [0, "All reps"],
                ].map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    aria-pressed={reps === value}
                    onClick={() => onRepsChange(Number(value))}
                    className={cn(
                      "flex-1 rounded px-2 py-1.5 text-xs",
                      reps === value ? "bg-accent text-foreground" : "text-muted-foreground",
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <label className="space-y-1 text-xs text-muted-foreground">
              <span>Model + thinking</span>
              <select
                aria-label="Model and thinking group"
                value={groupScope ?? ""}
                onChange={(event) => onGroupScopeChange(event.target.value)}
                className="h-9 w-full rounded-md border border-border bg-background px-2 text-sm text-foreground"
              >
                {!groupScope && <option value="">Choose a comparable group</option>}
                {groupOptions.map((group) => (
                  <option key={group.key} value={group.key}>
                    {group.key} · {group.count} configs
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              aria-pressed={includePartial}
              onClick={() => onIncludePartialChange(!includePartial)}
              className={cn(
                "h-9 rounded-md border px-3 text-xs",
                includePartial
                  ? "border-amber-500/60 bg-amber-500/10 text-amber-300"
                  : "border-border text-muted-foreground hover:bg-accent",
              )}
            >
              {includePartial ? "Partial included" : "Full coverage only"}
            </button>
          </div>
        </details>
      </CardContent>
    </Card>
  );
}

function PairSelector({
  rows,
  reference,
  challenger,
  subsetSize,
  onReferenceChange,
  onChallengerChange,
  onSwap,
}: {
  rows: ComparisonRun[];
  reference: ComparisonRun;
  challenger: ComparisonRun;
  subsetSize: number;
  onReferenceChange: (runId: string) => void;
  onChallengerChange: (runId: string) => void;
  onSwap: () => void;
}) {
  const isMobile = useIsMobile();
  return (
    <Card>
      <CardContent className="p-3">
        <details className="group" open={!isMobile}>
          <summary className="cursor-pointer list-none text-sm font-medium md:hidden">
            Pair · {compactName(reference.config)} vs {compactName(challenger.config)}
            <span className="float-right text-muted-foreground group-open:rotate-180">⌄</span>
          </summary>
          <div className="mt-3 grid gap-3 md:!mt-0 md:!grid md:grid-cols-[1fr_auto_1fr] md:items-stretch">
            <ConfigChoice
              slot="A"
              role="Reference"
              color={REFERENCE_COLOR}
              run={reference}
              rows={rows.filter((row) => row.run_id !== challenger.run_id)}
              subsetSize={subsetSize}
              onChange={onReferenceChange}
            />
            <button
              type="button"
              onClick={onSwap}
              className="self-center rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              Swap A ↔ B
            </button>
            <ConfigChoice
              slot="B"
              role="Challenger"
              color={CHALLENGER_COLOR}
              run={challenger}
              rows={rows.filter((row) => row.run_id !== reference.run_id)}
              subsetSize={subsetSize}
              onChange={onChallengerChange}
            />
          </div>
        </details>
      </CardContent>
    </Card>
  );
}

function ConfigChoice({
  slot,
  role,
  color,
  run,
  rows,
  subsetSize,
  onChange,
}: {
  slot: "A" | "B";
  role: string;
  color: string;
  run: ComparisonRun;
  rows: ComparisonRun[];
  subsetSize: number;
  onChange: (runId: string) => void;
}) {
  const fullCoverage = run.distinct_tasks >= subsetSize;
  return (
    <div className="rounded-md border border-border bg-background/40 p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          <span
            className="inline-flex h-5 w-5 items-center justify-center rounded text-[11px] font-semibold text-background"
            style={{ backgroundColor: color }}
          >
            {slot}
          </span>
          {role}
        </span>
        <div className="flex gap-1">
          {run.config === "baseline" && <Badge>Canonical baseline</Badge>}
          {!fullCoverage && <Badge className="border-amber-500/50 text-amber-400">Partial</Badge>}
          {run.total_cost <= 0 && (
            <Badge className="border-amber-500/50 text-amber-400">Cost untracked</Badge>
          )}
        </div>
      </div>
      <select
        aria-label={`${role} config`}
        value={run.run_id}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 w-full rounded-md border border-border bg-background px-2 text-sm font-medium text-foreground"
      >
        {rows.map((row) => (
          <option key={row.run_id} value={row.run_id}>
            {row.config} · {row.solve_rate.toFixed(1)}% reps · {row.distinct_tasks}/{subsetSize}{" "}
            tasks
          </option>
        ))}
      </select>
      <div className="mt-2 text-xs tabular-nums text-muted-foreground">
        {run.solved}/{run.total_cells} reps solved · {run.distinct_tasks}/{subsetSize} task coverage
      </div>
    </div>
  );
}

function ComparisonVerdict({
  reference,
  challenger,
  comparison,
  reps,
}: {
  reference: ComparisonRun;
  challenger: ComparisonRun;
  comparison: ConfigPairComparison;
  reps: number;
}) {
  const verdict = comparisonVerdict(challenger.config, comparison);
  const repDelta = challenger.solve_rate - reference.solve_rate;
  const noisy = comparison.discordant_tasks < 8;

  return (
    <Card className="overflow-hidden border-primary/35">
      <CardContent className="p-0">
        <div className="grid lg:grid-cols-[1.25fr_1fr]">
          <div className="bg-gradient-to-br from-primary/15 via-card to-card p-5">
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-primary">
              Paired result
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight" title={challenger.config}>
              {verdict.title}
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              {verdict.detail} {comparison.discordant_tasks} tasks flipped direction;{" "}
              {noisy
                ? "small discordant N, so treat the direction as noisy."
                : "this is descriptive evidence, not a significance test."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              <Badge className="border-green-500/50 text-green-400">
                B-only {comparison.challenger_only}
              </Badge>
              <Badge className="border-red-500/50 text-red-400">
                A-only {comparison.reference_only}
              </Badge>
              <Badge>Both {comparison.both_solved}</Badge>
              <Badge>Neither {comparison.neither_solved}</Badge>
            </div>
          </div>
          <div className="grid grid-cols-2 border-t border-border lg:border-l lg:border-t-0">
            <VerdictStat
              label="B task solve · shared"
              value={`${comparison.challenger_task_solve_rate.toFixed(1)}%`}
              detail={`A ${comparison.reference_task_solve_rate.toFixed(1)}% · ${formatPointDelta(comparison.task_solve_rate_delta)}`}
              tone={deltaTone(comparison.task_solve_rate_delta)}
            />
            {reps === 1 ? (
              <VerdictStat
                label="Discordant tasks"
                value={`${comparison.discordant_tasks}`}
                detail={`${comparison.challenger_only} B-only · ${comparison.reference_only} A-only`}
                tone="neutral"
              />
            ) : (
              <VerdictStat
                label="B rep solve · scoped"
                value={`${challenger.solve_rate.toFixed(1)}%`}
                detail={`A ${reference.solve_rate.toFixed(1)}% · ${formatPointDelta(repDelta)}`}
                tone={deltaTone(repDelta)}
              />
            )}
            <VerdictStat
              label="B mean partial · shared"
              value={formatPercent(comparison.challenger_mean_partial)}
              detail={`A ${formatPercent(comparison.reference_mean_partial)} · ${formatPointDelta(comparison.partial_delta * 100)}`}
              tone={deltaTone(comparison.partial_delta)}
            />
            <VerdictStat
              label={
                comparison.cost_per_successful_rep_delta == null
                  ? "B median tokens"
                  : "B cost / successful rep"
              }
              value={
                comparison.cost_per_successful_rep_delta == null
                  ? fmtTokens(challenger.median_tokens)
                  : fmtCost(comparison.challenger_cost_per_successful_rep)
              }
              detail={
                comparison.cost_per_successful_rep_delta == null
                  ? `A ${fmtTokens(reference.median_tokens)} · cost untracked`
                  : `A ${fmtCost(comparison.reference_cost_per_successful_rep)} · ${formatCostDelta(comparison.cost_per_successful_rep_delta)}`
              }
              tone={
                comparison.cost_per_successful_rep_delta == null
                  ? "neutral"
                  : deltaTone(-comparison.cost_per_successful_rep_delta)
              }
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function VerdictStat({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: "good" | "bad" | "neutral";
}) {
  return (
    <div className="border-b border-r border-border p-3 last:border-b-0">
      <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-xl font-semibold tabular-nums">{value}</div>
      <div
        className={cn(
          "mt-1 text-xs tabular-nums",
          tone === "good"
            ? "text-green-400"
            : tone === "bad"
              ? "text-red-400"
              : "text-muted-foreground",
        )}
      >
        {detail}
      </div>
    </div>
  );
}

function PairedPartialScatter({
  reference,
  challenger,
  comparison,
  reps,
}: {
  reference: ComparisonRun;
  challenger: ComparisonRun;
  comparison: ConfigPairComparison;
  reps: number;
}) {
  const isMobile = useIsMobile();
  const [zoomed, setZoomed] = useState(true);
  const data = comparison.tasks.map((task) => ({
    ...task,
    x: task.reference_partial,
    y: task.challenger_partial,
  }));
  const values = data.flatMap((task) => [task.x, task.y]);
  const valueMin = values.length ? Math.min(...values) : 0;
  const valueMax = values.length ? Math.max(...values) : 1;
  const padding = Math.max(0.01, (valueMax - valueMin) * 0.12);
  const zoomDomain: [number, number] = [
    Math.max(0, valueMin - padding),
    Math.min(1, valueMax + padding),
  ];
  const domain: [number, number] = zoomed ? zoomDomain : [0, 1];

  return (
    <Card className="min-w-0">
      <CardContent className="min-w-0 p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="font-medium">Per-task partial reward</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              One point per shared task · above diagonal favors B · {taskAggregationLabel(reps)}
            </p>
          </div>
          <div className="flex rounded-md border border-border bg-background p-0.5 text-xs">
            <button
              type="button"
              aria-pressed={zoomed}
              onClick={() => setZoomed(true)}
              className={cn(
                "rounded px-2 py-1",
                zoomed ? "bg-accent text-foreground" : "text-muted-foreground",
              )}
            >
              Zoom to variation
            </button>
            <button
              type="button"
              aria-pressed={!zoomed}
              onClick={() => setZoomed(false)}
              className={cn(
                "rounded px-2 py-1",
                !zoomed ? "bg-accent text-foreground" : "text-muted-foreground",
              )}
            >
              Full 0–100%
            </button>
          </div>
        </div>
        <MeasuredContainer height={isMobile ? 300 : 390}>
          {(width, height) => (
            <ScatterChart
              width={width}
              height={height}
              margin={{ top: 18, right: 18, bottom: 38, left: 12 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215 14% 22%)" />
              <XAxis
                type="number"
                dataKey="x"
                domain={domain}
                tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`}
                stroke="hsl(215 16% 65%)"
                tick={{ fontSize: 11 }}
                label={{
                  value: `A · ${compactName(reference.config)}`,
                  position: "insideBottom",
                  offset: -14,
                  fill: REFERENCE_COLOR,
                  fontSize: 11,
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                domain={domain}
                tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`}
                stroke="hsl(215 16% 65%)"
                tick={{ fontSize: 11 }}
                label={{
                  value: `B · ${compactName(challenger.config)}`,
                  angle: -90,
                  position: "insideLeft",
                  fill: CHALLENGER_COLOR,
                  fontSize: 11,
                }}
              />
              <ReferenceLine
                segment={[
                  { x: domain[0], y: domain[0] },
                  { x: domain[1], y: domain[1] },
                ]}
                stroke="hsl(215 16% 55%)"
                strokeDasharray="5 4"
              />
              <Tooltip content={<TaskScatterTooltip />} />
              <Scatter data={data} isAnimationActive={false}>
                {data.map((task) => (
                  <RechartsCell
                    key={task.task}
                    fill={OUTCOME_COLORS[task.outcome]}
                    fillOpacity={task.outcome === "neither_solved" ? 0.45 : 0.82}
                    stroke={
                      task.outcome === "challenger_only" || task.outcome === "reference_only"
                        ? "#fff"
                        : "transparent"
                    }
                    strokeWidth={1}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          )}
        </MeasuredContainer>
        <OutcomeLegend />
      </CardContent>
    </Card>
  );
}

function TaskScatterTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload?: CompareTaskOutcome }>;
}) {
  const task = payload?.[0]?.payload;
  if (!active || !task) return null;
  return (
    <div className="max-w-72 rounded-md border border-border bg-card p-2 text-xs shadow-xl">
      <div className="font-medium">{task.task}</div>
      <div className="mt-1 text-muted-foreground">
        A {formatPercent(task.reference_partial)} · B {formatPercent(task.challenger_partial)} ·{" "}
        {formatPointDelta(task.partial_delta * 100)}
      </div>
      <div className="mt-1">{outcomeLabel(task.outcome)}</div>
    </div>
  );
}

function OutcomeLegend() {
  return (
    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
      {(Object.keys(OUTCOME_COLORS) as ComparePairOutcome[]).map((outcome) => (
        <span key={outcome} className="flex items-center gap-1.5">
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: OUTCOME_COLORS[outcome] }}
          />
          {outcomeLabel(outcome)}
        </span>
      ))}
    </div>
  );
}

function FlipEvidence({ comparison }: { comparison: ConfigPairComparison }) {
  const discordant = comparison.tasks.filter(
    (task) => task.outcome === "challenger_only" || task.outcome === "reference_only",
  );
  const total = Math.max(comparison.shared_tasks, 1);

  return (
    <Card className="min-w-0">
      <CardContent className="min-w-0 p-4">
        <h2 className="font-medium">Task flips</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Directional changes on the shared task intersection
        </p>
        <div className="mt-4 flex h-3 overflow-hidden rounded-full bg-muted">
          {(
            [
              ["challenger_only", comparison.challenger_only],
              ["reference_only", comparison.reference_only],
              ["both_solved", comparison.both_solved],
              ["neither_solved", comparison.neither_solved],
            ] as Array<[ComparePairOutcome, number]>
          ).map(([outcome, count]) => (
            <span
              key={outcome}
              style={{
                width: `${(count / total) * 100}%`,
                backgroundColor: OUTCOME_COLORS[outcome],
              }}
            />
          ))}
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <FlipCount label="B gained" value={comparison.challenger_only} tone="good" />
          <FlipCount label="B lost" value={comparison.reference_only} tone="bad" />
          <FlipCount label="Both solved" value={comparison.both_solved} />
          <FlipCount label="Neither" value={comparison.neither_solved} />
        </div>
        <div className="mt-4 border-t border-border pt-3">
          {discordant.length ? (
            <details>
              <summary className="cursor-pointer text-xs font-medium text-primary">
                View all {discordant.length} discordant task{discordant.length === 1 ? "" : "s"}
              </summary>
              <div className="mt-2 max-h-64 space-y-1 overflow-y-auto pr-1">
                {discordant.map((task) => (
                  <div
                    key={task.task}
                    className="flex items-center justify-between gap-2 rounded bg-background/50 px-2 py-1.5 text-xs"
                  >
                    <span className="truncate" title={task.task}>
                      {task.task}
                    </span>
                    <span
                      className={cn(
                        "shrink-0 tabular-nums",
                        task.outcome === "challenger_only" ? "text-green-400" : "text-red-400",
                      )}
                    >
                      {task.outcome === "challenger_only" ? "B gained" : "B lost"}
                    </span>
                  </div>
                ))}
              </div>
            </details>
          ) : (
            <p className="text-xs text-muted-foreground">No one-sided task flips.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function FlipCount({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: number;
  tone?: "good" | "bad" | "neutral";
}) {
  return (
    <div className="rounded-md border border-border bg-background/40 p-2">
      <div
        className={cn(
          "text-lg font-semibold tabular-nums",
          tone === "good" ? "text-green-400" : tone === "bad" ? "text-red-400" : "",
        )}
      >
        {value}
      </div>
      <div className="text-[11px] text-muted-foreground">{label}</div>
    </div>
  );
}

function SideBySideEvidence({
  reference,
  challenger,
  comparison,
  subsetSize,
}: {
  reference: ComparisonRun;
  challenger: ComparisonRun;
  comparison: ConfigPairComparison;
  subsetSize: number;
}) {
  const rows = [
    {
      metric: "Task solve · shared",
      reference: `${comparison.reference_task_solve_rate.toFixed(1)}%`,
      challenger: `${comparison.challenger_task_solve_rate.toFixed(1)}%`,
      delta: formatPointDelta(comparison.task_solve_rate_delta),
      tone: deltaTone(comparison.task_solve_rate_delta),
    },
    {
      metric: "Rep solve · scoped",
      reference: `${reference.solve_rate.toFixed(1)}% · ${reference.solved}/${reference.total_cells}`,
      challenger: `${challenger.solve_rate.toFixed(1)}% · ${challenger.solved}/${challenger.total_cells}`,
      delta: formatPointDelta(challenger.solve_rate - reference.solve_rate),
      tone: deltaTone(challenger.solve_rate - reference.solve_rate),
    },
    {
      metric: "Mean partial · shared",
      reference: formatPercent(comparison.reference_mean_partial),
      challenger: formatPercent(comparison.challenger_mean_partial),
      delta: formatPointDelta(comparison.partial_delta * 100),
      tone: deltaTone(comparison.partial_delta),
    },
    {
      metric: "Task coverage",
      reference: `${reference.distinct_tasks}/${subsetSize}`,
      challenger: `${challenger.distinct_tasks}/${subsetSize}`,
      delta: `${comparison.shared_tasks} shared`,
      tone: "neutral" as const,
    },
    {
      metric: "Median cost / rep",
      reference: comparison.reference_cost_tracked ? fmtCost(reference.median_cost) : "Untracked",
      challenger: comparison.challenger_cost_tracked
        ? fmtCost(challenger.median_cost)
        : "Untracked",
      delta:
        comparison.reference_cost_tracked && comparison.challenger_cost_tracked
          ? formatCostDelta(challenger.median_cost - reference.median_cost)
          : "—",
      tone:
        comparison.reference_cost_tracked && comparison.challenger_cost_tracked
          ? deltaTone(reference.median_cost - challenger.median_cost)
          : ("neutral" as const),
    },
    {
      metric: "Cost / successful rep",
      reference: fmtCost(comparison.reference_cost_per_successful_rep),
      challenger: fmtCost(comparison.challenger_cost_per_successful_rep),
      delta: formatCostDelta(comparison.cost_per_successful_rep_delta),
      tone:
        comparison.cost_per_successful_rep_delta == null
          ? ("neutral" as const)
          : deltaTone(-comparison.cost_per_successful_rep_delta),
    },
    {
      metric: "Median tokens / rep",
      reference: fmtTokens(reference.median_tokens),
      challenger: fmtTokens(challenger.median_tokens),
      delta: formatSignedCompact(challenger.median_tokens - reference.median_tokens, fmtTokens),
      tone: deltaTone(reference.median_tokens - challenger.median_tokens),
    },
    {
      metric: "Median wall / rep",
      reference: fmtSeconds(reference.median_wall_s),
      challenger: fmtSeconds(challenger.median_wall_s),
      delta: formatSignedCompact(challenger.median_wall_s - reference.median_wall_s, fmtSeconds),
      tone: deltaTone(reference.median_wall_s - challenger.median_wall_s),
    },
  ];

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="font-medium">Side-by-side evidence</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Task metrics use the shared intersection; rep metrics use the active API scope.
            </p>
          </div>
          <div className="flex gap-3 text-xs">
            <span style={{ color: REFERENCE_COLOR }}>A · {reference.config}</span>
            <span style={{ color: CHALLENGER_COLOR }}>B · {challenger.config}</span>
          </div>
        </div>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[680px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="px-2 py-2 font-medium">Metric</th>
                <th className="px-2 py-2 font-medium">A · Reference</th>
                <th className="px-2 py-2 font-medium">B · Challenger</th>
                <th className="px-2 py-2 text-right font-medium">B − A</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.metric} className="border-b border-border/70 last:border-0">
                  <td className="px-2 py-2 text-muted-foreground">{row.metric}</td>
                  <td className="px-2 py-2 tabular-nums">{row.reference}</td>
                  <td className="px-2 py-2 tabular-nums">{row.challenger}</td>
                  <td
                    className={cn(
                      "px-2 py-2 text-right tabular-nums",
                      row.tone === "good"
                        ? "text-green-400"
                        : row.tone === "bad"
                          ? "text-red-400"
                          : "text-muted-foreground",
                    )}
                  >
                    {row.delta}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function TaskEvidenceDetails({
  reference,
  challenger,
  comparison,
}: {
  reference: ComparisonRun;
  challenger: ComparisonRun;
  comparison: ConfigPairComparison;
}) {
  const sharedTasks = new Set(comparison.tasks.map((task) => task.task));
  const referenceDifficulty = difficultySolveSummary(reference.cells, sharedTasks);
  const challengerDifficulty = difficultySolveSummary(challenger.cells, sharedTasks);

  return (
    <Card>
      <CardContent className="p-4">
        <details>
          <summary className="cursor-pointer text-sm font-medium">
            Inspect all {comparison.shared_tasks} shared tasks and difficulty buckets
          </summary>
          <div className="mt-4 grid gap-4 xl:grid-cols-[360px_1fr]">
            <div>
              <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Task-difficulty buckets
              </h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Fixed task metadata; empty buckets show —, not 0%.
              </p>
              <table className="mt-2 w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="py-2">Bucket</th>
                    <th className="py-2">A</th>
                    <th className="py-2">B</th>
                    <th className="py-2 text-right">N</th>
                  </tr>
                </thead>
                <tbody>
                  {(["hard", "medium", "easy", "unknown"] as const).map((bucket) => (
                    <tr key={bucket} className="border-b border-border/70">
                      <td className="py-2 capitalize">{bucket}</td>
                      <td className="py-2 tabular-nums">
                        {formatBucket(referenceDifficulty[bucket])}
                      </td>
                      <td className="py-2 tabular-nums">
                        {formatBucket(challengerDifficulty[bucket])}
                      </td>
                      <td className="py-2 text-right tabular-nums">
                        {Math.max(
                          referenceDifficulty[bucket].total,
                          challengerDifficulty[bucket].total,
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="max-h-[420px] overflow-auto">
              <table className="w-full min-w-[620px] text-xs">
                <thead className="sticky top-0 bg-card text-left text-muted-foreground">
                  <tr>
                    <th className="px-2 py-2">Task</th>
                    <th className="px-2 py-2">Difficulty</th>
                    <th className="px-2 py-2">Outcome</th>
                    <th className="px-2 py-2 text-right">A partial</th>
                    <th className="px-2 py-2 text-right">B partial</th>
                    <th className="px-2 py-2 text-right">Δ</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.tasks.map((task) => (
                    <tr key={task.task} className="border-b border-border/70">
                      <td className="max-w-72 truncate px-2 py-2" title={task.task}>
                        {task.task}
                      </td>
                      <td className="px-2 py-2 capitalize text-muted-foreground">
                        {task.difficulty ?? "unknown"}
                      </td>
                      <td className="px-2 py-2" style={{ color: OUTCOME_COLORS[task.outcome] }}>
                        {outcomeLabel(task.outcome)}
                      </td>
                      <td className="px-2 py-2 text-right tabular-nums">
                        {formatPercent(task.reference_partial)}
                      </td>
                      <td className="px-2 py-2 text-right tabular-nums">
                        {formatPercent(task.challenger_partial)}
                      </td>
                      <td
                        className={cn(
                          "px-2 py-2 text-right tabular-nums",
                          task.partial_delta > 0
                            ? "text-green-400"
                            : task.partial_delta < 0
                              ? "text-red-400"
                              : "text-muted-foreground",
                        )}
                      >
                        {formatPointDelta(task.partial_delta * 100)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </details>
      </CardContent>
    </Card>
  );
}

function CompareLoading() {
  return (
    <div aria-label="Loading comparison" className="space-y-4">
      <span className="sr-only">Loading comparison data…</span>
      <div className="h-20 animate-pulse rounded-lg border border-border bg-card" />
      <div className="h-28 animate-pulse rounded-lg border border-border bg-card" />
      <div className="h-52 animate-pulse rounded-lg border border-border bg-card" />
    </div>
  );
}

function EmptyCompare({ message }: { message: string }) {
  return (
    <Card>
      <CardContent className="p-10 text-center">
        <p className="font-medium">No comparable pair</p>
        <p className="mt-1 text-sm text-muted-foreground">{message}</p>
      </CardContent>
    </Card>
  );
}

function comparisonVerdict(
  config: string,
  comparison: ConfigPairComparison,
): { title: string; detail: string } {
  const net = comparison.net_flips;
  const signedNet = net > 0 ? `+${net}` : net < 0 ? `−${Math.abs(net)}` : "0";
  return {
    title: `B · ${compactName(config)}: net ${signedNet} solved task${Math.abs(net) === 1 ? "" : "s"}`,
    detail: `${comparison.challenger_only} gained and ${comparison.reference_only} lost across ${comparison.shared_tasks} shared tasks.`,
  };
}

function formatRepScope(reps: number): string {
  if (reps === 0) return "all reps";
  return reps === 1 ? "first rep per task" : `first ${reps} reps per task`;
}

function taskAggregationLabel(reps: number): string {
  if (reps === 1) return "first rep per task";
  if (reps === 0) return "best observed outcome among all reps";
  return `best observed outcome among first ${reps} reps`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatPointDelta(value: number | null): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}pp`;
}

function formatCostDelta(value: number | null): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value > 0 ? "+" : value < 0 ? "−" : ""}${fmtCost(Math.abs(value))}`;
}

function formatSignedCompact(value: number, formatter: (value: number) => string): string {
  if (!Number.isFinite(value)) return "—";
  return `${value > 0 ? "+" : value < 0 ? "−" : ""}${formatter(Math.abs(value))}`;
}

function formatBucket(bucket: {
  solved: number;
  total: number;
  solve_rate: number | null;
}): string {
  if (bucket.solve_rate == null) return "—";
  return `${bucket.solve_rate.toFixed(1)}% · ${bucket.solved}/${bucket.total}`;
}

function deltaTone(value: number): "good" | "bad" | "neutral" {
  if (Math.abs(value) < 0.0001) return "neutral";
  return value > 0 ? "good" : "bad";
}

function compactName(value: string): string {
  const withoutVersion = value.replace(/@\d+(?:\.\d+)*$/, "");
  return withoutVersion.length > 24 ? `${withoutVersion.slice(0, 22)}…` : withoutVersion;
}

function outcomeLabel(outcome: ComparePairOutcome): string {
  if (outcome === "challenger_only") return "B-only";
  if (outcome === "reference_only") return "A-only";
  if (outcome === "both_solved") return "Both solved";
  return "Neither solved";
}

const OUTCOME_COLORS: Record<ComparePairOutcome, string> = {
  challenger_only: "#3fb950",
  reference_only: "#f85149",
  both_solved: "#58a6ff",
  neither_solved: "#6e7681",
};
