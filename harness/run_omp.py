#!/usr/bin/env python3
"""Run one DeepSWE cell with OMP instead of Pi.

This runner intentionally mirrors ``harness/run.py`` for sandbox setup,
patch capture, verifier execution, usage parsing, and result.json shape. The
only executor difference is the command inside the task container: ``omp`` in
RPC mode with skills/extensions/rules disabled and a restricted basic tool set.
Direct CLI use is a draft probe and requires scratch ``--probe-output``.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import parse_usage  # noqa: E402
import results_tree  # noqa: E402
from container_resources import (  # noqa: E402
    container_memory_result_fields,
    inspect_docker_container_oom,
    managed_container_start_guard,
    planned_container_resource_docker_args,
    record_subject_container_memory_status,
    run_managed_container_and_wait,
    verifier_container_memory_status,
    verifier_memory_events_shell_args,
)
from lib import (  # noqa: E402
    REPO,
    load_task,
    read_reward,
    result_record,
    subject_container_name,
)
from pi_rpc_runner import run_pi_rpc  # noqa: E402
from run import (  # noqa: E402
    TRANSIENT_EXIT,
    compact_verifier_stdout,
    config_append_text,
    credential_route_env_flags,
    ensure_env_image,
    ensure_pi_image,
    ensure_verifier_image,
    initial_context_capture_env,
    initial_context_capture_flags,
    initial_context_capture_mount,
    load_config,
    load_resolved_config,
    require_draft_probe_output,
    require_explicit_cell_output,
    sh,
    strip_patch_paths,
    transient_model_error,
)

DEFAULT_MODEL = "openai-codex/gpt-5.5"
DEFAULT_THINKING = "low"
OMP_BASIC_TOOLS = "read,bash,edit,write,grep,glob"
# Tool ids OMP accepts in its --tools enable-whitelist (from `omp --help` + binary
# strings). ast_grep / ast_edit are config-gated by astGrep.enabled / astEdit.enabled
# (both default true) but still must be listed in --tools to be enabled.
OMP_KNOWN_TOOLS = {
    "read", "bash", "edit", "write", "grep", "glob",
    "ast_grep", "ast_edit", "lsp", "python", "notebook",
    "inspect_image", "browser", "task", "todo", "web_search", "ask",
}


def resolve_omp_tools(config_dir: Path) -> str:
    """Resolve the OMP --tools whitelist for a config.

    Reads ``<config>/omp-tools.txt`` (comma- or newline-separated tool ids).
    Falls back to ``OMP_BASIC_TOOLS`` when absent. Validates every id against
    ``OMP_KNOWN_TOOLS`` so a typo fails fast instead of silently disabling a tool.
    """
    f = config_dir / "omp-tools.txt"
    if f.exists():
        tools = []
        for line in f.read_text().splitlines():
            line = line.split("#", 1)[0].strip()  # strip inline comments
            tools.extend(t.strip() for t in line.split(",") if t.strip())
    else:
        tools = OMP_BASIC_TOOLS.split(",")
    unknown = [t for t in tools if t not in OMP_KNOWN_TOOLS]
    if unknown:
        sys.exit(f"[omp] unknown tool id(s) in {f}: {unknown}. "
                 f"Known: {sorted(OMP_KNOWN_TOOLS)}")
    if not tools:
        sys.exit(f"[omp] empty tool list in {f}")
    return ",".join(tools)


def omp_overlay_in_container(config_dir: Path) -> str | None:
    """Return the in-container path of the config's OMP config overlay, or None.

    The config dir is mounted read-only at ``/arm`` (see run_cell), so an
    ``omp-overlay.yml`` there is reachable at ``/arm/omp-overlay.yml`` and passed
    to omp via ``--config``. Use it to pin OMP settings per config (e.g.
    ``bashInterceptor.enabled`` or ``astGrep.enabled``).
    """
    return "/arm/omp-overlay.yml" if (config_dir / "omp-overlay.yml").exists() else None


def render_omp_system_prompt_template(template: str) -> str:
    """Render approved OMP date and working-directory template variables."""
    return template.replace(
        "{{current_date}}",
        date.today().isoformat(),
    ).replace("{{cwd}}", "/app")


def render_omp_system_prompt(config_dir: Path) -> str | None:
    """Return a config-local OMP system prompt override, if present.

    ``omp-system-prompt.md`` is intentionally OMP-only: Pi configs use
    ``system_preamble.md``/``orchestration.md`` as append layers.  The few
    template variables here keep Pi-like prompts date/cwd-correct without
    allowing arbitrary prompt generation.
    """
    path = config_dir / "omp-system-prompt.md"
    if not path.exists():
        return None
    return render_omp_system_prompt_template(path.read_text())


def resolve_omp_extensions(config_dir: Path) -> list[str]:
    """Resolve config-local OMP extension paths listed in omp-extensions.txt.

    Paths are relative to the config root mounted at /arm inside the task
    container. This is separate from Pi ``pi-flags`` so OMP configs can load
    narrow benchmark-normalization instrumentation without pretending it is a Pi
    extension config.
    """
    f = config_dir / "omp-extensions.txt"
    if not f.exists():
        return []
    resolved = []
    for line in f.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        rel = Path(line)
        if rel.is_absolute() or ".." in rel.parts:
            sys.exit(f"[omp] invalid extension path in {f}: {line!r}")
        if not (config_dir / rel).exists():
            sys.exit(f"[omp] extension listed in {f} does not exist: {line}")
        resolved.append(f"/arm/{line}")
    return resolved


def _sqlite_columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in con.execute(f"pragma table_info({table})")]


def create_filtered_omp_agent_db(dst: Path, *, provider: str = "openai-codex") -> None:
    """Create an OMP agent.db containing only the requested auth provider.

    The host OMP profile may contain unrelated provider credentials. Benchmark
    cells should not receive those, so this copies schema/version tables and only
    ``auth_credentials`` rows for the executor provider.
    """
    src = Path.home() / ".omp" / "agent" / "agent.db"
    if not src.exists():
        sys.exit(f"OMP auth db not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    target = sqlite3.connect(dst)
    try:
        for (sql,) in source.execute(
            "select sql from sqlite_master where type='table' and name not like 'sqlite_%' order by name"
        ):
            if sql:
                target.execute(sql)
        for table in ("schema_version", "auth_schema_version"):
            try:
                cols = _sqlite_columns(source, table)
                rows = source.execute(f"select * from {table}").fetchall()
            except sqlite3.Error:
                continue
            if rows:
                placeholders = ",".join("?" for _ in cols)
                target.executemany(f"insert into {table} ({','.join(cols)}) values ({placeholders})", rows)
        cols = _sqlite_columns(source, "auth_credentials")
        rows = source.execute("select * from auth_credentials where provider=?", (provider,)).fetchall()
        if not rows:
            sys.exit(f"OMP auth db has no credential for provider {provider!r}")
        placeholders = ",".join("?" for _ in cols)
        target.executemany(f"insert into auth_credentials ({','.join(cols)}) values ({placeholders})", rows)
        target.commit()
    finally:
        source.close()
        target.close()


def omp_binary() -> Path:
    candidate = os.environ.get("OMP_BINARY") or shutil.which("omp")
    if not candidate:
        sys.exit("omp binary not found on host PATH; set OMP_BINARY=/path/to/omp")
    path = Path(candidate)
    if not path.exists():
        sys.exit(f"omp binary not found: {path}")
    return path


def omp_cmd(model: str, thinking: str, append_text: str, tools: str,
            overlay: str | None = None,
            capture_initial_context: bool = True,
            system_prompt: str | None = None,
            extension_paths: list[str] | None = None) -> list[str]:
    cmd = [
        "omp",
        "--mode", "rpc",
        "--cwd", "/app",
        "--model", model,
        "--thinking", thinking,
        "--session-dir", "/out/session",
        "--no-skills",
        "--no-rules",
        f"--tools={tools}",
        "--no-lsp",
        "--no-pty",
        "--approval-mode", "yolo",
    ]
    if system_prompt is not None:
        cmd += ["--system-prompt", system_prompt]
    if append_text:
        cmd += ["--append-system-prompt", append_text]
    if overlay:
        cmd += ["--config", overlay]
    extension_paths = extension_paths or []
    for path in extension_paths:
        cmd += ["-e", path]
    if capture_initial_context:
        # OMP 16.3.5 help claims explicit -e paths still load with --no-extensions,
        # but live probes show they do not. Omit --no-extensions when any explicit
        # instrumentation/normalization extension is loaded; the benchmark profile
        # is isolated and contains no discovered extensions.
        cmd += initial_context_capture_flags(True)
    elif not extension_paths:
        cmd += ["--no-extensions"]
    return cmd


def run_cell(
    config: str,
    task_id: str,
    *,
    model: str,
    thinking: str,
    rep: int,
    agent_timeout: float | None,
    keep: bool,
    pass_openai_codex_oauth: bool,
    rpc_quiescence: float,
    capture_initial_context: bool = True,
    credential_routes: tuple[str, ...] = (),
    resource_policy: Mapping[str, object] | None = None,
    container_labels: Mapping[str, str] | None = None,
    output_cell: Path | None = None,
    persist_result_file: bool = True,
    persist_result_index: bool = True,
    config_root: Path | None = None,
    config_leaf: Path | None = None,
    task_root: Path | None = None,
    subject_behavior: dict[str, object] | None = None,
    omp_binary_path: Path | None = None,
) -> dict:
    """Execute one OMP subject cell using explicit resolved launch inputs."""
    if not model.startswith("openai-codex/"):
        sys.exit("OMP benchmark runner currently requires explicit openai-codex/<model> model ids")
    if not pass_openai_codex_oauth:
        sys.exit("OMP openai-codex models require --pass-openai-codex-oauth")

    task = load_task(task_id, root=task_root)
    agent_timeout = agent_timeout or task.agent_timeout_s
    if (config_root is None) != (config_leaf is None):
        raise ValueError(
            "Confirmed config paths invalid: config root and leaf must be "
            "provided together"
        )
    cfg = (
        load_resolved_config(config_root, config_leaf)
        if config_root is not None and config_leaf is not None
        else load_config(
            config,
            model,
            thinking,
            repository_root=REPO,
        )
    )
    if subject_behavior is None:
        tools = resolve_omp_tools(cfg["dir"])
        overlay = omp_overlay_in_container(cfg["dir"])
        system_prompt = render_omp_system_prompt(cfg["dir"])
        omp_extensions = resolve_omp_extensions(cfg["dir"])
        append_text = config_append_text(cfg)
    else:
        tool_values = subject_behavior.get("toolWhitelist")
        if not isinstance(tool_values, list):
            raise TypeError(
                "Confirmed OMP behavior invalid: tool whitelist must be a list"
            )
        tools = ",".join(str(tool) for tool in tool_values)
        overlay_value = subject_behavior.get("overlay")
        overlay = str(overlay_value) if overlay_value is not None else None
        system_prompt_value = subject_behavior.get("systemPrompt")
        system_prompt = (
            str(system_prompt_value)
            if system_prompt_value is not None
            else None
        )
        extension_values = subject_behavior.get("extensions", [])
        if not isinstance(extension_values, list):
            raise TypeError(
                "Confirmed OMP behavior invalid: extensions must be a list"
            )
        omp_extensions = [str(path) for path in extension_values]
        append_text = str(subject_behavior.get("appendSystemPrompt", ""))
    if cfg["skill_dirs"]:
        sys.exit("baseline OMP configs must not define skills")
    if cfg["pi_flags"]:
        sys.exit("baseline OMP configs must not define pi-flags/extensions")
    if cfg.get("models_json") or cfg.get("advisor_json") or cfg.get("settings_json"):
        sys.exit("baseline OMP configs must not define model/advisor/settings leaves")

    cell = require_explicit_cell_output(output_cell)
    ensure_env_image(task.env_image)
    agent_image = ensure_pi_image(task)

    cell.mkdir(parents=True, exist_ok=True)
    (cell / "artifacts").mkdir(exist_ok=True)
    (cell / "verifier").mkdir(exist_ok=True)
    (cell / "logs").mkdir(exist_ok=True)
    (cell / "transient_error.json").unlink(missing_ok=True)

    cname = subject_container_name(
        config,
        task_id,
        rep=rep,
        process_id=os.getpid(),
    )

    task_public = tempfile.mkdtemp(prefix="dsw-task-public-")
    auth_tmp = tempfile.mkdtemp(prefix="dsw-omp-auth-")
    shutil.copy2(task.dir / "instruction.md", Path(task_public) / "instruction.md")
    shutil.copy2(task.dir / "pre_artifacts.sh", Path(task_public) / "pre_artifacts.sh")
    create_filtered_omp_agent_db(Path(auth_tmp) / "agent" / "agent.db")
    omp_path = omp_binary_path or omp_binary()

    env_flag = ["-e", "PI_CODING_AGENT_DIR=/root/.omp/agent"]
    for k, v in cfg["env"].items():
        env_flag += ["-e", f"{k}={v}"]
    env_flag += credential_route_env_flags(credential_routes)
    env_flag += initial_context_capture_env(capture_initial_context)
    if omp_extensions:
        env_flag += [
            "-e", "OMP_PROJECT_MESSAGE_STRIP_DIR=/out/omp_project_message_strip",
            "-e", f"OMP_ALLOWED_TOOLS={tools}",
        ]

    print(f"[cell] task={task_id} config={config} lang={task.language} "
          f"budget={agent_timeout:.0f}s agent=omp model={model} thinking={thinking}", flush=True)

    run_args = [
        "docker", "run", "-d", "--name", cname,
        *planned_container_resource_docker_args(
            resource_policy,
            container_labels,
            role="subject",
        ),
        "--platform", "linux/amd64",
        "-w", "/app",
        "-v", f"{task_public}:/task:ro",
        "-v", f"{cell}:/out",
        "-v", f"{cfg['dir']}:/arm:ro",
        *initial_context_capture_mount(capture_initial_context),
        "-v", f"{cell}:/logs",
        "-v", f"{omp_path}:/usr/local/bin/omp:ro",
        "-v", f"{Path(auth_tmp) / 'agent'}:/root/.omp/agent",
        *env_flag,
        agent_image,
        "sleep", str(int(agent_timeout + 600)),
    ]
    with managed_container_start_guard(container_labels):
        r = sh(run_args)
    if r.returncode != 0:
        for d in (auth_tmp, task_public):
            shutil.rmtree(d, ignore_errors=True)
        sys.exit(f"[cell] docker run failed:\n{r.stderr[:800]}")

    started = time.time()
    status: dict = {}
    try:
        version = sh(["docker", "exec", cname, "omp", "--version"])
        (cell / "logs" / "omp-version.txt").write_text(version.stdout + version.stderr)
        status["omp_version"] = (version.stdout + version.stderr).strip()

        pre_session_paths = set((cell / "session").glob("*.jsonl"))
        cmd = omp_cmd(model, thinking, append_text, tools, overlay, capture_initial_context,
                      system_prompt=system_prompt, extension_paths=omp_extensions)
        rpc_result = run_pi_rpc(
            ["docker", "exec", "-i", "-w", "/app", cname, *cmd],
            prompt_text=(Path(task_public) / "instruction.md").read_text(),
            stderr_path=cell / "logs" / "omp.stderr.txt",
            runner_log_path=cell / "logs" / "pi-rpc-runner.jsonl",
            timeout_s=agent_timeout,
            quiescence_s=rpc_quiescence,
            quiesce_after_agent_end=True,
        )
        status["agent_exit"] = rpc_result.exit_code
        if rpc_result.timed_out:
            status["agent_timed_out"] = True
        status["agent_wall_s"] = round(time.time() - started, 1)
        status.update(
            record_subject_container_memory_status(
                cname,
                cell / "logs" / "subject-memory-events.json",
            )
        )

        transient_paths = [cell / "logs" / "omp.stderr.txt", cell / "logs" / "pi-rpc-runner.jsonl"]
        transient_paths += [p for p in (cell / "session").glob("*.jsonl") if p not in pre_session_paths]
        transient = transient_model_error(transient_paths)
        if transient and status.get("agent_exit") != "timeout":
            status["transient_model_error"] = transient
            (cell / "transient_error.json").write_text(json.dumps(status, indent=2))
            print(f"[pause] transient model error for {task_id}/{config}#{rep}: {transient}", flush=True)
            raise SystemExit(TRANSIENT_EXIT)

        sh(["docker", "exec", cname, "bash", "-lc", "find /app -type d -name .gocache -prune -exec rm -rf {} +"])
        for c in (["add", "-A"],
                  ["-c", "user.email=agent@dsw", "-c", "user.name=agent",
                   "commit", "-q", "-m", "agent work", "--allow-empty", "--no-verify"]):
            sh(["docker", "exec", cname, "git", *c])
        r = sh(["docker", "exec", cname, "bash", "/task/pre_artifacts.sh"], timeout=120)
        (cell / "logs" / "pre_artifacts.stdout.txt").write_text(r.stdout + r.stderr)
        patch = cell / "artifacts" / "model.patch"
        removed_patch_bytes = strip_patch_paths(patch)
        if removed_patch_bytes:
            status["patch_sanitized_bytes_removed"] = removed_patch_bytes
        status["patch_bytes"] = patch.stat().st_size if patch.exists() else 0
    finally:
        if not keep:
            sh(["docker", "rm", "-f", cname])
        for d in (auth_tmp, task_public):
            shutil.rmtree(d, ignore_errors=True)

    reward = {"reward": -1, "partial": 0.0}
    if status.get("patch_bytes", 0) > 0:
        ensure_verifier_image(task)
        verifier_cname = f"{cname}-verifier"
        verifier_memory_events_path = (
            cell / "verifier" / "memory-events.txt"
        )
        verifier_memory_events_path.unlink(missing_ok=True)
        try:
            r = run_managed_container_and_wait(
                [
                    "docker", "run", "-d", "--name", verifier_cname,
                *planned_container_resource_docker_args(
                    resource_policy,
                    container_labels,
                    role="verifier",
                ),
                "--network", "none", "--platform", "linux/amd64",
                "-v", f"{cell}:/logs",
                task.verifier_image,
                *verifier_memory_events_shell_args(),
                ],
                container_labels=container_labels,
                container_name=verifier_cname,
                timeout=task.verifier_timeout_s + 300,
            )
            verifier_stdout = compact_verifier_stdout(r.stdout + r.stderr, cell / "verifier")
            (cell / "logs" / "verifier.stdout.txt").write_text(verifier_stdout)
            status["verifier_exit"] = r.returncode
            reward = read_reward(cell / "verifier")
        except subprocess.TimeoutExpired:
            status["verifier_exit"] = "timeout"
        finally:
            status.update(
                verifier_container_memory_status(
                    verifier_memory_events_path,
                    oom_evidence=inspect_docker_container_oom(verifier_cname),
                    live_container_name=verifier_cname,
                )
            )
            sh(["docker", "rm", "-f", verifier_cname])
    else:
        status["verifier_exit"] = "skipped_empty_patch"

    usage = parse_usage.parse(session_dir=cell / "session")
    rec = result_record(
        task, config, model, rep,
        agent="omp",
        agent_runtime=status.get("omp_version"),
        omp_tools=tools,
        omp_system_prompt_override=system_prompt is not None,
        omp_system_prompt_chars=len(system_prompt or ""),
        omp_extensions=omp_extensions,
        omp_project_message_strip_enabled=any("strip" in path and "project" in path for path in omp_extensions),
        omp_no_skills=True,
        omp_no_extensions=not bool(omp_extensions),
        omp_no_rules=True,
        system_preamble_chars=len(cfg.get("system_preamble") or ""),
        orchestration_chars=len(cfg.get("orchestration") or ""),
        append_system_prompt_chars=len(append_text),
        thinking_level=thinking,
        openai_codex_oauth_passed=pass_openai_codex_oauth,
        initial_context_capture_enabled=capture_initial_context,
        initial_context_capture_path="initial_context" if capture_initial_context else None,
        reward_binary=reward.get("reward", -1),
        reward_partial=float(reward.get("partial", 0.0)),
        f2p=reward.get("f2p"), p2p=reward.get("p2p"),
        f2p_passed=reward.get("f2p_passed"), f2p_total=reward.get("f2p_total"),
        p2p_passed=reward.get("p2p_passed"), p2p_total=reward.get("p2p_total"),
        patch_bytes=status.get("patch_bytes", 0),
        agent_exit=status.get("agent_exit"),
        agent_timed_out=status.get("agent_timed_out", False),
        verifier_exit=status.get("verifier_exit"),
        agent_wall_s=status.get("agent_wall_s"),
        **container_memory_result_fields(status),
        **usage,
    )
    if persist_result_file:
        (cell / "result.json").write_text(json.dumps(rec, indent=2))
    if persist_result_index:
        rl = results_tree.Tree.of(model, thinking, repo=REPO).results_jsonl
        rl.parent.mkdir(parents=True, exist_ok=True)
        with open(rl, "a") as f:
            f.write(json.dumps(rec) + "\n")
    print(f"[done] {task_id}/{config}#{rep}: partial={rec['reward_partial']:.3f} "
          f"binary={rec['reward_binary']} tok={rec['total_tokens']} "
          f"cost=${rec['cost_usd']:.4f} wall={rec['agent_wall_s']}s "
          f"patch={rec['patch_bytes']}B", flush=True)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--thinking", default=DEFAULT_THINKING,
                    choices=["off", "minimal", "low", "medium", "high", "xhigh"])
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--agent-timeout", type=float, default=None,
                    help="override task agent timeout seconds")
    ap.add_argument("--rpc-quiescence", type=float, default=2.0,
                    help="seconds OMP RPC must remain idle after agent_end before the cell stops")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--pass-openai-codex-oauth", action="store_true",
                    help="copy only OMP's host openai-codex OAuth entry into each agent container")
    ap.add_argument("--no-initial-context-capture", action="store_true",
                    help="disable initial system/context/provider-request capture under result initial_context/")
    ap.add_argument(
        "--probe-output",
        type=Path,
        help="required scratch cell for direct draft/probe debugging",
    )
    args = ap.parse_args()
    probe_output = require_draft_probe_output(
        args.probe_output,
        REPO / "results",
    )
    task = load_task(args.task)
    timeout = args.agent_timeout or task.agent_timeout_s
    rec = run_cell(
        args.config,
        args.task,
        model=args.model,
        thinking=args.thinking,
        rep=args.rep,
        agent_timeout=timeout,
        keep=args.keep,
        pass_openai_codex_oauth=args.pass_openai_codex_oauth,
        rpc_quiescence=args.rpc_quiescence,
        capture_initial_context=not args.no_initial_context_capture,
        output_cell=probe_output,
        persist_result_index=False,
    )
    print(json.dumps(rec))


if __name__ == "__main__":
    main()
