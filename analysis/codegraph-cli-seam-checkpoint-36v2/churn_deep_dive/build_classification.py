#!/usr/bin/env python3
"""Assemble full flip classification: reviewer verdicts for the 6 meaningful flips
plus programmatic threshold-noise bucketing for the remaining 13."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
idx = json.loads((OUT / "flip_packets_index.json").read_text())

# Reviewer verdicts (transcribed from parallel delegate classification)
REVIEWER = {
    "claude-code-by-agents-recursive-delegation/0/seam_gain": {
        "primary_bucket": "verifier_artifact (OOM false positive)",
        "mechanism": "SEAM patch does NOT fix the provider context-array seam; it builds providerRequest with no `context` field (gold tests assert orchestratorCalls[1].context). SEAM's runDelegatedAgent returns a tool_result on circular detection, so its while-loop re-invokes the agent forever against the circular gold-test mock -> heap OOM -> vitest crashed AFTER writing reward.json with a degenerate all-pass JUnit (new.xml: 7 passed, time=0, no stdout). OLD scored a genuine 2/7 via a catchable stack overflow. The 7/7 is a verifier false positive, not a real solve.",
        "seam_text_plausibly_mattered": "no — not a real solve",
        "confidence": "high",
        "evidence": ["SEAM logs end with 'FATAL ERROR: ... JavaScript heap out of memory' AFTER reward.json f2p 7/7 written", "SEAM reports/new.xml degenerate: 7 passed, time=0, no stdout; same reporter's base_backend.xml has real timings", "SEAM patch grep for `context` returns zero matches -> structurally cannot pass the 5 context gold tests", "OLD reports/new.xml genuine: 5 real failures with real timings, all 'expected undefined to be defined' on continuationCall.context"],
    },
    "go-critic-doc-link-checker/0/seam_loss": {
        "primary_bucket": "capability-edge variance (misread stdlib signature)",
        "mechanism": "SEAM's checkMember binds the 3rd return of types.LookupFieldOrMethod (`indirect` bool = whether pointer indirection was needed) to `ok` and uses it as the found-indicator, instead of checking the 1st return (Object) for nil. Every valid method ref returns non-nil Object with indirect==false, so SEAM flags 5 valid methods as broken. Field cases pass only because a separate recursive hasStructField fallback (which OLD lacks) rescues them. PROVEN by applying patches + gold test to go-critic@9aea378: OLD passes, SEAM reproduces all 6 mismatches.",
        "seam_text_plausibly_mattered": "no",
        "confidence": "medium-high",
        "evidence": ["Whole delta is one line: OLD `if member,_,_ := LookupFieldOrMethod(...); member==nil` vs SEAM `if _,_,ok := LookupFieldOrMethod(...); ok`", "Reproduced on go-critic@9aea378: OLD patch -> PASS; SEAM patch -> FAIL with identical 6 mismatches", "Instrumented SEAM debug: failing methods all return obj=<method>, indirect=false", "Nothing in the seam text directs the model to misread a stdlib return signature"],
    },
    "go-critic-doc-link-checker/1/seam_loss": {
        "primary_bucket": "capability-edge variance (orthogonal edge-case gap)",
        "mechanism": "DIFFERENT bug than rep0. SEAM routes two-part DocLinks like [notimported.Foo] and [strings.NewReader] into the local-type-lookup path and emits 'type X not found in current package'; gold expects 'package X is not imported'. The agent's own positive_tests.go only covered the three-part [x.T.M] case, never the two-part case. SEAM actually DISCOVERED the correct LookupPackage semantics during exploration but did not carry it into the final checker. Two seam runs, two orthogonal defects = capability-edge variance.",
        "seam_text_plausibly_mattered": "no (proximate); weak aggregate signal only (old 2/2, seam 0/2)",
        "confidence": "medium",
        "evidence": ["rep1 verifier FAIL: 'type notimported not found' vs gold 'package notimported is not imported'", "SEAM's own positive_tests.go never included a two-part unimported-package case", "SEAM bash timeline shows it prototyped correct LookupPackage but final checker diverged", "rep0 and rep1 seam losses are orthogonal defects (method resolution vs package message) — signature of capability-edge variance"],
    },
    "etree-xml-diff-patch/2/seam_gain": {
        "primary_bucket": "real fix — chose correct behavioral seam (reuse existing API)",
        "mechanism": "OLD hand-rolled a custom selectElem selector parser (~49 lines) inside its patch that mis-resolved test selectors, making every ApplyPatch op a no-op. SEAM reused etree's existing (*Document).FindElement API (correct seam) + small removeSel/replaceSel helpers, producing a smaller correct patch. This DIRECTLY aligns with seam-skill's 'choose the behavioral seam before editing' + 'make the edit smaller' rules: SEAM ran 3 API-discovery greps (AddChild/RemoveChild/FindElement — the exact APIs it reused) and a self-verification go run that OLD never did.",
        "seam_text_plausibly_mattered": "yes (behavioral alignment is specific)",
        "confidence": "medium (~0.55; single rep + SEAM spent +136k tokens, so cannot separate seam-text from larger budget at n=1)",
        "evidence": ["OLD ApplyPatch calls custom selectElem (603 adds); SEAM calls doc.FindElement (563 adds) — seam is smaller where the skill demands it", "OLD verifier run.log: 5 Action=fail all TestApplyPatch*, all no-op symptom messages", "SEAM did 3 targeted etree-API greps + `go run /tmp/check.go` self-check absent from OLD", "Cost confound: SEAM +136k tokens / +$0.146 / +32.5s"],
    },
    "happy-dom-deterministic-intersectionobserver/1/seam_gain": {
        "primary_bucket": "real fix — async lifecycle correctness",
        "mechanism": "OLD's #queueCallback() is a one-shot setTimeout(0) that drains records once and never re-checks geometry or re-schedules, so post-initial-delivery threshold crossing is never detected (500ms timeout). SEAM's #scheduleCallback() is a self-rescheduling poll loop that re-runs #checkForIntersections() each tick and re-schedules while observations remain -> passes in 0.021s. Real deterministic correctness gap.",
        "seam_text_plausibly_mattered": "weak (the 'make edit smaller' rule is CONTRADICTED — SEAM patch larger 449 vs 357 lines; turns/tools/codegraph identical)",
        "confidence": "low-medium",
        "evidence": ["Single f2p test flipped: 'Detects threshold crossings in subsequent async delivery cycles' — OLD timeout 500ms, SEAM 0.021s", "SEAM #scheduleCallback self-reschedules + re-checks; OLD #queueCallback one-shot, no re-check", "Neither patch touches the grading test file -> gain from src impl", "SEAM patch LARGER (449 vs 357 lines) contradicts seam 'smaller edit' rule"],
    },
    "happy-dom-deterministic-intersectionobserver/2/seam_loss": {
        "primary_bucket": "variance (perfect cross-rep inversion, net skill effect = 0)",
        "mechanism": "PERFECT INVERSION with rep1: rep1 seam GAIN +0.0435, rep2 seam LOSS -0.0435 -> net skill effect across reps = 0. Skill-independent regularity: the losing patch in BOTH reps is the one that extracted a NEW file IIntersectionObserverInit.ts (rep1-old 13/14, rep2-seam 13/14); passing patches in both reps share the shape {IntersectionObserver.ts, test} with no extra interface file. SEAM rep2 also VIOLATED the 'make edit smaller' rule (larger patch, +6 tool calls, +112k tokens for a worse result).",
        "seam_text_plausibly_mattered": "no",
        "confidence": "high",
        "evidence": ["Cross-rep inversion: rep1 +0.0435 / rep2 -0.0435 -> net 0", "Losing patch in both reps extracts IIntersectionObserverInit.ts (over-abstraction)", "rep2-seam patch larger (429 lines/3 files) than old (362/2) — violates seam 'smaller edit' rule", "Only f2p moved (14->13); p2p 9/9 unchanged -> single borderline test"],
    },
}

classified = []
for p in idx:
    key = f"{p['task']}/{p['rep']}/{p['direction']}"
    o = p["old_skill"]["result"]; s = p["seam_skill"]["result"]
    base = {"task": p["task"], "rep": p["rep"], "direction": p["direction"],
            "delta_partial": p["cell"]["delta_partial"],
            "old_f2p": f"{o.get('f2p_passed')}/{o.get('f2p_total')}",
            "seam_f2p": f"{s.get('f2p_passed')}/{s.get('f2p_total')}",
            "old_p2p": f"{o.get('p2p_passed')}/{o.get('p2p_total')}",
            "seam_p2p": f"{s.get('p2p_passed')}/{s.get('p2p_total')}"}
    if key in REVIEWER:
        r = REVIEWER[key]
        base.update({"bucket": r["primary_bucket"], "mechanism": r["mechanism"],
                     "seam_text_plausibly_mattered": r["seam_text_plausibly_mattered"],
                     "confidence": r["confidence"], "evidence": r["evidence"], "category": "meaningful"})
    else:
        df2p = (s.get("f2p_passed", 0) - o.get("f2p_passed", 0))
        dp2p = (s.get("p2p_passed", 0) - o.get("p2p_passed", 0))
        base.update({"bucket": "threshold_noise", "category": "noise",
                     "mechanism": f"{'+' if df2p>=0 else ''}{df2p} f2p / {'+' if dp2p>=0 else ''}{dp2p} p2p boundary tests flipped; |Δpartial|={abs(p['cell']['delta_partial']):.4f}",
                     "seam_text_plausibly_mattered": "no", "confidence": "high",
                     "evidence": [f"Δf2p={df2p}, Δp2p={dp2p}, |Δpartial|<0.04 -> single-digit boundary test churn"]})
    classified.append(base)

(OUT / "classification.json").write_text(json.dumps({"method": "paired-trajectory packet extraction + parallel delegate reviewer classification for |Δpartial|>0.04 flips; programmatic threshold-noise bucketing for the rest", "flips": classified}, indent=2))
print(f"classified {len(classified)} flips -> {OUT/'classification.json'}")
# summary counts
from collections import Counter
cats = Counter(f["category"] for f in classified)
buckets = Counter(f["bucket"] for f in classified)
print("categories", dict(cats))
print("top buckets", dict(buckets.most_common(6)))
PY
