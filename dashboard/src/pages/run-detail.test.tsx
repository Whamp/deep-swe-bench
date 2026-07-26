import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { RunDetail as RunDetailData } from '@/lib/types'
import RunDetail from '@/pages/run-detail'
import { mockDashboardJson, renderDashboardRoute } from '@/test/dashboard-test-harness'

function renderRunDetail(run: RunDetailData) {
  mockDashboardJson(run)
  return renderDashboardRoute(<RunDetail />, '/run/:runId', '/run/confirmed-run')
}

describe('Run detail confirmed-launch summary', () => {
  it('shows approval identity, workspace, progress, and preflight verdict', async () => {
    renderRunDetail({
      active_count: 0,
      configs: ['pi-check@1.0.1'],
      counts: {
        batch_done: 1,
        batch_skipped: 1,
        batch_total: 1,
        preflight_done: 1,
        preflight_failed: 0,
      },
      kind: 'structured',
      launch_metadata: 'confirmed_plan',
      launch_plan_identity: 'sha256:4489b49b',
      preflight_state: 'passed',
      run_id: 'confirmed-run',
      stage: 'done',
      stale_cell_count: 0,
      state: 'completed',
      workspace: '/repo/.worktrees/confirmed-launch',
    })

    expect(await screen.findByText('confirmed-run')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Run detail level' })).toBeInTheDocument()
    expect(screen.getByText('plan sha256:4489b49b')).toBeInTheDocument()
    expect(screen.getByText('preflight passed')).toBeInTheDocument()
    expect(screen.getByText('/repo/.worktrees/confirmed-launch')).toBeInTheDocument()
    expect(screen.getByText('1/1 done')).toBeInTheDocument()
  })
})
