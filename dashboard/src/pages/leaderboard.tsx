import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Cell as RechartsCell,
  LabelList,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchCompare, fetchSubsets } from "@/lib/api";
import type { LeaderboardHighlights, LeaderboardRow } from "@/lib/leaderboard-metrics";
import {
  deriveLeaderboardRows,
  leaderboardCostFrontier,
  selectLeaderboardHighlights,
} from "@/lib/leaderboard-metrics";
import { fmtCost, fmtPercent, fmtSeconds, fmtTokens } from "@/lib/metrics";
import { useIsMobile } from "@/lib/use-mobile";
import { MeasuredContainer } from "@/components/measured-container";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ErrorState } from "@/components/error-state";
import { cn } from "@/lib/utils";

const MODEL_COLORS = [
  "#58a6ff",
  "#3fb950",
  "#f0883e",
  "#bc8cff",
  "#f85149",
  "#39c5cf",
  "#d29922",
  "#ff7b72",
  "#79c0ff",
  "#7ee787",
  "#d2a8ff",
  "#ffa657",
  "#a5d6ff",
  "#f2cc60",
];

type SortKey =
  | "solve_rate"
  | "task_solve_rate"
  | "baseline_delta"
  | "median_cost"
  | "cost_per_successful_rep"
  | "mean_partial"
  | "median_tokens"
  | "median_wall_s"
  | "total_cost";
type SortDir = "asc" | "desc";
type CostAxis = "cost_per_successful_rep" | "median_cost";
type ScatterShape = "circle" | "diamond" | "triangle" | "square" | "star" | "cross";

const LOWER_BETTER: SortKey[] = [
  "median_cost",
  "cost_per_successful_rep",
  "median_tokens",
  "median_wall_s",
  "total_cost",
];

export default function Leaderboard() {
  const { data: subsetsData } = useQuery({
    queryKey: ["subsets"],
    queryFn: fetchSubsets,
    staleTime: 5 * 60 * 1000,
  });
  const subsets = useMemo(() => subsetsData?.subsets || [], [subsetsData]);

  const [subset, setSubset] = useState("36_v2");
  const [includePartial, setIncludePartial] = useState(false);
  const [reps, setReps] = useState(0);
  const [groupScope, setGroupScope] = useState("all");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("solve_rate");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [showMoreMetrics, setShowMoreMetrics] = useState(false);
  const [costAxis, setCostAxis] = useState<CostAxis>("cost_per_successful_rep");
  const [fullChartRange, setFullChartRange] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["compare", subset, reps],
    queryFn: () => fetchCompare({ subset, reps: reps || undefined }),
    refetchInterval: 30_000,
  });

  const subsetObj = subsets.find((item) => item.name === subset);
  const subsetSize = subsetObj?.task_count ?? 0;
  const allRows = useMemo(
    () => deriveLeaderboardRows(data?.runs || [], subsetSize),
    [data, subsetSize],
  );
  const groupOptions = useMemo(
    () => [...new Set(allRows.map((row) => row.group_key))].sort(),
    [allRows],
  );
  const modelColors = useMemo(() => {
    const models = [...new Set(allRows.map((row) => row.model ?? "unknown"))].sort();
    return new Map(models.map((model, index) => [model, leaderboardModelColor(model, index)]));
  }, [allRows]);

  const filteredRows = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return allRows.filter((row) => {
      if (!includePartial && !row.full_coverage) return false;
      if (groupScope !== "all" && row.group_key !== groupScope) return false;
      const searchable = `${row.config} ${row.run_id} ${row.model ?? ""} ${row.thinking ?? ""} ${row.group_key}`;
      if (needle && !searchable.toLowerCase().includes(needle)) return false;
      return true;
    });
  }, [allRows, groupScope, includePartial, search]);

  const sortedRows = useMemo(() => {
    return [...filteredRows].sort((a, b) => {
      const av = sortableMetric(a, sortKey);
      const bv = sortableMetric(b, sortKey);
      if (av == null && bv == null) return a.run_id.localeCompare(b.run_id);
      if (av == null) return 1;
      if (bv == null) return -1;
      return sortDir === "asc" ? av - bv : bv - av;
    });
  }, [filteredRows, sortDir, sortKey]);

  const highlights = useMemo(() => selectLeaderboardHighlights(filteredRows), [filteredRows]);
  const effectiveSelectedRunId = selectedRunId ?? highlights.balanced_pick?.run_id ?? null;
  const paretoIds = useMemo(
    () => new Set(leaderboardCostFrontier(filteredRows, costAxis).map((row) => row.run_id)),
    [costAxis, filteredRows],
  );

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((direction) => (direction === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setSortDir(LOWER_BETTER.includes(key) ? "asc" : "desc");
  };

  const resetFilters = () => {
    setIncludePartial(false);
    setReps(0);
    setGroupScope("all");
    setSearch("");
  };

  const hasNonDefaultFilters =
    includePartial || reps !== 0 || groupScope !== "all" || search.trim() !== "";
  const filteredFullCoverageCount = filteredRows.filter((row) => row.full_coverage).length;

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-primary">
            Config comparison
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Leaderboard</h1>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            Choose a config using measured solve quality, same-group baseline lift, and cost
            efficiency. Rep and task success are shown separately.
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-semibold tabular-nums">{filteredRows.length}</div>
          <div className="text-xs text-muted-foreground">
            config{filteredRows.length === 1 ? "" : "s"} in current view ·{" "}
            {filteredFullCoverageCount} full coverage
          </div>
        </div>
      </header>

      {!isLoading && !error && highlights.balanced_pick && (
        <MobilePrimaryDecision
          row={highlights.balanced_pick}
          color={modelColors.get(highlights.balanced_pick.model ?? "unknown")}
          scopeSummary={`${subset} · ${formatRepScope(reps)} · ${
            groupScope === "all" ? "all model + thinking groups" : groupScope
          }`}
          onSelect={setSelectedRunId}
        />
      )}

      <LeaderboardToolbar
        subsets={subsets}
        subset={subset}
        onSubsetChange={(value) => {
          setSubset(value);
          setSelectedRunId(null);
        }}
        reps={reps}
        onRepsChange={setReps}
        includePartial={includePartial}
        onIncludePartialChange={setIncludePartial}
        groupScope={groupScope}
        onGroupScopeChange={setGroupScope}
        groupOptions={groupOptions}
        search={search}
        onSearchChange={setSearch}
        subsetSize={subsetSize}
        hasNonDefaultFilters={hasNonDefaultFilters}
        onReset={resetFilters}
      />

      {isLoading ? (
        <LeaderboardLoading />
      ) : error ? (
        <ErrorState title="Unable to load leaderboard" message={String(error)} />
      ) : filteredRows.length === 0 ? (
        <Card>
          <CardContent className="p-10 text-center">
            <p className="font-medium">No comparable configs match these filters.</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Clear search, broaden model scope, or include partial coverage.
            </p>
            {hasNonDefaultFilters && (
              <button
                type="button"
                onClick={resetFilters}
                className="mt-4 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent"
              >
                Reset filters
              </button>
            )}
          </CardContent>
        </Card>
      ) : (
        <>
          <DecisionHighlights
            highlights={highlights}
            selectedRunId={effectiveSelectedRunId}
            onSelect={setSelectedRunId}
            modelColors={modelColors}
          />
          <ValueTradeoffChart
            rows={filteredRows}
            paretoIds={paretoIds}
            selectedRunId={effectiveSelectedRunId}
            onSelect={setSelectedRunId}
            modelColors={modelColors}
            costAxis={costAxis}
            onCostAxisChange={setCostAxis}
            fullRange={fullChartRange}
            onFullRangeChange={setFullChartRange}
          />
          <LeaderboardTable
            rows={sortedRows}
            paretoIds={paretoIds}
            selectedRunId={effectiveSelectedRunId}
            onSelect={setSelectedRunId}
            modelColors={modelColors}
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={toggleSort}
            showMoreMetrics={showMoreMetrics}
            onShowMoreMetricsChange={setShowMoreMetrics}
          />
        </>
      )}
    </div>
  );
}

interface ToolbarProps {
  subsets: Array<{ name: string; task_count: number }>;
  subset: string;
  onSubsetChange: (value: string) => void;
  reps: number;
  onRepsChange: (value: number) => void;
  includePartial: boolean;
  onIncludePartialChange: (value: boolean) => void;
  groupScope: string;
  onGroupScopeChange: (value: string) => void;
  groupOptions: string[];
  search: string;
  onSearchChange: (value: string) => void;
  subsetSize: number;
  hasNonDefaultFilters: boolean;
  onReset: () => void;
}

function LeaderboardToolbar(props: ToolbarProps) {
  const controlClass =
    "h-9 rounded-md border border-border bg-background px-2.5 text-sm outline-none focus:border-primary";
  return (
    <Card>
      <CardContent className="p-3">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[auto_auto_minmax(220px,1fr)_minmax(220px,1fr)_auto] xl:items-end">
          <label className="order-1 space-y-1 text-xs text-muted-foreground xl:order-4">
            <span>Find a config</span>
            <input
              aria-label="Search configs"
              type="search"
              value={props.search}
              onChange={(event) => props.onSearchChange(event.target.value)}
              placeholder="Search config, model, or thinking…"
              className={cn(controlClass, "block w-full")}
            />
          </label>
          <label className="hidden space-y-1 text-xs text-muted-foreground md:block xl:order-1">
            <span>Dataset</span>
            <select
              aria-label="Dataset"
              value={props.subset}
              onChange={(event) => props.onSubsetChange(event.target.value)}
              className={cn(controlClass, "block w-full")}
            >
              {props.subsets.map((item) => (
                <option key={item.name} value={item.name}>
                  {item.name} · {item.task_count} tasks
                </option>
              ))}
            </select>
          </label>
          <label className="hidden space-y-1 text-xs text-muted-foreground md:block xl:order-2">
            <span>Rep cap</span>
            <select
              aria-label="Reps cap"
              value={props.reps}
              onChange={(event) => props.onRepsChange(Number(event.target.value))}
              className={cn(controlClass, "block w-full")}
            >
              <option value={0}>All reps</option>
              <option value={1}>First rep</option>
              <option value={3}>First 3 reps</option>
            </select>
          </label>
          <label className="hidden space-y-1 text-xs text-muted-foreground md:block xl:order-3">
            <span>Model + thinking</span>
            <select
              aria-label="Model and thinking"
              value={props.groupScope}
              onChange={(event) => props.onGroupScopeChange(event.target.value)}
              className={cn(controlClass, "block w-full")}
            >
              <option value="all">All model + thinking groups</option>
              {props.groupOptions.map((group) => (
                <option key={group} value={group}>
                  {group}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={props.onReset}
            disabled={!props.hasNonDefaultFilters}
            className="order-2 h-9 rounded-md border border-border px-3 text-sm text-muted-foreground hover:bg-accent hover:text-foreground disabled:cursor-default disabled:opacity-40 xl:order-5"
          >
            Reset
          </button>
        </div>

        <details className="mt-3 rounded-md border border-border md:hidden">
          <summary className="cursor-pointer px-3 py-2 text-sm text-muted-foreground">
            Dataset, reps, model + thinking
          </summary>
          <div className="grid gap-3 border-t border-border p-3">
            <label className="space-y-1 text-xs text-muted-foreground">
              <span>Dataset</span>
              <select
                aria-label="Mobile dataset"
                value={props.subset}
                onChange={(event) => props.onSubsetChange(event.target.value)}
                className={cn(controlClass, "block w-full")}
              >
                {props.subsets.map((item) => (
                  <option key={item.name} value={item.name}>
                    {item.name} · {item.task_count} tasks
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              <span>Rep cap</span>
              <select
                aria-label="Mobile reps cap"
                value={props.reps}
                onChange={(event) => props.onRepsChange(Number(event.target.value))}
                className={cn(controlClass, "block w-full")}
              >
                <option value={0}>All reps</option>
                <option value={1}>First rep</option>
                <option value={3}>First 3 reps</option>
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              <span>Model + thinking</span>
              <select
                aria-label="Mobile model and thinking"
                value={props.groupScope}
                onChange={(event) => props.onGroupScopeChange(event.target.value)}
                className={cn(controlClass, "block w-full")}
              >
                <option value="all">All model + thinking groups</option>
                {props.groupOptions.map((group) => (
                  <option key={group} value={group}>
                    {group}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </details>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3">
          <div className="flex items-center gap-1 rounded-md border border-border bg-background p-0.5 text-xs">
            <button
              type="button"
              aria-pressed={!props.includePartial}
              onClick={() => props.onIncludePartialChange(false)}
              className={cn(
                "rounded px-2.5 py-1.5",
                !props.includePartial
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground",
              )}
            >
              Full coverage
            </button>
            <button
              type="button"
              aria-pressed={props.includePartial}
              onClick={() => props.onIncludePartialChange(true)}
              className={cn(
                "rounded px-2.5 py-1.5",
                props.includePartial
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground",
              )}
            >
              Include partial
            </button>
          </div>
          <p className="text-xs text-muted-foreground">
            Full coverage = all {props.subsetSize || "selected"} tasks. Cost charts exclude $0
            untracked cost.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function MobilePrimaryDecision({
  row,
  color,
  scopeSummary,
  onSelect,
}: {
  row: LeaderboardRow;
  color?: string;
  scopeSummary: string;
  onSelect: (runId: string) => void;
}) {
  return (
    <section className="md:hidden" aria-label="Start here">
      <button
        type="button"
        onClick={() => onSelect(row.run_id)}
        className="w-full rounded-lg border border-primary/60 bg-primary/10 p-3 text-left"
      >
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-primary">
            Start here · balanced pick
          </span>
          {row.cost_tracked ? null : (
            <Badge className="border-amber-500/50 text-amber-400">Cost untracked</Badge>
          )}
        </div>
        <div className="mt-2 flex items-start gap-2">
          <span
            className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
            style={{ backgroundColor: color }}
          />
          <div className="min-w-0">
            <div className="truncate font-medium">{row.config}</div>
            <div className="text-xs text-muted-foreground">
              {row.model} · {row.thinking}
            </div>
          </div>
        </div>
        <div className="mt-2 flex items-baseline gap-1.5">
          <span className="text-xl font-semibold tabular-nums">
            {fmtCost(row.cost_per_successful_rep)}
          </span>
          <span className="text-xs text-muted-foreground">cost / successful rep</span>
        </div>
        <div className="mt-1 text-xs tabular-nums text-muted-foreground">
          {row.solve_rate.toFixed(1)}% reps · {row.task_solve_rate.toFixed(1)}% tasks
        </div>
        <div className="mt-2 border-t border-primary/20 pt-2 text-[11px] text-muted-foreground">
          View: {scopeSummary}
        </div>
        <div className="mt-1 text-[11px] text-muted-foreground">
          Equal-weight normalized solve/value frontier; chart controls do not change this pick.
        </div>
      </button>
    </section>
  );
}

function DecisionHighlights({
  highlights,
  selectedRunId,
  onSelect,
  modelColors,
}: {
  highlights: LeaderboardHighlights;
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
  modelColors: Map<string, string>;
}) {
  const cards = [
    {
      label: "Balanced pick",
      row: highlights.balanced_pick,
      headline: (row: LeaderboardRow) => fmtCost(row.cost_per_successful_rep),
      unit: "cost / successful rep",
      rule: "Equal-weight 0–1 normalization of rep solve and cost / successful rep across the frontier; smallest distance to ideal wins. Chart controls do not change it.",
      primary: true,
    },
    {
      label: "Highest solve",
      row: highlights.best_solve,
      headline: (row: LeaderboardRow) => `${row.solve_rate.toFixed(1)}%`,
      unit: "per rep",
      rule: "Highest observed rep solve rate among full-coverage configs.",
      primary: false,
    },
    {
      label: "Best value",
      row: highlights.best_value,
      headline: (row: LeaderboardRow) => fmtCost(row.cost_per_successful_rep),
      unit: "cost / successful rep",
      rule: "Lowest observed total cost per successful rep.",
      primary: false,
    },
    {
      label: "Biggest baseline lift",
      row: highlights.biggest_lift,
      headline: (row: LeaderboardRow) => formatDelta(row.baseline_delta),
      unit: "vs baseline",
      rule: "Largest rep solve-rate lift vs baseline at the same model + thinking.",
      primary: false,
    },
  ];

  return (
    <section aria-labelledby="decision-highlights-heading">
      <div className="mb-2 flex items-end justify-between gap-3">
        <div>
          <h2 id="decision-highlights-heading" className="font-medium">
            Measured standouts
          </h2>
          <p className="text-xs text-muted-foreground">
            Start with Balanced pick; use the others when optimizing one criterion. These are
            observations, not significance claims.
          </p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <DecisionCard
            key={card.label}
            {...card}
            selected={card.row?.run_id === selectedRunId}
            onSelect={onSelect}
            color={card.row ? modelColors.get(card.row.model ?? "unknown") : undefined}
          />
        ))}
      </div>
    </section>
  );
}

function DecisionCard({
  label,
  row,
  headline,
  unit,
  rule,
  selected,
  onSelect,
  color,
  primary,
}: {
  label: string;
  row: LeaderboardRow | null;
  headline: (row: LeaderboardRow) => string;
  unit: string;
  rule: string;
  selected: boolean;
  onSelect: (runId: string) => void;
  color?: string;
  primary: boolean;
}) {
  return (
    <button
      type="button"
      disabled={!row}
      onClick={() => row && onSelect(row.run_id)}
      className={cn(
        "rounded-lg border bg-card p-3 text-left transition hover:border-primary/60 hover:bg-accent/20 disabled:cursor-default",
        primary && "hidden border-primary/60 bg-primary/5 md:block",
        selected ? "border-primary ring-1 ring-primary/50" : !primary && "border-border",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
        <div className="flex gap-1">
          {primary && <Badge className="border-primary/50 text-primary">Start here</Badge>}
          {row && !row.cost_tracked && (
            <Badge className="border-amber-500/50 text-amber-400">Cost untracked</Badge>
          )}
        </div>
      </div>
      {row ? (
        <>
          <div className="mt-3 flex items-start gap-2">
            <span
              className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: color }}
            />
            <div className="min-w-0">
              <div className="truncate font-medium" title={row.config}>
                {row.config}
              </div>
              <div className="truncate text-xs text-muted-foreground">
                {row.model} · {row.thinking}
              </div>
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-1.5">
            <span className="text-2xl font-semibold tabular-nums">{headline(row)}</span>
            <span className="text-xs text-muted-foreground">{unit}</span>
          </div>
          <div className="mt-1 text-xs tabular-nums text-muted-foreground">
            {row.solve_rate.toFixed(1)}% reps · {row.task_solve_rate.toFixed(1)}% tasks
          </div>
          <p className="mt-3 border-t border-border pt-2 text-[11px] leading-relaxed text-muted-foreground">
            {rule}
          </p>
        </>
      ) : (
        <p className="mt-6 text-sm text-muted-foreground">No eligible config</p>
      )}
    </button>
  );
}

function ValueTradeoffChart({
  rows,
  paretoIds,
  selectedRunId,
  onSelect,
  modelColors,
  costAxis,
  onCostAxisChange,
  fullRange,
  onFullRangeChange,
}: {
  rows: LeaderboardRow[];
  paretoIds: Set<string>;
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
  modelColors: Map<string, string>;
  costAxis: CostAxis;
  onCostAxisChange: (axis: CostAxis) => void;
  fullRange: boolean;
  onFullRangeChange: (value: boolean) => void;
}) {
  const isMobile = useIsMobile();
  const eligible = rows.filter(
    (row) =>
      row.full_coverage &&
      row.cost_tracked &&
      (costAxis === "median_cost" || row.cost_per_successful_rep != null),
  );
  const xValue = (row: LeaderboardRow) =>
    costAxis === "cost_per_successful_rep" ? row.cost_per_successful_rep! : row.median_cost;
  const sortedX = eligible.map(xValue).sort((a, b) => a - b);
  const decisionMax = sortedX[Math.max(0, Math.ceil(sortedX.length * 0.95) - 1)] ?? 0;
  const visible = fullRange
    ? eligible
    : eligible.filter((row) => xValue(row) <= decisionMax || row.run_id === selectedRunId);
  const hiddenCount = eligible.length - visible.length;
  const chartData = visible.map((row) => ({
    runId: row.run_id,
    name: `${row.config} · ${row.model}/${row.thinking}`,
    costMetric: xValue(row),
    solveRate: row.solve_rate,
    thinking: row.thinking ?? "unknown",
    color: modelColors.get(row.model ?? "unknown") ?? MODEL_COLORS[0],
    isPareto: paretoIds.has(row.run_id),
    isSelected: row.run_id === selectedRunId,
    label: row.run_id === selectedRunId ? compactConfigName(row.config) : "",
  }));
  const thinkingGroups = [...new Set(chartData.map((point) => point.thinking))].sort();
  const visibleModels = [...new Set(visible.map((row) => row.model ?? "unknown"))].sort();
  const selectedRow = rows.find((row) => row.run_id === selectedRunId) ?? null;
  const selectedPoint = chartData.find((point) => point.runId === selectedRunId) ?? null;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-medium">Value frontier</h2>
            <p className="text-xs text-muted-foreground">
              Frontier follows the active cost axis · full coverage and tracked cost only ·
              upper-left is better
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs">
              <a href="#ranked-evidence" className="text-primary hover:underline">
                Jump to ranked evidence ↓
              </a>
              {selectedRow && (
                <span className="flex items-center gap-1.5 text-foreground">
                  <span className="text-white">★</span>
                  Selected: {selectedRow.config} · {selectedRow.model}/{selectedRow.thinking}
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <SegmentedControl
              value={costAxis}
              options={[
                ["cost_per_successful_rep", "Cost / successful rep"],
                ["median_cost", "Median cost"],
              ]}
              onChange={(value) => onCostAxisChange(value as CostAxis)}
            />
            <SegmentedControl
              value={fullRange ? "full" : "decision"}
              options={[
                ["decision", "Decision range"],
                ["full", "Full range"],
              ]}
              onChange={(value) => onFullRangeChange(value === "full")}
            />
          </div>
        </div>

        <MeasuredContainer height={isMobile ? 260 : 300}>
          {(width, height) => (
            <ScatterChart
              width={width}
              height={height}
              margin={{ top: 26, right: 24, bottom: 34, left: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215 14% 22%)" />
              <XAxis
                type="number"
                dataKey="costMetric"
                name={
                  costAxis === "cost_per_successful_rep" ? "Cost / successful rep" : "Median cost"
                }
                domain={[0, "dataMax"]}
                tickFormatter={(value) => fmtCost(Number(value))}
                stroke="hsl(215 16% 65%)"
                tick={{ fontSize: isMobile ? 10 : 12 }}
                label={{
                  value:
                    costAxis === "cost_per_successful_rep"
                      ? "Cost / successful rep"
                      : "Median cost / rep",
                  position: "insideBottom",
                  offset: -12,
                  fill: "hsl(215 16% 65%)",
                  fontSize: 11,
                }}
              />
              <YAxis
                type="number"
                dataKey="solveRate"
                name="Rep solve rate"
                domain={[0, 100]}
                unit="%"
                stroke="hsl(215 16% 65%)"
                tick={{ fontSize: isMobile ? 10 : 12 }}
                label={{
                  value: "Rep solve rate",
                  angle: -90,
                  position: "insideLeft",
                  fill: "hsl(215 16% 65%)",
                  fontSize: 11,
                }}
              />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                contentStyle={{
                  background: "hsl(215 14% 11%)",
                  border: "1px solid hsl(215 14% 22%)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value: number, name: string) =>
                  name === "Rep solve rate"
                    ? `${Number(value).toFixed(1)}%`
                    : fmtCost(Number(value))
                }
                labelFormatter={(_, payload) => payload?.[0]?.payload?.name || ""}
              />
              {thinkingGroups.map((thinking) => {
                const group = chartData.filter((point) => point.thinking === thinking);
                return (
                  <Scatter
                    key={thinking}
                    data={group}
                    shape={thinkingShape(thinking)}
                    isAnimationActive={false}
                    onClick={(entry) => {
                      const point = entry as unknown as { runId?: string };
                      if (point.runId) onSelect(point.runId);
                    }}
                  >
                    {group.map((point) => (
                      <RechartsCell
                        key={point.runId}
                        fill={point.color}
                        fillOpacity={point.isPareto || point.isSelected ? 0.95 : 0.48}
                        stroke={
                          point.isSelected ? "#fff" : point.isPareto ? point.color : "transparent"
                        }
                        strokeWidth={point.isSelected ? 3 : point.isPareto ? 2 : 0}
                        className="cursor-pointer outline-none"
                      />
                    ))}
                  </Scatter>
                );
              })}
              {selectedPoint && (
                <Scatter
                  data={[selectedPoint]}
                  shape="star"
                  fill="#ffffff"
                  stroke="hsl(215 20% 8%)"
                  strokeWidth={1.5}
                  isAnimationActive={false}
                >
                  <LabelList
                    dataKey="label"
                    position="top"
                    offset={8}
                    fill="hsl(210 20% 94%)"
                    fontSize={11}
                    fontWeight={600}
                  />
                </Scatter>
              )}
            </ScatterChart>
          )}
        </MeasuredContainer>

        <div className="mt-2 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3 text-xs">
          <div className="flex flex-wrap gap-x-3 gap-y-1.5">
            {visibleModels.map((model) => (
              <span key={model} className="flex items-center gap-1.5 text-muted-foreground">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: modelColors.get(model) }}
                />
                {model}
              </span>
            ))}
          </div>
          <div className="flex flex-wrap gap-2 text-muted-foreground">
            {thinkingGroups.map((thinking) => (
              <span key={thinking}>
                {thinkingGlyph(thinking)} {thinkingShapeName(thinking)} = {thinking}
              </span>
            ))}
            <span className="text-foreground">colored ring = Pareto</span>
            <span className="text-foreground">white ring = selected</span>
          </div>
        </div>
        {hiddenCount > 0 && !fullRange && (
          <p className="mt-2 text-xs text-amber-400">
            {hiddenCount} extreme-cost config{hiddenCount === 1 ? "" : "s"} hidden from the decision
            range; use Full range to inspect.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function LeaderboardTable({
  rows,
  paretoIds,
  selectedRunId,
  onSelect,
  modelColors,
  sortKey,
  sortDir,
  onSort,
  showMoreMetrics,
  onShowMoreMetricsChange,
}: {
  rows: LeaderboardRow[];
  paretoIds: Set<string>;
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
  modelColors: Map<string, string>;
  sortKey: SortKey;
  sortDir: SortDir;
  onSort: (key: SortKey) => void;
  showMoreMetrics: boolean;
  onShowMoreMetricsChange: (value: boolean) => void;
}) {
  return (
    <Card id="ranked-evidence" className="scroll-mt-16">
      <CardContent className="p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
          <div>
            <h2 className="font-medium">Ranked evidence</h2>
            <p className="text-xs text-muted-foreground">
              Default rank is observed rep solve rate. Click a header to rerank.
            </p>
          </div>
          <button
            type="button"
            aria-pressed={showMoreMetrics}
            onClick={() => onShowMoreMetricsChange(!showMoreMetrics)}
            className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            {showMoreMetrics ? "Fewer metrics" : "More metrics"}
          </button>
        </div>

        <div className="space-y-2 p-3 md:hidden">
          {rows.map((row, index) => (
            <MobileLeaderboardCard
              key={row.run_id}
              row={row}
              rank={index + 1}
              selected={row.run_id === selectedRunId}
              pareto={paretoIds.has(row.run_id)}
              color={modelColors.get(row.model ?? "unknown")}
              onSelect={onSelect}
            />
          ))}
        </div>

        <div className="hidden overflow-x-auto md:block">
          <Table className="min-w-[980px]">
            <TableHeader className="sticky top-12 z-20 bg-card">
              <TableRow>
                <TableHead className="sticky left-0 z-30 min-w-[300px] bg-card">Config</TableHead>
                <TableHead className="min-w-[170px] text-right">
                  <SortButton
                    label="Solve"
                    sortKey="solve_rate"
                    activeKey={sortKey}
                    direction={sortDir}
                    onSort={onSort}
                  />
                </TableHead>
                <TableHead className="min-w-[110px] text-right">
                  <SortButton
                    label="Δ baseline"
                    sortKey="baseline_delta"
                    activeKey={sortKey}
                    direction={sortDir}
                    onSort={onSort}
                  />
                </TableHead>
                <TableHead className="min-w-[100px] text-right">
                  <SortButton
                    label="Med cost"
                    sortKey="median_cost"
                    activeKey={sortKey}
                    direction={sortDir}
                    onSort={onSort}
                  />
                </TableHead>
                <TableHead className="min-w-[110px] text-right">
                  <SortButton
                    label="Cost / successful rep"
                    sortKey="cost_per_successful_rep"
                    activeKey={sortKey}
                    direction={sortDir}
                    onSort={onSort}
                  />
                </TableHead>
                <TableHead className="min-w-[130px] text-right">Sample</TableHead>
                {showMoreMetrics && (
                  <>
                    <TableHead className="text-right">
                      <SortButton
                        label="Mean partial"
                        sortKey="mean_partial"
                        activeKey={sortKey}
                        direction={sortDir}
                        onSort={onSort}
                      />
                    </TableHead>
                    <TableHead className="text-right">
                      <SortButton
                        label="Med tokens"
                        sortKey="median_tokens"
                        activeKey={sortKey}
                        direction={sortDir}
                        onSort={onSort}
                      />
                    </TableHead>
                    <TableHead className="text-right">
                      <SortButton
                        label="Med time"
                        sortKey="median_wall_s"
                        activeKey={sortKey}
                        direction={sortDir}
                        onSort={onSort}
                      />
                    </TableHead>
                    <TableHead className="text-right">
                      <SortButton
                        label="Total cost"
                        sortKey="total_cost"
                        activeKey={sortKey}
                        direction={sortDir}
                        onSort={onSort}
                      />
                    </TableHead>
                  </>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row, index) => {
                const selected = row.run_id === selectedRunId;
                return (
                  <TableRow
                    key={row.run_id}
                    onClick={() => onSelect(row.run_id)}
                    className={cn(
                      "cursor-pointer",
                      selected && "bg-primary/10",
                      !row.full_coverage && "bg-amber-500/5",
                    )}
                  >
                    <TableCell
                      className={cn(
                        "sticky left-0 z-10 bg-card",
                        selected &&
                          "bg-[hsl(var(--card))] shadow-[inset_3px_0_hsl(var(--primary))]",
                      )}
                    >
                      <ConfigIdentity
                        row={row}
                        rank={index + 1}
                        pareto={paretoIds.has(row.run_id)}
                        color={modelColors.get(row.model ?? "unknown")}
                      />
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      <div className="text-base font-semibold">{row.solve_rate.toFixed(1)}%</div>
                      <div className="text-[11px] text-muted-foreground">
                        {row.solved}/{row.total_cells} reps · {row.task_solved}/{row.task_total}{" "}
                        tasks ({row.task_solve_rate.toFixed(1)}%)
                      </div>
                    </TableCell>
                    <TableCell
                      className={cn("text-right font-mono", deltaColor(row.baseline_delta))}
                    >
                      {formatDelta(row.baseline_delta)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {row.cost_tracked ? fmtCost(row.median_cost) : "untracked"}
                    </TableCell>
                    <TableCell className="text-right font-mono font-medium">
                      {fmtCost(row.cost_per_successful_rep)}
                    </TableCell>
                    <TableCell className="text-right text-xs tabular-nums text-muted-foreground">
                      {row.sample_label}
                    </TableCell>
                    {showMoreMetrics && (
                      <>
                        <TableCell className="text-right font-mono">
                          {fmtPercent(row.mean_partial)}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {fmtTokens(row.median_tokens)}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {fmtSeconds(row.median_wall_s)}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {fmtCost(row.total_cost)}
                        </TableCell>
                      </>
                    )}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

function ConfigIdentity({
  row,
  rank,
  pareto,
  color,
}: {
  row: LeaderboardRow;
  rank: number;
  pareto: boolean;
  color?: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <span className="w-6 pt-0.5 text-right font-mono text-xs text-muted-foreground">{rank}</span>
      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: color }} />
      <div className="min-w-0">
        <div className="max-w-[235px] truncate font-medium" title={row.config}>
          {row.config}
        </div>
        <div className="text-xs text-muted-foreground">
          {row.model} · {row.thinking}
        </div>
        <div className="mt-1 flex flex-wrap gap-1">
          {pareto && <Badge className="border-primary/50 text-primary">Pareto</Badge>}
          {row.is_baseline && <Badge>Baseline</Badge>}
          {!row.cost_tracked && (
            <Badge className="border-amber-500/50 text-amber-400">Cost untracked</Badge>
          )}
          {!row.full_coverage && (
            <Badge className="border-amber-500/50 text-amber-400">Partial</Badge>
          )}
        </div>
      </div>
    </div>
  );
}

function MobileLeaderboardCard({
  row,
  rank,
  selected,
  pareto,
  color,
  onSelect,
}: {
  row: LeaderboardRow;
  rank: number;
  selected: boolean;
  pareto: boolean;
  color?: string;
  onSelect: (runId: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(row.run_id)}
      className={cn(
        "w-full rounded-md border p-3 text-left",
        selected ? "border-primary bg-primary/10" : "border-border",
        !row.full_coverage && "border-amber-500/40",
      )}
    >
      <ConfigIdentity row={row} rank={rank} pareto={pareto} color={color} />
      <div className="mt-3 grid grid-cols-3 gap-2 border-t border-border pt-3 text-right">
        <MobileMetric label="Rep solve" value={`${row.solve_rate.toFixed(1)}%`} />
        <MobileMetric
          label="Δ baseline"
          value={formatDelta(row.baseline_delta)}
          className={deltaColor(row.baseline_delta)}
        />
        <MobileMetric label="Cost / successful rep" value={fmtCost(row.cost_per_successful_rep)} />
      </div>
      <div className="mt-2 text-right text-[11px] text-muted-foreground">
        {row.task_solved}/{row.task_total} tasks · {row.sample_label}
      </div>
    </button>
  );
}

function MobileMetric({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={cn("mt-0.5 font-mono font-medium", className)}>{value}</div>
    </div>
  );
}

function SortButton({
  label,
  sortKey,
  activeKey,
  direction,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  activeKey: SortKey;
  direction: SortDir;
  onSort: (key: SortKey) => void;
}) {
  const active = sortKey === activeKey;
  return (
    <button
      type="button"
      onClick={() => onSort(sortKey)}
      className={cn(
        "w-full select-none text-right hover:text-foreground",
        active && "text-foreground",
      )}
    >
      {label} {active ? (direction === "asc" ? "▲" : "▼") : ""}
    </button>
  );
}

function SegmentedControl({
  value,
  options,
  onChange,
}: {
  value: string;
  options: Array<[string, string]>;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex rounded-md border border-border bg-background p-0.5">
      {options.map(([optionValue, label]) => (
        <button
          key={optionValue}
          type="button"
          aria-pressed={value === optionValue}
          onClick={() => onChange(optionValue)}
          className={cn(
            "rounded px-2 py-1",
            value === optionValue ? "bg-accent text-foreground" : "text-muted-foreground",
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function LeaderboardLoading() {
  return (
    <div aria-label="Loading leaderboard" className="space-y-4">
      <span className="sr-only">Loading leaderboard…</span>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <div key={index} className="h-44 animate-pulse rounded-lg border border-border bg-card" />
        ))}
      </div>
      <div className="h-80 animate-pulse rounded-lg border border-border bg-card" />
    </div>
  );
}

function sortableMetric(row: LeaderboardRow, key: SortKey): number | null {
  const value = row[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function compactConfigName(config: string): string {
  const withoutVersion = config.replace(/@\d+(?:\.\d+)*$/, "");
  return withoutVersion.length > 24 ? `${withoutVersion.slice(0, 22)}…` : withoutVersion;
}

function formatDelta(delta: number | null): string {
  if (delta == null || !Number.isFinite(delta)) return "—";
  return `${delta > 0 ? "+" : ""}${delta.toFixed(1)}pp`;
}

function deltaColor(delta: number | null): string {
  if (delta == null || Math.abs(delta) < 0.05) return "text-muted-foreground";
  return delta > 0 ? "text-green-400" : "text-red-400";
}

function formatRepScope(reps: number): string {
  if (reps === 0) return "all reps";
  return reps === 1 ? "first rep" : `first ${reps} reps`;
}

function leaderboardModelColor(model: string, fallbackIndex: number): string {
  const value = model.toLowerCase();
  if (value.includes("gpt-5.6")) return "#58a6ff";
  if (value.includes("gpt-5.5")) return "#3fb950";
  if (value.includes("deepseek")) return "#f0883e";
  if (value.includes("qwen")) return "#bc8cff";
  if (value.includes("ornith")) return "#39c5cf";
  if (value.includes("composer")) return "#d29922";
  if (value.includes("gemma")) return "#ff7b72";
  if (value.includes("laguna")) return "#79c0ff";
  if (value.includes("spark")) return "#d2a8ff";
  return MODEL_COLORS[fallbackIndex % MODEL_COLORS.length]!;
}

function thinkingShape(thinking: string): ScatterShape {
  if (thinking === "xhigh") return "star";
  if (thinking === "high") return "triangle";
  if (thinking === "medium") return "diamond";
  if (thinking === "low") return "circle";
  if (thinking === "minimal") return "square";
  return "cross";
}

function thinkingShapeName(thinking: string): string {
  if (thinking === "xhigh") return "star";
  if (thinking === "high") return "triangle";
  if (thinking === "medium") return "diamond";
  if (thinking === "low") return "circle";
  if (thinking === "minimal") return "square";
  return "cross";
}

function thinkingGlyph(thinking: string): string {
  if (thinking === "xhigh") return "★";
  if (thinking === "high") return "▲";
  if (thinking === "medium") return "◆";
  if (thinking === "low") return "●";
  if (thinking === "minimal") return "■";
  return "✚";
}
