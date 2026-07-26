import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { RunSummary } from '@/lib/types'
import Overview from '@/pages/overview'
import { mockDashboardJson, renderDashboardRoute } from '@/test/dashboard-test-harness'

describe('Overview page', () => {
  it('renders loading state initially', () => {
    mockDashboardJson({ runs: [] })
    renderDashboardRoute(<Overview />, '/', '/')
    expect(screen.getByText(/Loading runs/i)).toBeInTheDocument()
  })

  it('renders run cards when data loads', async () => {
    const runs: RunSummary[] = [
      {
        run_id: 'test-run-1',
        state: 'completed',
        kind: 'structured',
        counts: { batch_done: 10, batch_total: 10, ok: 8 },
        active_count: 0,
        stale_cell_count: 0,
        model: 'test-model',
        thinking: 'low',
        configs: ['baseline@1.0.0'],
        launch_metadata: 'confirmed_plan',
        launch_plan_identity: 'sha256:1234567890abcdef',
        preflight_state: 'passed',
      },
    ]
    mockDashboardJson({ runs })
    renderDashboardRoute(<Overview />, '/', '/')

    expect(await screen.findByText('test-run-1')).toBeInTheDocument()
    expect(screen.getByText(/test-model/i)).toBeInTheDocument()
    expect(screen.getByText('baseline@1.0.0')).toBeInTheDocument()
    expect(screen.getByText('plan sha256:1234567890ab')).toBeInTheDocument()
    expect(screen.getByText('preflight passed')).toBeInTheDocument()
    expect(screen.getByText(/10\/10 done/i)).toBeInTheDocument()
  })

  it('renders empty state when no runs', async () => {
    mockDashboardJson({ runs: [] })
    renderDashboardRoute(<Overview />, '/', '/')
    expect(await screen.findByText(/No structured state/i)).toBeInTheDocument()
  })
})

describe('Overview stale cell badge', () => {
  it('shows stale badge when stale_cell_count > 0', async () => {
    const runs: RunSummary[] = [
      {
        run_id: 'stale-run',
        state: 'running',
        kind: 'structured',
        counts: { batch_done: 5, batch_total: 10 },
        active_count: 3,
        stale_cell_count: 2,
        max_cell_age_s: 2400,
        launch_metadata: 'legacy_structured',
        preflight_state: 'running',
      },
    ]
    mockDashboardJson({ runs })
    renderDashboardRoute(<Overview />, '/', '/')

    expect(await screen.findByText('2 stale')).toBeInTheDocument()
  })
})
