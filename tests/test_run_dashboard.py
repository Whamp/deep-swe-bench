import json
import threading
import urllib.error
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
    assert dash["launch_metadata"] == "legacy_structured"
    assert dash["launch_plan_identity"] is None
    assert dash["preflight_state"] == "not_required"
    assert "active_cells" not in dash


def test_dashboard_ignores_malformed_run_without_hiding_healthy_run(
    tmp_path: Path,
) -> None:
    """Malformed abandoned state does not break central run discovery."""
    state_root = make_state(tmp_path, "healthy-run")
    malformed = state_root / "abandoned-run"
    malformed.mkdir()
    (malformed / "manifest.json").write_text('[{"not":"a manifest"}]\n')
    (malformed / "status.json").write_text('[{"not":"a status"}]\n')

    runs = run_dashboard.load_dashboard_runs(
        state_root,
        detail="summary",
        include_legacy=False,
        legacy_root=None,
    )

    assert "healthy-run" in {run["run_id"] for run in runs}


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


# ---------------------------------------------------------------------------
# Comparison / subset filtering
# ---------------------------------------------------------------------------

def _make_result(path: Path, *, reward_binary=0, reward_partial=0.0, task="", rep=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "agent_exit": 0,
        "verifier_exit": 0,
        "reward_binary": reward_binary,
        "reward_partial": reward_partial,
        "total_tokens": 1000,
        "cost_usd": 0.1,
        "agent_wall_s": 10.0,
        "patch_bytes": 100,
    }
    if task:
        payload["task"] = task
    if rep is not None:
        payload["rep"] = rep
    path.write_text(json.dumps(payload))


def test_load_subsets_reads_txt_files(tmp_path):
    subs = tmp_path / "subsets"
    subs.mkdir()
    (subs / "36_v2.txt").write_text("task-a\ntask-b\n\ntask-c\n")
    (subs / "12_v0.txt").write_text("task-a\n")
    out = run_dashboard.load_subsets(subs)
    names = [s["name"] for s in out]
    assert names == ["12_v0", "36_v2"]  # sorted
    v2 = next(s for s in out if s["name"] == "36_v2")
    assert v2["task_count"] == 3
    assert v2["tasks"] == ["task-a", "task-b", "task-c"]


def test_load_subset_tasks_missing_returns_none(tmp_path):
    assert run_dashboard.load_subset_tasks(tmp_path / "nope.txt") is None


def test_rep_from_parts():
    assert run_dashboard._rep_from_parts(("m", "t", "c", "task", "rep2", "result.json")) == 2
    assert run_dashboard._rep_from_parts(("m", "t", "c", "task", "rep0", "result.json")) == 0
    assert run_dashboard._rep_from_parts(("m", "t", "c", "task", "weird", "result.json")) == 0


def test_comparison_subset_filter_excludes_other_tasks(tmp_path):
    res = tmp_path / "results"
    # config has cells for task-a (in subset) and task-z (not in subset)
    _make_result(res / "gpt-5.5" / "low" / "baseline" / "task-a" / "rep0" / "result.json", reward_binary=1, reward_partial=1.0, task="task-a", rep=0)
    _make_result(res / "gpt-5.5" / "low" / "baseline" / "task-a" / "rep1" / "result.json", reward_binary=0, reward_partial=0.0, task="task-a", rep=1)
    _make_result(res / "gpt-5.5" / "low" / "baseline" / "task-z" / "rep0" / "result.json", reward_binary=1, reward_partial=1.0, task="task-z", rep=0)

    # No filter: all 3 cells
    all_runs = run_dashboard.load_comparison_data(res)
    assert all_runs[0]["total_cells"] == 3

    # Subset filter to {task-a}: only 2 cells, 1 solved -> 50%
    filt = run_dashboard.load_comparison_data(res, subset_tasks={"task-a"})
    assert len(filt) == 1
    assert filt[0]["total_cells"] == 2
    assert filt[0]["distinct_tasks"] == 1  # only task-a covered
    assert filt[0]["solved"] == 1
    assert abs(filt[0]["solve_rate"] - 50.0) < 1e-9
    # the task-z cell is excluded
    assert {c["task"] for c in filt[0]["cells"]} == {"task-a"}


def test_comparison_discovers_symlinked_config_directory(tmp_path):
    res = tmp_path / "results"
    source = tmp_path / "worktree-results" / "pi-check"
    _make_result(
        source / "task-a" / "rep0" / "result.json",
        reward_binary=1,
        reward_partial=1.0,
        task="task-a",
        rep=0,
    )
    config = res / "gpt-5.5" / "low" / "pi-check"
    config.parent.mkdir(parents=True)
    config.symlink_to(source, target_is_directory=True)

    out = run_dashboard.load_comparison_data(res)

    assert [run["run_id"] for run in out] == ["gpt-5.5/low/pi-check"]
    assert out[0]["total_cells"] == 1
    assert out[0]["solved"] == 1


def test_comparison_max_reps_caps_per_task(tmp_path):
    res = tmp_path / "results"
    for rep in range(5):
        _make_result(res / "gpt-5.5" / "low" / "baseline" / "task-a" / f"rep{rep}" / "result.json", reward_binary=1, task="task-a", rep=rep)
    _make_result(res / "gpt-5.5" / "low" / "baseline" / "task-b" / "rep0" / "result.json", reward_binary=0, task="task-b", rep=0)

    capped = run_dashboard.load_comparison_data(res, max_reps=2)
    # task-a keeps rep0, rep1 (2 of 5); task-b keeps rep0 -> total 3
    assert capped[0]["total_cells"] == 3
    a_reps = sorted(c["rep"] for c in capped[0]["cells"] if c["task"] == "task-a")
    assert a_reps == [0, 1]


def test_comparison_subset_and_reps_combined(tmp_path):
    res = tmp_path / "results"
    for rep in range(4):
        _make_result(res / "gpt-5.5" / "low" / "baseline" / "task-a" / f"rep{rep}" / "result.json", reward_binary=1, task="task-a", rep=rep)
    out = run_dashboard.load_comparison_data(res, subset_tasks={"task-a"}, max_reps=3)
    assert out[0]["total_cells"] == 3


def test_comparison_contaminated_skipped(tmp_path):
    res = tmp_path / "results"
    _make_result(res / "gpt-5.5" / "low" / "baseline" / "task-a" / "rep0" / "result.json", reward_binary=1, task="task-a")
    _make_result(res / "_contaminated" / "gpt-5.5" / "low" / "bad" / "task-a" / "rep0" / "result.json", reward_binary=1, task="task-a")
    out = run_dashboard.load_comparison_data(res)
    assert {r["config"] for r in out} == {"baseline"}


def test_http_api_subsets_and_compare_subset(tmp_path):
    """The /api/subsets and /api/compare?subset= endpoints serve filtered data."""
    state_root = make_state(tmp_path, "dash-test")
    # add a subset file under repo_root/subsets
    (tmp_path / "subsets").mkdir()
    (tmp_path / "subsets" / "mini.txt").write_text("task-a\n")
    server = run_dashboard.make_server(
        host="127.0.0.1", port=0, state_root=state_root, detail="summary",
        repo_root=tmp_path, legacy_root=tmp_path / "runs", results_root=tmp_path / "results",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urllib.request.urlopen(f"{base}/api/subsets", timeout=5) as r:
            subs = json.loads(r.read().decode("utf-8"))["subsets"]
        assert [s["name"] for s in subs] == ["mini"]
        with urllib.request.urlopen(f"{base}/api/compare?subset=mini", timeout=5) as r:
            cmp = json.loads(r.read().decode("utf-8"))
        assert cmp["subset"] == "mini"
        # make_state created a task-a cell -> present under the mini filter
        assert any(c["task"] == "task-a" for c in cmp["runs"][0]["cells"])
        # unknown subset -> 404
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(f"{base}/api/compare?subset=nonexistent", timeout=5)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
