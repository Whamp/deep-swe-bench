import json
import threading
import urllib.request
from pathlib import Path

import pytest

from harness.run_state import RunStateWriter, base_manifest, make_cell
from scripts import run_dashboard


def make_state(tmp_path: Path, run_id: str = "dash-test") -> Path:
    state_root = tmp_path / "results" / "_runs"
    result = tmp_path / "results" / "model" / "high" / "cfg" / "task-a" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(json.dumps({
        "agent_exit": 0,
        "verifier_exit": 0,
        "reward_partial": 0.5,
        "total_tokens": 100,
    }))
    log = tmp_path / "results" / "model" / "high" / "logs" / "task-a__cfg__rep0.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("raw log content should stay behind a link\n")
    cell = make_cell(task="task-a", config="cfg", rep=0, result_path=result, log_path=log)
    manifest = base_manifest(
        run_id=run_id,
        command=["cmd"],
        cwd=tmp_path,
        model="model",
        thinking="high",
        configs=["cfg"],
        selection={"mode": "tasks", "tasks": ["task-a"]},
        runs=1,
        workers=1,
        agent_timeout_s=None,
        rpc_quiescence_s=None,
        progress_interval_s=15,
        batch_cells=[cell],
        preflight=[],
    )
    writer = RunStateWriter(state_root, manifest)
    writer.start()
    writer.cell_started(cell)
    writer.cell_finished(cell, result_path=result, log_path=log, exit_code=0)
    return state_root


def test_dashboard_discovers_structured_and_incomplete_runs(tmp_path):
    state_root = make_state(tmp_path, "dash-test")
    incomplete = state_root / "incomplete"
    incomplete.mkdir(parents=True)
    (incomplete / "status.json").write_text(json.dumps({"run_id": "incomplete", "state": "running"}))

    runs = run_dashboard.load_dashboard_runs(state_root, detail="summary", include_legacy=False, legacy_root=None)

    ids = {run["run_id"] for run in runs}
    assert {"dash-test", "incomplete"} <= ids
    dash = next(run for run in runs if run["run_id"] == "dash-test")
    assert dash["counts"]["batch_done"] == 1
    assert "active_cells" not in dash


def test_dashboard_detail_projection_and_legacy_track(tmp_path):
    state_root = make_state(tmp_path, "dash-test")
    legacy_root = tmp_path / "runs"
    track = legacy_root / "old-comparison" / "track.out"
    track.parent.mkdir(parents=True)
    track.write_text("running 1 cells: cfg\n[1/1] task-a / cfg / rep0  ok\ndone: 1/1\n")

    structured = run_dashboard.load_dashboard_run("dash-test", state_root, detail="operational", legacy_root=legacy_root)
    legacy = run_dashboard.load_dashboard_run("legacy-old-comparison", state_root, detail="operational", legacy_root=legacy_root)

    assert structured is not None
    assert structured["recent_finished"][0]["summary"]["total_tokens"] == 100
    assert "raw log content" not in json.dumps(structured)
    assert legacy is not None
    assert legacy["kind"] == "legacy_track"
    assert legacy["counts"]["batch_done"] == 1


def test_safe_file_links_are_allowlisted_and_tailed(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    state_root = repo / "results" / "_runs"
    path = repo / "results" / "x.log"
    path.parent.mkdir(parents=True)
    path.write_text("one\ntwo\nthree\n")

    resolved = run_dashboard.resolve_dashboard_path("results/x.log", repo_root=repo, state_root=state_root)

    assert resolved == path.resolve()
    assert run_dashboard.tail_file(resolved, lines=2) == "two\nthree\n"
    with pytest.raises(ValueError):
        run_dashboard.resolve_dashboard_path(str(tmp_path / "outside.log"), repo_root=repo, state_root=state_root)


def test_dashboard_http_api_smoke(tmp_path):
    state_root = make_state(tmp_path, "dash-test")
    server = run_dashboard.make_server(
        host="127.0.0.1",
        port=0,
        state_root=state_root,
        detail="summary",
        repo_root=tmp_path,
        legacy_root=tmp_path / "runs",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/api/runs"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        assert data["runs"][0]["run_id"] == "dash-test"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
