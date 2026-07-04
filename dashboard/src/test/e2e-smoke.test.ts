/**
 * E2E smoke test: starts the Python dashboard API in a subprocess and verifies
 * all endpoints respond correctly. This catches regressions in the API contract
 * that unit tests (which mock fetch) would miss.
 *
 * The Vite dev server is NOT required for this test — we hit the Python API
 * directly. The frontend-to-API integration is covered by the component tests
 * which mock the same endpoints.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { spawn, type ChildProcess } from 'child_process'
import { resolve } from 'path'

const REPO_ROOT = resolve(__dirname, '..', '..', '..')
const PORT = 18789 // non-default to avoid conflicts
const API = `http://127.0.0.1:${PORT}`

let serverProc: ChildProcess | null = null

function waitForServer(url: string, timeoutMs = 10000): Promise<void> {
  const start = Date.now()
  return new Promise((resolve, reject) => {
    function check() {
      fetch(url)
        .then(() => resolve())
        .catch(() => {
          if (Date.now() - start > timeoutMs) reject(new Error('server did not start'))
          else setTimeout(check, 200)
        })
    }
    check()
  })
}

async function getJSON(path: string): Promise<any> {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) throw new Error(`${path} returned ${res.status}`)
  return res.json()
}

describe('dashboard API e2e smoke', () => {
  beforeAll(async () => {
    serverProc = spawn('python3', [
      'scripts/run_dashboard.py',
      '--host', '127.0.0.1',
      '--port', String(PORT),
    ], {
      cwd: REPO_ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
    })

    // Capture stderr for debugging
    serverProc.stderr?.on('data', (data) => {
      const msg = data.toString()
      if (msg.includes('Traceback') || msg.includes('Error')) {
        console.error('API server error:', msg)
      }
    })

    await waitForServer(`${API}/api/runs?detail=summary`)
  }, 15000)

  afterAll(() => {
    if (serverProc) {
      serverProc.kill('SIGTERM')
      serverProc = null
    }
  })

  it('GET /api/runs returns a list of runs', async () => {
    const data = await getJSON('/api/runs?detail=summary')
    expect(data).toHaveProperty('runs')
    expect(Array.isArray(data.runs)).toBe(true)
    if (data.runs.length > 0) {
      const run = data.runs[0]
      expect(run).toHaveProperty('run_id')
      expect(run).toHaveProperty('state')
      expect(run).toHaveProperty('counts')
      expect(run).toHaveProperty('active_count')
      expect(run).toHaveProperty('stale_cell_count')
    }
  })

  it('GET /api/runs/<id> returns detailed run', async () => {
    const list = await getJSON('/api/runs?detail=summary')
    if (list.runs.length === 0) return
    const runId = list.runs[0].run_id
    const run = await getJSON(`/api/runs/${encodeURIComponent(runId)}?detail=operational`)
    expect(run.run_id).toBe(runId)
    expect(run).toHaveProperty('counts')
    expect(run).toHaveProperty('paths')
  })

  it('GET /api/compare returns aggregated benchmark data', async () => {
    const data = await getJSON('/api/compare')
    expect(data).toHaveProperty('runs')
    expect(Array.isArray(data.runs)).toBe(true)
    if (data.runs.length > 0) {
      const run = data.runs[0]
      expect(run).toHaveProperty('run_id')
      expect(run).toHaveProperty('solve_rate')
      expect(run).toHaveProperty('mean_partial')
      expect(run).toHaveProperty('median_cost')
      expect(run).toHaveProperty('cells')
      expect(Array.isArray(run.cells)).toBe(true)
    }
  })

  it('GET /api/file returns file content', async () => {
    const res = await fetch(`${API}/api/file?path=README.md&tail=5`)
    expect(res.ok).toBe(true)
    const text = await res.text()
    expect(text.length).toBeGreaterThan(0)
  })

  it('GET /api/runs/<unknown-id> returns 404', async () => {
    const res = await fetch(`${API}/api/runs/nonexistent-run-id-12345`)
    expect(res.status).toBe(404)
  })

  it('GET / unknown path returns 404 (API-only, no HTML)', async () => {
    const res = await fetch(`${API}/`)
    expect(res.status).toBe(404)
    const body = await res.json()
    expect(body).toHaveProperty('error')
  })
})
