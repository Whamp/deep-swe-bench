import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchRun, ApiError } from '@/lib/api'
import type { RunDetail as RunDetailData, Cell, DetailLevel } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { StateBadge, OutcomeBadge, Badge } from '@/components/ui/badge'
import { ErrorState } from '@/components/error-state'
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from '@/components/ui/table'
import { fmtSeconds, fmtTokens, fmtCost } from '@/lib/metrics'

const DETAIL_OPTIONS: DetailLevel[] = ['summary', 'operational', 'diagnostic']

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const [detail, setDetail] = useState<DetailLevel>('operational')

  const { data: run, isLoading, error } = useQuery({
    queryKey: ['run', runId, detail],
    queryFn: () => fetchRun(runId!, detail),
    enabled: !!runId,
    refetchInterval: 5000,
  })

  if (!runId) return <p className="text-muted-foreground">No run selected.</p>
  if (isLoading) return <p className="text-muted-foreground">Loading…</p>
  if (error) {
    const isNotFound = error instanceof ApiError && error.status === 404
    return (
      <ErrorState
        title={isNotFound ? 'Run not found' : 'Unable to load run'}
        message={isNotFound ? 'This run does not exist or has been removed.' : String(error)}
        runId={runId}
      />
    )
  }
  if (!run) return <ErrorState runId={runId} />

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">← Overview</Link>
        <h2 className="text-xl font-bold break-all">{run.run_id}</h2>
        <StateBadge state={run.state} />
        <div className="ml-auto flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Detail</span>
          <select
            value={detail}
            onChange={(e) => setDetail(e.target.value as DetailLevel)}
            className="rounded-md border border-border bg-card px-2 py-1 text-sm"
          >
            {DETAIL_OPTIONS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
      </div>

      <RunSummary run={run} />
      <CellTable title="Preflight / smoke" cells={Object.values(run.preflight || {})} showAge={false} />
      <CellTable title="Active cells" cells={run.active_cells || []} showAge={true} />
      <CellTable title="Recent finished" cells={run.recent_finished || []} showAge={false} />

      {detail === 'diagnostic' && <DiagnosticPanels run={run} />}
    </div>
  )
}

function RunSummary({ run }: { run: RunDetailData }) {
  const c = run.counts || {}
  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div className="text-sm text-muted-foreground">
          {run.model || run.kind} {run.thinking || ''} · configs: {(run.configs || []).join(', ') || '—'}
        </div>
        <div className="text-xs text-muted-foreground">
          updated {run.updated_at || 'unknown'} · heartbeat {fmtSeconds(run.heartbeat_age_s)}
        </div>
        <div>
          <Progress value={c.batch_done || 0} max={c.batch_total || 1} />
          <div className="mt-1 text-xs text-muted-foreground">
            {c.batch_done || 0}/{c.batch_total || 0} done
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
          <Metric label="Active" value={String(run.active_count || c.batch_running || 0)} />
          <Metric label="OK / empty" value={`${c.ok || 0} / ${c.empty || 0}`} />
          <Metric label="Skipped" value={String(c.batch_skipped || 0)} />
          <Metric label="Timeout / transient" value={`${c.timeout || 0} / ${c.transient || 0}`} />
          <Metric label="Failed" value={String(c.failed || 0)} />
          <Metric label="ETA" value={fmtSeconds(run.eta_s)} />
          <Metric
            label="Stale / oldest"
            value={run.stale_cell_count > 0
              ? `${run.stale_cell_count} / ${fmtSeconds(run.max_cell_age_s)}`
              : '0'}
          />
        </div>
        {run.paths && (
          <div className="flex flex-wrap gap-4 text-xs">
            <FileLink path={run.paths.manifest} label="manifest" />
            <FileLink path={run.paths.status} label="status" />
            <FileLink path={run.paths.events} label="events" />
          </div>
        )}
        {run.failure_buckets && Object.keys(run.failure_buckets).length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground">Failures:</span>
            {Object.entries(run.failure_buckets).map(([k, v]) => (
              <Badge key={k} variant="failed">{k}: {v}</Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-background/50 p-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  )
}

function FileLink({ path, label }: { path?: string; label: string }) {
  if (!path) return <span className="text-muted-foreground">{label}: —</span>
  return (
    <a
      href={`/api/file?path=${encodeURIComponent(path)}&tail=200`}
      target="_blank"
      rel="noreferrer"
      className="text-primary hover:underline"
    >
      {label}
    </a>
  )
}

function CellTable({ title, cells, showAge }: { title: string; cells: Cell[]; showAge: boolean }) {
  if (!cells || cells.length === 0) return null
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Task</TableHead>
              <TableHead>Config</TableHead>
              <TableHead>Rep</TableHead>
              <TableHead>State</TableHead>
              {showAge && <TableHead>Age</TableHead>}
              <TableHead>Outcome</TableHead>
              <TableHead>Metrics</TableHead>
              <TableHead>Files</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {cells.map((cell, i) => {
              const s = cell.summary || {}
              const bits: string[] = []
              if (s.reward_partial !== undefined) bits.push(`partial=${s.reward_partial}`)
              if (s.reward_binary !== undefined) bits.push(`binary=${s.reward_binary}`)
              if (s.total_tokens !== undefined) bits.push(`tok=${fmtTokens(s.total_tokens as number)}`)
              if (s.combined_total_tokens !== undefined) bits.push(`combined=${fmtTokens(s.combined_total_tokens as number)}`)
              if (s.cost_usd !== undefined) bits.push(`$=${fmtCost(s.cost_usd as number)}`)
              if (s.agent_wall_s !== undefined) bits.push(`wall=${fmtSeconds(s.agent_wall_s as number)}`)
              return (
                <TableRow key={`${cell.cell_id || 'cell'}-${i}`}>
                  <TableCell className="font-medium">{cell.task || '—'}</TableCell>
                  <TableCell>{cell.config || '—'}</TableCell>
                  <TableCell>{cell.rep ?? '—'}</TableCell>
                  <TableCell>{cell.state || '—'}</TableCell>
                  {showAge && (
                    <TableCell>
                      {cell.potentially_stale ? (
                        <Badge variant="stale">{fmtSeconds(cell.cell_age_s)}</Badge>
                      ) : cell.cell_age_s != null ? (
                        fmtSeconds(cell.cell_age_s)
                      ) : '—'}
                    </TableCell>
                  )}
                  <TableCell><OutcomeBadge outcome={cell.outcome} /></TableCell>
                  <TableCell className="text-xs text-muted-foreground">{bits.join(' · ')}</TableCell>
                  <TableCell className="text-xs">
                    {cell.result_path && (
                      <a href={`/api/file?path=${encodeURIComponent(cell.result_path)}&tail=50`} target="_blank" rel="noreferrer" className="text-primary hover:underline">result</a>
                    )}
                    {cell.result_path && cell.log_path && ' · '}
                    {cell.log_path && (
                      <a href={`/api/file?path=${encodeURIComponent(cell.log_path)}&tail=200`} target="_blank" rel="noreferrer" className="text-primary hover:underline">log</a>
                    )}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

function DiagnosticPanels({ run }: { run: RunDetailData }) {
  return (
    <>
      {run.events_tail && run.events_tail.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">Recent events</CardTitle></CardHeader>
          <CardContent>
            <pre className="max-h-96 overflow-auto rounded-md border border-border bg-background/80 p-3 text-xs">
              {run.events_tail.map((e) => JSON.stringify(e)).join('\n')}
            </pre>
          </CardContent>
        </Card>
      )}
      {run.status && (
        <Card>
          <CardHeader><CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">status.json</CardTitle></CardHeader>
          <CardContent>
            <pre className="max-h-96 overflow-auto rounded-md border border-border bg-background/80 p-3 text-xs">
              {JSON.stringify(run.status, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
      {run.manifest && (
        <Card>
          <CardHeader><CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">manifest.json</CardTitle></CardHeader>
          <CardContent>
            <pre className="max-h-96 overflow-auto rounded-md border border-border bg-background/80 p-3 text-xs">
              {JSON.stringify(run.manifest, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </>
  )
}
