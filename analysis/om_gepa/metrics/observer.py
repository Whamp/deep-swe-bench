from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from ..common import RELEVANCE_VALUES, TIMESTAMP_RE


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _best_similarity(text: str, gold: list[dict[str, Any]]) -> float:
    if not gold:
        return 1.0 if not text else 0.0
    return max(SequenceMatcher(None, _norm(text), _norm(str(g.get("content", "")))).ratio() for g in gold)


def score_observer_output(case: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    observations = output.get("observations", [])
    gold = case.get("goldObservations", [])
    allowed = set(case.get("allowedSourceEntryIds", []))
    feedback: list[str] = []
    valid = True

    if not isinstance(observations, list):
        return {"score": 0.0, "valid": False, "feedback": "observations is not a list"}

    bad_source_ids = 0
    bad_timestamps = 0
    bad_relevance = 0
    multiline = 0
    duplicates = 0
    seen_content: set[str] = set()
    similarities: list[float] = []
    source_recall_hits = 0

    for obs in observations:
        if not isinstance(obs, dict):
            valid = False
            feedback.append("non-object observation emitted")
            continue
        content = str(obs.get("content", ""))
        norm = _norm(content)
        if norm in seen_content:
            duplicates += 1
        seen_content.add(norm)
        if "\n" in content or not content.strip():
            multiline += 1
        if obs.get("relevance") not in RELEVANCE_VALUES:
            bad_relevance += 1
        if not isinstance(obs.get("timestamp"), str) or not TIMESTAMP_RE.match(obs["timestamp"]):
            bad_timestamps += 1
        source_ids = obs.get("sourceEntryIds", [])
        if not isinstance(source_ids, list) or not source_ids or any(sid not in allowed for sid in source_ids):
            bad_source_ids += 1
        elif any(sid in set(gsid for g in gold for gsid in g.get("sourceEntryIds", [])) for sid in source_ids):
            source_recall_hits += 1
        similarities.append(_best_similarity(content, gold))

    gold_contents = [str(g.get("content", "")) for g in gold if isinstance(g, dict)]
    recall_scores = []
    for content in gold_contents:
        recall_scores.append(max((SequenceMatcher(None, _norm(content), _norm(str(o.get("content", "")))).ratio() for o in observations if isinstance(o, dict)), default=0.0))

    precision = sum(1 for s in similarities if s >= 0.55) / max(1, len(similarities))
    recall = sum(1 for s in recall_scores if s >= 0.55) / max(1, len(recall_scores))
    if precision + recall:
        content_f1 = 2 * precision * recall / (precision + recall)
    else:
        content_f1 = 0.0

    penalties = 0.0
    for label, count in [
        ("invented/invalid source ids", bad_source_ids),
        ("bad timestamps", bad_timestamps),
        ("bad relevance", bad_relevance),
        ("multiline/empty content", multiline),
        ("duplicate content", duplicates),
    ]:
        if count:
            valid = False
            feedback.append(f"{count} {label}")
            penalties += min(0.25, 0.05 * count)

    count_ratio = min(len(observations), len(gold)) / max(1, max(len(observations), len(gold))) if observations or gold else 1.0
    source_component = source_recall_hits / max(1, len(observations))
    score = max(0.0, min(1.0, 0.62 * content_f1 + 0.18 * source_component + 0.12 * count_ratio + 0.08 * (1.0 if valid else 0.0) - penalties))

    if not feedback:
        feedback.append("observer output passed deterministic schema/source checks")
    feedback.append(f"content_f1={content_f1:.3f}; precision={precision:.3f}; recall={recall:.3f}; count={len(observations)} gold={len(gold)}")
    return {"score": score, "valid": valid, "feedback": "; ".join(feedback)}
