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
An operational monitor, not an archive wall:

- **Ongoing** is the default. Truly running sessions get rich health cards with
  phase, progress, active workers, task-level solve rate, and heartbeat age.
  Preflight is labeled explicitly instead of showing a misleading `0 active`.
- **Needs attention** shows only recent stalled/failed runs as compact rows;
  older incidents stay hidden unless requested. A stale declared `running`
  state is reclassified to **stalled** after 3× its configured heartbeat cadence
  (with a 15-minute floor), so abandoned processes never look live.
- **History** keeps completed, paused, old failed/stalled, and legacy runs in a
  dense row list rather than full cards.
- Search filters by run id/key, model, thinking level, or config. When no run is
  active, the page says so plainly and offers direct links to attention/history.

### Run detail (`/run/:runId`)
The live-monitoring centerpiece. Three things at a glance:

- **Live score hero** — one big solve-rate number (green/amber/red by band), a
  running *Δ vs a baseline* (auto-paired on the same model+thinking from
  `results/`, with a flip count: new solves / regressions), cumulative +
  projected cost, cost-per-solve, throughput (cells/hr), throughput-based ETA,
  and a failure-mode breakdown. Four fixed-size plots track solved-vs-finished,
  cost, cumulative mean partial reward, and cumulative tool-call error rate.
  Mean partial uses the same 0–1 aggregate as the headline. Native tool errors
  are `toolResult.isError`; Fabric uses failed/aborted/timed-out inner trace
  operations, falling back to the outer result when trace telemetry is absent.
  Reused cells are excluded from the operational error-rate denominator.
  Updates every 5s from the event log plus mtime-cached compact session summaries.
- **What the agents are doing** — the *Active cells* table is sorted
  anomaly-first (stale, then oldest). Click **view session** on any cell to
  open a drill-in that parses the agent's session transcript (server-side) into
  a **turn timeline**: each turn shows the agent's self-narrated intent (from
  its `thinking` block), the tools/files it touched, and its token/cost delta.
  Works for both native-pi (`read`/`edit`/`bash`) and pi-fabric (`fabric_exec`
  wrapping JS) sessions — fabric's inner tool calls are unwrapped with a
  tolerant regex. A `LIVE` dot confirms the transcript is still being written.
- **Recent results** — failures first as rows; a quiet `N ok` summary when
  nothing needs attention. Three detail levels (summary, operational,
  diagnostic) toggle the raw `status.json` / `manifest.json` / events tail.

### Compare (`/compare`)
A scoped two-config workspace for answering whether one config beats another on
matched evidence:

- **Scope first:** subset, rep cap, and model+thinking must match. The default is
  `36_v2`, first rep per task, full coverage only.
- **Reference versus challenger:** the default pair is the canonical `baseline`
  and strongest full-coverage challenger in the largest comparable group. Both
  sides remain changeable; partial evidence requires an explicit opt-in.
- **Paired task result:** tasks are intersected before comparison. The verdict
  reports B-only gains, A-only losses, net flips, both solved, neither solved,
  shared-task partial reward, and the discordant sample size. These are
  descriptive measurements, not significance claims.
- **Per-task evidence:** the partial-reward scatter defaults to the observed
  variation range and retains a full 0–100% toggle. Every discordant task and
  every shared task remain inspectable.
- **Honest secondary metrics:** task success and rep success keep separate
  denominators. `$0` cost is shown as untracked rather than free. Empty
  difficulty buckets show `—`, not 0%.

`/api/compare` rows represent aggregated config paths, not individual launches.
Subset and rep parameters constrain that aggregation; Compare does not claim
batch-level isolation or statistical significance.

### Leaderboard (`/leaderboard`)
A decision surface for choosing a config on one fixed subset:

- **Measured standouts** name the balanced frontier pick, highest rep solve rate,
  lowest cost per successful rep, and largest solve-rate lift over the canonical
  `baseline` at the same model and thinking level. Each card states its rule;
  none claims statistical significance.
- **Rep and task success stay separate.** A config can solve one of three reps on
  every task: 33% rep success but 100% task coverage. Cards and rows show both.
- **Value frontier** plots rep solve rate against either cost per successful rep
  or median rep cost. Frontier membership follows the selected axis. `$0` means
  cost untracked, so those configs remain in the table but never appear in cost
  cards or charts.
- **Filters** cover subset, rep cap, full/partial coverage, model+thinking, and
  search across config/run/model/thinking. Mobile shows the balanced pick first
  and collapses advanced filters.
- **Ranked evidence** defaults to rep solve rate and shows same-group baseline
  delta, median cost, cost per successful rep, task success, and `tasks × reps`.
  Mean partial, tokens, wall time, and total cost stay behind **More metrics**.

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /api/runs?detail=summary\|operational\|diagnostic` | List all discovered runs |
| `GET /api/runs/<id>?detail=...` | Detailed projection of a single run |
| `GET /api/runs/<id>/score` | Live score replay (solve/partial rates, tool-call error rate, cost, throughput, ETA, timeline, per-task results) |
| `GET /api/runs/<id>/events?limit=N` | Events tail |
| `GET /api/cell-session?path=&tail=N` | Agent session turn timeline for one cell (intent + tools + token/cost deltas) |
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
