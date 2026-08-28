import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from harness.run_state import RunStateWriter, base_manifest, make_cell
from scripts import run_dashboard


def make_state(tmp_path: Path, run_id: str = "dash-test") -> Path:
    state_root = tmp_path / "results" / "_runs"
    result = (
        tmp_path
        / "results"
        / "model"
        / "high"
        / "cfg"
        / "task-a"
        / "rep0"
        / "result.json"
    )
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(
        json.dumps(
            {
                "agent_exit": 0,
                "verifier_exit": 0,
                "reward_partial": 0.5,
                "total_tokens": 100,
            }
        )
    )
    log = tmp_path / "results" / "model" / "high" / "logs" / "task-a__cfg__rep0.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("raw log content should stay behind a link\n")
    cell = make_cell(
        task="task-a", config="cfg", rep=0, result_path=result, log_path=log
    )
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
    (incomplete / "status.json").write_text(
        json.dumps({"run_id": "incomplete", "state": "running"})
    )

    runs = run_dashboard.load_dashboard_runs(
        state_root, detail="summary", include_legacy=False, legacy_root=None
    )

    ids = {run["run_id"] for run in runs}
    assert {"dash-test", "incomplete"} <= ids
    dash = next(run for run in runs if run["run_id"] == "dash-test")
    assert dash["counts"]["batch_done"] == 1
    assert dash["launch_metadata"] == "legacy_structured"
    assert dash["launch_plan_identity"] is None
    assert dash["preflight_state"] == "not_required"
    assert "active_cells" not in dash


def test_operational_run_detail_includes_finished_cell_tool_error_metrics(tmp_path):
    state_root = make_state(tmp_path, "tool-metrics-run")
    result = (
        tmp_path
        / "results"
        / "model"
        / "high"
        / "cfg"
        / "task-a"
        / "rep0"
        / "result.json"
    )
    _write_session(
        result.parent / "session" / "s.jsonl",
        [
            _tool_result("read", is_error=False),
            _tool_result("bash", is_error=True),
        ],
    )
    run_dashboard._SESSION_CACHE.clear()

    run = run_dashboard.load_dashboard_run(
        "tool-metrics-run",
        state_root,
        detail="operational",
        legacy_root=None,
        repo_root=tmp_path,
    )

    summary = run["finished_cells"][0]["summary"]
    assert summary["tool_calls"] == 2
    assert summary["tool_call_errors"] == 1
    assert summary["tool_call_error_rate"] == 0.5


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

    structured = run_dashboard.load_dashboard_run(
        "dash-test", state_root, detail="operational", legacy_root=legacy_root
    )
    legacy = run_dashboard.load_dashboard_run(
        "legacy-old-comparison",
        state_root,
        detail="operational",
        legacy_root=legacy_root,
    )

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

    resolved = run_dashboard.resolve_dashboard_path(
        "results/x.log", repo_root=repo, state_root=state_root
    )

    assert resolved == path.resolve()
    assert run_dashboard.head_file(resolved, lines=2) == "one\ntwo\n"
    assert run_dashboard.tail_file(resolved, lines=2) == "two\nthree\n"
    with pytest.raises(ValueError):
        run_dashboard.resolve_dashboard_path(
            str(tmp_path / "outside.log"), repo_root=repo, state_root=state_root
        )


def test_dashboard_follows_launch_plan_structured_state_path(tmp_path: Path) -> None:
    """A launch wrapper under _runs can point at live state under results/."""
    run_id = "external-state-run"
    state_root = make_state(tmp_path, run_id)
    source = state_root / run_id
    target = tmp_path / "results" / f"{run_id}--plan-hash"
    source.rename(target)
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["run_key"] = target.name
    manifest_path.write_text(json.dumps(manifest))
    wrapper = state_root / run_id
    wrapper.mkdir()
    (wrapper / "launch-plan.json").write_text(
        json.dumps(
            {
                "runId": run_id,
                "paths": {
                    "statePath": str(target),
                    "stateRoot": str(tmp_path / "results"),
                },
            }
        )
    )

    server = run_dashboard.make_server(
        host="127.0.0.1",
        port=0,
        state_root=state_root,
        detail="summary",
        repo_root=tmp_path,
        legacy_root=tmp_path / "runs",
        results_root=tmp_path / "results",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urllib.request.urlopen(f"{base}/api/runs", timeout=5) as response:
            runs = json.loads(response.read().decode("utf-8"))["runs"]
        projected = next(run for run in runs if run["run_id"] == run_id)
        assert projected["counts"]["batch_done"] == 1
        assert projected["run_key"] == target.name

        with urllib.request.urlopen(
            f"{base}/api/runs/{target.name}?detail=operational", timeout=5
        ) as response:
            detail = json.loads(response.read().decode("utf-8"))
        assert detail["counts"]["batch_done"] == 1

        with urllib.request.urlopen(
            f"{base}/api/runs/{target.name}/score", timeout=5
        ) as response:
            score = json.loads(response.read().decode("utf-8"))["score"]
        assert score["finished"] == 1
        assert len(score["timeline"]) == 1

        with urllib.request.urlopen(
            f"{base}/api/runs/{target.name}/events", timeout=5
        ) as response:
            events = json.loads(response.read().decode("utf-8"))["events"]
        assert any(event["event"] == "cell_finished" for event in events)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_dashboard_refuses_launch_plan_state_path_outside_results(tmp_path: Path) -> None:
    state_root = tmp_path / "repo" / "results" / "_runs"
    wrapper = state_root / "guarded-run"
    wrapper.mkdir(parents=True)
    outside = tmp_path / "outside-state"
    outside.mkdir()
    (outside / "manifest.json").write_text(json.dumps({"run_id": "guarded-run"}))
    (wrapper / "launch-plan.json").write_text(
        json.dumps(
            {
                "runId": "guarded-run",
                "paths": {"statePath": str(outside)},
            }
        )
    )

    assert run_dashboard.resolve_dashboard_run_state_dir("guarded-run", state_root) == wrapper


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
    assert (
        run_dashboard._rep_from_parts(("m", "t", "c", "task", "rep2", "result.json"))
        == 2
    )
    assert (
        run_dashboard._rep_from_parts(("m", "t", "c", "task", "rep0", "result.json"))
        == 0
    )
    assert (
        run_dashboard._rep_from_parts(("m", "t", "c", "task", "weird", "result.json"))
        == 0
    )


def test_comparison_subset_filter_excludes_other_tasks(tmp_path):
    res = tmp_path / "results"
    # config has cells for task-a (in subset) and task-z (not in subset)
    _make_result(
        res / "gpt-5.5" / "low" / "baseline" / "task-a" / "rep0" / "result.json",
        reward_binary=1,
        reward_partial=1.0,
        task="task-a",
        rep=0,
    )
    _make_result(
        res / "gpt-5.5" / "low" / "baseline" / "task-a" / "rep1" / "result.json",
        reward_binary=0,
        reward_partial=0.0,
        task="task-a",
        rep=1,
    )
    _make_result(
        res / "gpt-5.5" / "low" / "baseline" / "task-z" / "rep0" / "result.json",
        reward_binary=1,
        reward_partial=1.0,
        task="task-z",
        rep=0,
    )

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
    # the task-z cell is excluded, and each retained cell is directly inspectable.
    assert {c["task"] for c in filt[0]["cells"]} == {"task-a"}
    assert {Path(c["result_path"]).name for c in filt[0]["cells"]} == {"result.json"}
    assert all(Path(c["result_path"]).is_absolute() for c in filt[0]["cells"])


def test_cache_adjusted_token_summary_discounts_known_cache_reads():
    summary = run_dashboard.cache_adjusted_token_summary(
        {
            "combined_total_tokens": 1_000,
            "cache_read_tokens": 500,
            "advisor_cache_read_tokens": 100,
        }
    )

    assert summary == {
        "reported_total_tokens": 1_000,
        "cache_read_tokens": 600,
        "adjusted_tokens": 460.0,
        "cache_read_share": 0.6,
        "token_policy": "cache-read-10pct-v1",
        "cache_read_weight": 0.1,
    }


def test_cache_adjusted_token_summary_never_drops_main_total():
    summary = run_dashboard.cache_adjusted_token_summary(
        {
            "combined_total_tokens": 900,
            "total_tokens": 1_000,
            "cache_read_tokens": 500,
        }
    )

    assert summary["reported_total_tokens"] == 1_000
    assert summary["adjusted_tokens"] == 550.0


def test_comparison_backfills_cache_adjusted_efficiency(tmp_path):
    res = tmp_path / "results"
    first = res / "gpt-5.5" / "low" / "baseline" / "task-a" / "rep0" / "result.json"
    second = res / "gpt-5.5" / "low" / "baseline" / "task-b" / "rep0" / "result.json"
    _make_result(first, reward_binary=1, task="task-a", rep=0)
    _make_result(second, reward_binary=0, task="task-b", rep=0)
    first_payload = json.loads(first.read_text())
    first_payload.update(
        {
            "combined_total_tokens": 1_000,
            "cache_read_tokens": 500,
            "advisor_cache_read_tokens": 100,
        }
    )
    first.write_text(json.dumps(first_payload))
    second_payload = json.loads(second.read_text())
    second_payload.update(
        {
            "combined_total_tokens": 2_000,
            "cache_read_tokens": 1_000,
            "workflow_cache_read_tokens": 200,
        }
    )
    second.write_text(json.dumps(second_payload))

    [run] = run_dashboard.load_comparison_data(res)

    assert run["total_reported_tokens"] == 3_000
    assert run["total_cache_read_tokens"] == 1_800
    assert run["total_adjusted_tokens"] == 1_380.0
    assert run["cache_read_share"] == 0.6
    assert run["solves_per_million_adjusted_tokens"] == pytest.approx(724.637681)
    assert run["token_policy"] == "cache-read-10pct-v1"
    assert run["cache_read_weight"] == 0.1
    adjusted_by_task = {cell["task"]: cell["adjusted_tokens"] for cell in run["cells"]}
    assert adjusted_by_task == {"task-a": 460.0, "task-b": 920.0}


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
        _make_result(
            res
            / "gpt-5.5"
            / "low"
            / "baseline"
            / "task-a"
            / f"rep{rep}"
            / "result.json",
            reward_binary=1,
            task="task-a",
            rep=rep,
        )
    _make_result(
        res / "gpt-5.5" / "low" / "baseline" / "task-b" / "rep0" / "result.json",
        reward_binary=0,
        task="task-b",
        rep=0,
    )

    capped = run_dashboard.load_comparison_data(res, max_reps=2)
    # task-a keeps rep0, rep1 (2 of 5); task-b keeps rep0 -> total 3
    assert capped[0]["total_cells"] == 3
    a_reps = sorted(c["rep"] for c in capped[0]["cells"] if c["task"] == "task-a")
    assert a_reps == [0, 1]


def test_comparison_subset_and_reps_combined(tmp_path):
    res = tmp_path / "results"
    for rep in range(4):
        _make_result(
            res
            / "gpt-5.5"
            / "low"
            / "baseline"
            / "task-a"
            / f"rep{rep}"
            / "result.json",
            reward_binary=1,
            task="task-a",
            rep=rep,
        )
    out = run_dashboard.load_comparison_data(res, subset_tasks={"task-a"}, max_reps=3)
    assert out[0]["total_cells"] == 3


def test_comparison_contaminated_skipped(tmp_path):
    res = tmp_path / "results"
    _make_result(
        res / "gpt-5.5" / "low" / "baseline" / "task-a" / "rep0" / "result.json",
        reward_binary=1,
        task="task-a",
    )
    _make_result(
        res
        / "_contaminated"
        / "gpt-5.5"
        / "low"
        / "bad"
        / "task-a"
        / "rep0"
        / "result.json",
        reward_binary=1,
        task="task-a",
    )
    out = run_dashboard.load_comparison_data(res)
    assert {r["config"] for r in out} == {"baseline"}


# ---------------------------------------------------------------------------
# Live run scoring (events.ndjson replay)
# ---------------------------------------------------------------------------


def _make_scored_run(tmp_path: Path, run_id: str = "score-test") -> Path:
    """Build a run with several finished cells carrying real summaries."""
    state_root = tmp_path / "results" / "_runs"
    cells = []
    outcomes = [
        ("task-a", 0, 1, 1.0, 0.5, "ok"),  # solved
        ("task-a", 1, 1, 1.0, 0.6, "ok"),  # solved (rep1)
        ("task-b", 0, 0, 0.2, 0.7, "ok"),  # not solved
        ("task-c", 0, 0, 0.0, 0.0, "timeout"),  # failure
    ]
    for task, rep, rb, rp, cost, _ in outcomes:
        result = (
            tmp_path
            / "results"
            / "model"
            / "high"
            / "cfg"
            / task
            / f"rep{rep}"
            / "result.json"
        )
        result.parent.mkdir(parents=True, exist_ok=True)
        timed_out = _ == "timeout"
        result.write_text(
            json.dumps(
                {
                    "agent_exit": 0,
                    "verifier_exit": 0,
                    "agent_timed_out": timed_out,
                    "reward_binary": rb,
                    "reward_partial": rp,
                    "combined_cost_usd": cost,
                    "cost_usd": cost,
                    "total_tokens": 1000,
                    "agent_wall_s": 0.0,
                }
            )
        )
        log = result.parent / "cell.log"
        log.write_text("log\n")
        cell = make_cell(
            task=task, config="cfg", rep=rep, result_path=result, log_path=log
        )
        cells.append((cell, result, log))
    manifest = base_manifest(
        run_id=run_id,
        command=["cmd"],
        cwd=tmp_path,
        model="model",
        thinking="high",
        configs=["cfg"],
        selection={"mode": "tasks", "tasks": ["task-a", "task-b", "task-c"]},
        runs=1,
        workers=1,
        agent_timeout_s=None,
        rpc_quiescence_s=None,
        progress_interval_s=15,
        batch_cells=[c for c, _, _ in cells],
        preflight=[],
    )
    writer = RunStateWriter(state_root, manifest)
    writer.start()
    for cell, result, log in cells:
        writer.cell_started(cell)
        writer.cell_finished(cell, result_path=result, log_path=log, exit_code=0)
    return state_root / run_id


def test_load_run_score_aggregates_events(tmp_path):
    run_dir = _make_scored_run(tmp_path)
    score = run_dashboard.load_run_score(run_dir)
    assert score["finished"] == 4  # done cells (finished + skipped)
    assert score["solved"] == 2  # rep-level solved cells (task-a x2)
    assert score["processed"] == 4  # all real finishes here (no skips)
    # Solve rate is TASK-LEVEL: task-a solved, task-b/c not -> 1/3.
    assert score["tasks_total"] == 3
    assert score["tasks_solved"] == 1
    assert abs(score["solve_rate"] - 33.33) < 1e-6
    assert score["active"] == 0
    assert score["failure_breakdown"] == {"timeout": 1}
    by_task = {t["task"]: t for t in score["tasks"]}
    assert by_task["task-a"]["solved"] is True
    assert by_task["task-a"]["reps"] == 2
    assert by_task["task-b"]["solved"] is False
    assert by_task["task-c"]["last_outcome"] == "timeout"
    assert len(score["timeline"]) == 4
    # timeline.solved is the running task-level solved count (1 task solved).
    assert score["timeline"][-1]["solved"] == 1


def test_load_run_score_empty_run(tmp_path):
    run_dir = tmp_path / "empty-run"
    run_dir.mkdir()
    (run_dir / "events.ndjson").write_text("")
    score = run_dashboard.load_run_score(run_dir)
    assert score["finished"] == 0
    assert score["solve_rate"] == 0.0
    assert score["tool_calls"] == 0
    assert score["tool_call_errors"] == 0
    assert score["tool_call_error_rate"] is None
    assert score["tasks"] == []
    assert score["timeline"] == []


def test_load_run_score_plots_mean_partial_and_tool_call_error_rate(tmp_path):
    run_dir = _make_scored_run(tmp_path)
    events = [
        json.loads(line)
        for line in (run_dir / "events.ndjson").read_text().splitlines()
    ]
    finished = [event for event in events if event.get("event") == "cell_finished"]
    for index, event in enumerate(finished):
        result = Path(event["result_path"])
        _write_session(
            result.parent / "session" / "s.jsonl",
            [
                _tool_result("read", is_error=False),
                _tool_result("bash", is_error=index == len(finished) - 1),
            ],
        )

    run_dashboard._SESSION_CACHE.clear()
    score = run_dashboard.load_run_score(
        run_dir,
        repo_root=tmp_path,
        state_root=tmp_path / "results" / "_runs",
    )

    assert [point["mean_partial"] for point in score["timeline"]] == [
        1.0,
        1.0,
        0.7333,
        0.55,
    ]
    assert score["tool_calls"] == 8
    assert score["tool_call_errors"] == 1
    assert score["tool_call_error_rate"] == 0.125
    assert score["timeline"][-1]["tool_call_error_rate"] == 0.125


def test_load_run_score_excludes_skips_from_cost_and_throughput(tmp_path):
    """Reused (skipped) cells count toward progress + task solve rate, but NOT
    toward this-run cost, throughput, or the timeline. Regression for the
    reuse-heavy run shape where skips otherwise double-count prior spend and
    inflate the finish rate."""
    state_root = tmp_path / "results" / "_runs"
    # task-a: real finish, solved, $0.50 this-run spend
    ra = tmp_path / "results" / "m" / "h" / "c" / "task-a" / "rep0" / "result.json"
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(
        json.dumps(
            {
                "agent_exit": 0,
                "verifier_exit": 0,
                "reward_binary": 1,
                "reward_partial": 1.0,
                "combined_cost_usd": 0.5,
                "cost_usd": 0.5,
            }
        )
    )
    # task-b: SKIPPED (reused) — prior result solved, but carries $0.30 PRIOR cost
    rb = tmp_path / "results" / "m" / "h" / "c" / "task-b" / "rep0" / "result.json"
    rb.parent.mkdir(parents=True, exist_ok=True)
    rb.write_text(
        json.dumps(
            {
                "agent_exit": 0,
                "verifier_exit": 0,
                "reward_binary": 1,
                "reward_partial": 1.0,
                "combined_cost_usd": 0.3,
                "cost_usd": 0.3,
            }
        )
    )
    # task-c: real finish, not solved, $0.20 this-run spend
    rc = tmp_path / "results" / "m" / "h" / "c" / "task-c" / "rep0" / "result.json"
    rc.parent.mkdir(parents=True, exist_ok=True)
    rc.write_text(
        json.dumps(
            {
                "agent_exit": 0,
                "verifier_exit": 0,
                "reward_binary": 0,
                "reward_partial": 0.0,
                "combined_cost_usd": 0.2,
                "cost_usd": 0.2,
            }
        )
    )
    cells = []
    for task_name, result in [
        ("task-a", ra),
        ("task-b", rb),
        ("task-c", rc),
    ]:
        log = result.parent / "l"
        log.write_text("x")
        cells.append(
            (
                make_cell(
                    task=task_name,
                    config="c",
                    rep=0,
                    result_path=result,
                    log_path=log,
                ),
                result,
                log,
            )
        )
    manifest = base_manifest(
        run_id="reuse-run",
        command=["cmd"],
        cwd=tmp_path,
        model="m",
        thinking="h",
        configs=["c"],
        selection={"mode": "tasks", "tasks": ["task-a", "task-b", "task-c"]},
        runs=1,
        workers=1,
        agent_timeout_s=None,
        rpc_quiescence_s=None,
        progress_interval_s=15,
        batch_cells=[c for c, _, _ in cells],
        preflight=[],
    )
    writer = RunStateWriter(state_root, manifest)
    writer.start()
    writer.cell_started(cells[0][0])
    writer.cell_finished(cells[0][0], result_path=ra, log_path=cells[0][2], exit_code=0)
    writer.cell_skipped(cells[1][0], reason="existing_result")  # reused
    writer.cell_started(cells[2][0])
    writer.cell_finished(cells[2][0], result_path=rc, log_path=cells[2][2], exit_code=0)

    score = run_dashboard.load_run_score(state_root / "reuse-run")
    assert score["finished"] == 3  # skip counts as done
    assert score["processed"] == 2  # only the two real finishes
    assert score["tasks_total"] == 3 and score["tasks_solved"] == 2  # a + b solved
    assert abs(score["solve_rate"] - 66.67) < 1e-6
    # Cost excludes the skip's prior $0.30 -> 0.5 + 0.2 = 0.7.
    assert abs(score["cumulative_cost"] - 0.7) < 1e-6
    assert score["timeline"][-1]["cost"] == round(0.7, 4)
    # Timeline only has real-finish points (2), and the skip's task still counts.
    assert len(score["timeline"]) == 2


def test_load_run_score_solve_rate_is_task_level_on_multi_rep(tmp_path):
    """With multiple reps, task-level solve rate diverges from rep-level.
    Two tasks, each 3 reps, each solved in exactly 1 of 3 reps:
    rep-level = 33%, task-level (any-rep) = 100%. The hero must show task-level
    so it is comparable to the baseline's any-rep rate."""
    state_root = tmp_path / "results" / "_runs"
    cells = []
    for task in ("task-a", "task-b"):
        for rep in range(3):
            solved = 1 if rep == 0 else 0
            result = (
                tmp_path
                / "results"
                / "m"
                / "h"
                / "c"
                / task
                / f"rep{rep}"
                / "result.json"
            )
            result.parent.mkdir(parents=True, exist_ok=True)
            result.write_text(
                json.dumps(
                    {
                        "agent_exit": 0,
                        "verifier_exit": 0,
                        "reward_binary": solved,
                        "reward_partial": float(solved),
                        "cost_usd": 0.1,
                        "combined_cost_usd": 0.1,
                    }
                )
            )
            log = result.parent / "l"
            log.write_text("x")
            cells.append(
                (
                    make_cell(
                        task=task, config="c", rep=rep, result_path=result, log_path=log
                    ),
                    result,
                    log,
                )
            )
    manifest = base_manifest(
        run_id="multirep-run",
        command=["cmd"],
        cwd=tmp_path,
        model="m",
        thinking="h",
        configs=["c"],
        selection={"mode": "tasks", "tasks": ["task-a", "task-b"]},
        runs=1,
        workers=1,
        agent_timeout_s=None,
        rpc_quiescence_s=None,
        progress_interval_s=15,
        batch_cells=[c for c, _, _ in cells],
        preflight=[],
    )
    writer = RunStateWriter(state_root, manifest)
    writer.start()
    for cell, result, log in cells:
        writer.cell_started(cell)
        writer.cell_finished(cell, result_path=result, log_path=log, exit_code=0)
    score = run_dashboard.load_run_score(state_root / "multirep-run")
    assert score["finished"] == 6 and score["solved"] == 2  # 2 solved cells of 6
    assert score["tasks_total"] == 2 and score["tasks_solved"] == 2
    assert score["solve_rate"] == 100.0  # task-level, not 33%


def test_http_api_score_endpoint(tmp_path):
    _make_scored_run(tmp_path)
    server = run_dashboard.make_server(
        host="127.0.0.1",
        port=0,
        state_root=tmp_path / "results" / "_runs",
        detail="summary",
        repo_root=tmp_path,
        legacy_root=tmp_path / "runs",
        results_root=tmp_path / "results",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urllib.request.urlopen(
            f"{base}/api/runs/score-test/score", timeout=5
        ) as r:
            score = json.loads(r.read().decode("utf-8"))["score"]
        assert score["finished"] == 4
        assert score["solved"] == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


# ---------------------------------------------------------------------------
# Cell session activity (JSONL turn timeline)
# ---------------------------------------------------------------------------


def _write_session(path: Path, turns: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        fh.write(
            json.dumps(
                {
                    "type": "session",
                    "version": 3,
                    "id": "s1",
                    "timestamp": "2026-01-01T00:00:00.000Z",
                    "cwd": "/app",
                }
            )
            + "\n"
        )
        for t in turns:
            fh.write(json.dumps(t) + "\n")


def _assistant_turn(content, *, ts="2026-01-01T00:00:01.000Z", usage=None):
    return {
        "type": "message",
        "message": {
            "role": "assistant",
            "content": content,
            "usage": usage or {"totalTokens": 100, "cost": {"total": 0.01}},
            "timestamp": ts,
        },
    }


def _tool_result(
    tool_name: str,
    *,
    is_error: bool,
    details: dict | None = None,
):
    return {
        "type": "message",
        "message": {
            "role": "toolResult",
            "toolName": tool_name,
            "toolCallId": "call-1",
            "content": [{"type": "text", "text": "result"}],
            "isError": is_error,
            "details": details,
            "timestamp": 1_767_225_601_000,
        },
    }


def test_cell_trajectory_returns_complete_paginated_native_turns(tmp_path):
    result = (
        tmp_path
        / "results"
        / "m"
        / "high"
        / "cfg"
        / "task-a"
        / "rep0"
        / "result.json"
    )
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(
        json.dumps(
            {
                "task": "task-a",
                "config": "cfg",
                "rep": 0,
                "model": "provider/model-a",
                "thinking_level": "high",
                "reward_binary": 1,
                "reward_partial": 0.75,
                "agent_wall_s": 12.5,
            }
        )
    )
    complete_output = "first line\n" + ("x" * 5_000) + "\nlast line"
    first_assistant = _assistant_turn(
        [
            {"type": "thinking", "thinking": "Inspect the implementation in full."},
            {"type": "text", "text": "I will run the focused test."},
            {
                "type": "toolCall",
                "id": "call-1",
                "name": "bash",
                "arguments": {"command": "pytest -q tests/test_feature.py"},
            },
            {"type": "provider_meta", "payload": {"retained": "exactly"}},
        ],
        ts="2026-01-01T00:00:02.000Z",
        usage={
            "input": 200,
            "output": 40,
            "cacheRead": 100,
            "reasoning": 10,
            "totalTokens": 350,
            "cost": {"total": 0.02},
        },
    )
    first_assistant["timestamp"] = "2026-01-01T00:00:02.000Z"
    tool_result = {
        "type": "message",
        "timestamp": "2026-01-01T00:00:04.000Z",
        "message": {
            "role": "toolResult",
            "toolCallId": "call-1",
            "toolName": "bash",
            "content": [{"type": "text", "text": complete_output}],
            "isError": False,
            "details": {"exitCode": 0, "trace": {"outcome": "success"}},
            "timestamp": 1_767_225_604_000,
        },
    }
    orphan_result = {
        "type": "message",
        "timestamp": "2026-01-01T00:00:04.500Z",
        "message": {
            "role": "toolResult",
            "toolCallId": "missing-call",
            "toolName": "provider_tool",
            "content": [{"type": "text", "text": "orphan output"}],
            "isError": True,
            "details": {"providerTrace": "retained"},
            "timestamp": 1_767_225_604_500,
        },
    }
    second_assistant = _assistant_turn(
        [{"type": "text", "text": "The focused test passes."}],
        ts="2026-01-01T00:00:05.000Z",
        usage={"input": 300, "output": 20, "totalTokens": 320, "cost": {"total": 0.01}},
    )
    second_assistant["timestamp"] = "2026-01-01T00:00:05.000Z"
    _write_session(
        result.parent / "session" / "s.jsonl",
        [
            {
                "type": "model_change",
                "provider": "provider",
                "modelId": "model-a",
                "timestamp": "2026-01-01T00:00:00.500Z",
            },
            {
                "type": "thinking_level_change",
                "thinkingLevel": "high",
                "timestamp": "2026-01-01T00:00:00.600Z",
            },
            {
                "type": "message",
                "timestamp": "2026-01-01T00:00:01.000Z",
                "message": {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Implement the requested behavior."}
                    ],
                },
            },
            first_assistant,
            tool_result,
            orphan_result,
            second_assistant,
        ],
    )

    first_page = run_dashboard.load_cell_trajectory(
        str(result),
        offset=0,
        limit=1,
        repo_root=tmp_path,
        state_root=tmp_path / "results" / "_runs",
    )

    assert first_page["found"] is True
    assert first_page["total_turns"] == 2
    assert first_page["offset"] == 0
    assert first_page["has_previous"] is False
    assert first_page["has_next"] is True
    assert first_page["prompt"] == "Implement the requested behavior."
    assert first_page["cell"]["task"] == "task-a"
    assert first_page["session"]["model"] == "model-a"
    assert first_page["session"]["thinking_level"] == "high"
    assert len(first_page["metrics"]) == 2
    assert first_page["metrics"][0]["context_tokens"] == 300
    assert first_page["metrics"][0]["output_tokens"] == 40
    assert first_page["metrics"][0]["observation_chars"] == len(complete_output) + len(
        "orphan output"
    )
    assert first_page["metrics"][0]["command_time_ms"] == 2_000

    turn = first_page["turns"][0]
    assert turn["idx"] == 1
    assert turn["blocks"][0] == {
        "type": "thinking",
        "text": "Inspect the implementation in full.",
    }
    assert turn["blocks"][1] == {
        "type": "text",
        "text": "I will run the focused test.",
    }
    call = turn["blocks"][2]
    assert call["type"] == "tool_call"
    assert call["name"] == "bash"
    assert call["arguments"] == {"command": "pytest -q tests/test_feature.py"}
    assert call["result"]["text"] == complete_output
    assert call["result"]["is_error"] is False
    assert call["result"]["details"] == {
        "exitCode": 0,
        "trace": {"outcome": "success"},
    }
    assert turn["blocks"][3] == {
        "type": "unknown",
        "data": {"type": "provider_meta", "payload": {"retained": "exactly"}},
    }
    assert turn["blocks"][4]["type"] == "tool_result"
    assert turn["blocks"][4]["id"] == "missing-call"
    assert turn["blocks"][4]["text"] == "orphan output"
    assert turn["blocks"][4]["is_error"] is True
    assert turn["blocks"][4]["details"] == {"providerTrace": "retained"}

    second_page = run_dashboard.load_cell_trajectory(
        str(result),
        offset=1,
        limit=1,
        repo_root=tmp_path,
        state_root=tmp_path / "results" / "_runs",
    )
    assert second_page["has_previous"] is True
    assert second_page["has_next"] is False
    assert second_page["turns"][0]["idx"] == 2
    assert second_page["turns"][0]["blocks"][0]["text"] == "The focused test passes."


def test_cell_trajectory_inventories_artifacts_and_verifier_summary(tmp_path):
    result = (
        tmp_path
        / "results"
        / "m"
        / "high"
        / "cfg"
        / "task-a"
        / "rep0"
        / "result.json"
    )
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(json.dumps({"task": "task-a", "reward_binary": 0}))
    _write_session(
        result.parent / "session" / "s.jsonl",
        [_assistant_turn([{"type": "text", "text": "Done."}])],
    )
    patch = result.parent / "artifacts" / "model.patch"
    patch.parent.mkdir()
    patch.write_text("diff --git a/a.py b/a.py\n")
    log = result.parent / "logs" / "verifier.stdout.txt"
    log.parent.mkdir()
    log.write_text("verifier output\n")
    ctrf = result.parent / "verifier" / "ctrf.json"
    ctrf.parent.mkdir()
    ctrf.write_text(
        json.dumps(
            {
                "results": {
                    "summary": {
                        "tests": 3,
                        "passed": 2,
                        "failed": 1,
                        "skipped": 0,
                        "pending": 0,
                        "other": 0,
                    }
                }
            }
        )
    )

    trajectory = run_dashboard.load_cell_trajectory(
        str(result),
        repo_root=tmp_path,
        state_root=tmp_path / "results" / "_runs",
    )

    artifacts = {item["relative_path"]: item for item in trajectory["artifacts"]}
    assert artifacts["artifacts/model.patch"]["kind"] == "patch"
    assert artifacts["logs/verifier.stdout.txt"]["kind"] == "log"
    assert artifacts["verifier/ctrf.json"]["kind"] == "tests"
    assert artifacts["session/s.jsonl"]["kind"] == "session"
    assert artifacts["artifacts/model.patch"]["size"] == len(patch.read_bytes())
    assert trajectory["test_summary"] == {
        "tests": 3,
        "passed": 2,
        "failed": 1,
        "skipped": 0,
        "pending": 0,
        "other": 0,
    }


def test_cell_session_native_pi_extracts_tools_and_intent(tmp_path):
    result = tmp_path / "results" / "m" / "h" / "c" / "task" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("{}")
    _write_session(
        result.parent / "session" / "s.jsonl",
        [
            _assistant_turn(
                [
                    {
                        "type": "thinking",
                        "thinking": "**Reading the main module** to understand it",
                    },
                    {
                        "type": "toolCall",
                        "id": "1",
                        "name": "read",
                        "arguments": {"path": "src/main.go"},
                    },
                    {
                        "type": "toolCall",
                        "id": "2",
                        "name": "bash",
                        "arguments": {"command": "go test ./..."},
                    },
                ]
            ),
            _assistant_turn(
                [{"type": "text", "text": "Done."}],
                usage={"totalTokens": 50, "cost": {"total": 0.005}},
            ),
        ],
    )
    run_dashboard._SESSION_CACHE.clear()
    out = run_dashboard.load_cell_session(
        str(result), repo_root=tmp_path, state_root=tmp_path / "results" / "_runs"
    )
    assert out["found"] is True
    assert out["turns"] == 2
    assert set(out["distinct_tools"]) == {"read", "bash"}
    # last_intent reflects the most recent turn (the final summary text).
    assert out["last_intent"] == "Done."
    first = out["turns_list"][0]
    assert first["intent"] == "Reading the main module to understand it"
    assert first["tools"] == ["read", "bash"]
    assert first["targets"] == ["src/main.go", "go test ./..."]


def test_cell_session_counts_native_tool_call_errors(tmp_path):
    result = tmp_path / "results" / "m" / "h" / "c" / "task" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("{}")
    _write_session(
        result.parent / "session" / "s.jsonl",
        [
            _tool_result("read", is_error=False),
            _tool_result("bash", is_error=True),
        ],
    )
    run_dashboard._SESSION_CACHE.clear()
    out = run_dashboard.load_cell_session(
        str(result), repo_root=tmp_path, state_root=tmp_path / "results" / "_runs"
    )
    assert out["tool_calls"] == 2
    assert out["tool_call_errors"] == 1
    assert out["tool_call_error_rate"] == 0.5


def test_cell_session_counts_fabric_inner_operation_errors(tmp_path):
    result = tmp_path / "results" / "m" / "h" / "c" / "task" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("{}")
    details = {
        "success": True,
        "trace": {
            "operations": [
                {"type": "call", "ref": "pi.read", "outcome": "succeeded"},
                {"type": "call", "ref": "pi.bash", "outcome": "failed"},
                {"type": "call", "ref": "pi.grep", "outcome": "aborted"},
            ]
        },
    }
    _write_session(
        result.parent / "session" / "s.jsonl",
        [_tool_result("fabric_exec", is_error=False, details=details)],
    )
    run_dashboard._SESSION_CACHE.clear()
    out = run_dashboard.load_cell_session(
        str(result), repo_root=tmp_path, state_root=tmp_path / "results" / "_runs"
    )
    assert out["tool_calls"] == 3
    assert out["tool_call_errors"] == 2
    assert abs(out["tool_call_error_rate"] - 2 / 3) < 1e-4


def test_cell_session_fabric_exec_unwraps_inner_tools(tmp_path):
    result = tmp_path / "results" / "m" / "h" / "c" / "task" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("{}")
    code = (
        "const r = await Promise.all([\n"
        "  pi.bash({cmd:'git status --short'}),\n"
        "  pi.grep({pattern:'TODO', path:'src'}),\n"
        "  pi.read({path:'config.yml'})\n"
        "]);"
    )
    _write_session(
        result.parent / "session" / "s.jsonl",
        [
            _assistant_turn(
                [
                    {"type": "thinking", "thinking": "Surveying the repo"},
                    {
                        "type": "toolCall",
                        "id": "1",
                        "name": "fabric_exec",
                        "arguments": {"code": code},
                    },
                ]
            ),
        ],
    )
    run_dashboard._SESSION_CACHE.clear()
    out = run_dashboard.load_cell_session(
        str(result), repo_root=tmp_path, state_root=tmp_path / "results" / "_runs"
    )
    assert out["turns"] == 1
    assert set(out["distinct_tools"]) == {"bash", "grep", "read"}
    turn = out["turns_list"][0]
    assert turn["tools"] == ["bash", "grep", "read"]
    assert "src" in turn["targets"]
    assert "config.yml" in turn["targets"]


def test_cell_session_not_found(tmp_path):
    result = tmp_path / "results" / "m" / "h" / "c" / "task" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("{}")
    out = run_dashboard.load_cell_session(
        str(result), repo_root=tmp_path, state_root=tmp_path / "results" / "_runs"
    )
    assert out["found"] is False


def test_cell_session_cache_respects_requested_tail_turns(tmp_path):
    result = tmp_path / "results" / "m" / "h" / "c" / "task" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("{}")
    _write_session(
        result.parent / "session" / "s.jsonl",
        [
            _assistant_turn([{"type": "thinking", "thinking": "first"}]),
            _assistant_turn([{"type": "thinking", "thinking": "second"}]),
            _assistant_turn([{"type": "thinking", "thinking": "third"}]),
        ],
    )
    run_dashboard._SESSION_CACHE.clear()

    compact = run_dashboard.load_cell_session(
        str(result),
        tail_turns=1,
        repo_root=tmp_path,
        state_root=tmp_path / "results" / "_runs",
    )
    expanded = run_dashboard.load_cell_session(
        str(result),
        tail_turns=3,
        repo_root=tmp_path,
        state_root=tmp_path / "results" / "_runs",
    )

    assert [turn["intent"] for turn in compact["turns_list"]] == ["third"]
    assert [turn["intent"] for turn in expanded["turns_list"]] == [
        "first",
        "second",
        "third",
    ]
    assert expanded["truncated"] is False


def test_cell_session_cache_invalidates_on_mtime(tmp_path):
    import os
    import time as _time

    result = tmp_path / "results" / "m" / "h" / "c" / "task" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("{}")
    p = result.parent / "session" / "s.jsonl"
    _write_session(p, [_assistant_turn([{"type": "thinking", "thinking": "first"}])])
    run_dashboard._SESSION_CACHE.clear()
    first = run_dashboard.load_cell_session(
        str(result), repo_root=tmp_path, state_root=tmp_path / "results" / "_runs"
    )
    assert first["turns"] == 1
    _write_session(
        p,
        [
            _assistant_turn([{"type": "thinking", "thinking": "first"}]),
            _assistant_turn([{"type": "thinking", "thinking": "second"}]),
        ],
    )
    future = _time.time() + 5
    os.utime(p, (future, future))
    second = run_dashboard.load_cell_session(
        str(result),
        repo_root=tmp_path,
        state_root=tmp_path / "results" / "_runs",
        now_ts=future + 1,
    )
    assert second["turns"] == 2
    assert second["last_intent"] == "second"


def test_http_api_cell_session_endpoint(tmp_path):
    result = tmp_path / "results" / "m" / "h" / "c" / "task" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("{}")
    _write_session(
        result.parent / "session" / "s.jsonl",
        [
            _assistant_turn([{"type": "thinking", "thinking": "hello"}]),
        ],
    )
    run_dashboard._SESSION_CACHE.clear()
    server = run_dashboard.make_server(
        host="127.0.0.1",
        port=0,
        state_root=tmp_path / "results" / "_runs",
        detail="summary",
        repo_root=tmp_path,
        legacy_root=tmp_path / "runs",
        results_root=tmp_path / "results",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        rel = "results/m/h/c/task/rep0/result.json"
        with urllib.request.urlopen(
            f"{base}/api/cell-session?path={rel}&tail=5", timeout=5
        ) as r:
            session = json.loads(r.read().decode("utf-8"))["session"]
        assert session["found"] is True
        assert session["turns"] == 1
        assert session["last_intent"] == "hello"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_api_cell_trajectory_endpoint_paginates(tmp_path):
    result = tmp_path / "results" / "m" / "h" / "c" / "task" / "rep0" / "result.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(json.dumps({"task": "task", "config": "c", "rep": 0}))
    _write_session(
        result.parent / "session" / "s.jsonl",
        [
            _assistant_turn([{"type": "text", "text": "first"}]),
            _assistant_turn([{"type": "text", "text": "second"}]),
        ],
    )
    server = run_dashboard.make_server(
        host="127.0.0.1",
        port=0,
        state_root=tmp_path / "results" / "_runs",
        detail="summary",
        repo_root=tmp_path,
        legacy_root=tmp_path / "runs",
        results_root=tmp_path / "results",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        rel = urllib.parse.quote("results/m/h/c/task/rep0/result.json")
        with urllib.request.urlopen(
            f"{base}/api/cell-trajectory?path={rel}&offset=1&limit=1",
            timeout=5,
        ) as response:
            trajectory = json.loads(response.read().decode("utf-8"))["trajectory"]
        assert trajectory["total_turns"] == 2
        assert trajectory["turns"][0]["idx"] == 2
        assert trajectory["has_previous"] is True
        assert trajectory["has_next"] is False

        with urllib.request.urlopen(
            f"{base}/api/cell-trajectory?path={rel}&offset=latest&limit=1",
            timeout=5,
        ) as response:
            latest = json.loads(response.read().decode("utf-8"))["trajectory"]
        assert latest["offset"] == 1
        assert latest["turns"][0]["idx"] == 2
        assert latest["has_previous"] is True
        assert latest["has_next"] is False

        with urllib.request.urlopen(
            f"{base}/api/file?path={rel}&download=1",
            timeout=5,
        ) as response:
            downloaded = response.read()
            disposition = response.headers["Content-Disposition"]
        assert downloaded == result.read_bytes()
        assert disposition == "attachment; filename*=UTF-8''result.json"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_api_cell_trajectory_allows_launch_worktree_preflight_result(tmp_path):
    dashboard_repo = tmp_path / "dashboard-repo"
    state_root = dashboard_repo / "results" / "_runs"
    launch_workspace = tmp_path / "launch-worktree"
    result = (
        launch_workspace
        / "results"
        / "model"
        / "high"
        / "cfg"
        / "smoke-task"
        / "rep0"
        / "result.json"
    )
    result.parent.mkdir(parents=True)
    result.write_text(json.dumps({"task": "smoke-task", "config": "cfg", "rep": 0}))
    _write_session(
        result.parent / "session" / "s.jsonl",
        [_assistant_turn([{"type": "text", "text": "preflight work"}])],
    )

    run_dir = state_root / "worktree-preflight--planhash"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": "worktree-preflight"}))
    (run_dir / "launch-plan.json").write_text(
        json.dumps(
            {
                "runId": "worktree-preflight",
                "paths": {
                    "resultsRoot": str(launch_workspace / "results"),
                    "statePath": str(run_dir),
                    "stateRoot": str(state_root),
                    "workspace": str(launch_workspace),
                },
            }
        )
    )

    undeclared_result = tmp_path / "undeclared-results" / "result.json"
    undeclared_result.parent.mkdir()
    undeclared_result.write_text("{}")
    _write_session(
        undeclared_result.parent / "session" / "s.jsonl",
        [_assistant_turn([{"type": "text", "text": "must stay private"}])],
    )
    unattributed_run_dir = state_root / "unattributed-plan"
    unattributed_run_dir.mkdir()
    (unattributed_run_dir / "launch-plan.json").write_text(
        json.dumps(
            {
                "runId": "unattributed-plan",
                "paths": {
                    "resultsRoot": str(undeclared_result.parent),
                    "statePath": str(unattributed_run_dir),
                },
            }
        )
    )

    server = run_dashboard.make_server(
        host="127.0.0.1",
        port=0,
        state_root=state_root,
        detail="summary",
        repo_root=dashboard_repo,
        legacy_root=dashboard_repo / "runs",
        results_root=dashboard_repo / "results",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        declared_query = urllib.parse.urlencode({"path": str(result)})
        with urllib.request.urlopen(
            f"{base}/api/cell-trajectory?{declared_query}", timeout=5
        ) as response:
            trajectory = json.loads(response.read().decode("utf-8"))["trajectory"]
        assert trajectory["found"] is True
        assert trajectory["turns"][0]["blocks"][0]["text"] == "preflight work"

        undeclared_query = urllib.parse.urlencode({"path": str(undeclared_result)})
        with urllib.request.urlopen(
            f"{base}/api/cell-trajectory?{undeclared_query}", timeout=5
        ) as response:
            blocked = json.loads(response.read().decode("utf-8"))["trajectory"]
        assert blocked == {
            "found": False,
            "error": "path outside dashboard allowlist",
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_stale_running_run_is_reclassified_as_stalled(tmp_path):
    """A run whose heartbeat went stale was abandoned; project it as 'stalled',
    not 'running', while preserving the declared state for transparency."""
    from datetime import UTC, datetime, timedelta

    state_root = tmp_path / "results" / "_runs"
    run_dir = state_root / "abandoned"
    run_dir.mkdir(parents=True)
    old = (datetime.now(UTC) - timedelta(hours=2)).isoformat(timespec="seconds")
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": "abandoned", "progress_interval_s": 15})
    )
    (run_dir / "status.json").write_text(
        json.dumps(
            {
                "run_id": "abandoned",
                "state": "running",
                "heartbeat_at": old,
                "cells": {},
                "active_cell_ids": [],
            }
        )
    )
    proj = run_dashboard.load_dashboard_run(
        "abandoned", state_root, detail="summary", legacy_root=None
    )
    assert proj is not None
    assert proj["state"] == "stalled"
    assert proj["declared_state"] == "running"


def test_http_api_subsets_and_compare_subset(tmp_path):
    """The /api/subsets and /api/compare?subset= endpoints serve filtered data."""
    state_root = make_state(tmp_path, "dash-test")
    # add a subset file under repo_root/subsets
    (tmp_path / "subsets").mkdir()
    (tmp_path / "subsets" / "mini.txt").write_text("task-a\n")
    server = run_dashboard.make_server(
        host="127.0.0.1",
        port=0,
        state_root=state_root,
        detail="summary",
        repo_root=tmp_path,
        legacy_root=tmp_path / "runs",
        results_root=tmp_path / "results",
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
