import json
from pathlib import Path

from harness.run_state import (
    RunStateWriter,
    base_manifest,
    classify_result,
    make_cell,
    project_structured_run,
)


def write_result(path: Path, **overrides) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "agent_exit": 0,
        "verifier_exit": 0,
        "agent_timed_out": False,
        "reward_partial": 0.7,
        "reward_binary": 0,
        "patch_bytes": 123,
        "agent_wall_s": 12.5,
        "total_tokens": 456,
        "cost_usd": 0.01,
    }
    record.update(overrides)
    path.write_text(json.dumps(record))
    return path


def test_classify_result_matches_progress_labels():
    assert classify_result({"agent_exit": 0, "verifier_exit": 0}) == "ok"
    assert classify_result({"agent_exit": 0, "verifier_exit": "skipped_empty_patch"}) == "empty"
    assert classify_result({"agent_exit": 0, "verifier_exit": 0, "agent_timed_out": True}) == "timeout"
    assert classify_result({"agent_exit": 75, "transient_model_error": True}) == "transient"
    assert classify_result({"agent_exit": 2, "verifier_exit": None}) == "exit=2"


def test_run_state_writer_keeps_preflight_and_batch_counts_separate(tmp_path):
    state_root = tmp_path / "results" / "_runs"
    result = write_result(tmp_path / "results" / "model" / "high" / "cfg" / "task-a" / "rep0" / "result.json")
    log = tmp_path / "results" / "model" / "high" / "logs" / "task-a__cfg__rep0.log"
    log.parent.mkdir(parents=True)
    log.write_text("compact log path only")
    batch_cell = make_cell(task="task-a", config="cfg", rep=0, result_path=result, log_path=log)
    preflight_cell = make_cell(task="task-a", config="cfg", rep=0, result_path=result, log_path=log)
    manifest = base_manifest(
        run_id="state-test",
        command=["python3", "harness/run_batch.py"],
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
        batch_cells=[batch_cell],
        preflight=[preflight_cell],
    )

    writer = RunStateWriter(state_root, manifest)
    writer.start()
    writer.preflight_skipped(preflight_cell, reason="existing_results")
    midway = json.loads((state_root / "state-test" / "status.json").read_text())
    assert midway["counts"]["preflight_done"] == 1
    assert midway["counts"]["batch_done"] == 0

    writer.cell_started(batch_cell)
    writer.cell_finished(batch_cell, result_path=result, log_path=log, exit_code=0)
    writer.run_completed()

    run_dir = state_root / "state-test"
    status = json.loads((run_dir / "status.json").read_text())
    assert status["state"] == "completed"
    assert status["counts"]["batch_total"] == 1
    assert status["counts"]["batch_done"] == 1
    assert status["counts"]["ok"] == 1
    assert status["counts"]["preflight_total"] == 1
    assert status["counts"]["preflight_done"] == 1
    cell = status["cells"]["task-a/cfg/rep0"]
    assert cell["summary"]["reward_partial"] == 0.7
    assert cell["summary"]["total_tokens"] == 456

    events = [json.loads(line) for line in (run_dir / "events.ndjson").read_text().splitlines()]
    assert [event["event"] for event in events] == [
        "run_started",
        "preflight_skipped",
        "cell_started",
        "cell_finished",
        "run_completed",
    ]
    assert all("seq" in event for event in events)


def test_project_structured_run_detail_levels_do_not_inline_logs(tmp_path):
    state_root = tmp_path / "results" / "_runs"
    result = write_result(tmp_path / "result.json")
    log = tmp_path / "huge.log"
    log.write_text("SECRET RAW LOG\n" * 20)
    cell = make_cell(task="task-a", config="cfg", rep=0, result_path=result, log_path=log)
    manifest = base_manifest(
        run_id="detail-test",
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

    summary = project_structured_run(state_root / "detail-test", detail="summary")
    operational = project_structured_run(state_root / "detail-test", detail="operational")
    diagnostic = project_structured_run(state_root / "detail-test", detail="diagnostic")

    assert "active_cells" not in summary
    assert "status" not in summary
    assert "recent_finished" in operational
    assert "status" not in operational
    assert "status" in diagnostic
    assert "events_tail" in diagnostic
    assert "SECRET RAW LOG" not in json.dumps(operational)
