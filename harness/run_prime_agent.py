#!/usr/bin/env python3
"""Run one DeepSWE rep with Prime Agent's stock depth-one RLM behavior.

Prime Agent is pinned to direct ``zai/glm-5.2`` at ``max`` thinking. The runner
isolates its config and session state per rep while retaining shipped built-in
skills, compaction, auto-refine, retries, and non-autonomous execution.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import parse_usage
import results_tree
import zai_bounded_proxy
from container_resources import (
    VERIFIER_MEMORY_EVENTS_SHELL_COMMAND,
    container_memory_result_fields,
    inspect_docker_container_oom,
    managed_container_start_guard,
    planned_container_resource_docker_args,
    record_subject_container_memory_status,
    run_managed_container_and_wait,
    verifier_container_memory_status,
)
from lib import (
    REPO,
    load_task,
    read_reward,
    result_record,
    subject_container_name,
)
from pi_rpc_runner import run_pi_rpc
from run import (
    TRANSIENT_EXIT,
    compact_verifier_stdout,
    config_append_text,
    credential_route_env_flags,
    ensure_env_image,
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

DEFAULT_MODEL = "zai/glm-5.2"
DEFAULT_THINKING = "max"
PRIME_AGENT_VERSION = "0.7.0"
PRIME_AGENT_SETTINGS_KEYS = frozenset(
    {"defaultProvider", "defaultModel", "defaultThinkingLevel", "rlmMaxDepth"}
)
PRIME_AGENT_CONFIG_DIR = "/root/.prime/agent"
ZAI_PROXY_PORT = 8765
ZAI_MAX_REQUESTS_PER_CELL = 64
ZAI_MAX_CONCURRENCY = 8
ZAI_PROXY_USAGE_PATH = Path("logs/zai-proxy-usage.jsonl")


def validate_prime_agent_settings(settings_path: Path) -> dict[str, object]:
    """Validate the complete Prime Agent config used by this benchmark release."""
    try:
        document = json.loads(settings_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        sys.exit(f"Prime Agent settings unreadable at {settings_path}: {error}")
    if not isinstance(document, dict):
        sys.exit("Prime Agent settings must be a JSON object")
    unsupported = sorted(set(document) - PRIME_AGENT_SETTINGS_KEYS)
    if unsupported:
        sys.exit(f"Prime Agent unsupported settings keys: {unsupported}")
    expected = {
        "defaultProvider": "zai",
        "defaultModel": "glm-5.2",
        "defaultThinkingLevel": "max",
        "rlmMaxDepth": 1,
    }
    if document != expected:
        sys.exit(
            "Prime Agent settings must pin direct zai/glm-5.2, max thinking, "
            f"and shipped RLM depth 1; got {document!r}"
        )
    return document


def prime_agent_proxy_models() -> dict[str, object]:
    """Redirect only the built-in ZAI provider through the per-cell guard."""
    return {
        "providers": {
            "zai": {
                "baseUrl": f"http://127.0.0.1:{ZAI_PROXY_PORT}",
            }
        }
    }


def start_zai_proxy(container_name: str) -> None:
    """Start the bounded direct-ZAI proxy and require a healthy response."""
    started = sh(
        [
            "docker",
            "exec",
            "-d",
            container_name,
            "zai-bounded-proxy",
            "--usage-log",
            f"/out/{ZAI_PROXY_USAGE_PATH}",
            "--max-requests",
            str(ZAI_MAX_REQUESTS_PER_CELL),
            "--max-concurrency",
            str(ZAI_MAX_CONCURRENCY),
            "--port",
            str(ZAI_PROXY_PORT),
        ]
    )
    if started.returncode != 0:
        sys.exit(f"Prime Agent ZAI proxy failed to start: {started.stderr[-800:]}")
    health_command = (
        "import urllib.request; "
        f"urllib.request.urlopen('http://127.0.0.1:{ZAI_PROXY_PORT}/health', "
        "timeout=1).read()"
    )
    for _attempt in range(50):
        health = sh(["docker", "exec", container_name, "python3", "-c", health_command])
        if health.returncode == 0:
            return
        time.sleep(0.1)
    sys.exit("Prime Agent ZAI proxy did not become healthy")


def read_zai_proxy_health(container_name: str) -> dict[str, object]:
    """Read final request-limit counters while the subject container is live."""
    command = (
        "import urllib.request; print(urllib.request.urlopen("
        f"'http://127.0.0.1:{ZAI_PROXY_PORT}/health', timeout=1).read().decode())"
    )
    result = sh(["docker", "exec", container_name, "python3", "-c", command])
    if result.returncode != 0:
        return {}
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}
    return document if isinstance(document, dict) else {}


def ensure_prime_agent_image(task) -> str:
    """Build or reuse the task image containing pinned Prime Agent 0.7.0."""
    image = task.prime_agent_image
    inspected = sh(["docker", "image", "inspect", image])
    if inspected.returncode == 0:
        return image
    print(f"[image] building Prime Agent layer {image}", flush=True)
    built = sh(
        [
            "docker",
            "build",
            "--build-arg",
            f"ENV_IMAGE={task.env_image}",
            "-t",
            image,
            "-f",
            str(HERE / "Dockerfile.prime-agent"),
            str(HERE),
        ],
        timeout=900,
    )
    if built.returncode != 0:
        sys.exit(f"[image] Prime Agent build failed:\n{built.stderr[-1500:]}")
    return image


def prime_agent_cmd(
    model: str, thinking: str, capture_initial_context: bool = True
) -> list[str]:
    """Build the stock, non-autonomous Prime Agent RPC command for GLM-5.2."""
    if model != DEFAULT_MODEL:
        sys.exit(
            "Prime Agent benchmark runner requires exact model zai/glm-5.2; "
            f"got {model!r}"
        )
    if thinking != "max":
        sys.exit(
            f"Prime Agent benchmark runner requires max thinking; got {thinking!r}"
        )
    command = [
        "prime-agent",
        "--mode",
        "rpc",
        "--cwd",
        "/app",
        "--provider",
        "zai",
        "--model",
        "glm-5.2",
        "--thinking",
        "max",
        "--session-dir",
        "/out/session",
        "--no-extensions",
    ]
    command += initial_context_capture_flags(capture_initial_context)
    return command


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
) -> dict:
    """Execute one Prime Agent subject rep using explicit resolved inputs."""
    prime_agent_cmd(model, thinking, capture_initial_context=False)
    if pass_openai_codex_oauth:
        sys.exit("Prime Agent direct ZAI reps must not receive OpenAI Codex OAuth")

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
    if cfg["skill_dirs"]:
        sys.exit("Prime Agent stock config must not define custom skills")
    if cfg["pi_flags"]:
        sys.exit("Prime Agent stock config must not define Pi flags or extensions")
    if cfg.get("models_json") or cfg.get("advisor_json"):
        sys.exit("Prime Agent stock config must not define model or advisor files")
    settings_path = cfg.get("settings_json")
    if settings_path is None:
        sys.exit("Prime Agent config requires leaf-local settings.json")
    settings = validate_prime_agent_settings(Path(settings_path))
    append_text = config_append_text(cfg)
    if append_text:
        sys.exit("Prime Agent stock config must not define prompt layers")

    cell = require_explicit_cell_output(output_cell)
    ensure_env_image(task.env_image)
    agent_image = ensure_prime_agent_image(task)

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
    prime_config_tmp = tempfile.mkdtemp(prefix="dsw-prime-agent-config-")
    shutil.copy2(task.dir / "instruction.md", Path(task_public) / "instruction.md")
    shutil.copy2(task.dir / "pre_artifacts.sh", Path(task_public) / "pre_artifacts.sh")
    shutil.copy2(settings_path, Path(prime_config_tmp) / "settings.json")
    (Path(prime_config_tmp) / "models.json").write_text(
        json.dumps(prime_agent_proxy_models(), indent=2) + "\n"
    )

    env_flag = ["-e", f"PRIME_AGENT_CODING_AGENT_DIR={PRIME_AGENT_CONFIG_DIR}"]
    for key, value in cfg["env"].items():
        env_flag += ["-e", f"{key}={value}"]
    env_flag += credential_route_env_flags(credential_routes)
    env_flag += initial_context_capture_env(capture_initial_context)

    print(
        f"[cell] task={task_id} config={config} lang={task.language} "
        f"budget={agent_timeout:.0f}s agent=prime-agent "
        f"model={model} thinking={thinking}",
        flush=True,
    )

    run_args = [
        "docker",
        "run",
        "-d",
        "--name",
        cname,
        *planned_container_resource_docker_args(
            resource_policy,
            container_labels,
            role="subject",
        ),
        "--platform",
        "linux/amd64",
        "-w",
        "/app",
        "-v",
        f"{task_public}:/task:ro",
        "-v",
        f"{cell}:/out",
        "-v",
        f"{cfg['dir']}:/arm:ro",
        *initial_context_capture_mount(capture_initial_context),
        "-v",
        f"{cell}:/logs",
        "-v",
        f"{prime_config_tmp}:{PRIME_AGENT_CONFIG_DIR}",
        *env_flag,
        agent_image,
        "sleep",
        str(int(agent_timeout + 600)),
    ]
    with managed_container_start_guard(container_labels):
        r = sh(run_args)
    if r.returncode != 0:
        for d in (prime_config_tmp, task_public):
            shutil.rmtree(d, ignore_errors=True)
        sys.exit(f"[cell] docker run failed:\n{r.stderr[:800]}")

    started = time.time()
    status: dict = {}
    try:
        version = sh(["docker", "exec", cname, "prime-agent", "--version"])
        version_output = (version.stdout + version.stderr).strip()
        (cell / "logs" / "prime-agent-version.txt").write_text(
            version.stdout + version.stderr
        )
        if version.returncode != 0 or version_output != PRIME_AGENT_VERSION:
            sys.exit(
                "Prime Agent runtime version mismatch: expected "
                f"{PRIME_AGENT_VERSION}, got {version_output!r}"
            )
        status["prime_agent_version"] = version_output
        start_zai_proxy(cname)

        pre_session_paths = set((cell / "session").glob("*.jsonl"))
        cmd = prime_agent_cmd(model, thinking, capture_initial_context)
        rpc_result = run_pi_rpc(
            ["docker", "exec", "-i", "-w", "/app", cname, *cmd],
            prompt_text=(Path(task_public) / "instruction.md").read_text(),
            stderr_path=cell / "logs" / "prime-agent.stderr.txt",
            runner_log_path=cell / "logs" / "pi-rpc-runner.jsonl",
            timeout_s=agent_timeout,
            quiescence_s=rpc_quiescence,
            quiesce_after_agent_end=True,
        )
        status["agent_exit"] = rpc_result.exit_code
        if rpc_result.timed_out:
            status["agent_timed_out"] = True
        status["agent_wall_s"] = round(time.time() - started, 1)
        proxy_health = read_zai_proxy_health(cname)
        status["prime_agent_request_limit"] = ZAI_MAX_REQUESTS_PER_CELL
        status["prime_agent_concurrency_limit"] = ZAI_MAX_CONCURRENCY
        status["prime_agent_requests_admitted"] = proxy_health.get("requestsAdmitted")
        status["prime_agent_peak_concurrency"] = proxy_health.get("peakConcurrency")
        status.update(
            record_subject_container_memory_status(
                cname,
                cell / "logs" / "subject-memory-events.json",
            )
        )

        transient_paths = [
            cell / "logs" / "prime-agent.stderr.txt",
            cell / "logs" / "pi-rpc-runner.jsonl",
        ]
        transient_paths += [
            p for p in (cell / "session").glob("*.jsonl") if p not in pre_session_paths
        ]
        request_limit_exceeded = zai_bounded_proxy.request_limit_was_exceeded(
            cell / ZAI_PROXY_USAGE_PATH
        )
        if request_limit_exceeded:
            status["prime_agent_request_limit_exceeded"] = True
        transient = transient_model_error(transient_paths)
        if (
            transient
            and not request_limit_exceeded
            and status.get("agent_exit") != "timeout"
        ):
            status["transient_model_error"] = transient
            (cell / "transient_error.json").write_text(json.dumps(status, indent=2))
            print(
                f"[pause] transient model error for {task_id}/{config}#{rep}: {transient}",
                flush=True,
            )
            raise SystemExit(TRANSIENT_EXIT)

        sh(
            [
                "docker",
                "exec",
                cname,
                "bash",
                "-lc",
                "find /app -type d -name .gocache -prune -exec rm -rf {} +",
            ]
        )
        for c in (
            ["add", "-A"],
            [
                "-c",
                "user.email=agent@dsw",
                "-c",
                "user.name=agent",
                "commit",
                "-q",
                "-m",
                "agent work",
                "--allow-empty",
                "--no-verify",
            ],
        ):
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
        for d in (prime_config_tmp, task_public):
            shutil.rmtree(d, ignore_errors=True)

    reward = {"reward": -1, "partial": 0.0}
    if status.get("patch_bytes", 0) > 0:
        ensure_verifier_image(task)
        verifier_cname = f"{cname}-verifier"
        verifier_memory_events_path = cell / "verifier" / "memory-events.txt"
        verifier_memory_events_path.unlink(missing_ok=True)
        try:
            r = run_managed_container_and_wait(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    verifier_cname,
                    *planned_container_resource_docker_args(
                        resource_policy,
                        container_labels,
                        role="verifier",
                    ),
                    "--network",
                    "none",
                    "--platform",
                    "linux/amd64",
                    "-v",
                    f"{cell}:/logs",
                    task.verifier_image,
                    "bash",
                    "-lc",
                    VERIFIER_MEMORY_EVENTS_SHELL_COMMAND,
                ],
                container_labels=container_labels,
                container_name=verifier_cname,
                timeout=task.verifier_timeout_s + 300,
            )
            verifier_stdout = compact_verifier_stdout(
                r.stdout + r.stderr, cell / "verifier"
            )
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
                )
            )
            sh(["docker", "rm", "-f", verifier_cname])
    else:
        status["verifier_exit"] = "skipped_empty_patch"

    usage = parse_usage.parse(session_dir=cell / "session")
    provider_usage = zai_bounded_proxy.aggregate_usage(cell / ZAI_PROXY_USAGE_PATH)
    if provider_usage["requests"]:
        # The provider trace includes root, child, compaction, and auto-refine
        # calls. Keep native session fields as role-level breakdowns, but use
        # this complete trace for canonical totals.
        usage.update(
            {
                "input_tokens": provider_usage["input"],
                "output_tokens": provider_usage["output"],
                "cache_read_tokens": provider_usage["cache_read"],
                "cache_write_tokens": provider_usage["cache_write"],
                "reported_total_tokens": provider_usage["total_tokens"],
                "total_tokens": provider_usage["total_tokens"],
                "cost_usd": 0.0,
            }
        )
    admitted_requests = status.get("prime_agent_requests_admitted")
    provider_request_count = (
        admitted_requests
        if isinstance(admitted_requests, int)
        else provider_usage["requests"]
    )
    rec = result_record(
        task,
        config,
        model,
        rep,
        agent="prime-agent",
        agent_runtime=status.get("prime_agent_version"),
        prime_agent_provider="zai",
        prime_agent_rlm_max_depth=settings["rlmMaxDepth"],
        prime_agent_autonomous=False,
        prime_agent_builtin_skills=True,
        prime_agent_auto_compaction=True,
        prime_agent_auto_refine=True,
        prime_agent_request_limit=ZAI_MAX_REQUESTS_PER_CELL,
        prime_agent_concurrency_limit=ZAI_MAX_CONCURRENCY,
        prime_agent_provider_requests=provider_request_count,
        prime_agent_reasoning_tokens=provider_usage["reasoning"],
        prime_agent_requests_admitted=status.get("prime_agent_requests_admitted"),
        prime_agent_peak_concurrency=status.get("prime_agent_peak_concurrency"),
        prime_agent_request_limit_exceeded=status.get(
            "prime_agent_request_limit_exceeded", False
        ),
        system_preamble_chars=len(cfg.get("system_preamble") or ""),
        orchestration_chars=len(cfg.get("orchestration") or ""),
        append_system_prompt_chars=len(append_text),
        thinking_level=thinking,
        openai_codex_oauth_passed=pass_openai_codex_oauth,
        initial_context_capture_enabled=capture_initial_context,
        initial_context_capture_path="initial_context"
        if capture_initial_context
        else None,
        reward_binary=reward.get("reward", -1),
        reward_partial=float(reward.get("partial", 0.0)),
        f2p=reward.get("f2p"),
        p2p=reward.get("p2p"),
        f2p_passed=reward.get("f2p_passed"),
        f2p_total=reward.get("f2p_total"),
        p2p_passed=reward.get("p2p_passed"),
        p2p_total=reward.get("p2p_total"),
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
    print(
        f"[done] {task_id}/{config}#{rep}: partial={rec['reward_partial']:.3f} "
        f"binary={rec['reward_binary']} tok={rec['total_tokens']} "
        f"cost=${rec['cost_usd']:.4f} wall={rec['agent_wall_s']}s "
        f"patch={rec['patch_bytes']}B",
        flush=True,
    )
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--thinking", default=DEFAULT_THINKING, choices=["max"])
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument(
        "--agent-timeout",
        type=float,
        default=None,
        help="override task agent timeout seconds",
    )
    ap.add_argument(
        "--rpc-quiescence",
        type=float,
        default=2.0,
        help="seconds Prime Agent RPC remains idle after agent_end",
    )
    ap.add_argument("--keep", action="store_true")
    ap.add_argument(
        "--pass-openai-codex-oauth", action="store_true", help=argparse.SUPPRESS
    )
    ap.add_argument(
        "--no-initial-context-capture",
        action="store_true",
        help="disable initial system/context/provider-request capture under result initial_context/",
    )
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
