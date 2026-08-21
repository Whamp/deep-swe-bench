"""llama.cpp-backed scorer for the LLM-as-a-Verifier method.

Reuses the paper's own prompt builder and score extractor from the cloned
`llm_verifier` package (build_prompt, SCALE, extract_score). The only new
code is the transport: one OpenAI-compatible chat call to a local
llama.cpp server with logprobs=true / top_logprobs=20, adapted to the
(text, tokens, position_logprobs) shape extract_score expects.

Unlike the package's vLLM path, we do not use the prefill trick
(`continue_final_message` + `structured_outputs.choice` are vLLM/SGLang-only).
We rely on Qwen3.8-27B emitting the <score_A>/<score_B> tags itself; if the
tags are missing we retry once with a nudge (multi-turn, prefix stays cached).
Every call records the raw top-20 distribution at both score positions so the
discrete-judge baseline (argmax) is computed from the same data offline.
"""
import json
import time
import urllib.request

VALID = None  # lazy from llm_verifier


def _scale():
    global VALID
    if VALID is None:
        from llm_verifier.fine_grained_reward import SCALE
        VALID = SCALE["valid_tokens"]
    return VALID


def chat(base_url, model, messages, max_tokens=900, temperature=1.0,
         top_logprobs=20, timeout=1800):
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "logprobs": True,
        "top_logprobs": top_logprobs,
        # honored by llama.cpp's jinja chat template for Qwen3.x
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.load(r)
    latency = time.time() - t0
    choice = resp["choices"][0]
    text = choice["message"].get("content") or ""
    tokens, position_logprobs = None, None
    lp = choice.get("logprobs")
    if lp and lp.get("content"):
        tokens, position_logprobs = [], []
        for pos in lp["content"]:
            tokens.append(pos.get("token", ""))
            alts = [(a.get("token", ""), a.get("logprob", 0.0))
                    for a in (pos.get("top_logprobs") or [])]
            if not alts:
                alts = [(pos.get("token", ""), pos.get("logprob", 0.0))]
            position_logprobs.append(alts)
    usage = resp.get("usage") or {}
    return text, tokens, position_logprobs, usage, latency


def letter_distribution(tokens, position_logprobs, tag):
    """Raw {letter: prob} at the position after `tag`, for offline analysis.
    Mirrors extract_score's matching (strip, '>'-fused, last match)."""
    valid = _scale()
    if not tokens or not position_logprobs:
        return None
    # Same semantics as llm_verifier's _find_tag_logprobs: full tag first;
    # only if it never matches (fused '>X' tokenization) fall back to the
    # tag without '>'. The first suffix that matches ANYWHERE wins — do not
    # let the shorter suffix overwrite the full-tag match.
    found = None
    for suffix in (tag, tag[:-1]):
        found = None
        text_so_far = ""
        for i, tok in enumerate(tokens):
            text_so_far += tok
            if text_so_far.rstrip().endswith(suffix) and \
                    i + 1 < len(position_logprobs):
                found = position_logprobs[i + 1]  # LAST match for this suffix
        if found is not None:
            break
    if not found:
        return None
    import math
    probs = {}
    for tok_str, logprob in found:
        tok = tok_str.strip()
        if tok.startswith(">"):
            tok = tok[1:].strip()
        if tok in valid:
            p = math.exp(logprob)
            probs[tok] = max(probs.get(tok, 0.0), p)
    return probs or None


class Verifier:
    """Pairwise scorer: (problem, trace_a, trace_b, criterion) -> rewards."""

    def __init__(self, base_url, model, ground_truth_note=""):
        from llm_verifier.fine_grained_reward import build_prompt  # noqa
        from llm_verifier.fine_grained_reward import extract_score  # noqa
        self.base_url = base_url
        self.model = model
        self.gt_note = ground_truth_note
        self._build_prompt = build_prompt
        self._extract = extract_score

    def score_pair(self, problem, trace_a, trace_b, criterion):
        """Return dict(score_A, score_B, detail). Scores in [0, 1]."""
        prompt = self._build_prompt(problem, trace_a, trace_b, criterion,
                                    self.gt_note)
        messages = [{"role": "user", "content": prompt}]
        nudges = 0
        text, tokens, lps, usage, latency = chat(self.base_url, self.model,
                                                 messages)
        dist_a = letter_distribution(tokens, lps, "<score_A>")
        dist_b = letter_distribution(tokens, lps, "<score_B>")
        if dist_a is None or dist_b is None:
            # truncated or tags missing: nudge for just the score lines
            # (prefix is cached server-side, decode is short)
            nudges = 1
            messages = messages + [
                {"role": "assistant", "content": text},
                {"role": "user", "content":
                    "Now end with exactly these two lines, each a single "
                    "letter A-T:\n<score_A> X </score_A>\n"
                    "<score_B> Y </score_B>"},
            ]
            text2, tokens2, lps2, usage2, lat2 = chat(
                self.base_url, self.model, messages, max_tokens=200)
            text = (text or "") + "\n" + (text2 or "")
            tokens, lps = tokens2, lps2
            latency += lat2
            usage = {k: usage.get(k, 0) + usage2.get(k, 0)
                     for k in set(usage) | set(usage2)}
            dist_a = letter_distribution(tokens, lps, "<score_A>")
            dist_b = letter_distribution(tokens, lps, "<score_B>")
        ra = self._extract(text, tokens, lps, "<score_A>")
        rb = self._extract(text, tokens, lps, "<score_B>")
        return {
            "score_A": ra, "score_B": rb,
            "detail": {
                "dist_A": dist_a, "dist_B": dist_b,
                "argmax_A": max(dist_a, key=dist_a.get) if dist_a else None,
                "argmax_B": max(dist_b, key=dist_b.get) if dist_b else None,
                "nudges": nudges, "latency_s": round(latency, 1),
                "usage": usage, "analysis_chars": len(text),
                "analysis_tail": text[-600:],
            },
        }
