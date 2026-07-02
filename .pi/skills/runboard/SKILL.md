---
name: runboard
description: Open a Herdr tail tab for a harness run when the user explicitly asks for a runboard, tail, Herdr tab, or raw log view. For new harness/run_batch.py monitoring, prefer the structured dashboard at scripts/run_dashboard.py reading results/_runs/<run_id>; this skill is the compatibility/tail workflow.
---

# runboard

A **runboard** is a live `.out` file plus a Herdr tab tailing it. For new batch
launches, prefer the structured dashboard:

```sh
python3 scripts/run_dashboard.py --state-root results/_runs --port 8765
```

Use this skill when the user specifically wants a Herdr/tail view or when a
legacy run only has `runs/<run>/track.out`. Prefer the helper; do not hand-roll
Herdr discovery unless the helper fails.

Native line shape:

```txt
[71/113] onedump-dump-encryption-pipeline / observational-memory / rep0  ok
```

Status legend: `ok` | `empty` | `timeout` | `transient` | `exit=<n>`.

## Tight path: open an existing live track

Use this path when `runs/<run>/track.out` already exists, especially for legacy
`harness/run_batch.py ... | tee runs/<run>/track.out` launches that predate
structured state.

1. Run the helper:

   ```sh
   scripts/open_runboard.py --run '<run>' --label '<short label>'
   # or: scripts/open_runboard.py --track runs/<run>/track.out --label '<short label>'
   ```

2. Report only the returned `pane`, `track`, `reused`, and current progress from
   `visible_preview`.

Completion: helper output has `"status": "live"`. The helper has already proved
Herdr env, current workspace, exact `tail -f` process, and visible runboard
content.

## If there is no track.out

Only for historical/result-only runs, build a compatibility tracker first. Read
[`result-tracker.md`](result-tracker.md), then rerun the tight path.

Completion: `runs/<run>/track.out` exists and the helper returns `status=live`.

## Guardrails

- If the helper says `HERDR_ENV != 1`, stop; do not control Herdr from outside
  Herdr.
- Do not use runboard as the default monitor for a new run if structured
  `results/_runs/<run_id>/` state is available; use the dashboard instead.
- Do not dump panes, containers, token counts, streamed text, or repeated state
  snapshots. A runboard is one native line per cell.
- Do not claim success from a pidfile or existing `track.out`; success requires
  the helper's verified `status=live` result.
- For single `harness/run.py` cells, there is no batch runboard; tail that cell's
  logs only if asked.
