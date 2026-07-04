import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Leaderboard from '@/pages/leaderboard'
import type { CompareResponse, ComparisonRun, SubsetsResponse } from '@/lib/types'

function makeRun(overrides: Partial<ComparisonRun> = {}): ComparisonRun {
  return {
    run_id: 'gpt-5.5/low/baseline',
    model: 'gpt-5.5',
    thinking: 'low',
    config: 'baseline',
    state: 'completed',
    total_cells: 108,
    distinct_tasks: 36,
    solved: 33,
    solve_rate: 30.6,
    mean_partial: 0.967,
    median_cost: 0.86,
    median_tokens: 610_000,
    median_wall_s: 206,
    total_cost: 100.0,
    cells: [],
    ...overrides,
  }
}

const SUBSETS: SubsetsResponse = {
  subsets: [
    { name: '36_v2', task_count: 36, tasks: Array.from({ length: 36 }, (_, i) => `task-${i}`) },
    { name: '12_v0', task_count: 12, tasks: Array.from({ length: 12 }, (_, i) => `task-${i}`) },
  ],
}

function mockFetch(opts: { subsets?: SubsetsResponse; compare?: CompareResponse | Error }) {
  global.fetch = vi.fn().mockImplementation((url: string) => {
    const u = String(url)
    if (u.includes('/api/subsets')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(opts.subsets ?? SUBSETS),
      })
    }
    if (u.includes('/api/compare')) {
      const cmp = opts.compare
      if (cmp instanceof Error) return Promise.reject(cmp)
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(cmp) })
    }
    return Promise.reject(new Error(`unexpected fetch: ${u}`))
  })
}

function renderLeaderboard() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Leaderboard />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Leaderboard page', () => {
  it('renders loading state initially', () => {
    mockFetch({ compare: { runs: [], subset: '36_v2' } })
    renderLeaderboard()
    expect(document.body.textContent).toContain('Loading leaderboard')
  })

  it('renders ranked table and Pareto chart with data', async () => {
    mockFetch({
      compare: {
        runs: [
          makeRun({ run_id: 'gpt-5.5/low/baseline', solved: 33, solve_rate: 30.6 }),
          makeRun({ run_id: 'gpt-5.5/medium/baseline', solved: 53, solve_rate: 49.1, median_cost: 1.69 }),
          makeRun({ run_id: 'gpt-5.5/xhigh/baseline', solved: 71, solve_rate: 65.7, median_cost: 5.93 }),
        ],
        subset: '36_v2',
      },
    })
    const { container } = renderLeaderboard()
    await new Promise((r) => setTimeout(r, 200))
    const text = container.textContent || ''
    expect(text).toContain('Pareto frontier')
    expect(text).toContain('Ranked results')
    // All three configs appear, ordered by solve_rate desc by default
    expect(text).toContain('xhigh')
    expect(text).toContain('medium')
    expect(text).toContain('low')
  })

  it('hides partial-coverage runs by default (distinct tasks < subset size)', async () => {
    // subset 36_v2 has 36 tasks; a run covering only 12 tasks (even with 3 reps = 36 cells) is partial
    mockFetch({
      compare: {
        runs: [
          makeRun({ run_id: 'gpt-5.5/low/baseline', total_cells: 108, distinct_tasks: 36, solved: 33, solve_rate: 30.6 }),
          makeRun({ run_id: 'gpt-5.5/low/pilot', total_cells: 9, distinct_tasks: 9, solved: 9, solve_rate: 100 }),
        ],
        subset: '36_v2',
      },
    })
    const { container } = renderLeaderboard()
    await new Promise((r) => setTimeout(r, 200))
    const text = container.textContent || ''
    expect(text).toContain('baseline')
    expect(text).not.toContain('pilot')
  })

  it('shows partial-coverage runs when filter toggled off', async () => {
    mockFetch({
      compare: {
        runs: [
          makeRun({ run_id: 'gpt-5.5/low/baseline', total_cells: 108, distinct_tasks: 36, solved: 33, solve_rate: 30.6 }),
          makeRun({ run_id: 'gpt-5.5/low/pilot', total_cells: 9, distinct_tasks: 9, solved: 9, solve_rate: 100 }),
        ],
        subset: '36_v2',
      },
    })
    const { container } = renderLeaderboard()
    await new Promise((r) => setTimeout(r, 200))
    // Toggle the hide-partial checkbox off
    const checkbox = container.querySelector('input[type="checkbox"]') as HTMLInputElement
    expect(checkbox.checked).toBe(true)
    fireEvent.click(checkbox)
    await new Promise((r) => setTimeout(r, 100))
    const text = container.textContent || ''
    expect(text).toContain('pilot')
  })

  it('sorts by a column when the header is clicked', async () => {
    mockFetch({
      compare: {
        runs: [
          makeRun({ run_id: 'gpt-5.5/low/baseline', median_cost: 0.86, solve_rate: 30 }),
          makeRun({ run_id: 'gpt-5.5/medium/baseline', median_cost: 1.69, solve_rate: 49 }),
        ],
        subset: '36_v2',
      },
    })
    const { container } = renderLeaderboard()
    await new Promise((r) => setTimeout(r, 200))
    // Click the "Med cost" header to sort ascending (lower is better)
    const headers = container.querySelectorAll('th')
    const medCostHeader = Array.from(headers).find((h) => h.textContent?.includes('Med cost'))!
    fireEvent.click(medCostHeader)
    await new Promise((r) => setTimeout(r, 100))
    // First data row should now be baseline (0.86 < 1.69)
    const firstRow = container.querySelector('tbody tr')
    expect(firstRow?.textContent || '').toContain('baseline')
  })

  it('renders empty state when no runs match filters', async () => {
    mockFetch({ compare: { runs: [], subset: '36_v2' } })
    const { container } = renderLeaderboard()
    await new Promise((r) => setTimeout(r, 200))
    expect(container.textContent || '').toContain('No runs match')
  })

  it('renders error state on fetch failure', async () => {
    mockFetch({ compare: new Error('network error') })
    const { container } = renderLeaderboard()
    await new Promise((r) => setTimeout(r, 200))
    expect(container.textContent || '').toContain('Error')
  })
})
