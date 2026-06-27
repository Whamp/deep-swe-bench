#!/usr/bin/env python3
"""Build configs/ from arms/ per RENAME-PLAN §9-11.

Each config splits into:
  - constants at configs/<config>/         (orchestration.md, pi-flags, env, skills/, extensions/)
  - model leaves at configs/<config>/<model-leaf>/<thinking>/  (models.json, advisor.json, settings.json)

model-leaf is lib.model_leaf() (executor-only for the results path; the +advisor
form is configs-leaf-only). Leaf-file provenance follows §10:
  - models.json: placed only when local-vllm is involved (executor or worker) —
    for advisor, the arm's openrouter+zai models.json. NEVER trust the mutated
    arms/baseline/models.json for a non-qwen executor (critical #2).
  - settings.json: leaf-level for observational-memory (carries the WORKER model,
    which differs by leaf — Qwen vs gpt-5.4-mini; critical #1).
  - advisor.json: advisor leaf only.

Usage: python3 scripts/materialize_configs.py --dry-run   (inspect, writes nothing)
       python3 scripts/materialize_configs.py             (build configs/)
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
from lib import model_leaf

REPO = Path(__file__).resolve().parent.parent
ARMS = REPO / "arms"
CONFIGS = REPO / "configs"

# §11 arm -> config map (folds collapse multiple arms into one config).
ARM_TO_CONFIG = {
    "baseline": "baseline", "baseline-codex": "baseline", "baseline-codex-wf": "baseline-wf",
    "pi-advisor-glm52": "advisor",
    "pi-observational-memory": "observational-memory",
    "pi-observational-memory-codex54mini": "observational-memory",
    "ponytail-full": "ponytail-full", "ponytail-lite": "ponytail-lite",
    "ponytail-pi-extension": "ponytail-extension", "ponytail-ultra": "ponytail-ultra",
}
# Primary arm that donates CONSTANT files to each config (for folded configs, the
# canonical one with the full constant set).
PRIMARY_ARM = {
    "baseline": "baseline", "baseline-wf": "baseline-codex-wf",
    "advisor": "pi-advisor-glm52", "observational-memory": "pi-observational-memory",
    "ponytail-full": "ponytail-full", "ponytail-lite": "ponytail-lite",
    "ponytail-extension": "ponytail-pi-extension", "ponytail-ultra": "ponytail-ultra",
}
CONSTANT_NAMES = {"orchestration.md", "pi-flags", "env", "skills", "extensions"}
LEAF_NAMES = {"models.json", "advisor.json", "settings.json"}  # model-identity files -> leaf

# Inventory of (config, model-leaf, thinking, producing-arm) from result.json.
# Each leaf's files come from its producing arm (with the §10 consistency check).
# Format: (config, model_leaf, thinking, arm, executor_model, worker_model_or_None)
# worker_model only for observational-memory (from that arm's settings.json).
LEAVES = [
    # config,              mleaf,                          thinking, arm,                              exec_model,                                  worker
    ("advisor",            "deepseek-v4-flash+glm-5.2",    "high",   "pi-advisor-glm52",               "openrouter/deepseek/deepseek-v4-flash",     None),
    ("baseline",           "Qwen3.6-27B-AWQ-BF16-INT4",    "high",   "baseline",                       "local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4", None),
    ("baseline",           "deepseek-v4-flash",            "high",   "baseline",                       "openrouter/deepseek/deepseek-v4-flash",     None),
    ("baseline",           "gpt-5.3-codex-spark",          "high",   "baseline",                       "openai-codex/gpt-5.3-codex-spark",          None),
    ("baseline",           "gpt-5.5",                      "medium", "baseline-codex",                 "openai-codex/gpt-5.5",                      None),
    ("baseline-wf",        "deepseek-v4-flash",            "high",   "baseline-codex-wf",              "openrouter/deepseek/deepseek-v4-flash",     None),
    ("baseline-wf",        "gpt-5.5",                      "medium", "baseline-codex-wf",              "openai-codex/gpt-5.5",                      None),
    ("observational-memory","Qwen3.6-27B-AWQ-BF16-INT4",   "high",   "pi-observational-memory",        "local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4", "local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4"),
    ("observational-memory","deepseek-v4-flash",           "high",   "pi-observational-memory",        "openrouter/deepseek/deepseek-v4-flash",     "local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4"),
    ("observational-memory","gpt-5.5",                     "medium", "pi-observational-memory-codex54mini","openai-codex/gpt-5.5",                  "openai-codex/gpt-5.4-mini"),
    ("ponytail-extension", "deepseek-v4-flash",            "high",   "ponytail-pi-extension",          "openrouter/deepseek/deepseek-v4-flash",     None),
    ("ponytail-full",      "deepseek-v4-flash",            "high",   "ponytail-full",                  "openrouter/deepseek/deepseek-v4-flash",     None),
]


def leaf_needs_models_json(exec_model: str, worker_model, arm: str) -> tuple[bool, Path | None]:
    """Whether this leaf needs models.json and which source. local-vllm involved
    (executor or worker) -> the canonical local-vllm models.json; advisor arm ->
    its openrouter+zai models.json. Otherwise path-only (critical #2: never place
    the mutated qwen models.json under a non-qwen executor leaf)."""
    canon_localvllm = ARMS / "baseline" / "models.json"
    if "local-vllm/" in (exec_model or "") or "local-vllm/" in (worker_model or ""):
        return True, canon_localvllm
    if arm == "pi-advisor-glm52":
        return True, ARMS / "pi-advisor-glm52" / "models.json"
    return False, None


def plan() -> list[str]:
    """Return a human-readable plan of every file placement (for --dry-run)."""
    lines = []
    for config in sorted(set(ARM_TO_CONFIG.values())):
        parmarms = ARMS / PRIMARY_ARM[config]
        consts = sorted(p.name for p in parmarms.iterdir() if p.name in CONSTANT_NAMES)
        lines.append(f"configs/{config}/  (constants from arms/{PRIMARY_ARM[config]}/: {consts})")
    lines.append("")
    lines.append("model leaves:")
    for cfg, mleaf, thinking, arm, exec_model, worker in LEAVES:
        leafdir = CONFIGS / cfg / mleaf / thinking
        rel = f"configs/{cfg}/{mleaf}/{thinking}/"
        parts = []
        need, src = leaf_needs_models_json(exec_model, worker, arm)
        if need:
            parts.append(f"models.json<={src.relative_to(REPO)}")
        # settings.json: leaf-level only for observational-memory (carries worker)
        if cfg == "observational-memory":
            ssrc = ARMS / arm / "settings.json"
            parts.append(f"settings.json<={ssrc.relative_to(REPO)}")
        # advisor.json
        if (ARMS / arm / "advisor.json").exists():
            parts.append(f"advisor.json<={((ARMS/arm/'advisor.json').relative_to(REPO))}")
        lines.append(f"  {rel}  [{', '.join(parts) if parts else 'path-only'}]")
    return lines


def build():
    if CONFIGS.exists():
        sys.exit(f"refusing to overwrite existing {CONFIGS} — remove it first")
    for config in sorted(set(ARM_TO_CONFIG.values())):
        dst = CONFIGS / config
        src = ARMS / PRIMARY_ARM[config]
        dst.mkdir(parents=True, exist_ok=True)
        for p in src.iterdir():
            if p.name in CONSTANT_NAMES:
                shutil.copytree(p, dst / p.name) if p.is_dir() else shutil.copy2(p, dst / p.name)
    for cfg, mleaf, thinking, arm, exec_model, worker in LEAVES:
        leafdir = CONFIGS / cfg / mleaf / thinking
        leafdir.mkdir(parents=True, exist_ok=True)
        need, src = leaf_needs_models_json(exec_model, worker, arm)
        if need and src and src.exists():
            shutil.copy2(src, leafdir / "models.json")
        if cfg == "observational-memory":
            ssrc = ARMS / arm / "settings.json"
            if ssrc.exists():
                shutil.copy2(ssrc, leafdir / "settings.json")
        asrc = ARMS / arm / "advisor.json"
        if asrc.exists():
            shutil.copy2(asrc, leafdir / "advisor.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.dry_run:
        print("\n".join(plan()))
        print(f"\n{len(LEAVES)} leaves across {len(set(ARM_TO_CONFIG.values()))} configs")
        print("(dry-run: nothing written)")
        return
    build()
    print(f"built configs/ ({len(LEAVES)} leaves)")


if __name__ == "__main__":
    main()
