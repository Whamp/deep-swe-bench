import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Compare from '@/pages/compare'
import type { CompareResponse, ComparisonRun } from '@/lib/types'

function mockFetchCompare(response: CompareResponse | Error) {
  if (response instanceof Error) {
    global.fetch = vi.fn().mockRejectedValue(response)
  } else {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(response),
    })
  }
}

function renderCompare() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Compare />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function makeRun(overrides: Partial<ComparisonRun> = {}): ComparisonRun {
  return {
    run_id: 'test-run',
    model: 'test-model',
    thinking: 'low',
    config: 'baseline',
    state: 'completed',
    total_cells: 10,
    solved: 5,
    solve_rate: 50,
    mean_partial: 0.85,
    median_cost: 1.5,
    median_tokens: 1_000_000,
    median_wall_s: 300,
    total_cost: 15.0,
    cells: [
      { task: 'task-a', config: 'baseline', rep: 0, reward_binary: 1, reward_partial: 1.0, total_tokens: 500_000, cost_usd: 1.0, agent_wall_s: 200, patch_bytes: 5000, difficulty: 'easy' },
      { task: 'task-b', config: 'baseline', rep: 0, reward_binary: 0, reward_partial: 0.5, total_tokens: 1_500_000, cost_usd: 2.0, agent_wall_s: 400, patch_bytes: 3000, difficulty: 'hard' },
    ],
    ...overrides,
  }
}

describe('Compare page', () => {
  it('renders loading state initially', () => {
    mockFetchCompare({ runs: [] })
    renderCompare()
    expect(document.body.textContent).toContain('Loading comparison')
  })

  it('renders empty state when no runs', async () => {
    mockFetchCompare({ runs: [] })
    const { container } = renderCompare()
    // Wait for query to settle
    await new Promise((r) => setTimeout(r, 100))
    expect(container.textContent || '').toContain('No completed runs')
  })

  it('renders charts when data loads', async () => {
    mockFetchCompare({ runs: [makeRun({ run_id: 'test-run-a' }), makeRun({ run_id: 'test-run-b', solve_rate: 70 })] })
    const { container } = renderCompare()
    await new Promise((r) => setTimeout(r, 200))
    // Should have chart containers (recharts renders lazily in jsdom, so check for titles)
    expect(container.textContent || '').toContain('Pareto')
    expect(container.textContent || '').toContain('Select runs')
  })

  it('renders error state on fetch failure', async () => {
    mockFetchCompare(new Error('network error'))
    const { container } = renderCompare()
    await new Promise((r) => setTimeout(r, 100))
    expect(container.textContent || '').toContain('Error')
  })

  it('handles runs with empty cells gracefully', async () => {
    mockFetchCompare({ runs: [makeRun({ cells: [], solved: 0, solve_rate: 0 })] })
    const { container } = renderCompare()
    await new Promise((r) => setTimeout(r, 200))
    // Should not crash, should show the run name
    expect(container.textContent || '').toContain('Pareto')
  })
})
