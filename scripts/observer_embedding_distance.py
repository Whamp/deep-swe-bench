#!/usr/bin/env python3
"""Embed observational-memory observer outputs and compare configs semantically.

The script stores every recorded observer observation in a local zvec collection,
then computes per-task distances from a reference/best observer config. It is
intended for small screening subsets such as 12_v0.

Default embedding service is the local Octen endpoint on endurance documented in
~/.pi/agent/TAILNET.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import requests

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "harness"))

from lib import model_leaf  # noqa: E402


DEFAULT_EMBED_URL = "http://100.77.237.75:8090/v1/embeddings"
DEFAULT_EMBED_MODEL = "octen-embed"
DEFAULT_BEST_CONFIG = "observational-memory-gpt54mini-low"
DEFAULT_OUT_ROOT = REPO / "analysis" / "observer-embeddings"
VECTOR_DIM = 2560
SOURCE_TYPES = {"message", "custom_message", "branch_summary"}


@dataclass(frozen=True)
class ObservationDoc:
    doc_id: str
    model: str
    thinking: str
    config: str
    task: str
    rep: int
    observation_id: str
    observation_index: int
    relevance: str
    token_count: int
    content: str
    reward_partial: float
    reward_binary: int | None
    agent_timed_out: bool
    cell_path: str


@dataclass
class EmbeddedDoc:
    meta: ObservationDoc
    vector: np.ndarray


def load_task_filter(subset: str | None, tasks: str | None) -> set[str] | None:
    if subset and tasks:
        raise SystemExit("pass only one of --subset / --tasks")
    if tasks:
        return {t.strip() for t in tasks.split(",") if t.strip()}
    if subset:
        path = REPO / "subsets" / f"{subset}.txt"
        if not path.exists():
            raise SystemExit(f"subset file not found: {path}")
        return {t.strip() for t in path.read_text().splitlines() if t.strip()}
    return None


def discover_configs(result_root: Path) -> list[str]:
    return sorted(
        p.name for p in result_root.iterdir()
        if p.is_dir() and p.name.startswith("observational-memory-")
    )


def parse_configs(value: str | None, result_root: Path) -> list[str]:
    if not value or value == "all":
        return discover_configs(result_root)
    return [x.strip() for x in value.split(",") if x.strip()]


def stable_doc_id(parts: list[str]) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:32]


def load_cell_observations(
    *, model: str, thinking: str, config: str, result_json: Path
) -> list[ObservationDoc]:
    try:
        result = json.loads(result_json.read_text())
    except Exception as exc:
        raise RuntimeError(f"failed to read {result_json}: {exc}") from exc

    task = str(result.get("task") or result_json.parts[-3])
    rep_text = result_json.parts[-2].replace("rep", "")
    rep = int(result.get("rep", rep_text or 0))
    reward_partial = float(result.get("reward_partial") or 0.0)
    rb = result.get("reward_binary")
    reward_binary = int(rb) if isinstance(rb, int) else None
    timed_out = bool(result.get("agent_timed_out"))

    observations: list[dict[str, Any]] = []
    for session_path in sorted((result_json.parent / "session").glob("*.jsonl")):
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if entry.get("type") == "custom" and entry.get("customType") == "om.observations.recorded":
                observations.extend((entry.get("data") or {}).get("observations") or [])

    docs: list[ObservationDoc] = []
    for idx, obs in enumerate(observations):
        content = str(obs.get("content") or "").strip()
        if not content:
            continue
        obs_id = str(obs.get("id") or f"obs{idx}")
        doc_id = stable_doc_id([model, thinking, config, task, str(rep), obs_id, content])
        docs.append(
            ObservationDoc(
                doc_id=doc_id,
                model=model,
                thinking=thinking,
                config=config,
                task=task,
                rep=rep,
                observation_id=obs_id,
                observation_index=idx,
                relevance=str(obs.get("relevance") or ""),
                token_count=int(obs.get("tokenCount") or 0),
                content=content,
                reward_partial=reward_partial,
                reward_binary=reward_binary,
                agent_timed_out=timed_out,
                cell_path=str(result_json.parent.relative_to(REPO)),
            )
        )
    return docs


def extract_observations(
    *, model: str, thinking: str, configs: list[str], task_filter: set[str] | None
) -> list[ObservationDoc]:
    result_root = REPO / "results" / model_leaf(model) / thinking
    docs: list[ObservationDoc] = []
    for config in configs:
        config_root = result_root / config
        if not config_root.exists():
            print(f"warning: config result path missing: {config_root}", file=sys.stderr)
            continue
        for result_json in sorted(config_root.glob("*/rep*/result.json")):
            task = result_json.parts[-3]
            if task_filter is not None and task not in task_filter:
                continue
            docs.extend(load_cell_observations(model=model_leaf(model), thinking=thinking, config=config, result_json=result_json))
    return docs


def embed_batch(texts: list[str], *, url: str, model: str, timeout: float) -> list[list[float]]:
    response = requests.post(url, json={"model": model, "input": texts}, timeout=timeout)
    response.raise_for_status()
    data = response.json().get("data") or []
    if len(data) != len(texts):
        raise RuntimeError(f"embedding response count mismatch: got {len(data)}, expected {len(texts)}")
    data = sorted(data, key=lambda item: item.get("index", 0))
    return [item["embedding"] for item in data]


def embed_docs(
    docs: list[ObservationDoc], *, url: str, model: str, batch_size: int, timeout: float
) -> list[EmbeddedDoc]:
    embedded: list[EmbeddedDoc] = []
    for start in range(0, len(docs), batch_size):
        batch = docs[start:start + batch_size]
        attempt = 0
        while True:
            attempt += 1
            try:
                vectors = embed_batch([d.content for d in batch], url=url, model=model, timeout=timeout)
                break
            except Exception:
                if attempt >= 3 or len(batch) == 1:
                    raise
                time.sleep(2 * attempt)
        for doc, vector in zip(batch, vectors):
            arr = np.asarray(vector, dtype=np.float32)
            if arr.shape != (VECTOR_DIM,):
                raise RuntimeError(f"unexpected embedding dim for {doc.doc_id}: {arr.shape}")
            embedded.append(EmbeddedDoc(meta=doc, vector=arr))
        print(f"embedded {min(start + len(batch), len(docs))}/{len(docs)}", file=sys.stderr)
    return embedded


def open_zvec_collection(path: Path, *, rebuild: bool):
    import zvec
    from zvec import CollectionSchema, FieldSchema, VectorSchema
    from zvec.model.param import HnswIndexParam
    from zvec.typing import DataType, MetricType

    if rebuild and path.exists():
        shutil.rmtree(path)
    if path.exists():
        return zvec.open(path=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = CollectionSchema(
        name="observer_observations",
        fields=[
            FieldSchema("model", DataType.STRING, nullable=False),
            FieldSchema("thinking", DataType.STRING, nullable=False),
            FieldSchema("config", DataType.STRING, nullable=False),
            FieldSchema("task", DataType.STRING, nullable=False),
            FieldSchema("rep", DataType.INT32, nullable=False),
            FieldSchema("observation_id", DataType.STRING, nullable=False),
            FieldSchema("relevance", DataType.STRING, nullable=True),
            FieldSchema("token_count", DataType.INT32, nullable=False),
            FieldSchema("reward_partial", DataType.FLOAT, nullable=False),
            FieldSchema("reward_binary", DataType.INT32, nullable=True),
            FieldSchema("cell_path", DataType.STRING, nullable=False),
            FieldSchema("content", DataType.STRING, nullable=False),
        ],
        vectors=[
            VectorSchema(
                "embedding",
                DataType.VECTOR_FP32,
                dimension=VECTOR_DIM,
                index_param=HnswIndexParam(metric_type=MetricType.COSINE),
            )
        ],
    )
    return zvec.create_and_open(path=str(path), schema=schema)


def store_zvec(path: Path, docs: list[EmbeddedDoc], *, rebuild: bool) -> None:
    import zvec
    from zvec import Doc

    collection = open_zvec_collection(path, rebuild=rebuild)
    try:
        zdocs = []
        for item in docs:
            m = item.meta
            fields = {
                "model": m.model,
                "thinking": m.thinking,
                "config": m.config,
                "task": m.task,
                "rep": m.rep,
                "observation_id": m.observation_id,
                "relevance": m.relevance,
                "token_count": m.token_count,
                "reward_partial": float(m.reward_partial),
                "reward_binary": int(m.reward_binary) if m.reward_binary is not None else None,
                "cell_path": m.cell_path,
                "content": m.content,
            }
            zdocs.append(Doc(id=m.doc_id, fields=fields, vectors={"embedding": item.vector.tolist()}))
        for start in range(0, len(zdocs), 200):
            collection.insert(zdocs[start:start + 200])
    finally:
        # zvec API docs: flush() forces pending writes to disk; destroy()
        # permanently deletes the collection. Do not destroy the analysis store.
        collection.flush()


def normalize_matrix(vectors: list[np.ndarray]) -> np.ndarray:
    if not vectors:
        return np.zeros((0, VECTOR_DIM), dtype=np.float32)
    mat = np.vstack(vectors).astype(np.float32)
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def normalized_centroid(mat: np.ndarray) -> np.ndarray | None:
    if mat.shape[0] == 0:
        return None
    vec = mat.mean(axis=0)
    norm = float(np.linalg.norm(vec))
    if norm == 0.0:
        return None
    return vec / norm


def nn_metrics(candidate: np.ndarray, reference: np.ndarray) -> tuple[float, float, float]:
    """Return precision-ish, recall-ish, and F1-ish semantic overlap.

    precision-ish = each candidate observation's nearest reference observation.
    recall-ish    = each reference observation's nearest candidate observation.
    """
    if candidate.shape[0] == 0 or reference.shape[0] == 0:
        return (math.nan, math.nan, math.nan)
    sims = candidate @ reference.T
    precision = float(np.mean(np.max(sims, axis=1)))
    recall = float(np.mean(np.max(sims, axis=0)))
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def quality_by_config(
    *, model: str, thinking: str, configs: list[str], task_filter: set[str] | None
) -> dict[str, dict[str, float]]:
    root = REPO / "results" / model_leaf(model) / thinking
    out: dict[str, dict[str, float]] = {}
    for config in configs:
        by_task: dict[str, list[dict[str, Any]]] = {}
        for rp in (root / config).glob("*/rep*/result.json"):
            task = rp.parts[-3]
            if task_filter is not None and task not in task_filter:
                continue
            try:
                rec = json.loads(rp.read_text())
            except Exception:
                continue
            by_task.setdefault(str(rec.get("task") or task), []).append(rec)
        if not by_task:
            continue
        task_medians = []
        task_solves = []
        for rows in by_task.values():
            partials = [float(r.get("reward_partial") or 0.0) for r in rows]
            solves = [1.0 if r.get("reward_binary") == 1 else 0.0 for r in rows]
            task_medians.append(float(np.median(partials)))
            task_solves.append(float(np.mean(solves)))
        out[config] = {
            "quality_tasks": float(len(by_task)),
            "quality_cells": float(sum(len(v) for v in by_task.values())),
            "robust_partial": float(np.mean(task_medians)),
            "solve_rate": float(np.mean(task_solves)),
        }
    return out


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt_float(value: float | None, digits: int = 3) -> str:
    if value is None or math.isnan(value):
        return ""
    return f"{value:.{digits}f}"


def build_report(
    embedded: list[EmbeddedDoc], *, best_config: str, model: str, thinking: str, configs: list[str], task_filter: set[str] | None, out_dir: Path
) -> None:
    groups: dict[tuple[str, str], list[np.ndarray]] = {}
    obs_counts: dict[tuple[str, str], int] = {}
    token_counts: dict[tuple[str, str], int] = {}
    for item in embedded:
        key = (item.meta.config, item.meta.task)
        groups.setdefault(key, []).append(item.vector)
        obs_counts[key] = obs_counts.get(key, 0) + 1
        token_counts[key] = token_counts.get(key, 0) + item.meta.token_count

    best_tasks = {task for (config, task), vectors in groups.items() if config == best_config and vectors}
    if not best_tasks:
        raise SystemExit(f"best config has no embedded observations: {best_config}")

    per_task_rows: list[dict[str, Any]] = []
    for config in configs:
        for task in sorted(best_tasks):
            ref_vectors = groups.get((best_config, task), [])
            cand_vectors = groups.get((config, task), [])
            ref = normalize_matrix(ref_vectors)
            cand = normalize_matrix(cand_vectors)
            ref_centroid = normalized_centroid(ref)
            cand_centroid = normalized_centroid(cand)
            if ref_centroid is None or cand_centroid is None:
                centroid_similarity = math.nan
                centroid_distance = math.nan
            else:
                centroid_similarity = float(np.dot(cand_centroid, ref_centroid))
                centroid_distance = 1.0 - centroid_similarity
            precision, recall, f1 = nn_metrics(cand, ref)
            best_obs = obs_counts.get((best_config, task), 0)
            cand_obs = obs_counts.get((config, task), 0)
            per_task_rows.append({
                "task": task,
                "config": config,
                "best_config": best_config,
                "obs_count": cand_obs,
                "best_obs_count": best_obs,
                "obs_count_ratio": (cand_obs / best_obs) if best_obs else math.nan,
                "obs_tokens": token_counts.get((config, task), 0),
                "best_obs_tokens": token_counts.get((best_config, task), 0),
                "centroid_similarity": centroid_similarity,
                "centroid_distance": centroid_distance,
                "semantic_precision_vs_best": precision,
                "semantic_recall_vs_best": recall,
                "semantic_f1_vs_best": f1,
                "has_observations": bool(cand_obs),
            })

    # aggregate by config with equal task weight
    quality = quality_by_config(model=model, thinking=thinking, configs=configs, task_filter=task_filter)
    summary_rows: list[dict[str, Any]] = []
    for config in configs:
        rows = [r for r in per_task_rows if r["config"] == config]
        comparable = [r for r in rows if r["has_observations"] and not math.isnan(float(r["centroid_distance"]))]
        def avg(key: str, pool: list[dict[str, Any]] = comparable) -> float:
            vals = [float(r[key]) for r in pool if not math.isnan(float(r[key]))]
            return float(np.mean(vals)) if vals else math.nan
        def med(key: str, pool: list[dict[str, Any]] = comparable) -> float:
            vals = [float(r[key]) for r in pool if not math.isnan(float(r[key]))]
            return float(np.median(vals)) if vals else math.nan
        q = quality.get(config, {})
        summary_rows.append({
            "rank_by_semantic_f1": 0,
            "config": config,
            "best_config": best_config,
            "tasks_total": len(rows),
            "tasks_with_observations": len(comparable),
            "no_observation_tasks": len(rows) - len(comparable),
            "mean_centroid_distance": avg("centroid_distance"),
            "median_centroid_distance": med("centroid_distance"),
            "mean_semantic_precision_vs_best": avg("semantic_precision_vs_best"),
            "mean_semantic_recall_vs_best": avg("semantic_recall_vs_best"),
            "mean_semantic_f1_vs_best": avg("semantic_f1_vs_best"),
            "mean_obs_count_ratio": avg("obs_count_ratio", rows),
            "robust_partial": q.get("robust_partial", math.nan),
            "solve_rate": q.get("solve_rate", math.nan),
            "quality_tasks": q.get("quality_tasks", 0),
            "quality_cells": q.get("quality_cells", 0),
        })
    summary_rows.sort(key=lambda r: (float(r["mean_semantic_f1_vs_best"]), -float(r["mean_centroid_distance"])), reverse=True)
    for idx, row in enumerate(summary_rows, 1):
        row["rank_by_semantic_f1"] = idx

    write_jsonl(out_dir / "semantic-distance-per-task.jsonl", per_task_rows)
    write_csv(
        out_dir / "semantic-distance-per-task.csv",
        per_task_rows,
        [
            "task", "config", "best_config", "obs_count", "best_obs_count", "obs_count_ratio",
            "obs_tokens", "best_obs_tokens", "centroid_similarity", "centroid_distance",
            "semantic_precision_vs_best", "semantic_recall_vs_best", "semantic_f1_vs_best", "has_observations",
        ],
    )
    write_csv(
        out_dir / "semantic-distance-summary.csv",
        summary_rows,
        [
            "rank_by_semantic_f1", "config", "best_config", "tasks_total", "tasks_with_observations",
            "no_observation_tasks", "mean_centroid_distance", "median_centroid_distance",
            "mean_semantic_precision_vs_best", "mean_semantic_recall_vs_best", "mean_semantic_f1_vs_best",
            "mean_obs_count_ratio", "robust_partial", "solve_rate", "quality_tasks", "quality_cells",
        ],
    )

    md = out_dir / "semantic-distance-summary.md"
    with md.open("w") as f:
        f.write("# Observer semantic distance to best config\n\n")
        f.write(f"Best/reference config: `{best_config}`. Distances use Octen embeddings stored in zvec.\n\n")
        f.write("Nearest-neighbor metrics treat the best config's observation set for each task as the semantic reference. `recall` asks whether the candidate covers best observations; `precision` asks whether candidate observations are close to best observations.\n\n")
        f.write("| rank | config | semantic F1 | recall vs best | precision vs best | centroid distance | obs ratio | quality solve | robust partial | no-obs tasks |\n")
        f.write("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in summary_rows:
            f.write(
                f"| {row['rank_by_semantic_f1']} | {row['config']} | "
                f"{fmt_float(row['mean_semantic_f1_vs_best'])} | {fmt_float(row['mean_semantic_recall_vs_best'])} | "
                f"{fmt_float(row['mean_semantic_precision_vs_best'])} | {fmt_float(row['mean_centroid_distance'])} | "
                f"{fmt_float(row['mean_obs_count_ratio'])} | {fmt_float(row['solve_rate'])} | "
                f"{fmt_float(row['robust_partial'])} | {row['no_observation_tasks']} |\n"
            )
        f.write("\nOutputs:\n")
        f.write("- `observer-observations.zvec/` zvec collection with every observation embedding.\n")
        f.write("- `observer-observations.jsonl` metadata for each embedded observation.\n")
        f.write("- `semantic-distance-per-task.csv/jsonl` per-task distances.\n")
        f.write("- `semantic-distance-summary.csv` aggregate ranking.\n")


def write_observation_manifest(path: Path, docs: list[ObservationDoc]) -> None:
    rows = []
    for d in docs:
        rows.append({
            "doc_id": d.doc_id,
            "model": d.model,
            "thinking": d.thinking,
            "config": d.config,
            "task": d.task,
            "rep": d.rep,
            "observation_id": d.observation_id,
            "observation_index": d.observation_index,
            "relevance": d.relevance,
            "token_count": d.token_count,
            "content": d.content,
            "reward_partial": d.reward_partial,
            "reward_binary": d.reward_binary,
            "agent_timed_out": d.agent_timed_out,
            "cell_path": d.cell_path,
        })
    write_jsonl(path, rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--thinking", default="low")
    parser.add_argument("--configs", default="all", help="comma list or all observational-memory-* configs")
    parser.add_argument("--best", default=DEFAULT_BEST_CONFIG, help="reference/best config")
    parser.add_argument("--subset", default="12_v0")
    parser.add_argument("--tasks", help="comma-separated task ids; mutually exclusive with --subset")
    parser.add_argument("--embed-url", default=DEFAULT_EMBED_URL)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--keep-existing", action="store_true", help="do not delete existing zvec store before writing")
    args = parser.parse_args()

    result_root = REPO / "results" / model_leaf(args.model) / args.thinking
    configs = parse_configs(args.configs, result_root)
    if args.best not in configs:
        configs.append(args.best)
    task_filter = load_task_filter(args.subset, args.tasks)
    subset_label = args.subset or "custom"
    if args.out_dir is None:
        out_dir = DEFAULT_OUT_ROOT / f"{model_leaf(args.model)}-{args.thinking}-{subset_label}"
    else:
        out_dir = args.out_dir if args.out_dir.is_absolute() else REPO / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    docs = extract_observations(model=args.model, thinking=args.thinking, configs=configs, task_filter=task_filter)
    if not docs:
        raise SystemExit("no observer observations found")
    write_observation_manifest(out_dir / "observer-observations.jsonl", docs)

    embedded = embed_docs(docs, url=args.embed_url, model=args.embed_model, batch_size=args.batch_size, timeout=args.timeout)
    zvec_path = out_dir / "observer-observations.zvec"
    store_zvec(zvec_path, embedded, rebuild=not args.keep_existing)

    manifest = {
        "model": model_leaf(args.model),
        "thinking": args.thinking,
        "subset": args.subset,
        "configs": configs,
        "best_config": args.best,
        "embedding_url": args.embed_url,
        "embedding_model": args.embed_model,
        "embedding_dim": VECTOR_DIM,
        "observations": len(docs),
        "zvec_path": str(zvec_path.relative_to(REPO)),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    build_report(embedded, best_config=args.best, model=args.model, thinking=args.thinking, configs=configs, task_filter=task_filter, out_dir=out_dir)
    print(out_dir)
    print(f"embedded observations: {len(docs)}")
    print(f"zvec store: {zvec_path}")
    print(f"summary: {out_dir / 'semantic-distance-summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
