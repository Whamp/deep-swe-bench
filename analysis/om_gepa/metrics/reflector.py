from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def score_reflector_output(case: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    reflections = output.get("reflections", [])
    gold = case.get("goldReflections", [])
    allowed = {str(o.get("id")) for o in case.get("observations", []) if isinstance(o, dict) and o.get("id")}
    feedback: list[str] = []
    valid = True

    if not isinstance(reflections, list):
        return {"score": 0.0, "valid": False, "feedback": "reflections is not a list"}

    invalid_support = 0
    multiline = 0
    duplicates = 0
    seen: set[str] = set()
    support_counts: list[int] = []
    precision_hits = 0

    for ref in reflections:
        if not isinstance(ref, dict):
            valid = False
            feedback.append("non-object reflection emitted")
            continue
        content = str(ref.get("content", ""))
        norm = _norm(content)
        if norm in seen:
            duplicates += 1
        seen.add(norm)
        if "\n" in content or not content.strip():
            multiline += 1
        support = ref.get("supportingObservationIds", [])
        if not isinstance(support, list) or not support or any(str(sid) not in allowed for sid in support):
            invalid_support += 1
        else:
            support_counts.append(len(set(str(sid) for sid in support)))
        if gold:
            best = max(SequenceMatcher(None, norm, _norm(str(g.get("content", "")))).ratio() for g in gold if isinstance(g, dict))
            if best >= 0.52:
                precision_hits += 1

    recall_hits = 0
    for g in gold:
        if not isinstance(g, dict):
            continue
        best = max((SequenceMatcher(None, _norm(str(g.get("content", ""))), _norm(str(r.get("content", "")))).ratio() for r in reflections if isinstance(r, dict)), default=0.0)
        if best >= 0.52:
            recall_hits += 1

    precision = precision_hits / max(1, len(reflections))
    recall = recall_hits / max(1, len(gold))
    content_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    support_valid_rate = 1.0 - invalid_support / max(1, len(reflections))
    count_ratio = min(len(reflections), len(gold)) / max(1, max(len(reflections), len(gold))) if reflections or gold else 1.0
    avg_support = sum(support_counts) / max(1, len(support_counts))
    support_shape = min(1.0, avg_support / 3.0)

    penalties = 0.0
    for label, count in [
        ("invalid support ids", invalid_support),
        ("multiline/empty content", multiline),
        ("duplicate reflections", duplicates),
    ]:
        if count:
            valid = False
            feedback.append(f"{count} {label}")
            penalties += min(0.25, 0.06 * count)

    score = max(0.0, min(1.0, 0.58 * content_f1 + 0.22 * support_valid_rate + 0.10 * count_ratio + 0.10 * support_shape - penalties))
    if not feedback:
        feedback.append("reflector output passed deterministic support/schema checks")
    feedback.append(f"content_f1={content_f1:.3f}; precision={precision:.3f}; recall={recall:.3f}; count={len(reflections)} gold={len(gold)}; avg_support={avg_support:.2f}")
    return {"score": score, "valid": valid, "feedback": "; ".join(feedback)}
