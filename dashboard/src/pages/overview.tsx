import { useQuery } from '@tanstack/react-query'
import { fetchRuns } from '@/lib/api'
import type { RunSummary, Counts } from '@/lib/types'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { StateBadge, Badge } from '@/components/ui/badge'
import { ErrorState } from '@/components/error-state'
import { fmtSeconds } from '@/lib/metrics'

export default function Overview() {
  const {
    data: runs,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['runs'],
    queryFn: () => fetchRuns('summary'),
    refetchInterval: 5000,
  })

  if (isLoading) return <p className="text-muted-foreground">Loading runs…</p>
  if (error) {
    return <ErrorState title="Unable to load runs" message={String(error)} />
  }
  if (!runs || runs.length === 0)
    return <p className="text-muted-foreground">No structured state or legacy track files found.</p>

  return (
    <>
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-lg font-bold">Runs</h1>
        <span className="text-sm text-muted-foreground">{runs.length} total</span>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {runs.map((run, idx) => (
          <RunCard key={run.run_key || `${run.run_id}-${idx}`} run={run} />
        ))}
      </div>
    </>
  )
}

function runHref(run: RunSummary): string {
  const key = run.run_key || run.run_id
  return `/run/${encodeURIComponent(key)}`
}

function RunCard({ run }: { run: RunSummary }) {
  const c: Counts = run.counts || {}
  const done = c.batch_done || 0
  const total = c.batch_total || 0
  const bad = (c.failed || 0) + (c.timeout || 0) + (c.transient || 0)
  const isDup = run.run_key && run.run_key !== run.run_id

  return (
    <Card className="transition-colors hover:border-primary">
      {/* Real anchor for accessibility: open-in-new-tab, copy-link, keyboard nav */}
      <CardContent className="space-y-3 p-4">
        <a
          href={runHref(run)}
          className="block space-y-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-md"
        >
          <div className="flex items-start justify-between gap-2">
            <span className="break-all text-sm font-semibold">{run.run_id}</span>
            <StateBadge state={run.state} />
          </div>
          {isDup && <div className="text-xs text-amber-400/80">↳ {run.run_key}</div>}
          <div className="text-xs text-muted-foreground">
            {run.model || run.kind} {run.thinking || ''}
          </div>
          <div className="flex flex-wrap gap-1">
            <Badge>{(run.configs || []).join(', ') || 'no config identity'}</Badge>
            <Badge>
              {run.launch_plan_identity
                ? `plan ${run.launch_plan_identity.slice(0, 19)}`
                : run.launch_metadata}
            </Badge>
            <Badge variant={run.preflight_state === 'failed' ? 'failed' : 'default'}>
              preflight {run.preflight_state}
            </Badge>
          </div>
          <div>
            <Progress value={done} max={total || 1} />
            <div className="mt-1 text-xs text-muted-foreground">
              {done}/{total} done
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            <span>active {run.active_count || c.batch_running || 0}</span>
            <span title="failed + timeout + transient">bad {bad}</span>
            <span title="heartbeat age">hb {fmtSeconds(run.heartbeat_age_s)}</span>
            {run.stale_cell_count > 0 && (
              <Badge variant="stale">{run.stale_cell_count} stale</Badge>
            )}
            {run.max_cell_age_s != null && (
              <span title="oldest active cell">oldest {fmtSeconds(run.max_cell_age_s)}</span>
            )}
          </div>
        </a>
      </CardContent>
    </Card>
  )
}
