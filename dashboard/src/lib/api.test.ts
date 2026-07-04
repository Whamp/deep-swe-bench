import { describe, it, expect } from 'vitest'
import { fetchRuns, fetchRun, fetchCompare, ApiError } from '@/lib/api'

describe('api client error handling', () => {
  it('ApiError has status and message', () => {
    const err = new ApiError(404, 'not found')
    expect(err.status).toBe(404)
    expect(err.message).toBe('not found')
    expect(err.name).toBe('ApiError')
  })

  it('fetchRuns throws ApiError on non-ok response', async () => {
    const original = global.fetch
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500, text: () => Promise.resolve('server error') })
    await expect(fetchRuns()).rejects.toThrow('server error')
    global.fetch = original
  })

  it('fetchRuns returns parsed JSON on success', async () => {
    const original = global.fetch
    const mockRuns = { runs: [{ run_id: 'test', state: 'completed', counts: {}, active_count: 0, stale_cell_count: 0 }] }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockRuns),
    })
    const result = await fetchRuns()
    expect(result).toHaveLength(1)
    expect(result[0].run_id).toBe('test')
    global.fetch = original
  })

  it('fetchRun includes runId in URL', async () => {
    const original = global.fetch
    let calledUrl = ''
    global.fetch = vi.fn().mockImplementation((url: string) => {
      calledUrl = url
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ run_id: 'abc', state: 'completed', counts: {}, active_count: 0, stale_cell_count: 0 }),
      })
    })
    await fetchRun('abc', 'summary')
    expect(calledUrl).toContain('/api/runs/abc')
    expect(calledUrl).toContain('detail=summary')
    global.fetch = original
  })

  it('fetchCompare returns parsed response', async () => {
    const original = global.fetch
    const mock = { runs: [] }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mock),
    })
    const result = await fetchCompare()
    expect(result.runs).toEqual([])
    global.fetch = original
  })
})

import { vi } from 'vitest'
