import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Overview from '@/pages/overview'
import type { RunSummary } from '@/lib/types'

function mockFetch(data: { runs: RunSummary[] }) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
  })
}

function renderWithProviders(initialPath: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route index element={<Overview />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Overview page', () => {
  it('renders loading state initially', () => {
    mockFetch({ runs: [] })
    renderWithProviders('/')
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
    mockFetch({ runs })
    renderWithProviders('/')

    expect(await screen.findByText('test-run-1')).toBeInTheDocument()
    expect(screen.getByText(/test-model/i)).toBeInTheDocument()
    expect(screen.getByText('baseline@1.0.0')).toBeInTheDocument()
    expect(screen.getByText('plan sha256:1234567890ab')).toBeInTheDocument()
    expect(screen.getByText('preflight passed')).toBeInTheDocument()
    expect(screen.getByText(/10\/10 done/i)).toBeInTheDocument()
  })

  it('renders empty state when no runs', async () => {
    mockFetch({ runs: [] })
    // Override: we need to wait for the query to resolve with empty
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <Overview />
        </MemoryRouter>
      </QueryClientProvider>,
    )
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
    mockFetch({ runs })
    renderWithProviders('/')

    expect(await screen.findByText('2 stale')).toBeInTheDocument()
  })
})
