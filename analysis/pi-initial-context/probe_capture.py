#!/usr/bin/env python3
"""Capture Pi/OMP initial instruction surface for a few DeepSWE tasks without grading.

This launches the same task container setup as the benchmark runners, loads the
initial-context capture extension, asks it to stop at before_agent_start, and
saves the generated system prompt/options/user prompt under analysis artifacts.
It intentionally skips patch extraction, verifier execution, and result.json.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "harness"))

from lib import load_task, model_leaf  # noqa: E402
from pi_rpc_runner import run_pi_rpc  # noqa: E402
from run import (  # noqa: E402
    agent_auth_mount,
    ensure_env_image,
    ensure_pi_image,
    initial_context_capture_mount,
    load_config,
    config_append_text,
    pi_cmd,
    sh,
)
from run_omp import (  # noqa: E402
    create_filtered_omp_agent_db,
    omp_binary,
    omp_cmd,
    omp_overlay_in_container,
    render_omp_system_prompt,
    resolve_omp_extensions,
    resolve_omp_tools,
)

DEFAULT_MODEL = "openai-codex/gpt-5.5"
DEFAULT_THINKING = "low"
DEFAULT_AGENTS = ["pi", "omp"]
DEFAULT_TASKS = [
    "participle-grammar-conflict-analysis",
    "updo-policy-alerting",
    "tengo-destructuring-bindings",
]


def timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def append_text(config: str, model: str, thinking: str) -> tuple[dict, str]:
    cfg = load_config(config, model, thinking)
    return cfg, config_append_text(cfg)


def write_task_public(task_id: str) -> str:
    task = load_task(task_id)
    task_public = tempfile.mkdtemp(prefix="dsw-task-public-")
    shutil.copy2(task.dir / "instruction.md", Path(task_public) / "instruction.md")
    shutil.copy2(task.dir / "pre_artifacts.sh", Path(task_public) / "pre_artifacts.sh")
    return task_public


def docker_env_for_capture(stop_after: str) -> list[str]:
    max_provider_requests = "1" if stop_after == "before_provider_request" else "0"
    env = [
        "-e", "PI_INITIAL_CONTEXT_DIR=/out/initial_context",
        "-e", f"PI_INITIAL_CONTEXT_STOP_AFTER={stop_after}",
        "-e", "PI_INITIAL_CONTEXT_MAX_CONTEXTS=0",
        "-e", f"PI_INITIAL_CONTEXT_MAX_PROVIDER_REQUESTS={max_provider_requests}",
    ]
    return env


def run_probe_cell(*, agent: str, config: str, task_id: str, model: str, thinking: str,
                   out_root: Path, timeout_s: float, stop_after: str) -> dict:
    task = load_task(task_id)
    cfg, app = append_text(config, model, thinking)
    ensure_env_image(task.env_image)
    image = ensure_pi_image(task)
    cell = out_root / agent / config / task_id
    cell.mkdir(parents=True, exist_ok=True)
    (cell / "logs").mkdir(exist_ok=True)
    task_public = write_task_public(task_id)
    auth_tmp: str | None = None
    auth_mount: list[str] = []
    cname = f"dsw-initctx-{agent}-{task_id}-{os.getpid()}"
    env_flag = docker_env_for_capture(stop_after)
    mounts = [
        "-v", f"{task_public}:/task:ro",
        "-v", f"{cell}:/out",
        "-v", f"{cfg['dir']}:/arm:ro",
        *initial_context_capture_mount(True),
    ]

    if agent == "pi":
        auth_mount, auth_tmp = agent_auth_mount(
            pass_openai_codex_oauth=model.startswith("openai-codex/"),
            pass_openrouter_env=False,
        )
        mounts += auth_mount
        cmd = pi_cmd(cfg, model, thinking, app, capture_initial_context=True)
        exec_prefix = ["docker", "exec", "-i", cname]
    elif agent == "omp":
        tools = resolve_omp_tools(cfg["dir"])
        overlay = omp_overlay_in_container(cfg["dir"])
        system_prompt = render_omp_system_prompt(cfg["dir"])
        omp_extensions = resolve_omp_extensions(cfg["dir"])
        auth_tmp = tempfile.mkdtemp(prefix="dsw-omp-auth-")
        create_filtered_omp_agent_db(Path(auth_tmp) / "agent" / "agent.db")
        omp_path = omp_binary()
        mounts += [
            "-v", f"{omp_path}:/usr/local/bin/omp:ro",
            "-v", f"{Path(auth_tmp) / 'agent'}:/root/.omp/agent",
        ]
        env_flag += ["-e", "PI_CODING_AGENT_DIR=/root/.omp/agent"]
        if omp_extensions:
            env_flag += [
                "-e", "OMP_PROJECT_MESSAGE_STRIP_DIR=/out/omp_project_message_strip",
                "-e", f"OMP_ALLOWED_TOOLS={tools}",
            ]
        cmd = omp_cmd(model, thinking, app, tools, overlay, capture_initial_context=True,
                      system_prompt=system_prompt, extension_paths=omp_extensions)
        exec_prefix = ["docker", "exec", "-i", "-w", "/app", cname]
    else:
        raise ValueError(f"unknown agent: {agent}")

    run_args = [
        "docker", "run", "-d", "--name", cname, "--platform", "linux/amd64",
        "-w", "/app",
        *mounts,
        *env_flag,
        image,
        "sleep", str(int(timeout_s + 120)),
    ]
    started = time.time()
    r = sh(run_args)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:1000])
    try:
        if agent == "pi" and (
            auth_mount
            or cfg.get("advisor_json")
            or cfg.get("models_json")
            or cfg.get("settings_json")
        ):
            sh(["docker", "exec", cname, "mkdir", "-p", "/root/.pi/agent"])
            if auth_mount:
                sh(["docker", "exec", cname, "cp", "/agent-auth/auth.json", "/root/.pi/agent/auth.json"])
            if cfg.get("advisor_json"):
                sh([
                    "docker", "exec", cname, "cp",
                    f"/arm/{cfg['leaf_rel']}/advisor.json",
                    "/root/.pi/agent/advisor.json",
                ])
            if cfg.get("models_json"):
                sh([
                    "docker", "exec", cname, "cp",
                    f"/arm/{cfg['leaf_rel']}/models.json",
                    "/root/.pi/agent/models.json",
                ])
            if cfg.get("settings_json"):
                sh([
                    "docker", "exec", cname, "cp",
                    f"/arm/{cfg['leaf_rel']}/settings.json",
                    "/root/.pi/agent/settings.json",
                ])
        rpc = run_pi_rpc(
            [*exec_prefix, *cmd],
            prompt_text=(Path(task_public) / "instruction.md").read_text(),
            stderr_path=cell / "logs" / f"{agent}.stderr.txt",
            runner_log_path=cell / "logs" / "pi-rpc-runner.jsonl",
            timeout_s=timeout_s,
            quiescence_s=0.25,
            state_poll_s=0.05,
            quiesce_after_agent_end=True,
        )
        elapsed = round(time.time() - started, 2)
    finally:
        sh(["docker", "rm", "-f", cname])
        shutil.rmtree(task_public, ignore_errors=True)
        if auth_tmp:
            shutil.rmtree(auth_tmp, ignore_errors=True)

    initial = cell / "initial_context"
    artifacts = sorted(p.name for p in initial.glob("*")) if initial.exists() else []
    provider_requests = [name for name in artifacts if name.startswith("provider_request_")]
    rec = {
        "agent": agent,
        "config": config,
        "task": task_id,
        "model": model,
        "thinking": thinking,
        "elapsed_s": elapsed,
        "rpc_exit_code": rpc.exit_code,
        "rpc_timed_out": rpc.timed_out,
        "initial_context_dir": str(initial.relative_to(out_root)),
        "artifacts": artifacts,
        "provider_request_count": len(provider_requests),
        "system_prompt_bytes": (initial / "system_prompt.txt").stat().st_size if (initial / "system_prompt.txt").exists() else 0,
        "user_prompt_bytes": (initial / "user_prompt.txt").stat().st_size if (initial / "user_prompt.txt").exists() else 0,
    }
    (cell / "probe_result.json").write_text(json.dumps(rec, indent=2))
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=",".join(DEFAULT_TASKS), help="comma-list of task ids")
    ap.add_argument("--agents", default=",".join(DEFAULT_AGENTS), help="comma-list: pi,omp")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--thinking", default=DEFAULT_THINKING)
    ap.add_argument("--pi-config", default="baseline")
    ap.add_argument("--omp-config", default="baseline-omp")
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--stop-after", choices=["before_agent_start", "before_provider_request"],
                    default="before_agent_start")
    args = ap.parse_args()

    tasks = [x.strip() for x in args.tasks.split(",") if x.strip()]
    agents = [x.strip() for x in args.agents.split(",") if x.strip()]
    out_root = args.out or (Path(__file__).resolve().parent / "probes" / f"{timestamp_id()}-{model_leaf(args.model)}-{args.thinking}")
    out_root = out_root.resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    records = []
    for task in tasks:
        for agent in agents:
            config = args.pi_config if agent == "pi" else args.omp_config
            print(f"[probe] {agent}/{config}/{task}", flush=True)
            records.append(run_probe_cell(
                agent=agent,
                config=config,
                task_id=task,
                model=args.model,
                thinking=args.thinking,
                out_root=out_root,
                timeout_s=args.timeout,
                stop_after=args.stop_after,
            ))
    (out_root / "manifest.json").write_text(json.dumps({
        "model": args.model,
        "thinking": args.thinking,
        "tasks": tasks,
        "agents": agents,
        "stop_after": args.stop_after,
        "records": records,
    }, indent=2))
    print(out_root)


if __name__ == "__main__":
    main()
