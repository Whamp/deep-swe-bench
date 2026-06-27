"""Shared helpers: parse a DeepSWE task.toml into a Task, tag images, read reward."""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, asdict
from pathlib import Path

# Tasks live in the sibling DeepSWE checkout (~/evals/deep-swe/tasks).
# Override with the DEEP_SWE_TASKS env var to point elsewhere.
def tasks_root() -> Path:
    import os
    env = os.environ.get("DEEP_SWE_TASKS")
    if env:
        return Path(env)
    return Path.home() / "evals" / "deep-swe" / "tasks"


@dataclass
class Task:
    id: str
    dir: Path
    env_image: str
    base_commit: str
    language: str
    agent_timeout_s: float
    verifier_timeout_s: float
    title: str
    category: str

    @property
    def pi_image(self) -> str:
        # one env image per task; tag a pi-augmented layer off it.
        slug = re.sub(r"[^a-zA-Z0-9_.-]", "-", self.env_image.split(":")[-1])
        return f"deep-swe-pi:{slug}"

    @property
    def verifier_image(self) -> str:
        return f"deep-swe-verifier:{self.id}"


def load_task(task_id: str, root: Path | None = None) -> Task:
    root = root or tasks_root()
    tdir = root / task_id
    if not tdir.exists():
        raise FileNotFoundError(f"task dir not found: {tdir}")
    meta = tomllib.loads((tdir / "task.toml").read_text())
    md = meta["metadata"]
    env = meta["environment"]
    return Task(
        id=task_id,
        dir=tdir,
        env_image=env["docker_image"],
        base_commit=md["base_commit_hash"],
        language=md.get("language", "unknown"),
        agent_timeout_s=float(meta["agent"]["timeout_sec"]),
        verifier_timeout_s=float(meta["verifier"]["timeout_sec"]),
        title=md.get("display_title", task_id),
        category=md.get("category", ""),
    )


def instruction_text(task: Task) -> str:
    return (task.dir / "instruction.md").read_text()


def read_reward(verifier_dir: Path) -> dict:
    """Parse the verifier's reward.json (continuous metric = 'partial')."""
    rj = verifier_dir / "reward.json"
    if not rj.exists():
        # crash sentinel from test.sh's EXIT trap
        rt = verifier_dir / "reward.txt"
        if rt.exists():
            return {"reward": -1, "partial": 0.0, "_sentinel": rt.read_text().strip()}
        return {"reward": -1, "partial": 0.0, "_missing": True}
    d = json.loads(rj.read_text())
    return d


def model_leaf(model: str, advisor_model: str | None = None) -> str:
    """Path segment for a model: the last '/'-segment of the model id, with an
    optional '+advisor' suffix for advisor configs.

    SINGLE source of truth for the <model-leaf> path segment shared by configs/
    leaves and results/ paths, so migrate_results.py and the harness derive it
    identically (the resume-re-runs-everything failure mode if they diverge).
    The results path is EXECUTOR-ONLY (never carries +advisor); the +advisor form
    is configs-leaf-only and exists so a resumed run_batch can recompute the
    results path from the executor --model alone.
    """
    leaf = model.rstrip("/").split("/")[-1]
    if advisor_model:
        leaf = f"{leaf}+{advisor_model.rstrip('/').split('/')[-1]}"
    return leaf


def result_record(task: Task, arm: str, model: str, rep: int, **kw) -> dict:
    rec = {
        "task": task.id,
        "language": task.language,
        "category": task.category,
        "arm": arm,
        "model": model,
        "rep": rep,
    }
    rec.update(kw)
    return rec
