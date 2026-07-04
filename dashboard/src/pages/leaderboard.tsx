import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell as RechartsCell,
} from 'recharts'
import { fetchCompare, fetchSubsets } from '@/lib/api'
import type { ComparisonRun } from '@/lib/types'
import { paretoFrontier, fmtCost, fmtTokens } from '@/lib/metrics'
import { useIsMobile } from '@/lib/use-mobile'
import { MeasuredContainer } from '@/components/measured-container'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from '@/components/ui/table'
import { ErrorState } from '@/components/error-state'
import { cn } from '@/lib/utils'

const COLORS = ['#58a6ff', '#3fb950', '#f85149', '#d29922', '#bc8cff', '#ff7b72', '#79c0ff', '#7ee787']

type SortKey = 'solve_rate' | 'mean_partial' | 'median_cost' | 'median_tokens' | 'total_cost' | 'solved' | 'median_wall_s'
type SortDir = 'asc' | 'desc'

// Columns where lower is better (so ascending sort = best first by default).
const LOWER_BETTER: SortKey[] = ['median_cost', 'median_tokens', 'total_cost', 'median_wall_s']

export default function Leaderboard() {
  const { data: subsetsData } = useQuery({ queryKey: ['subsets'], queryFn: fetchSubsets, staleTime: 5 * 60 * 1000 })
  const subsets = useMemo(() => subsetsData?.subsets || [], [subsetsData])

  const [subset, setSubset] = useState('36_v2')
  const [hidePartial, setHidePartial] = useState(true)
  const [reps, setReps] = useState(0) // 0 = all reps
  const [sortKey, setSortKey] = useState<SortKey>('solve_rate')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const { data, isLoading, error } = useQuery({
    queryKey: ['compare', subset, reps],
    queryFn: () => fetchCompare({ subset, reps: reps || undefined }),
    refetchInterval: 30000,
  })

  const subsetObj = subsets.find((s) => s.name === subset)
  const subsetSize = subsetObj?.task_count ?? 0

  const runs = useMemo(() => {
    let rs = data?.runs || []
    if (hidePartial && subsetSize > 0) {
      // Full coverage = the run has data for at least every task in the subset.
      // Count distinct tasks (not raw cells) so 3-reps-on-12-of-36 doesn't slip through.
      rs = rs.filter((r) => r.distinct_tasks >= subsetSize)
    }
    return rs
  }, [data, hidePartial, subsetSize])

  const sorted = useMemo(() => {
    const arr = [...runs]
    arr.sort((a, b) => {
      const av = a[sortKey] ?? 0
      const bv = b[sortKey] ?? 0
      return sortDir === 'asc' ? av - bv : bv - av
    })
    return arr
  }, [runs, sortKey, sortDir])

  const maxN = useMemo(() => Math.max(1, ...runs.map((r) => r.total_cells)), [runs])

  if (isLoading) return <p className="text-muted-foreground">Loading leaderboard…</p>
  if (error) return <ErrorState title="Unable to load leaderboard" message={String(error)} />

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      // When switching to a lower-is-better column for the first time, default to ascending (best first).
      setSortDir(LOWER_BETTER.includes(key) ? 'asc' : 'desc')
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
            Leaderboard — rank configs on a fixed dataset
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Dataset</span>
            <select
              value={subset}
              onChange={(e) => setSubset(e.target.value)}
              className="rounded-md border border-border bg-background px-2 py-1 text-sm"
            >
              {subsets.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name} ({s.task_count} tasks)
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Reps cap</span>
            <select
              value={reps}
              onChange={(e) => setReps(Number(e.target.value))}
              className="rounded-md border border-border bg-background px-2 py-1 text-sm"
            >
              <option value={0}>all</option>
              <option value={1}>1</option>
              <option value={3}>3</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={hidePartial}
              onChange={(e) => setHidePartial(e.target.checked)}
              className="h-4 w-4"
            />
            <span className="text-muted-foreground">
              Hide partial-coverage runs (n &ge; {subsetSize})
            </span>
          </label>
          <span className="text-xs text-muted-foreground">
            {sorted.length} run{sorted.length === 1 ? '' : 's'} shown
          </span>
        </CardContent>
      </Card>

      {sorted.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-sm text-muted-foreground">
            No runs match these filters. Try disabling “Hide partial-coverage runs”.
          </CardContent>
        </Card>
      ) : (
        <>
          <ParetoScatter runs={sorted} />
          <LeaderboardTable
            runs={sorted}
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={toggleSort}
            maxN={maxN}
          />
        </>
      )}
    </div>
  )
}

function ParetoScatter({ runs }: { runs: ComparisonRun[] }) {
  const isMobile = useIsMobile()
  const points = runs.map((r) => ({ id: r.run_id, cost: r.median_cost, value: r.solve_rate, r }))
  const annotated = paretoFrontier(points)
  const chartData = annotated.map((p, i) => ({
    name: p.r.run_id,
    cost: p.cost,
    solveRate: p.value,
    isPareto: p.isPareto,
    color: COLORS[i % COLORS.length],
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Pareto frontier — solve rate vs median cost (upper-left = better) · hover a point for details
        </CardTitle>
      </CardHeader>
      <CardContent>
        <MeasuredContainer height={isMobile ? 320 : 380}>
          {(w, h) => (
            <ScatterChart width={w} height={h} margin={{ top: 16, right: 24, bottom: 28, left: 12 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215 14% 22%)" />
              <XAxis
                type="number" dataKey="cost" name="Median Cost"
                tickFormatter={(v) => fmtCost(v)}
                stroke="hsl(215 16% 65%)" tick={{ fontSize: isMobile ? 11 : 13 }}
                domain={[0, 'dataMax']}
                padding={{ left: 20, right: 20 }}
                label={{ value: 'Median Cost ($)', position: 'insideBottom', offset: -8, fill: 'hsl(215 16% 65%)', fontSize: 12 }}
              />
              <YAxis
                type="number" dataKey="solveRate" name="Solve Rate"
                domain={[0, 100]} unit="%"
                stroke="hsl(215 16% 65%)" tick={{ fontSize: isMobile ? 11 : 13 }}
                padding={{ top: 12, bottom: 12 }}
                label={{ value: 'Solve Rate (%)', angle: -90, position: 'insideLeft', fill: 'hsl(215 16% 65%)', fontSize: 12 }}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ background: 'hsl(215 14% 11%)', border: '1px solid hsl(215 14% 22%)', borderRadius: 8, fontSize: 13 }}
                formatter={(value: number, name: string) =>
                  name === 'Solve Rate' ? `${value.toFixed(1)}%` : fmtCost(value)}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.name || ''}
              />
              <Scatter data={chartData} isAnimationActive={false}>
                {chartData.map((entry, i) => (
                  <RechartsCell
                    key={i}
                    fill={entry.color}
                    fillOpacity={entry.isPareto ? 0.95 : 0.45}
                    stroke={entry.isPareto ? '#fff' : 'none'}
                    strokeWidth={entry.isPareto ? 2 : 0}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          )}
        </MeasuredContainer>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="text-muted-foreground">★ Pareto-optimal:</span>
          {chartData.filter((d) => d.isPareto).map((d) => (
            <Badge key={d.name} className="text-xs">★ {d.name}</Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

interface LeaderboardTableProps {
  runs: ComparisonRun[]
  sortKey: SortKey
  sortDir: SortDir
  onSort: (key: SortKey) => void
  maxN: number
}

function LeaderboardTable({ runs, sortKey, sortDir, onSort, maxN }: LeaderboardTableProps) {
  // Precompute Pareto set for badge display
  const paretoIds = useMemo(() => {
    const pts = runs.map((r) => ({ id: r.run_id, cost: r.median_cost, value: r.solve_rate }))
    return new Set(paretoFrontier(pts).filter((p) => p.isPareto).map((p) => p.id))
  }, [runs])

  const arrow = (key: SortKey) => (key === sortKey ? (sortDir === 'asc' ? ' ▲' : ' ▼') : '')

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Ranked results (click a column to sort)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12 text-right">#</TableHead>
                <TableHead>Config</TableHead>
                <TableHead className="text-right cursor-pointer select-none" onClick={() => onSort('solved')}>
                  Solves{arrow('solved')}
                </TableHead>
                <TableHead className="text-right cursor-pointer select-none" onClick={() => onSort('solve_rate')}>
                  Solve %{arrow('solve_rate')}
                </TableHead>
                <TableHead className="hidden text-right cursor-pointer select-none md:table-cell" onClick={() => onSort('mean_partial')}>
                  Mean partial{arrow('mean_partial')}
                </TableHead>
                <TableHead className="text-right cursor-pointer select-none" onClick={() => onSort('median_cost')}>
                  Med cost{arrow('median_cost')}
                </TableHead>
                <TableHead className="hidden text-right cursor-pointer select-none md:table-cell" onClick={() => onSort('median_tokens')}>
                  Med tokens{arrow('median_tokens')}
                </TableHead>
                <TableHead className="text-right cursor-pointer select-none" onClick={() => onSort('total_cost')}>
                  Total cost{arrow('total_cost')}
                </TableHead>
                <TableHead className="text-right">n</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((r, i) => {
                const isPareto = paretoIds.has(r.run_id)
                const [model, thinking, config] = r.run_id.split('/')
                const coverage = r.total_cells / maxN
                return (
                  <TableRow key={r.run_id} className={isPareto ? 'bg-accent/40' : undefined}>
                    <TableCell className="text-right font-mono text-muted-foreground">{i + 1}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {isPareto && <span title="Pareto-optimal">★</span>}
                        <div>
                          <div className="font-medium">{config}</div>
                          <div className="text-xs text-muted-foreground">{model} · {thinking}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {r.solved}/{r.total_cells}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="hidden h-2 w-16 overflow-hidden rounded bg-muted sm:block">
                          <div
                            className="h-full rounded"
                            style={{
                              width: `${Math.min(100, r.solve_rate)}%`,
                              backgroundColor: solveColor(r.solve_rate),
                            }}
                          />
                        </div>
                        <span className="font-mono">{r.solve_rate.toFixed(1)}</span>
                      </div>
                    </TableCell>
                    <TableCell className="hidden text-right font-mono text-muted-foreground md:table-cell">
                      {(r.mean_partial * 100).toFixed(1)}
                    </TableCell>
                    <TableCell className="text-right font-mono">{fmtCost(r.median_cost)}</TableCell>
                    <TableCell className="hidden text-right font-mono text-muted-foreground md:table-cell">{fmtTokens(r.median_tokens)}</TableCell>
                    <TableCell className="text-right font-mono">{fmtCost(r.total_cost)}</TableCell>
                    <TableCell className={cn('text-right font-mono text-xs', coverage < 1 && 'text-amber-500')}>
                      {r.total_cells}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}

function solveColor(rate: number): string {
  // green (good) -> amber -> red (poor)
  if (rate >= 60) return '#3fb950'
  if (rate >= 30) return '#d29922'
  return '#f85149'
}
