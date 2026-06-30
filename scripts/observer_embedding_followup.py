#!/usr/bin/env python3
"""Follow-up analyses for observational-memory observer embeddings.

Inputs are produced by scripts/observer_embedding_distance.py:
- observer-observations.jsonl
- observer-observations.zvec/

This script does not call the embedding service. It reuses the persisted zvec
vectors and derives durable CSV/JSONL/Markdown artifacts for:
1. unique-observation mining between two reference configs,
2. per-task topic clustering and topic coverage,
3. helpful/harmful topic correlation,
4. heuristic observation-type classification,
5. timeliness-adjusted topic/observation coverage,
6. pairwise complementarity scores.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import zvec

REPO = Path(__file__).resolve().parents[1]
DEFAULT_BASE = REPO / "analysis" / "observer-embeddings" / "gpt55-low-12v0-all-observers"
DEFAULT_LEFT = "observational-memory-glm52-off"
DEFAULT_RIGHT = "observational-memory-gpt54mini-low"
SOURCE_TYPES = {"message", "custom_message", "branch_summary"}
VECTOR_DIM = 2560


@dataclass
class Observation:
    doc_id: str
    config: str
    task: str
    rep: int
    observation_id: str
    observation_index: int
    content: str
    token_count: int
    relevance: str
    reward_partial: float
    reward_binary: int | None
    agent_timed_out: bool
    cell_path: str
    vector: np.ndarray | None = None
    primary_type: str = "other"
    type_flags: tuple[str, ...] = ()
    covers_up_to_id: str | None = None
    source_count: int | None = None
    covers_source_index: int | None = None
    source_coverage_fraction: float | None = None
    phase: str = "unknown"
    append_timestamp: str | None = None
    topic_id: str | None = None


@dataclass
class Topic:
    topic_id: str
    task: str
    member_doc_ids: list[str] = field(default_factory=list)
    vector_sum: np.ndarray | None = None
    centroid: np.ndarray | None = None
    representative_doc_id: str | None = None
    representative_text: str = ""
    primary_type: str = "other"

    def add(self, obs: Observation) -> None:
        if obs.vector is None:
            raise ValueError("missing vector")
        self.member_doc_ids.append(obs.doc_id)
        if self.vector_sum is None:
            self.vector_sum = obs.vector.astype(np.float32).copy()
        else:
            self.vector_sum += obs.vector.astype(np.float32)
        norm = float(np.linalg.norm(self.vector_sum))
        self.centroid = self.vector_sum / norm if norm else self.vector_sum


@dataclass(frozen=True)
class CellQuality:
    config: str
    task: str
    rep: int
    reward_partial: float
    reward_binary: int | None
    agent_timed_out: bool
    result_path: str

    @property
    def solved(self) -> int:
        return 1 if self.reward_binary == 1 else 0


class Analysis:
    def __init__(self, base_dir: Path, out_dir: Path, left: str, right: str, cluster_threshold: float, unique_threshold: float):
        self.base_dir = base_dir
        self.out_dir = out_dir
        self.left = left
        self.right = right
        self.gold_configs = {left, right}
        self.cluster_threshold = cluster_threshold
        self.unique_threshold = unique_threshold
        self.docs: list[Observation] = []
        self.docs_by_id: dict[str, Observation] = {}
        self.topics: dict[str, Topic] = {}
        self.cell_quality: dict[tuple[str, str, int], CellQuality] = {}
        self.cell_topics: dict[tuple[str, str, int], set[str]] = defaultdict(set)

    # ---------- Loading ----------

    def load(self) -> None:
        self.docs = load_observations(self.base_dir / "observer-observations.jsonl")
        self.docs_by_id = {d.doc_id: d for d in self.docs}
        vectors = load_vectors(self.base_dir / "observer-observations.zvec", list(self.docs_by_id))
        missing = sorted(set(self.docs_by_id) - set(vectors))
        if missing:
            raise RuntimeError(f"zvec is missing {len(missing)} observation vectors; first={missing[:3]}")
        for doc_id, vector in vectors.items():
            self.docs_by_id[doc_id].vector = vector
        for doc in self.docs:
            doc.primary_type, doc.type_flags = classify_observation(doc.content)
        augment_timeliness(self.docs)
        self.cell_quality = load_cell_quality(self.docs)

    # ---------- Analysis 1: unique observations ----------

    def unique_observation_mining(self) -> None:
        out = self.out_dir / "unique-observations-glm52-off-vs-gpt54mini-low"
        out.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, Any]] = []
        for source, target in [(self.left, self.right), (self.right, self.left)]:
            source_docs = [d for d in self.docs if d.config == source and d.vector is not None]
            target_by_task: dict[str, list[Observation]] = defaultdict(list)
            for d in self.docs:
                if d.config == target and d.vector is not None:
                    target_by_task[d.task].append(d)
            for d in source_docs:
                candidates = target_by_task.get(d.task, [])
                best_sim = math.nan
                best: Observation | None = None
                if candidates:
                    mat = np.vstack([c.vector for c in candidates if c.vector is not None])
                    sims = mat @ d.vector  # type: ignore[operator]
                    idx = int(np.argmax(sims))
                    best_sim = float(sims[idx])
                    best = candidates[idx]
                rows.append({
                    "direction": f"{source} -> {target}",
                    "source_config": source,
                    "target_config": target,
                    "task": d.task,
                    "rep": d.rep,
                    "observation_id": d.observation_id,
                    "doc_id": d.doc_id,
                    "nearest_similarity": best_sim,
                    "is_unique_lt_threshold": bool(not math.isnan(best_sim) and best_sim < self.unique_threshold),
                    "is_environment_tooling_note": is_environment_tooling_note(d.content),
                    "primary_type": d.primary_type,
                    "type_flags": ";".join(d.type_flags),
                    "relevance": d.relevance,
                    "token_count": d.token_count,
                    "content": d.content,
                    "nearest_doc_id": best.doc_id if best else "",
                    "nearest_rep": best.rep if best else "",
                    "nearest_primary_type": best.primary_type if best else "",
                    "nearest_content": best.content if best else "",
                })
        write_csv(out / "nearest-neighbor-observations.csv", rows)
        write_jsonl(out / "nearest-neighbor-observations.jsonl", rows)

        summary_rows: list[dict[str, Any]] = []
        for direction, group in groupby(rows, "direction").items():
            sims = [float(r["nearest_similarity"]) for r in group if not math.isnan(float(r["nearest_similarity"]))]
            unique = [r for r in group if r["is_unique_lt_threshold"]]
            substantive = [r for r in group if not r["is_environment_tooling_note"]]
            substantive_unique = [r for r in substantive if r["is_unique_lt_threshold"]]
            summary_rows.append({
                "direction": direction,
                "observations": len(group),
                "unique_lt_threshold": len(unique),
                "unique_rate": len(unique) / len(group) if group else math.nan,
                "environment_tooling_notes": len(group) - len(substantive),
                "substantive_observations": len(substantive),
                "substantive_unique_lt_threshold": len(substantive_unique),
                "substantive_unique_rate": len(substantive_unique) / len(substantive) if substantive else math.nan,
                "mean_nearest_similarity": float(np.mean(sims)) if sims else math.nan,
                "median_nearest_similarity": float(np.median(sims)) if sims else math.nan,
                "threshold": self.unique_threshold,
            })
        write_csv(out / "summary.csv", summary_rows)

        with (out / "examples.md").open("w") as f:
            f.write("# Unique observations: GLM-5.2 off vs GPT-5.4-mini low\n\n")
            f.write(f"Nearest-neighbor search is task-local. An observation is marked unique when its best cross-config neighbor has cosine similarity `< {self.unique_threshold}`.\n\n")
            f.write("## Summary\n\n")
            f.write("| direction | observations | unique | unique rate | environment/tooling notes | substantive unique rate | mean nearest sim | median nearest sim |\n")
            f.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")
            for r in summary_rows:
                f.write(f"| {r['direction']} | {r['observations']} | {r['unique_lt_threshold']} | {fmt(r['unique_rate'])} | {r['environment_tooling_notes']} | {fmt(r['substantive_unique_rate'])} | {fmt(r['mean_nearest_similarity'])} | {fmt(r['median_nearest_similarity'])} |\n")
            for direction in [f"{self.left} -> {self.right}", f"{self.right} -> {self.left}"]:
                f.write(f"\n## Lowest-similarity examples: {direction}\n\n")
                examples = sorted([r for r in rows if r["direction"] == direction], key=lambda r: float(r["nearest_similarity"]))[:8]
                for r in examples:
                    write_unique_example(f, r)
                f.write(f"\n## Lowest-similarity substantive examples: {direction}\n\n")
                examples = sorted([r for r in rows if r["direction"] == direction and not r["is_environment_tooling_note"]], key=lambda r: float(r["nearest_similarity"]))[:12]
                for r in examples:
                    write_unique_example(f, r)

    # ---------- Analysis 2: topic clustering and coverage ----------

    def cluster_topics(self) -> None:
        out = self.out_dir / "topic-clusters"
        out.mkdir(parents=True, exist_ok=True)
        for task in sorted({d.task for d in self.docs}):
            task_docs = sorted([d for d in self.docs if d.task == task and d.vector is not None], key=lambda d: (d.config, d.rep, d.observation_index, d.doc_id))
            task_topics: list[Topic] = []
            for doc in task_docs:
                if not task_topics:
                    topic = Topic(topic_id=f"{safe_task(task)}-topic-000", task=task)
                    topic.add(doc)
                    task_topics.append(topic)
                    doc.topic_id = topic.topic_id
                    continue
                centroids = np.vstack([t.centroid for t in task_topics if t.centroid is not None])
                sims = centroids @ doc.vector  # type: ignore[operator]
                best_idx = int(np.argmax(sims))
                if float(sims[best_idx]) >= self.cluster_threshold:
                    topic = task_topics[best_idx]
                else:
                    topic = Topic(topic_id=f"{safe_task(task)}-topic-{len(task_topics):03d}", task=task)
                    task_topics.append(topic)
                topic.add(doc)
                doc.topic_id = topic.topic_id
            for topic in task_topics:
                finalize_topic(topic, self.docs_by_id)
                self.topics[topic.topic_id] = topic

        for d in self.docs:
            if d.topic_id:
                self.cell_topics[(d.config, d.task, d.rep)].add(d.topic_id)

        topic_rows = []
        for topic in sorted(self.topics.values(), key=lambda t: (t.task, t.topic_id)):
            members = [self.docs_by_id[i] for i in topic.member_doc_ids]
            configs = sorted({m.config for m in members})
            cells = sorted({f"{m.config}/{m.task}/rep{m.rep}" for m in members})
            topic_rows.append({
                "topic_id": topic.topic_id,
                "task": topic.task,
                "size_observations": len(members),
                "configs": len(configs),
                "cells": len(cells),
                "primary_type": topic.primary_type,
                "member_configs": ";".join(configs),
                "representative_doc_id": topic.representative_doc_id,
                "representative_text": topic.representative_text,
            })
        write_jsonl(out / "topics.jsonl", topic_rows)
        write_csv(out / "topics.csv", topic_rows)

        assignment_rows = []
        for d in self.docs:
            assignment_rows.append({
                "doc_id": d.doc_id,
                "topic_id": d.topic_id,
                "config": d.config,
                "task": d.task,
                "rep": d.rep,
                "observation_index": d.observation_index,
                "primary_type": d.primary_type,
                "phase": d.phase,
                "source_coverage_fraction": d.source_coverage_fraction,
                "content": d.content,
            })
        write_csv(out / "observation-topic-assignments.csv", assignment_rows)

        coverage_rows = self.topic_coverage_rows()
        write_csv(out / "topic-coverage-by-config.csv", coverage_rows)
        with (out / "summary.md").open("w") as f:
            f.write("# Topic clustering and coverage\n\n")
            f.write(f"Observations were clustered separately per task using greedy centroid clustering at cosine threshold `{self.cluster_threshold}`. Coverage counts each topic at most once per config/task/rep, so duplicate verbosity does not increase topic coverage.\n\n")
            f.write(f"Total topics: {len(self.topics)} across {len(set(t.task for t in self.topics.values()))} tasks.\n\n")
            f.write("| config | topics covered | topic recall | gold topic recall | mean task topic recall | obs/topic | solve | robust partial |\n")
            f.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")
            for r in sorted(coverage_rows, key=lambda r: (r["gold_topic_recall"], r["topic_recall"]), reverse=True):
                f.write(f"| {r['config']} | {r['topics_covered']} | {fmt(r['topic_recall'])} | {fmt(r['gold_topic_recall'])} | {fmt(r['mean_task_topic_recall'])} | {fmt(r['observations_per_topic_covered'])} | {fmt(r['solve_rate'])} | {fmt(r['robust_partial'])} |\n")

    def topic_coverage_rows(self) -> list[dict[str, Any]]:
        configs = sorted({d.config for d in self.docs})
        all_topics = set(self.topics)
        topics_by_task: dict[str, set[str]] = defaultdict(set)
        gold_topics: set[str] = set()
        for topic_id, topic in self.topics.items():
            topics_by_task[topic.task].add(topic_id)
        for d in self.docs:
            if d.config in self.gold_configs and d.topic_id:
                gold_topics.add(d.topic_id)

        quality = quality_by_config(self.cell_quality)
        rows = []
        for config in configs:
            docs = [d for d in self.docs if d.config == config]
            covered = {d.topic_id for d in docs if d.topic_id}
            task_recalls = []
            for task, task_topics in topics_by_task.items():
                task_covered = {d.topic_id for d in docs if d.task == task and d.topic_id}
                if task_topics:
                    task_recalls.append(len(task_covered & task_topics) / len(task_topics))
            q = quality.get(config, {})
            rows.append({
                "config": config,
                "topics_total": len(all_topics),
                "topics_covered": len(covered),
                "topic_recall": len(covered) / len(all_topics) if all_topics else math.nan,
                "gold_topics_total": len(gold_topics),
                "gold_topics_covered": len(covered & gold_topics),
                "gold_topic_recall": len(covered & gold_topics) / len(gold_topics) if gold_topics else math.nan,
                "mean_task_topic_recall": float(np.mean(task_recalls)) if task_recalls else math.nan,
                "observations": len(docs),
                "observations_per_topic_covered": len(docs) / len(covered) if covered else math.nan,
                "robust_partial": q.get("robust_partial", math.nan),
                "solve_rate": q.get("solve_rate", math.nan),
                "quality_cells": q.get("quality_cells", 0),
            })
        return rows

    # ---------- Analysis 3: helpful/harmful topic correlation ----------

    def topic_correlation(self) -> None:
        out = self.out_dir / "topic-correlation"
        out.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, Any]] = []
        cells_by_task: dict[str, list[CellQuality]] = defaultdict(list)
        for cell in self.cell_quality.values():
            cells_by_task[cell.task].append(cell)
        topic_categories = self.topic_category_flags()
        for topic in self.topics.values():
            task_cells = cells_by_task.get(topic.task, [])
            present: list[CellQuality] = []
            absent: list[CellQuality] = []
            for cell in task_cells:
                if topic.topic_id in self.cell_topics.get((cell.config, cell.task, cell.rep), set()):
                    present.append(cell)
                else:
                    absent.append(cell)
            present_partial = mean([c.reward_partial for c in present])
            absent_partial = mean([c.reward_partial for c in absent])
            present_solve = mean([c.solved for c in present])
            absent_solve = mean([c.solved for c in absent])
            rows.append({
                "topic_id": topic.topic_id,
                "task": topic.task,
                "primary_type": topic.primary_type,
                "type_flags": ";".join(sorted(topic_categories.get(topic.topic_id, set()))),
                "present_cells": len(present),
                "absent_cells": len(absent),
                "present_partial_mean": present_partial,
                "absent_partial_mean": absent_partial,
                "partial_delta_present_minus_absent": present_partial - absent_partial if not math.isnan(present_partial) and not math.isnan(absent_partial) else math.nan,
                "present_solve_rate": present_solve,
                "absent_solve_rate": absent_solve,
                "solve_delta_present_minus_absent": present_solve - absent_solve if not math.isnan(present_solve) and not math.isnan(absent_solve) else math.nan,
                "representative_text": topic.representative_text,
            })
        write_csv(out / "topic-quality-correlation.csv", rows)
        helpful = sorted([r for r in rows if r["present_cells"] >= 3 and r["absent_cells"] >= 3 and not math.isnan(r["partial_delta_present_minus_absent"])], key=lambda r: float(r["partial_delta_present_minus_absent"]), reverse=True)
        harmful = sorted(helpful, key=lambda r: float(r["partial_delta_present_minus_absent"]))
        with (out / "summary.md").open("w") as f:
            f.write("# Helpful vs harmful topic correlation\n\n")
            f.write("For each task-specific topic, cells where the topic appears are compared against same-task cells where it does not. This is correlational, not causal; task/config/repetition effects are not fully controlled.\n\n")
            f.write("## Most positive partial-reward correlations\n\n")
            write_topic_table(f, helpful[:15])
            f.write("\n## Most negative partial-reward correlations\n\n")
            write_topic_table(f, harmful[:15])
            poison = [r for r in harmful if "self_reported_completion" in str(r["type_flags"]) or r["primary_type"] == "self_reported_completion"][:12]
            f.write("\n## Potential poison-memory topics: self-reported completion with negative correlation\n\n")
            if poison:
                write_topic_table(f, poison)
            else:
                f.write("No self-reported-completion topics met the support threshold with negative partial correlation.\n")

    def topic_category_flags(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = defaultdict(set)
        for d in self.docs:
            if d.topic_id:
                out[d.topic_id].add(d.primary_type)
                out[d.topic_id].update(d.type_flags)
        return out

    # ---------- Analysis 4: observation type classification ----------

    def observation_type_split(self) -> None:
        out = self.out_dir / "observation-type-classification"
        out.mkdir(parents=True, exist_ok=True)
        rows = []
        for d in self.docs:
            rows.append({
                "doc_id": d.doc_id,
                "config": d.config,
                "task": d.task,
                "rep": d.rep,
                "primary_type": d.primary_type,
                "type_flags": ";".join(d.type_flags),
                "phase": d.phase,
                "source_coverage_fraction": d.source_coverage_fraction,
                "content": d.content,
            })
        write_csv(out / "observation-types.csv", rows)
        write_jsonl(out / "observation-types.jsonl", rows)

        config_rows = []
        for config, group in groupby(self.docs, "config").items():
            counts = Counter(d.primary_type for d in group)
            total = len(group)
            q = quality_by_config(self.cell_quality).get(config, {})
            row = {"config": config, "observations": total, "solve_rate": q.get("solve_rate", math.nan), "robust_partial": q.get("robust_partial", math.nan)}
            for cat in OBS_TYPES:
                row[f"{cat}_count"] = counts.get(cat, 0)
                row[f"{cat}_share"] = counts.get(cat, 0) / total if total else math.nan
            config_rows.append(row)
        write_csv(out / "type-summary-by-config.csv", config_rows)

        level_rows = []
        for level, group in groupby(self.docs, lambda d: config_level(d.config)).items():
            counts = Counter(d.primary_type for d in group)
            total = len(group)
            row = {"observer_thinking_level": level, "observations": total, "configs": len({d.config for d in group})}
            for cat in OBS_TYPES:
                row[f"{cat}_count"] = counts.get(cat, 0)
                row[f"{cat}_share"] = counts.get(cat, 0) / total if total else math.nan
            level_rows.append(row)
        write_csv(out / "type-summary-by-thinking-level.csv", level_rows)

        with (out / "summary.md").open("w") as f:
            f.write("# Observation type split\n\n")
            f.write("Classification is deterministic and heuristic. It is meant to surface patterns for inspection, not replace human review. Multi-label flags are retained, while `primary_type` is a single highest-priority bucket.\n\n")
            f.write("| config | obs | requirement | code structure | implementation | test/failure | self-report | solve | robust partial |\n")
            f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
            for r in sorted(config_rows, key=lambda r: r["config"]):
                f.write(f"| {r['config']} | {r['observations']} | {fmt(r['task_requirement_share'])} | {fmt(r['code_structure_share'])} | {fmt(r['implementation_state_share'])} | {fmt(r['test_failure_share'])} | {fmt(r['self_reported_completion_share'])} | {fmt(r['solve_rate'])} | {fmt(r['robust_partial'])} |\n")
            f.write("\n## By observer thinking level\n\n")
            f.write("| level | obs | configs | requirement | code structure | implementation | test/failure | self-report |\n")
            f.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")
            for r in sorted(level_rows, key=lambda r: r["observer_thinking_level"]):
                f.write(f"| {r['observer_thinking_level']} | {r['observations']} | {r['configs']} | {fmt(r['task_requirement_share'])} | {fmt(r['code_structure_share'])} | {fmt(r['implementation_state_share'])} | {fmt(r['test_failure_share'])} | {fmt(r['self_reported_completion_share'])} |\n")

    # ---------- Analysis 5: timeliness ----------

    def timeliness(self) -> None:
        out = self.out_dir / "timeliness-adjusted-coverage"
        out.mkdir(parents=True, exist_ok=True)
        rows = []
        config_rows = []
        topics_by_task: dict[str, set[str]] = defaultdict(set)
        for topic in self.topics.values():
            topics_by_task[topic.task].add(topic.topic_id)
        for config in sorted({d.config for d in self.docs}):
            config_docs = [d for d in self.docs if d.config == config]
            phase_counts = Counter(d.phase for d in config_docs)
            topic_by_phase: dict[str, set[str]] = {"early": set(), "mid": set(), "late": set(), "unknown": set()}
            for d in config_docs:
                if d.topic_id:
                    topic_by_phase.setdefault(d.phase, set()).add(d.topic_id)
            early_or_mid = topic_by_phase.get("early", set()) | topic_by_phase.get("mid", set())
            all_seen = set().union(*topic_by_phase.values()) if topic_by_phase else set()
            total_topics = len(self.topics)
            q = quality_by_config(self.cell_quality).get(config, {})
            config_rows.append({
                "config": config,
                "observations": len(config_docs),
                "early_obs_share": phase_counts.get("early", 0) / len(config_docs) if config_docs else math.nan,
                "mid_obs_share": phase_counts.get("mid", 0) / len(config_docs) if config_docs else math.nan,
                "late_obs_share": phase_counts.get("late", 0) / len(config_docs) if config_docs else math.nan,
                "unknown_obs_share": phase_counts.get("unknown", 0) / len(config_docs) if config_docs else math.nan,
                "mean_source_coverage_fraction": mean([d.source_coverage_fraction for d in config_docs if d.source_coverage_fraction is not None]),
                "early_topics": len(topic_by_phase.get("early", set())),
                "early_or_mid_topics": len(early_or_mid),
                "final_topics": len(all_seen),
                "early_topic_recall": len(topic_by_phase.get("early", set())) / total_topics if total_topics else math.nan,
                "early_or_mid_topic_recall": len(early_or_mid) / total_topics if total_topics else math.nan,
                "final_topic_recall": len(all_seen) / total_topics if total_topics else math.nan,
                "solve_rate": q.get("solve_rate", math.nan),
                "robust_partial": q.get("robust_partial", math.nan),
            })
            for task, task_topics in topics_by_task.items():
                docs = [d for d in config_docs if d.task == task]
                seen = {d.topic_id for d in docs if d.topic_id}
                early = {d.topic_id for d in docs if d.topic_id and d.phase == "early"}
                mid_or_early = {d.topic_id for d in docs if d.topic_id and d.phase in {"early", "mid"}}
                rows.append({
                    "config": config,
                    "task": task,
                    "observations": len(docs),
                    "topics_total": len(task_topics),
                    "topics_seen": len(seen),
                    "topics_seen_early": len(early),
                    "topics_seen_early_or_mid": len(mid_or_early),
                    "final_topic_recall": len(seen) / len(task_topics) if task_topics else math.nan,
                    "early_topic_recall": len(early) / len(task_topics) if task_topics else math.nan,
                    "early_or_mid_topic_recall": len(mid_or_early) / len(task_topics) if task_topics else math.nan,
                    "mean_source_coverage_fraction": mean([d.source_coverage_fraction for d in docs if d.source_coverage_fraction is not None]),
                })
        write_csv(out / "timeliness-by-config.csv", config_rows)
        write_csv(out / "timeliness-by-config-task.csv", rows)
        with (out / "summary.md").open("w") as f:
            f.write("# Timeliness-adjusted semantic coverage\n\n")
            f.write("Timeliness uses the observational-memory `coversUpToId` watermark mapped onto the final source-entry sequence in each session. Early/mid/late are thirds of final source-entry coverage. This measures whether memories landed early enough in the run, not wall-clock latency directly.\n\n")
            f.write("| config | early topic recall | early+mid topic recall | final topic recall | early obs share | late obs share | mean source coverage | solve | robust partial |\n")
            f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
            for r in sorted(config_rows, key=lambda r: r["early_or_mid_topic_recall"], reverse=True):
                f.write(f"| {r['config']} | {fmt(r['early_topic_recall'])} | {fmt(r['early_or_mid_topic_recall'])} | {fmt(r['final_topic_recall'])} | {fmt(r['early_obs_share'])} | {fmt(r['late_obs_share'])} | {fmt(r['mean_source_coverage_fraction'])} | {fmt(r['solve_rate'])} | {fmt(r['robust_partial'])} |\n")

    # ---------- Analysis 6: complementarity ----------

    def complementarity(self) -> None:
        out = self.out_dir / "pairwise-complementarity"
        out.mkdir(parents=True, exist_ok=True)
        configs = sorted({d.config for d in self.docs})
        config_topics = {c: {d.topic_id for d in self.docs if d.config == c and d.topic_id} for c in configs}
        total_topics = len(self.topics)
        task_quality = task_quality_by_config(self.cell_quality)
        quality = quality_by_config(self.cell_quality)
        rows = []
        for a, b in itertools.combinations(configs, 2):
            at = config_topics[a]
            bt = config_topics[b]
            union = at | bt
            inter = at & bt
            unique_a = at - bt
            unique_b = bt - at
            tasks = sorted(set(task_quality.get(a, {})) | set(task_quality.get(b, {})))
            oracle_partial = []
            oracle_solve = []
            for task in tasks:
                aq = task_quality.get(a, {}).get(task)
                bq = task_quality.get(b, {}).get(task)
                if aq and bq:
                    oracle_partial.append(max(aq["median_partial"], bq["median_partial"]))
                    oracle_solve.append(max(aq["solve_rate"], bq["solve_rate"]))
            qa = quality.get(a, {})
            qb = quality.get(b, {})
            rows.append({
                "config_a": a,
                "config_b": b,
                "topics_a": len(at),
                "topics_b": len(bt),
                "topics_union": len(union),
                "topics_overlap": len(inter),
                "unique_topics_a": len(unique_a),
                "unique_topics_b": len(unique_b),
                "union_topic_recall": len(union) / total_topics if total_topics else math.nan,
                "jaccard_overlap": len(inter) / len(union) if union else math.nan,
                "unique_add_a_over_b": len(unique_a) / len(at) if at else math.nan,
                "unique_add_b_over_a": len(unique_b) / len(bt) if bt else math.nan,
                "solve_a": qa.get("solve_rate", math.nan),
                "solve_b": qb.get("solve_rate", math.nan),
                "robust_partial_a": qa.get("robust_partial", math.nan),
                "robust_partial_b": qb.get("robust_partial", math.nan),
                "oracle_solve_rate": mean(oracle_solve),
                "oracle_robust_partial": mean(oracle_partial),
            })
        write_csv(out / "pairwise-complementarity.csv", rows)
        target = [r for r in rows if {r["config_a"], r["config_b"]} == self.gold_configs]
        with (out / "summary.md").open("w") as f:
            f.write("# Pairwise topic complementarity\n\n")
            f.write("Complementarity uses deduplicated topic coverage, not raw observation counts. `oracle_*` is a per-task quality oracle over the two configs' task-level medians/solve rates; it is descriptive and not an achievable combined-agent score by itself.\n\n")
            if target:
                r = target[0]
                f.write("## GLM-5.2 off + GPT-5.4-mini low\n\n")
                f.write("| pair | union topic recall | jaccard overlap | unique topics A | unique topics B | oracle solve | oracle robust partial |\n")
                f.write("|---|---:|---:|---:|---:|---:|---:|\n")
                f.write(f"| {r['config_a']} + {r['config_b']} | {fmt(r['union_topic_recall'])} | {fmt(r['jaccard_overlap'])} | {r['unique_topics_a']} | {r['unique_topics_b']} | {fmt(r['oracle_solve_rate'])} | {fmt(r['oracle_robust_partial'])} |\n\n")
            f.write("## Top pairs by union topic recall\n\n")
            write_pair_table(f, sorted(rows, key=lambda r: r["union_topic_recall"], reverse=True)[:15])
            f.write("\n## Low-overlap high-quality pairs\n\n")
            candidates = [r for r in rows if not math.isnan(r["oracle_robust_partial"])]
            candidates.sort(key=lambda r: (r["oracle_robust_partial"], -r["jaccard_overlap"], r["union_topic_recall"]), reverse=True)
            write_pair_table(f, candidates[:15])

    # ---------- Bonus: rep-to-rep self-consistency ----------

    def rep_self_consistency(self) -> None:
        out = self.out_dir / "rep-self-consistency"
        out.mkdir(parents=True, exist_ok=True)
        by_cell: dict[tuple[str, str, int], list[Observation]] = defaultdict(list)
        for d in self.docs:
            if d.vector is not None:
                by_cell[(d.config, d.task, d.rep)].append(d)
        pair_rows: list[dict[str, Any]] = []
        configs = sorted({d.config for d in self.docs})
        tasks = sorted({d.task for d in self.docs})
        for config in configs:
            for task in tasks:
                reps = sorted(rep for (c, t, rep), docs in by_cell.items() if c == config and t == task and docs)
                for rep_a, rep_b in itertools.combinations(reps, 2):
                    a = np.vstack([d.vector for d in by_cell[(config, task, rep_a)] if d.vector is not None])
                    b = np.vstack([d.vector for d in by_cell[(config, task, rep_b)] if d.vector is not None])
                    metrics = rep_pair_metrics(a, b)
                    pair_rows.append({
                        "config": config,
                        "task": task,
                        "rep_a": rep_a,
                        "rep_b": rep_b,
                        "obs_a": a.shape[0],
                        "obs_b": b.shape[0],
                        **metrics,
                    })
        write_csv(out / "per-rep-pair.csv", pair_rows)
        quality = quality_by_config(self.cell_quality)
        summary_rows: list[dict[str, Any]] = []
        for config in configs:
            rows = [r for r in pair_rows if r["config"] == config]
            q = quality.get(config, {})
            summary_rows.append({
                "rank_by_self_consistency": 0,
                "config": config,
                "rep_pairs": len(rows),
                "tasks_with_pairs": len({r["task"] for r in rows}),
                "mean_rep_pair_semantic_f1": mean(r["semantic_f1"] for r in rows),
                "median_rep_pair_semantic_f1": float(np.median([r["semantic_f1"] for r in rows])) if rows else math.nan,
                "mean_centroid_distance": mean(r["centroid_distance"] for r in rows),
                "mean_close_counterpart_f1_085": mean(r["close_counterpart_f1_085"] for r in rows),
                "mean_obs_count_per_side": mean([r["obs_a"] for r in rows] + [r["obs_b"] for r in rows]),
                "solve_rate": q.get("solve_rate", math.nan),
                "robust_partial": q.get("robust_partial", math.nan),
            })
        summary_rows.sort(key=lambda r: (r["mean_rep_pair_semantic_f1"], r["mean_close_counterpart_f1_085"]), reverse=True)
        for i, row in enumerate(summary_rows, 1):
            row["rank_by_self_consistency"] = i
        write_csv(out / "summary.csv", summary_rows)
        with (out / "summary.md").open("w") as f:
            f.write("# Observer rep-to-rep self-consistency\n\n")
            f.write("For each config/task, this compares every pair of reps by nearest-neighbor semantic overlap between recorded observations. Higher F1 means more similar memory content across independent reps of the same task; it is not necessarily better.\n\n")
            f.write("| rank | config | rep pairs | semantic F1 | close F1 @ .85 | centroid distance | mean obs/side | solve | robust partial |\n")
            f.write("|---:|---|---:|---:|---:|---:|---:|---:|---:|\n")
            for r in summary_rows:
                f.write(f"| {r['rank_by_self_consistency']} | {r['config']} | {r['rep_pairs']} | {fmt(r['mean_rep_pair_semantic_f1'])} | {fmt(r['mean_close_counterpart_f1_085'])} | {fmt(r['mean_centroid_distance'])} | {fmt(r['mean_obs_count_per_side'])} | {fmt(r['solve_rate'])} | {fmt(r['robust_partial'])} |\n")

    # ---------- Orchestration ----------

    def run_all(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.unique_observation_mining()
        self.cluster_topics()
        self.topic_correlation()
        self.observation_type_split()
        self.timeliness()
        self.complementarity()
        self.rep_self_consistency()
        self.write_index()

    def write_index(self) -> None:
        with (self.out_dir / "FOLLOWUP_ANALYSIS_INDEX.md").open("w") as f:
            f.write("# Observer embedding follow-up analysis index\n\n")
            f.write(f"Source embedding directory: `{self.base_dir.relative_to(REPO)}`\n\n")
            f.write(f"Observations loaded: {len(self.docs)}. Topics clustered: {len(self.topics)}. Cluster threshold: `{self.cluster_threshold}`. Unique threshold: `{self.unique_threshold}`.\n\n")
            f.write("## Generated analyses\n\n")
            f.write("1. `unique-observations-glm52-off-vs-gpt54mini-low/` — task-local nearest-neighbor uniqueness between the two best configs.\n")
            f.write("2. `topic-clusters/` — per-task semantic topic clusters plus deduplicated config coverage.\n")
            f.write("3. `topic-correlation/` — correlational topic presence vs solve/partial outcomes.\n")
            f.write("4. `observation-type-classification/` — deterministic heuristic requirement/code/implementation/test/self-report split.\n")
            f.write("5. `timeliness-adjusted-coverage/` — source-watermark phase and early/mid/final topic coverage.\n")
            f.write("6. `pairwise-complementarity/` — pairwise topic union, overlap, unique additions, and quality oracle.\n")
            f.write("7. `rep-self-consistency/` — refreshed rep-to-rep semantic consistency with all completed cells.\n\n")
            f.write("## Caveats\n\n")
            f.write("- Topic clustering is deterministic greedy centroid clustering; thresholds affect topic granularity.\n")
            f.write("- Topic-quality correlations are descriptive, not causal, and are noisy on 12_v0.\n")
            f.write("- Observation type labels are heuristic and should be spot-checked before strong claims.\n")
            f.write("- Timeliness uses OM coverage watermarks over source entries, not raw wall-clock observer latency.\n")


# ---------- Standalone helpers ----------


def load_observations(path: Path) -> list[Observation]:
    docs: list[Observation] = []
    with path.open() as f:
        for line in f:
            row = json.loads(line)
            docs.append(Observation(
                doc_id=row["doc_id"],
                config=row["config"],
                task=row["task"],
                rep=int(row["rep"]),
                observation_id=row["observation_id"],
                observation_index=int(row["observation_index"]),
                content=row["content"],
                token_count=int(row.get("token_count") or 0),
                relevance=row.get("relevance") or "",
                reward_partial=float(row.get("reward_partial") or 0.0),
                reward_binary=row.get("reward_binary"),
                agent_timed_out=bool(row.get("agent_timed_out")),
                cell_path=row["cell_path"],
            ))
    return docs


def load_vectors(zvec_path: Path, ids: list[str]) -> dict[str, np.ndarray]:
    collection = zvec.open(path=str(zvec_path.resolve()))
    vectors: dict[str, np.ndarray] = {}
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        fetched = collection.fetch(chunk, include_vector=True)
        for doc_id, doc in fetched.items():
            vector = np.asarray(doc.vector("embedding"), dtype=np.float32)
            norm = float(np.linalg.norm(vector))
            if norm:
                vector = vector / norm
            vectors[doc_id] = vector
    collection.flush()
    return vectors


def augment_timeliness(docs: list[Observation]) -> None:
    by_cell: dict[str, list[Observation]] = defaultdict(list)
    for d in docs:
        by_cell[d.cell_path].append(d)
    by_cell_obs: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    for d in docs:
        by_cell_obs[(d.cell_path, d.observation_id)].append(d)

    for cell_path, cell_docs in by_cell.items():
        root = REPO / cell_path
        session_dir = root / "session"
        if not session_dir.exists():
            continue
        entries = []
        for session_file in sorted(session_dir.glob("*.jsonl")):
            for line in session_file.read_text(errors="replace").splitlines():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
        source_entries = [e for e in entries if e.get("type") in SOURCE_TYPES]
        source_pos = {e.get("id"): idx for idx, e in enumerate(source_entries) if e.get("id")}
        source_count = len(source_entries)
        for d in cell_docs:
            d.source_count = source_count
        for e in entries:
            if e.get("type") == "custom" and e.get("customType") == "om.observations.recorded":
                data = e.get("data") or {}
                covers_id = data.get("coversUpToId")
                covers_index = source_pos.get(covers_id)
                if covers_index is None:
                    # Fallback: use max cited source entry position in this batch.
                    cited = []
                    for obs in data.get("observations") or []:
                        for source_id in obs.get("sourceEntryIds") or []:
                            if source_id in source_pos:
                                cited.append(source_pos[source_id])
                    covers_index = max(cited) if cited else None
                fraction = ((covers_index + 1) / source_count) if covers_index is not None and source_count else None
                phase = phase_for_fraction(fraction)
                for obs in data.get("observations") or []:
                    candidates = by_cell_obs.get((cell_path, str(obs.get("id"))), [])
                    for d in candidates:
                        if d.content == str(obs.get("content") or "").strip() or len(candidates) == 1:
                            d.covers_up_to_id = covers_id
                            d.covers_source_index = covers_index
                            d.source_coverage_fraction = fraction
                            d.phase = phase
                            d.append_timestamp = e.get("timestamp")
                            break


def phase_for_fraction(value: float | None) -> str:
    if value is None or math.isnan(value):
        return "unknown"
    if value <= 1 / 3:
        return "early"
    if value <= 2 / 3:
        return "mid"
    return "late"


OBS_TYPES = ["task_requirement", "code_structure", "implementation_state", "test_failure", "self_reported_completion", "other"]

REQ_RE = re.compile(r"\b(user (requested|specified|asked|wants?)|task (asks|requires)|must|should|expected|requirement|accepts?|rejects?|needs? to)\b", re.I)
CODE_RE = re.compile(r"(\b(file|module|class|function|method|type|schema|parser|AST|API|interface|field|struct|enum)\b|[\w./-]+\.(py|ts|tsx|js|go|rs|java|json|yaml|yml|toml)\b)", re.I)
IMPL_RE = re.compile(r"\b(current|implemented|implementation|added|modified|updated|changed|created|wired|returns?|sets?|stores?|uses?|calls?|branch|commit|patch)\b", re.I)
TEST_RE = re.compile(r"\b(test|tests|pytest|cargo check|cargo test|go test|npm test|failure|failed|failing|error|exception|traceback|compile|compiler|panic|E\d{4}|verifier|hidden)\b", re.I)
SELF_RE = re.compile(r"\b(agent|assistant|implementation|patch)\b.*\b(implemented|completed|added|modified|updated|changed|created|fixed|committed|finished)\b|^Agent\b", re.I)


def classify_observation(text: str) -> tuple[str, tuple[str, ...]]:
    flags = []
    if REQ_RE.search(text):
        flags.append("task_requirement")
    if CODE_RE.search(text):
        flags.append("code_structure")
    if IMPL_RE.search(text):
        flags.append("implementation_state")
    if TEST_RE.search(text):
        flags.append("test_failure")
    if SELF_RE.search(text):
        flags.append("self_reported_completion")
    if not flags:
        return "other", ("other",)
    for primary in ["test_failure", "self_reported_completion", "implementation_state", "task_requirement", "code_structure"]:
        if primary in flags:
            return primary, tuple(flags)
    return flags[0], tuple(flags)


def load_cell_quality(docs: list[Observation]) -> dict[tuple[str, str, int], CellQuality]:
    roots = sorted({REPO / d.cell_path for d in docs})
    # Expand to all result cells in each config, not only cells with observations.
    config_roots = sorted({p.parents[1] for p in roots})
    task_filter = {d.task for d in docs}
    out: dict[tuple[str, str, int], CellQuality] = {}
    for config_root in config_roots:
        config = config_root.name
        for result_json in sorted(config_root.glob("*/rep*/result.json")):
            task = result_json.parts[-3]
            if task not in task_filter:
                continue
            try:
                row = json.loads(result_json.read_text())
            except Exception:
                continue
            rep = int(result_json.parent.name.replace("rep", ""))
            rb = row.get("reward_binary")
            out[(config, task, rep)] = CellQuality(
                config=config,
                task=str(row.get("task") or task),
                rep=rep,
                reward_partial=float(row.get("reward_partial") or 0.0),
                reward_binary=int(rb) if isinstance(rb, int) else None,
                agent_timed_out=bool(row.get("agent_timed_out")),
                result_path=str(result_json.relative_to(REPO)),
            )
    return out


def quality_by_config(cells: dict[tuple[str, str, int], CellQuality]) -> dict[str, dict[str, float]]:
    by_config_task: dict[tuple[str, str], list[CellQuality]] = defaultdict(list)
    for cell in cells.values():
        by_config_task[(cell.config, cell.task)].append(cell)
    by_config: dict[str, list[dict[str, float]]] = defaultdict(list)
    for (config, _task), rows in by_config_task.items():
        by_config[config].append({
            "median_partial": float(np.median([r.reward_partial for r in rows])),
            "solve_rate": float(np.mean([r.solved for r in rows])),
            "cells": float(len(rows)),
        })
    out = {}
    for config, rows in by_config.items():
        out[config] = {
            "robust_partial": float(np.mean([r["median_partial"] for r in rows])),
            "solve_rate": float(np.mean([r["solve_rate"] for r in rows])),
            "quality_tasks": float(len(rows)),
            "quality_cells": float(sum(r["cells"] for r in rows)),
        }
    return out


def task_quality_by_config(cells: dict[tuple[str, str, int], CellQuality]) -> dict[str, dict[str, dict[str, float]]]:
    by_config_task: dict[tuple[str, str], list[CellQuality]] = defaultdict(list)
    for cell in cells.values():
        by_config_task[(cell.config, cell.task)].append(cell)
    out: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for (config, task), rows in by_config_task.items():
        out[config][task] = {
            "median_partial": float(np.median([r.reward_partial for r in rows])),
            "solve_rate": float(np.mean([r.solved for r in rows])),
            "cells": float(len(rows)),
        }
    return out


def finalize_topic(topic: Topic, docs_by_id: dict[str, Observation]) -> None:
    members = [docs_by_id[i] for i in topic.member_doc_ids]
    if topic.centroid is None:
        return
    sims = [(float(d.vector @ topic.centroid), d) for d in members if d.vector is not None]
    sims.sort(key=lambda x: x[0], reverse=True)
    if sims:
        rep = sims[0][1]
        topic.representative_doc_id = rep.doc_id
        topic.representative_text = rep.content
    type_counts = Counter(d.primary_type for d in members)
    topic.primary_type = type_counts.most_common(1)[0][0] if type_counts else "other"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    columns = list(rows[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def groupby(items: Iterable[Any], key: str | Any) -> dict[Any, list[Any]]:
    out: dict[Any, list[Any]] = defaultdict(list)
    if isinstance(key, str):
        for item in items:
            if isinstance(item, dict):
                out[item[key]].append(item)
            else:
                out[getattr(item, key)].append(item)
    else:
        for item in items:
            out[key(item)].append(item)
    return dict(out)


def mean(values: Iterable[float | int | None]) -> float:
    clean = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    return float(np.mean(clean)) if clean else math.nan


def fmt(value: Any, digits: int = 3) -> str:
    try:
        v = float(value)
    except Exception:
        return ""
    if math.isnan(v):
        return ""
    return f"{v:.{digits}f}"


def blockquote(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.splitlines()) + "\n"


def safe_task(task: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", task)


def config_level(config: str) -> str:
    for level in ["xhigh", "max", "high", "medium", "low", "off"]:
        if config.endswith(f"-{level}"):
            return level
    return "unknown"


ENV_TOOLING_RE = re.compile(r"\b(rg|ripgrep|grep|find)\b.*\b(unavailable|not available|not installed|not found|command not found|used instead)\b|\b(unavailable|not available|not installed|not found|command not found)\b.*\b(rg|ripgrep)\b", re.I)


def is_environment_tooling_note(text: str) -> bool:
    return bool(ENV_TOOLING_RE.search(text))


def write_unique_example(f, r: dict[str, Any]) -> None:
    note = " · environment/tooling" if r.get("is_environment_tooling_note") else ""
    f.write(f"### {r['task']} rep{r['rep']} · sim {fmt(r['nearest_similarity'], 3)} · {r['primary_type']}{note}\n\n")
    f.write("Observation:\n\n")
    f.write(blockquote(str(r["content"])))
    f.write("\nNearest other-config observation:\n\n")
    f.write(blockquote(str(r["nearest_content"])))
    f.write("\n")


def write_topic_table(f, rows: list[dict[str, Any]]) -> None:
    if not rows:
        f.write("No rows met the support threshold.\n")
        return
    f.write("| topic | task | type | present | absent | partial Δ | solve Δ | representative |\n")
    f.write("|---|---|---|---:|---:|---:|---:|---|\n")
    for r in rows:
        rep = str(r["representative_text"]).replace("|", "\\|")[:180]
        f.write(f"| {r['topic_id']} | {r['task']} | {r['primary_type']} | {r['present_cells']} | {r['absent_cells']} | {fmt(r['partial_delta_present_minus_absent'])} | {fmt(r['solve_delta_present_minus_absent'])} | {rep} |\n")


def rep_pair_metrics(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    if a.shape[0] == 0 or b.shape[0] == 0:
        return {
            "semantic_precision_a_to_b": math.nan,
            "semantic_recall_b_to_a": math.nan,
            "semantic_f1": math.nan,
            "centroid_distance": math.nan,
            "close_counterpart_rate_a_to_b_085": math.nan,
            "close_counterpart_rate_b_to_a_085": math.nan,
            "close_counterpart_f1_085": math.nan,
        }
    sims = a @ b.T
    a_to_b = np.max(sims, axis=1)
    b_to_a = np.max(sims, axis=0)
    precision = float(np.mean(a_to_b))
    recall = float(np.mean(b_to_a))
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    ca = a.mean(axis=0)
    cb = b.mean(axis=0)
    cdist = float(1 - np.dot(ca / np.linalg.norm(ca), cb / np.linalg.norm(cb))) if np.linalg.norm(ca) and np.linalg.norm(cb) else math.nan
    close_ab = float(np.mean(a_to_b >= 0.85))
    close_ba = float(np.mean(b_to_a >= 0.85))
    close_f1 = 2 * close_ab * close_ba / (close_ab + close_ba) if close_ab + close_ba else 0.0
    return {
        "semantic_precision_a_to_b": precision,
        "semantic_recall_b_to_a": recall,
        "semantic_f1": f1,
        "centroid_distance": cdist,
        "close_counterpart_rate_a_to_b_085": close_ab,
        "close_counterpart_rate_b_to_a_085": close_ba,
        "close_counterpart_f1_085": close_f1,
    }


def write_pair_table(f, rows: list[dict[str, Any]]) -> None:
    f.write("| config A | config B | union recall | overlap | unique A | unique B | oracle solve | oracle partial |\n")
    f.write("|---|---|---:|---:|---:|---:|---:|---:|\n")
    for r in rows:
        f.write(f"| {r['config_a']} | {r['config_b']} | {fmt(r['union_topic_recall'])} | {fmt(r['jaccard_overlap'])} | {r['unique_topics_a']} | {r['unique_topics_b']} | {fmt(r['oracle_solve_rate'])} | {fmt(r['oracle_robust_partial'])} |\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--out-dir", type=Path, help="default: <base-dir>/followup-analysis")
    parser.add_argument("--left", default=DEFAULT_LEFT)
    parser.add_argument("--right", default=DEFAULT_RIGHT)
    parser.add_argument("--unique-threshold", type=float, default=0.80)
    parser.add_argument("--cluster-threshold", type=float, default=0.84)
    args = parser.parse_args()

    base = args.base_dir if args.base_dir.is_absolute() else REPO / args.base_dir
    out = args.out_dir or (base / "followup-analysis")
    out = out if out.is_absolute() else REPO / out
    analysis = Analysis(base, out, args.left, args.right, args.cluster_threshold, args.unique_threshold)
    analysis.load()
    analysis.run_all()
    print(out)
    print(f"observations={len(analysis.docs)} topics={len(analysis.topics)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
