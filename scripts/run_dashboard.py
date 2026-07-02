#!/usr/bin/env python3
"""Serve a lightweight live dashboard for run_batch structured state.

Usage:
    python3 scripts/run_dashboard.py --host 127.0.0.1 --port 8765
"""
from __future__ import annotations

import argparse
import html
import json
import sys
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.run_state import (  # noqa: E402
    DETAIL_LEVELS,
    discover_runs,
    project_legacy_track,
    project_structured_run,
    read_events,
    sanitize_run_id,
)

DEFAULT_STATE_ROOT = ROOT / "results" / "_runs"
DEFAULT_LEGACY_ROOT = ROOT / "runs"


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>deep-swe-bench live dashboard</title>
  <style>
    :root { color-scheme: dark; --bg:#0d1117; --panel:#161b22; --muted:#8b949e; --text:#e6edf3; --line:#30363d; --good:#3fb950; --bad:#f85149; --warn:#d29922; --accent:#58a6ff; }
    body { margin:0; font:14px/1.45 ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; background:var(--bg); color:var(--text); }
    header { display:flex; gap:16px; align-items:center; padding:16px 20px; border-bottom:1px solid var(--line); position:sticky; top:0; background:rgba(13,17,23,.94); backdrop-filter: blur(8px); }
    h1 { font-size:18px; margin:0; }
    h2 { margin:0 0 10px; font-size:16px; }
    h3 { margin:18px 0 8px; font-size:14px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }
    main { display:grid; grid-template-columns:minmax(300px, 420px) 1fr; gap:16px; padding:16px; }
    .panel, .card { background:var(--panel); border:1px solid var(--line); border-radius:12px; }
    .panel { padding:14px; min-width:0; }
    .card { padding:12px; margin:0 0 10px; cursor:pointer; }
    .card:hover, .card.selected { border-color:var(--accent); }
    .muted { color:var(--muted); }
    .row { display:flex; justify-content:space-between; gap:12px; align-items:baseline; }
    .pill { display:inline-block; padding:2px 8px; border-radius:999px; border:1px solid var(--line); color:var(--muted); }
    .pill.running, .pill.completed { color:var(--good); border-color:rgba(63,185,80,.55); }
    .pill.paused { color:var(--warn); border-color:rgba(210,153,34,.55); }
    .pill.failed { color:var(--bad); border-color:rgba(248,81,73,.55); }
    progress { width:100%; height:10px; accent-color:var(--accent); }
    table { width:100%; border-collapse:collapse; }
    th, td { text-align:left; padding:7px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
    th { color:var(--muted); font-weight:600; }
    code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    pre { white-space:pre-wrap; overflow:auto; max-height:420px; background:#0b0f14; border:1px solid var(--line); border-radius:8px; padding:10px; }
    a { color:var(--accent); text-decoration:none; }
    .metric { display:grid; grid-template-columns:repeat(auto-fit, minmax(110px,1fr)); gap:8px; margin:10px 0; }
    .metric div { background:#0f141b; border:1px solid var(--line); border-radius:8px; padding:8px; }
    .metric b { display:block; font-size:18px; }
    @media (max-width: 900px) { main { grid-template-columns:1fr; } }
  </style>
</head>
<body>
<header>
  <h1>deep-swe-bench live dashboard</h1>
  <label>Detail
    <select id="detail">
      <option value="summary">summary</option>
      <option value="operational">operational</option>
      <option value="diagnostic">diagnostic</option>
    </select>
  </label>
  <span class="muted" id="updated">loading…</span>
</header>
<main>
  <section class="panel">
    <h2>Discovered executions</h2>
    <div id="runs"></div>
  </section>
  <section class="panel">
    <h2 id="detail-title">Select an execution</h2>
    <div id="run-detail" class="muted">Structured state is read from results/_runs/*; legacy runs/*/track.out files appear as compatibility cards.</div>
  </section>
</main>
<script>
const DEFAULT_DETAIL = "__DEFAULT_DETAIL__";
const params = new URLSearchParams(location.search);
let detail = params.get('detail') || DEFAULT_DETAIL;
let selected = params.get('run') || null;
document.getElementById('detail').value = detail;
document.getElementById('detail').addEventListener('change', (ev) => {
  detail = ev.target.value;
  params.set('detail', detail);
  if (selected) params.set('run', selected);
  history.replaceState(null, '', '?' + params.toString());
  refreshAll();
});
function esc(v) { return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function fmtSeconds(v) { if (v === null || v === undefined) return '—'; if (v < 60) return Math.round(v) + 's'; if (v < 3600) return Math.round(v/60) + 'm'; return (v/3600).toFixed(1) + 'h'; }
function fileLink(path, label) { return path ? `<a href="/api/file?path=${encodeURIComponent(path)}&tail=200" target="_blank" rel="noreferrer">${esc(label || path)}</a>` : '—'; }
async function getJSON(url) { const r = await fetch(url); if (!r.ok) throw new Error(await r.text()); return r.json(); }
function progress(counts) { const total = counts.batch_total || 0, done = counts.batch_done || 0; return `<progress value="${done}" max="${total || 1}"></progress><div class="muted">${done}/${total} done</div>`; }
function renderCards(runs) {
  const root = document.getElementById('runs');
  if (!runs.length) { root.innerHTML = '<p class="muted">No structured state or legacy track files found.</p>'; return; }
  root.innerHTML = runs.map(run => {
    const c = run.counts || {};
    const bad = (c.failed || 0) + (c.timeout || 0) + (c.transient || 0);
    return `<article class="card ${run.run_id === selected ? 'selected' : ''}" data-run="${esc(run.run_id)}">
      <div class="row"><b>${esc(run.run_id)}</b><span class="pill ${esc(run.state)}">${esc(run.state)}</span></div>
      <div class="muted">${esc(run.model || run.kind)} ${esc(run.thinking || '')}</div>
      ${progress(c)}
      <div class="row muted"><span>active ${run.active_count || c.batch_running || 0}</span><span>bad ${bad}</span><span>heartbeat ${fmtSeconds(run.heartbeat_age_s)}</span></div>
    </article>`;
  }).join('');
  root.querySelectorAll('.card').forEach(card => card.addEventListener('click', () => {
    selected = card.dataset.run;
    params.set('run', selected); params.set('detail', detail);
    history.replaceState(null, '', '?' + params.toString());
    refreshAll();
  }));
}
function metrics(run) {
  const c = run.counts || {};
  return `<div class="metric">
    <div><span class="muted">Done</span><b>${c.batch_done || 0}/${c.batch_total || 0}</b></div>
    <div><span class="muted">Active</span><b>${run.active_count || c.batch_running || 0}</b></div>
    <div><span class="muted">OK / empty</span><b>${c.ok || 0} / ${c.empty || 0}</b></div>
    <div><span class="muted">Timeout / transient</span><b>${c.timeout || 0} / ${c.transient || 0}</b></div>
    <div><span class="muted">Failed</span><b>${c.failed || 0}</b></div>
    <div><span class="muted">ETA-ish</span><b>${fmtSeconds(run.eta_s)}</b></div>
  </div>`;
}
function renderCellTable(title, cells) {
  if (!cells || !cells.length) return '';
  return `<h3>${esc(title)}</h3><table><thead><tr><th>Task</th><th>Config</th><th>Rep</th><th>State</th><th>Outcome</th><th>Metrics</th><th>Paths</th></tr></thead><tbody>` + cells.map(cell => {
    const s = cell.summary || {};
    const bits = [];
    if (s.reward_partial !== undefined) bits.push('partial=' + s.reward_partial);
    if (s.reward_binary !== undefined) bits.push('binary=' + s.reward_binary);
    if (s.total_tokens !== undefined) bits.push('tok=' + s.total_tokens);
    if (s.combined_total_tokens !== undefined) bits.push('combined=' + s.combined_total_tokens);
    if (s.cost_usd !== undefined) bits.push('$=' + s.cost_usd);
    if (s.agent_wall_s !== undefined) bits.push('wall=' + fmtSeconds(s.agent_wall_s));
    return `<tr><td>${esc(cell.task)}</td><td>${esc(cell.config)}</td><td>${esc(cell.rep)}</td><td>${esc(cell.state || '')}</td><td>${esc(cell.outcome || '')}</td><td>${esc(bits.join(' · '))}</td><td>${fileLink(cell.result_path, 'result')} · ${fileLink(cell.log_path, 'log')}</td></tr>`;
  }).join('') + '</tbody></table>';
}
function renderPreflight(preflight) {
  const cells = Object.values(preflight || {});
  return renderCellTable('Preflight / smoke', cells);
}
function renderDetail(run) {
  document.getElementById('detail-title').textContent = run.run_id;
  const c = run.counts || {};
  const active = run.active_cells || [];
  const recent = run.recent_finished || [];
  let html = `<div class="row"><span class="pill ${esc(run.state)}">${esc(run.state)}</span><span class="muted">updated ${esc(run.updated_at || 'unknown')} · heartbeat ${fmtSeconds(run.heartbeat_age_s)}</span></div>`;
  html += `<p class="muted">${esc(run.model || run.kind)} ${esc(run.thinking || '')} · configs: ${esc((run.configs || []).join(', ') || '—')}</p>`;
  html += progress(c) + metrics(run);
  html += `<p class="muted">State files: ${fileLink(run.paths && run.paths.manifest, 'manifest')} · ${fileLink(run.paths && run.paths.status, 'status')} · ${fileLink(run.paths && run.paths.events, 'events')}</p>`;
  if (Object.keys(run.failure_buckets || {}).length) html += `<h3>Failure buckets</h3><pre>${esc(JSON.stringify(run.failure_buckets, null, 2))}</pre>`;
  html += renderPreflight(run.preflight);
  html += renderCellTable('Active cells', active);
  html += renderCellTable('Recent finished cells', recent);
  if (detail === 'diagnostic') {
    if (run.events_tail) html += `<h3>Recent events</h3><pre>${esc(run.events_tail.map(e => JSON.stringify(e)).join('\n'))}</pre>`;
    if (run.status) html += `<h3>status.json</h3><pre>${esc(JSON.stringify(run.status, null, 2))}</pre>`;
    if (run.manifest) html += `<h3>manifest.json</h3><pre>${esc(JSON.stringify(run.manifest, null, 2))}</pre>`;
    if (run.track_tail) html += `<h3>legacy track tail</h3><pre>${esc(run.track_tail.join('\n'))}</pre>`;
  }
  document.getElementById('run-detail').innerHTML = html;
}
async function refreshAll() {
  try {
    const data = await getJSON('/api/runs?detail=' + encodeURIComponent(detail));
    const runs = data.runs || [];
    if (!selected && runs.length) selected = runs[0].run_id;
    renderCards(runs);
    if (selected) {
      const run = await getJSON('/api/runs/' + encodeURIComponent(selected) + '?detail=' + encodeURIComponent(detail));
      renderDetail(run);
    }
    document.getElementById('updated').textContent = 'updated ' + new Date().toLocaleTimeString();
  } catch (err) {
    document.getElementById('updated').textContent = 'error: ' + err.message;
  }
}
refreshAll();
setInterval(refreshAll, 3000);
</script>
</body>
</html>
"""


def load_dashboard_runs(
    state_root: str | Path = DEFAULT_STATE_ROOT,
    *,
    detail: str = "summary",
    include_legacy: bool = True,
    legacy_root: str | Path | None = DEFAULT_LEGACY_ROOT,
) -> list[dict[str, Any]]:
    return discover_runs(state_root, detail=detail, include_legacy=include_legacy, legacy_root=legacy_root)


def load_dashboard_run(
    run_id: str,
    state_root: str | Path = DEFAULT_STATE_ROOT,
    *,
    detail: str = "operational",
    legacy_root: str | Path | None = DEFAULT_LEGACY_ROOT,
) -> dict[str, Any] | None:
    if detail not in DETAIL_LEVELS:
        detail = "summary"
    if run_id.startswith("legacy-"):
        legacy_name = run_id.removeprefix("legacy-")
        if not legacy_name or "/" in legacy_name or "\\" in legacy_name:
            return None
        root = Path(legacy_root) if legacy_root is not None else DEFAULT_LEGACY_ROOT
        track = root / legacy_name / "track.out"
        if not track.exists():
            return None
        return project_legacy_track(track, detail=detail)
    try:
        safe_id = sanitize_run_id(run_id)
    except ValueError:
        return None
    run_dir = Path(state_root) / safe_id
    if not run_dir.exists():
        return None
    return project_structured_run(run_dir, detail=detail)


def resolve_dashboard_path(raw_path: str, *, repo_root: Path = ROOT, state_root: Path = DEFAULT_STATE_ROOT) -> Path:
    if not raw_path:
        raise ValueError("missing path")
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve()
    allowed_roots = [repo_root.resolve(), state_root.resolve()]
    for allowed in allowed_roots:
        try:
            resolved.relative_to(allowed)
            return resolved
        except ValueError:
            continue
    raise ValueError("path is outside the dashboard allowlist")


def tail_file(path: Path, *, lines: int = 200, max_bytes: int = 256_000) -> str:
    lines = max(1, min(lines, 2000))
    if not path.is_file():
        raise FileNotFoundError(path)
    chunks: list[bytes] = []
    size = path.stat().st_size
    remaining = min(size, max_bytes)
    with path.open("rb") as fh:
        while remaining > 0:
            step = min(8192, remaining)
            remaining -= step
            fh.seek(size - sum(len(c) for c in chunks) - step)
            chunk = fh.read(step)
            chunks.append(chunk)
            if b"\n".join(reversed(chunks)).count(b"\n") > lines:
                break
    data = b"".join(reversed(chunks)).decode("utf-8", errors="replace")
    return "\n".join(data.splitlines()[-lines:]) + ("\n" if data else "")


class DashboardHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        *,
        state_root: Path,
        detail: str,
        repo_root: Path = ROOT,
        legacy_root: Path | None = DEFAULT_LEGACY_ROOT,
    ):
        super().__init__(server_address, handler_class)
        self.state_root = state_root
        self.detail = detail
        self.repo_root = repo_root
        self.legacy_root = legacy_root


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardHTTPServer

    def log_message(self, fmt: str, *args: Any) -> None:  # keep dashboard quiet by default
        return

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urllib.parse.urlparse(self.path)
        try:
            if parsed.path == "/":
                self._send_html(INDEX_HTML.replace("__DEFAULT_DETAIL__", html.escape(self.server.detail)))
                return
            if parsed.path == "/api/runs":
                qs = urllib.parse.parse_qs(parsed.query)
                detail = qs.get("detail", [self.server.detail])[0]
                runs = load_dashboard_runs(
                    self.server.state_root,
                    detail=detail,
                    include_legacy=True,
                    legacy_root=self.server.legacy_root,
                )
                self._send_json({"runs": runs})
                return
            if parsed.path.startswith("/api/runs/"):
                parts = [urllib.parse.unquote(p) for p in parsed.path.split("/") if p]
                if len(parts) < 3:
                    self._send_error(HTTPStatus.NOT_FOUND, "missing run_id")
                    return
                run_id = parts[2]
                qs = urllib.parse.parse_qs(parsed.query)
                detail = qs.get("detail", [self.server.detail])[0]
                if len(parts) == 4 and parts[3] == "events":
                    after = qs.get("after", [None])[0]
                    limit = int(qs.get("limit", [100])[0])
                    if run_id.startswith("legacy-"):
                        self._send_json({"events": []})
                        return
                    try:
                        safe_id = sanitize_run_id(run_id)
                    except ValueError:
                        self._send_error(HTTPStatus.BAD_REQUEST, "invalid run_id")
                        return
                    events = read_events(self.server.state_root / safe_id, after=int(after) if after else None, limit=limit)
                    self._send_json({"events": events})
                    return
                if len(parts) == 3:
                    run = load_dashboard_run(
                        run_id,
                        self.server.state_root,
                        detail=detail,
                        legacy_root=self.server.legacy_root,
                    )
                    if run is None:
                        self._send_error(HTTPStatus.NOT_FOUND, "run not found")
                        return
                    self._send_json(run)
                    return
            if parsed.path == "/api/file":
                qs = urllib.parse.parse_qs(parsed.query)
                raw = qs.get("path", [""])[0]
                tail = int(qs.get("tail", [200])[0])
                path = resolve_dashboard_path(raw, repo_root=self.server.repo_root, state_root=self.server.state_root)
                text = tail_file(path, lines=tail)
                self._send_text(text)
                return
            self._send_error(HTTPStatus.NOT_FOUND, "not found")
        except FileNotFoundError as exc:
            self._send_error(HTTPStatus.NOT_FOUND, str(exc))
        except ValueError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, repr(exc))

    def _send_json(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        data = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_server(
    *,
    host: str,
    port: int,
    state_root: str | Path = DEFAULT_STATE_ROOT,
    detail: str = "operational",
    repo_root: str | Path = ROOT,
    legacy_root: str | Path | None = DEFAULT_LEGACY_ROOT,
) -> DashboardHTTPServer:
    if detail not in DETAIL_LEVELS:
        raise ValueError(f"detail must be one of {sorted(DETAIL_LEVELS)}")
    legacy = Path(legacy_root) if legacy_root is not None else None
    return DashboardHTTPServer(
        (host, port),
        DashboardHandler,
        state_root=Path(state_root),
        detail=detail,
        repo_root=Path(repo_root),
        legacy_root=legacy,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT), help="default: results/_runs")
    ap.add_argument("--detail", choices=sorted(DETAIL_LEVELS), default="operational")
    args = ap.parse_args(argv)

    server = make_server(host=args.host, port=args.port, state_root=args.state_root, detail=args.detail)
    url = f"http://{args.host}:{server.server_address[1]}/"
    print(f"serving deep-swe-bench dashboard at {url}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
