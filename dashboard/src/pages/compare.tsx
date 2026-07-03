import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  BarChart, Bar, Cell as RechartsCell, Legend,
} from 'recharts'
import { fetchCompare } from '@/lib/api'
import type { ComparisonRun } from '@/lib/types'
import { paretoFrontier, fmtCost, fmtTokens, solveRate } from '@/lib/metrics'
import { useIsMobile } from '@/lib/use-mobile'
import { MeasuredContainer } from '@/components/measured-container'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ErrorState } from '@/components/error-state'
import { cn } from '@/lib/utils'

const COLORS = ['#58a6ff', '#3fb950', '#f85149', '#d29922', '#bc8cff', '#ff7b72', '#79c0ff', '#7ee787']
const DEFAULT_COUNT = 8

export default function Compare() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['compare'],
    queryFn: fetchCompare,
    refetchInterval: 30000,
  })

  const [selected, setSelected] = useState<Set<string> | null>(null)

  const runs = useMemo(() => data?.runs || [], [data])

  useEffect(() => {
    if (selected === null && runs.length > 0) {
      setSelected(new Set(runs.slice(0, DEFAULT_COUNT).map((r) => r.run_id)))
    }
  }, [runs, selected])

  const visibleRuns = useMemo(() => {
    if (!selected || selected.size === 0) return []
    return runs.filter((r) => selected.has(r.run_id))
  }, [runs, selected])

  if (isLoading) return <p className="text-muted-foreground">Loading comparison data…</p>
  if (error) return <ErrorState title="Unable to load comparison data" message={String(error)} />
  if (runs.length === 0) return <p className="text-muted-foreground">No completed runs to compare.</p>

  const toggle = (id: string) => {
    setSelected((prev) => {
      const base = prev ?? new Set<string>()
      const next = new Set(base)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = () => setSelected(new Set(runs.map((r) => r.run_id)))
  const clearAll = () => setSelected(new Set())
  const reset = () => setSelected(new Set(runs.slice(0, DEFAULT_COUNT).map((r) => r.run_id)))

  return (
    <div className="space-y-4">
      <RunSelector
        runs={runs}
        selected={selected ?? new Set()}
        onToggle={toggle}
        onSelectAll={selectAll}
        onClear={clearAll}
        onReset={reset}
      />
      {visibleRuns.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-sm text-muted-foreground">
            No runs selected. Use the buttons above or “Reset” to restore the default selection.
          </CardContent>
        </Card>
      ) : (
        <>
          <ParetoChart runs={visibleRuns} />
          <SolveRateChart runs={visibleRuns} />
          <CostQualityChart runs={visibleRuns} />
          <DifficultyChart runs={visibleRuns} />
          <TokenDistChart runs={visibleRuns} />
        </>
      )}
    </div>
  )
}

function RunSelector({
  runs, selected, onToggle, onSelectAll, onClear, onReset,
}: {
  runs: ComparisonRun[]
  selected: Set<string>
  onToggle: (id: string) => void
  onSelectAll: () => void
  onClear: () => void
  onReset: () => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Select runs to compare ({selected.size} selected)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          <button onClick={onSelectAll} className="rounded-md border border-border px-3 py-1 text-xs hover:bg-accent">
            Select all
          </button>
          <button onClick={onClear} className="rounded-md border border-border px-3 py-1 text-xs hover:bg-accent">
            Clear
          </button>
          <button onClick={onReset} className="rounded-md border border-border px-3 py-1 text-xs hover:bg-accent">
            Reset to first {DEFAULT_COUNT}
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {runs.map((run, i) => {
            const isSelected = selected.has(run.run_id)
            return (
              <button
                key={run.run_id}
                onClick={() => onToggle(run.run_id)}
                aria-pressed={isSelected}
                className={cn(
                  'rounded-md border px-3 py-1 text-xs transition-colors',
                  isSelected ? 'bg-accent' : 'opacity-50 hover:opacity-80',
                )}
                style={isSelected ? { borderColor: COLORS[i % COLORS.length] } : undefined}
                title={`${run.config} · ${run.solve_rate.toFixed(1)}%`}
              >
                <span className="inline-block h-2 w-2 rounded-full mr-1.5 align-middle" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                {run.run_id.length > 28 ? `${run.run_id.slice(0, 12)}…${run.run_id.slice(-12)}` : run.run_id}
              </button>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

function ParetoChart({ runs }: { runs: ComparisonRun[] }) {
  const points = runs.map((r) => ({
    id: r.run_id,
    cost: r.median_cost,
    value: r.solve_rate,
    r,
  }))
  const annotated = paretoFrontier(points)
  const chartData = annotated.map((p, i) => ({
    name: p.r.run_id,
    cost: p.cost,
    solveRate: p.value,
    isPareto: p.isPareto,
    color: COLORS[i % COLORS.length],
    config: p.r.config,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Pareto frontier — solve rate vs median cost (upper-left = better)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <MeasuredContainer height={350}>
          {(w, h) => (
            <ScatterChart width={w} height={h} margin={{ top: 16, right: 32, bottom: 48, left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215 14% 22%)" />
              <XAxis
                type="number"
                dataKey="cost"
                name="Median Cost"
                tickFormatter={(v) => fmtCost(v)}
                stroke="hsl(215 16% 60%)"
                label={{ value: 'Median Cost ($)', position: 'bottom', offset: 16, fill: 'hsl(215 16% 60%)', fontSize: 12 }}
              />
              <YAxis
                type="number"
                dataKey="solveRate"
                name="Solve Rate"
                unit="%"
                domain={[0, 100]}
                stroke="hsl(215 16% 60%)"
                label={{ value: 'Solve Rate (%)', angle: -90, position: 'insideLeft', fill: 'hsl(215 16% 60%)', fontSize: 12 }}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ background: 'hsl(215 14% 11%)', border: '1px solid hsl(215 14% 22%)', borderRadius: 8 }}
                formatter={(value: number, name: string) => name === 'Solve Rate' ? `${value.toFixed(1)}%` : fmtCost(value)}
                labelFormatter={(_, payload) => {
                  if (!payload || !payload[0]) return ''
                  return payload[0].payload.name
                }}
              />
              <Scatter data={chartData} isAnimationActive={false}>
                {chartData.map((entry, i) => (
                  <RechartsCell
                    key={i}
                    fill={entry.color}
                    fillOpacity={entry.isPareto ? 1 : 0.4}
                    stroke={entry.isPareto ? '#fff' : 'none'}
                    strokeWidth={entry.isPareto ? 3 : 0}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          )}
        </MeasuredContainer>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {chartData.filter((d) => d.isPareto).map((d) => (
            <Badge key={d.name} className="text-xs">★ {d.name}</Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function SolveRateChart({ runs }: { runs: ComparisonRun[] }) {
  const isMobile = useIsMobile()
  const data = runs.map((r, i) => ({
    name: r.run_id.length > 20 ? r.run_id.slice(0, 18) + '…' : r.run_id,
    fullName: r.run_id,
    config: r.config,
    solveRate: r.solve_rate,
    solved: r.solved,
    total: r.total_cells,
    color: COLORS[i % COLORS.length],
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">Solve rate by run</CardTitle>
      </CardHeader>
      <CardContent>
        <MeasuredContainer height={300}>
          {(w, h) => (
            <BarChart width={w} height={h} data={data} margin={{ top: 8, right: 16, bottom: isMobile ? 80 : 48, left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215 14% 22%)" />
              <XAxis dataKey="name" stroke="hsl(215 16% 60%)" angle={isMobile ? -60 : -35} textAnchor="end" height={isMobile ? 80 : 60} interval={isMobile ? Math.max(0, Math.floor(data.length / 6) - 1) : 0} tick={{ fontSize: isMobile ? 9 : 12 }} />
              <YAxis stroke="hsl(215 16% 60%)" unit="%" domain={[0, 100]} />
              <Tooltip
                cursor={{ fill: 'hsl(215 14% 18%)' }}
                contentStyle={{ background: 'hsl(215 14% 11%)', border: '1px solid hsl(215 14% 22%)', borderRadius: 8 }}
                formatter={(value: number) => [`${value.toFixed(1)}%`, 'Solve Rate']}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName || ''}
              />
              <Bar dataKey="solveRate" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                {data.map((entry, i) => (
                  <RechartsCell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          )}
        </MeasuredContainer>
      </CardContent>
    </Card>
  )
}

function CostQualityChart({ runs }: { runs: ComparisonRun[] }) {
  const data = runs.map((r, i) => ({
    name: r.run_id,
    cost: r.median_cost,
    quality: r.mean_partial * 100,
    color: COLORS[i % COLORS.length],
    config: r.config,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Mean partial reward vs median cost
        </CardTitle>
      </CardHeader>
      <CardContent>
        <MeasuredContainer height={300}>
          {(w, h) => (
            <ScatterChart width={w} height={h} margin={{ top: 16, right: 32, bottom: 48, left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215 14% 22%)" />
              <XAxis
                type="number" dataKey="cost" name="Median Cost"
                tickFormatter={(v) => fmtCost(v)}
                stroke="hsl(215 16% 60%)"
                label={{ value: 'Median Cost ($)', position: 'bottom', offset: 16, fill: 'hsl(215 16% 60%)', fontSize: 12 }}
              />
              <YAxis
                type="number" dataKey="quality" name="Mean Partial"
                domain={[0, 100]} unit="%"
                stroke="hsl(215 16% 60%)"
                label={{ value: 'Mean Partial (%)', angle: -90, position: 'insideLeft', fill: 'hsl(215 16% 60%)', fontSize: 12 }}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ background: 'hsl(215 14% 11%)', border: '1px solid hsl(215 14% 22%)', borderRadius: 8 }}
                formatter={(value: number, name: string) => name === 'Mean Partial' ? `${value.toFixed(1)}%` : fmtCost(value)}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.name || ''}
              />
              <Scatter data={data} isAnimationActive={false}>
                {data.map((entry, i) => (
                  <RechartsCell key={i} fill={entry.color} />
                ))}
              </Scatter>
            </ScatterChart>
          )}
        </MeasuredContainer>
      </CardContent>
    </Card>
  )
}

function DifficultyChart({ runs }: { runs: ComparisonRun[] }) {
  const isMobile = useIsMobile()
  const data = useMemo(() => {
    return runs.map((r, i) => {
      const byDiff: Record<string, number[]> = { hard: [], medium: [], easy: [] }
      for (const cell of r.cells) {
        const diff = cell.difficulty
        if (diff && diff in byDiff) byDiff[diff].push(cell.reward_binary)
      }
      return {
        name: r.run_id.length > 20 ? r.run_id.slice(0, 18) + '…' : r.run_id,
        color: COLORS[i % COLORS.length],
        hard: solveRate(byDiff.hard) * 100,
        medium: solveRate(byDiff.medium) * 100,
        easy: solveRate(byDiff.easy) * 100,
      }
    })
  }, [runs])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Difficulty stratification — solve rate by difficulty bucket
        </CardTitle>
      </CardHeader>
      <CardContent>
        <MeasuredContainer height={300}>
          {(w, h) => (
            <BarChart width={w} height={h} data={data} margin={{ top: 8, right: 16, bottom: isMobile ? 80 : 48, left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215 14% 22%)" />
              <XAxis dataKey="name" stroke="hsl(215 16% 60%)" angle={isMobile ? -60 : -35} textAnchor="end" height={isMobile ? 80 : 60} interval={isMobile ? Math.max(0, Math.floor(data.length / 6) - 1) : 0} tick={{ fontSize: isMobile ? 9 : 12 }} />
              <YAxis stroke="hsl(215 16% 60%)" unit="%" domain={[0, 100]} />
              <Tooltip
                cursor={{ fill: 'hsl(215 14% 18%)' }}
                contentStyle={{ background: 'hsl(215 14% 11%)', border: '1px solid hsl(215 14% 22%)', borderRadius: 8 }}
                formatter={(value: number) => `${value.toFixed(1)}%`}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {/* Grouped bars (not stacked) — each is an independent 0-100% solve rate */}
              <Bar dataKey="hard" fill="#f85149" radius={[3, 3, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="medium" fill="#d29922" radius={[3, 3, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="easy" fill="#3fb950" radius={[3, 3, 0, 0]} isAnimationActive={false} />
            </BarChart>
          )}
        </MeasuredContainer>
      </CardContent>
    </Card>
  )
}

function TokenDistChart({ runs }: { runs: ComparisonRun[] }) {
  const isMobile = useIsMobile()
  const data = runs.map((r, i) => ({
    name: r.run_id.length > 20 ? r.run_id.slice(0, 18) + '…' : r.run_id,
    fullName: r.run_id,
    medianTokens: r.median_tokens,
    meanPartial: r.mean_partial,
    color: COLORS[i % COLORS.length],
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
          Median tokens per task
        </CardTitle>
      </CardHeader>
      <CardContent>
        <MeasuredContainer height={300}>
          {(w, h) => (
            <BarChart width={w} height={h} data={data} margin={{ top: 8, right: 16, bottom: isMobile ? 80 : 48, left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215 14% 22%)" />
              <XAxis dataKey="name" stroke="hsl(215 16% 60%)" angle={isMobile ? -60 : -35} textAnchor="end" height={isMobile ? 80 : 60} interval={isMobile ? Math.max(0, Math.floor(data.length / 6) - 1) : 0} tick={{ fontSize: isMobile ? 9 : 12 }} />
              <YAxis stroke="hsl(215 16% 60%)" tickFormatter={(v) => fmtTokens(v)} />
              <Tooltip
                cursor={{ fill: 'hsl(215 14% 18%)' }}
                contentStyle={{ background: 'hsl(215 14% 11%)', border: '1px solid hsl(215 14% 22%)', borderRadius: 8 }}
                formatter={(value: number) => fmtTokens(value)}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName || ''}
              />
              <Bar dataKey="medianTokens" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                {data.map((entry, i) => (
                  <RechartsCell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          )}
        </MeasuredContainer>
      </CardContent>
    </Card>
  )
}
