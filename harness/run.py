#!/usr/bin/env python3
"""Run one (arm, task) cell end-to-end through pi, then the DeepSWE verifier.

Topology (one task):
  env container  (pi-agent image: task env image + pi). repo at /app.
    |- pi -p @/task/instruction.md --model ... --mode json   (the agent)
    |- bash /task/pre_artifacts.sh  -> /logs/artifacts/model.patch
  verifier container (env image + hidden tests/, --network none)
    |- bash /tests/test.sh          -> /logs/verifier/reward.json

The agent works in the real task container so it can run the project's own tests
with the correct toolchain; the reward is always measured in a pristine verifier
container (separate-env grading), exactly as DeepSWE/Pier define it.

Usage:
  python run.py --arm baseline --task abs-module-cache-flags
  python run.py --arm ponytail-full --task <id> --run-name study1 --agent-timeout 600
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from lib import load_task, instruction_text, read_reward, result_record  # noqa: E402
import parse_usage  # noqa: E402

DEFAULT_MODEL = "openrouter/deepseek/deepseek-v4-flash"
DEFAULT_THINKING = "high"


def sh(cmd: list[str], timeout: float | None = None, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, timeout=timeout, capture_output=True, text=True, **kw)


def ensure_env_image(env_image: str):
    r = sh(["docker", "image", "inspect", env_image])
    if r.returncode == 0:
        return

    # ECR rate-limits parallel anonymous pulls. One global pull at a time is
    # slower than a stampede, but it actually finishes.
    lock_dir = REPO / "cache"
    lock_dir.mkdir(exist_ok=True)
    with open(lock_dir / "docker-pull.lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        r = sh(["docker", "image", "inspect", env_image])
        if r.returncode == 0:
            return
        for attempt in range(1, 7):
            print(f"[image] pulling env image {env_image} (attempt {attempt}/6)", flush=True)
            r = sh(["docker", "pull", "--platform", "linux/amd64", env_image], timeout=1200)
            if r.returncode == 0:
                return
            msg = (r.stderr or r.stdout or "")[-800:]
            if attempt == 6:
                sys.exit(f"[image] pull failed: {msg}")
            sleep_s = 30 * attempt
            print(f"[image] pull failed; retrying in {sleep_s}s: {msg[:300]}", flush=True)
            time.sleep(sleep_s)


def ensure_pi_image(task) -> str:
    img = task.pi_image
    r = sh(["docker", "image", "inspect", img])
    if r.returncode == 0:
        return img
    print(f"[image] building pi-agent layer {img}", flush=True)
    r = sh(["docker", "build", "--build-arg", f"ENV_IMAGE={task.env_image}",
            "-t", img, "-f", str(HERE / "Dockerfile.pi-agent"), str(HERE)], timeout=600)
    if r.returncode != 0:
        sys.exit(f"[image] pi-agent build failed:\n{r.stderr[-1500:]}")
    return img


def ensure_verifier_image(task) -> str:
    img = task.verifier_image
    r = sh(["docker", "image", "inspect", img])
    if r.returncode == 0:
        return img
    print(f"[image] building verifier {img}", flush=True)
    r = sh(["docker", "build", "--platform", "linux/amd64", "-t", img,
            "-f", str(task.dir / "tests" / "Dockerfile"), str(task.dir / "tests")], timeout=1800)
    if r.returncode != 0:
        sys.exit(f"[image] verifier build failed:\n{r.stderr[-1500:]}")
    return img


def load_arm(arm: str) -> dict:
    adir = REPO / "arms" / arm
    if not adir.exists():
        sys.exit(f"arm not found: {adir}")
    skill_dirs = []
    sd = adir / "skills"
    if sd.is_dir():
        skill_dirs = [p for p in sd.iterdir() if p.is_dir()]
    pi_flags = []
    pf = adir / "pi-flags"
    if pf.exists():
        pi_flags = [ln.strip() for ln in pf.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    env_lines = {}
    ef = adir / "env"
    if ef.exists():
        for ln in ef.read_text().splitlines():
            ln = ln.strip()
            if ln and "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                env_lines[k.strip()] = v.strip()
    advisor_json = adir / "advisor.json"
    models_json = adir / "models.json"
    settings_json = adir / "settings.json"
    return {"dir": adir, "orchestration": (adir / "orchestration.md").read_text(),
            "skill_dirs": skill_dirs, "pi_flags": pi_flags, "env": env_lines,
            "advisor_json": advisor_json if advisor_json.exists() else None,
            "models_json": models_json if models_json.exists() else None,
            "settings_json": settings_json if settings_json.exists() else None}


def pi_cmd(arm_cfg: dict, model: str, thinking: str, append_text: str) -> list[str]:
    cmd = ["pi", "-p", "@/task/instruction.md",
           "--model", model, "--thinking", thinking, "--mode", "json", "--offline",
           "--session-dir", "/out/session",
           "--append-system-prompt", append_text]
    flags = arm_cfg["pi_flags"]
    has_explicit_extension = any(f in ("-e", "--extension") or f.startswith("--extension=") for f in flags)

    # Baseline stays fully isolated. Extension arms must not get --no-extensions:
    # that would defeat the point of testing a normal installed Pi extension.
    if not arm_cfg["skill_dirs"]:
        cmd += ["--no-skills"]
    else:
        for s in arm_cfg["skill_dirs"]:
            cmd += ["--skill", f"/arm/skills/{s.name}"]
    if not has_explicit_extension:
        cmd += ["--no-extensions"]
    cmd += flags
    return cmd


def run_cell(arm: str, task_id: str, *, model: str, thinking: str, run_name: str, rep: int,
             agent_timeout: float, keep: bool) -> dict:
    task = load_task(task_id)
    arm_cfg = load_arm(arm)
    ensure_env_image(task.env_image)
    pi_image = ensure_pi_image(task)

    cell = REPO / "runs" / run_name / arm / task_id / f"rep{rep}"
    cell.mkdir(parents=True, exist_ok=True)
    (cell / "artifacts").mkdir(exist_ok=True)
    (cell / "verifier").mkdir(exist_ok=True)
    (cell / "logs").mkdir(exist_ok=True)

    preamble = (HERE / "system_preamble.md").read_text()
    append_text = preamble + "\n\n" + arm_cfg["orchestration"]

    suffix = f"{arm}-{task_id}-r{rep}-{os.getpid()}"
    cname = f"dsw-{suffix}"
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        sys.exit("OPENROUTER_API_KEY not set in environment")

    env_flag = ["-e", f"OPENROUTER_API_KEY={api_key}"]
    # Optional advisor/secondary-model providers. Passing these symmetrically is
    # harmless; only arms with matching extensions/models use them.
    if os.environ.get("ZAI_API_KEY"):
        env_flag += ["-e", f"ZAI_API_KEY={os.environ['ZAI_API_KEY']}"]
    for k, v in arm_cfg["env"].items():
        env_flag += ["-e", f"{k}={v}"]

    print(f"[cell] task={task_id} arm={arm} lang={task.language} "
          f"budget={agent_timeout:.0f}s model={model} thinking={thinking}", flush=True)

    # --- start env container (agent works here) ---
    run_args = ["docker", "run", "-d", "--name", cname, "--platform", "linux/amd64",
                "-w", "/app",
                "-v", f"{task.dir}:/task:ro",
                "-v", f"{cell}:/out",
                "-v", f"{arm_cfg['dir']}:/arm:ro",
                # /logs mount = same as /out so pre_artifacts + verifier land on host
                "-v", f"{cell}:/logs",
                *env_flag, pi_image, "sleep", str(int(agent_timeout + 600))]
    r = sh(run_args)
    if r.returncode != 0:
        sys.exit(f"[cell] docker run failed:\n{r.stderr[:800]}")

    started = time.time()
    status = {}
    try:
        if arm_cfg.get("advisor_json") or arm_cfg.get("models_json") or arm_cfg.get("settings_json"):
            sh(["docker", "exec", cname, "mkdir", "-p", "/root/.pi/agent"])
            if arm_cfg.get("advisor_json"):
                sh(["docker", "exec", cname, "cp", "/arm/advisor.json", "/root/.pi/agent/advisor.json"])
            if arm_cfg.get("models_json"):
                sh(["docker", "exec", cname, "cp", "/arm/models.json", "/root/.pi/agent/models.json"])
            if arm_cfg.get("settings_json"):
                sh(["docker", "exec", cname, "cp", "/arm/settings.json", "/root/.pi/agent/settings.json"])

        # --- run the agent ---
        cmd = pi_cmd(arm_cfg, model, thinking, append_text)
        with open(cell / "logs" / "pi.stderr.txt", "w") as se:
            with open(cell / "pi.jsonl", "w") as so:
                # argv list, not shell: the append-system-prompt text contains
                # newlines/spaces that a bash -lc join would mangle.
                proc = subprocess.Popen(["docker", "exec", cname, *cmd],
                                        stdout=so, stderr=se)
                try:
                    proc.wait(timeout=agent_timeout)
                    status["agent_exit"] = proc.returncode
                except subprocess.TimeoutExpired:
                    proc.kill()
                    status["agent_exit"] = "timeout"
                    status["agent_timed_out"] = True
        status["agent_wall_s"] = round(time.time() - started, 1)

        # --- capture ALL work (committed or not) then extract the submission patch ---
        # Commit any uncommitted edits so a forgetful agent is not scored 0 by accident.
        for c in (["add", "-A"],
                  ["-c", "user.email=agent@dsw", "-c", "user.name=agent",
                   "commit", "-q", "-m", "agent work", "--allow-empty", "--no-verify"]):
            sh(["docker", "exec", cname, "git", *c])
        # pre_artifacts.sh does: cd /app; git diff <base> HEAD > /logs/artifacts/model.patch
        r = sh(["docker", "exec", cname, "bash", "/task/pre_artifacts.sh"], timeout=120)
        (cell / "logs" / "pre_artifacts.stdout.txt").write_text(r.stdout + r.stderr)
        patch = cell / "artifacts" / "model.patch"
        status["patch_bytes"] = patch.stat().st_size if patch.exists() else 0
    finally:
        # Keep extension state/debug logs when an arm writes Pi agent-local data.
        sh(["docker", "exec", cname, "sh", "-lc",
            "if [ -d /root/.pi/agent/observational-memory ]; then "
            "mkdir -p /out/pi-agent && cp -a /root/.pi/agent/observational-memory /out/pi-agent/; fi"])
        if not keep:
            sh(["docker", "rm", "-f", cname])

    # --- verify in a pristine, air-gapped container ---
    reward = {"reward": -1, "partial": 0.0}
    if status.get("patch_bytes", 0) > 0:
        try:
            ensure_verifier_image(task)
            r = sh(["docker", "run", "--rm", "--network", "none", "--platform", "linux/amd64",
                    "-v", f"{cell}:/logs",
                    task.verifier_image, "bash", "/tests/test.sh"],
                   timeout=task.verifier_timeout_s + 300)
            (cell / "logs" / "verifier.stdout.txt").write_text(r.stdout + r.stderr)
            status["verifier_exit"] = r.returncode
            reward = read_reward(cell / "verifier")
        except subprocess.TimeoutExpired:
            status["verifier_exit"] = "timeout"
    else:
        status["verifier_exit"] = "skipped_empty_patch"

    usage = parse_usage.parse_stream(path=cell / "pi.jsonl")

    rec = result_record(
        task, arm, model, rep,
        thinking_level=thinking,
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
        **usage,
    )
    (cell / "result.json").write_text(json.dumps(rec, indent=2))
    rl = REPO / "runs" / run_name / "results.jsonl"
    with open(rl, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"[done] {task_id}/{arm}#{rep}: partial={rec['reward_partial']:.3f} "
          f"binary={rec['reward_binary']} tok={rec['total_tokens']} "
          f"cost=${rec['cost_usd']:.4f} wall={rec['agent_wall_s']}s "
          f"patch={rec['patch_bytes']}B", flush=True)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--run-name", default="default")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--thinking", default=DEFAULT_THINKING,
                    choices=["off", "minimal", "low", "medium", "high", "xhigh"])
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--agent-timeout", type=float, default=None,
                    help="override task's agent timeout (s). default: task.toml")
    ap.add_argument("--keep", action="store_true", help="keep the env container for debugging")
    args = ap.parse_args()

    task = load_task(args.task)
    to = args.agent_timeout or task.agent_timeout_s
    rec = run_cell(args.arm, args.task, model=args.model, thinking=args.thinking, run_name=args.run_name,
                   rep=args.rep, agent_timeout=to, keep=args.keep)
    print(json.dumps({"ok": True, "reward_partial": rec["reward_partial"],
                      "total_tokens": rec["total_tokens"]}))


if __name__ == "__main__":
    main()
