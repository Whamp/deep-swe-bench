# deep-swe-bench dashboard

Internal-only dev dashboard for monitoring benchmark runs and comparing results across configs. Built with React + Vite + TypeScript + shadcn/ui + Recharts.

## Architecture

Two services work together:

1. **Python API** (`scripts/run_dashboard.py`, port `:8789`) — serves JSON from `results/_runs/` and `results/`. Runs as `deep-swe-bench-dashboard.service`.
2. **Vite dev server** (`dashboard/`, port `:5173`) — the React SPA. Proxies `/api/*` to the Python API. Runs as `deep-swe-bench-vite.service`.

There is no production build step. `vite dev` is the only mode — this is an internal tool.

## Quick start

```bash
# Terminal 1: Python API
python3 scripts/run_dashboard.py --host 0.0.0.0 --port 8789

# Terminal 2: Vite dev server
cd dashboard && npm install && npm run dev
```

Open `http://localhost:5173` (or `http://<tailscale-ip>:5173`).

## systemd services

Both services are systemd user units with `Restart=always`:

```bash
# Python API (already set up)
~/.config/systemd/user/deep-swe-bench-dashboard.service  # :8789

# Vite dev server
~/.config/systemd/user/deep-swe-bench-vite.service        # :5173
```

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user enable deep-swe-bench-vite.service
systemctl --user start deep-swe-bench-vite.service
```

## Pages

### Overview (`/`)
Grid of run cards. Each card shows run_id, state, model/thinking, progress (done/total), active count, bad count, heartbeat age, stale-cell count, and oldest cell age. Click a card to see run detail.

### Run detail (`/run/:runId`)
Single run view with metrics row, progress bar, preflight/smoke table, active cells table (with cell age and stale flag), recent finished cells, and file links. Three detail levels (summary, operational, diagnostic).

### Compare (`/compare`)
Interactive charts reading real benchmark data from all `results/` directories:
- **Pareto frontier** — solve rate vs median cost (upper-left = better)
- **Solve rate by run** — bar chart
- **Mean partial vs median cost** — scatter
- **Difficulty stratification** — solve rate by hard/medium/easy bucket
- **Median tokens per task** — bar chart

Click run names in the selector to toggle which runs are visible. Note: `/api/compare`
aggregates **every** cell in a config group, so if a config ran on multiple subsets its
numbers mix subsets — use the Leaderboard page for clean per-subset comparisons.

### Leaderboard (`/leaderboard`)
Ranks every config on a single fixed dataset (subset) for an apples-to-apples comparison:
- **Dataset selector** — pick any subset (`36_v2`, `12_v2`, `113_v0`, …); cells are filtered to
  that task set so cross-subset contamination is eliminated.
- **Reps cap** — optionally keep only the first N reps per task for fairness.
- **Hide partial-coverage runs** — on by default; a run only qualifies if it has data for every
  task in the subset (distinct task count, not raw cell count, so 3-reps-on-12-of-36 is excluded).
- **Pareto scatter** — solve rate vs median cost, with frontier points starred.
- **Sortable ranked table** — solve %, mean partial, median/total cost, median tokens, n. Click
  any column header to sort.

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /api/runs?detail=summary\|operational\|diagnostic` | List all discovered runs |
| `GET /api/runs/<id>?detail=...` | Detailed projection of a single run |
| `GET /api/runs/<id>/events?limit=N` | Events tail |
| `GET /api/compare?subset=&reps=N` | Aggregated cross-run metrics, optionally filtered to a subset |
| `GET /api/subsets` | List available task subsets |
| `GET /api/file?path=&tail=N` | Tail a file (repo-allowlisted) |

## Development

```bash
# Type checking
npm run typecheck

# Linting
npm run lint

# Tests (unit + property-based + component)
npm test

# Tests with watch mode
npm run test:watch
```

### Adding a chart

1. Add data fetching in `src/lib/api.ts` if needed.
2. Add pure computation helpers in `src/lib/metrics.ts` (with property-based tests in `metrics.test.ts`).
3. Add the chart component in `src/pages/compare.tsx` using Recharts.
4. The `/api/compare` endpoint in `scripts/run_dashboard.py` aggregates results — extend it if new metrics are needed.

## Project structure

```
dashboard/
  src/
    components/ui/     shadcn-style primitives (card, badge, table, progress)
    lib/
      api.ts           typed fetch client
      types.ts         API response types
      metrics.ts       pure utilities (pareto, median, formatting)
      utils.ts         cn() classname merge
    pages/
      overview.tsx     run cards grid
      leaderboard.tsx  per-subset ranked leaderboard + Pareto scatter
      run-detail.tsx   single run detail
      compare.tsx      cross-run comparison charts
    test/setup.ts      vitest + testing-library setup
  screenshots/         verification screenshots
```
