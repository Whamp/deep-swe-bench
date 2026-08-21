---
name: write-benchmark-thread
description: Write a viral-but-honest X/Twitter thread for a benchmark or eval result (e.g. DeepSWE, ProgramBench, ponytail, pi-observational-memory runs). Use when the user asks to write, draft, rewrite, iterate on, or render a tweet thread about benchmark results, eval findings, A/B comparisons, agent evaluations, or model measurements, or says "thread", "tweet", "X post", or references the tweet-craft process. Enforces accuracy, human voice, and the accumulated review lessons. Read FEEDBACK_LOG.md before drafting.
argument-hint: <what the thread should cover>
---

# Write benchmark thread

Turn benchmark/eval results into a high-signal X/Twitter thread in a credible
human voice. Optimized for reach **without slop**: specific numbers, honest
scope, no AI prose tells, no over-claiming.

## Before you write anything — load context (do not skip)

1. **Read `tweet-craft/FEEDBACK_LOG.md` in full.** Every entry is a real mistake
   a reviewer caught. Treat them as hard constraints. **A fresh agent that skips
   this file repeats these mistakes.**
2. **Read `tweet-craft/THREAD_STRATEGY.md`** for the algorithm weights, hook
   data, METR template, and anti-slop research.
3. **Read `tweet-craft/HERO_IMAGE_PROCESS.md`** before making or requesting a
   hook image. The hero conclusion changes per analysis; preserve the reusable
   conclusion-first structure, not Ponytail-specific wording.
4. **Load the `clear-writing` skill** and apply Strunk's rules
   (active voice, concrete language, omit needless words). Load its
   `references/elements-of-style/03-elementary-principles-of-composition.md`
   for depth.
5. **Gather the actual results data** — paired deltas, difficulty buckets,
   solve counts, token/cost/patch sizes. Never invent a number. If a number
   isn't in the source data, say so or omit it.

## The process

1. **Find the surprise.** What would make a technical reader stop scrolling?
   State the tension (often "X and Y are both true"). This is the hook.
2. **Draft using the anatomy** (see THREAD_STRATEGY.md):
   - Hook (surprise + tension + specific number, no question, no list)
   - Preview (one-line payoff — the most-skipped tweet; do not skip)
   - Setup (the numbers, stated plainly, no "headline N ways" preamble)
   - Mechanism (why the result, not just what)
   - Cost / honest counter-result
   - Evidence (one concrete named example, never a wall of task names)
   - Synthesis (the generalizable lesson, scoped to what was tested)
   - Close (quotable standalone line + repo link + real question = reply bait)
   - Credit reply (tag every creator you built on)
3. **Run the pre-flight checklist** (below). Fix everything before review.
4. **Render for human review** over Tailscale (see "Review loop" below).
5. **Apply feedback → append to FEEDBACK_LOG.md → redraft.** This is the loop.
   If feedback is not logged, the next agent can't benefit and the iteration
   fails its purpose.

## Pre-flight checklist (must pass all before review)

Accuracy:
- [ ] No superlatives or unverifiable claims ("most popular", "the best").
- [ ] Every number is in the source data. None invented.
- [ ] Control and treatment named precisely (e.g. "unmodified Pi agent" vs
      "the Ponytail Pi extension"), never vague like "bare agent".
- [ ] Scope claims to what was measured. No generalizing one skill to all.

Voice (anti-slop — each is a logged failure mode):
- [ ] No setup phrases ("The headline, three ways", "Let me show you",
      "Here's the thing", "Worth noting").
- [ ] No self-referential closers ("in one sentence", "that's the takeaway").
- [ ] No strained metaphors. If a phrase needs parsing, rewrite it plainly.
- [ ] No false certainty. Use "can" where you mean possibility, not "does".
- [ ] No em-dashes as a connective in every clause.
- [ ] Active voice, concrete nouns, no needless words (Strunk §III).

Distribution:
- [ ] Hook has personal pronouns and a real question or tension (not a yes/no).
- [ ] **Hook tweet has a conclusion-first hero image** (images boost engagement
      +30-120%; the hook is the highest-value slot). It must be a dedicated
      scroll-stopping hero visual, NOT a dense analytical chart. Use
      `HERO_IMAGE_PROCESS.md`: preserve the reusable anatomy, but choose a new
      headline/conclusion/metrics for each analysis.
- [ ] No links or @s in the hook tweet.
- [ ] Each image is referenced by the tweet it attaches to.
- [ ] Primary metric is labeled inline so readers know what to weight.
- [ ] Credit tweet tags every creator; handles verified on X.
- [ ] Repo link only in the close, never the hook.

## Review loop (Tailscale, no Pi Annotate extension)

The `pi-annotate` extension's MV3 service worker sleeps and breaks auth on
remote machines. Use Lavish bound to the Tailnet IP instead:

```bash
cd <repo>
mkdir -p .lavish && cp <rendered>.html .lavish/   # + any relative assets
# lavish serves the file's directory; relative asset paths only, no leading /
LAVISH_AXI_HOST=100.112.72.93 LAVISH_AXI_LINK_HOST=100.112.72.93 \
  npx -y lavish-axi .lavish/<rendered>.html
# share the printed session URL with the reviewer's browser
# in another window, poll for feedback:
LAVISH_AXI_HOST=100.112.72.93 LAVISH_AXI_LINK_HOST=100.112.72.93 \
  npx -y lavish-axi poll .lavish/<rendered>.html
```

Lavish feedback posts over HTTP to the served origin, so it reaches the desktop
poll directly — no daemon pairing needed. Verify laptop→desktop fetch is HTTP
200 (session + artifact + first image) before asking the reviewer to act.

After feedback arrives: apply each annotation, **append every lesson to
`FEEDBACK_LOG.md`** as a (mistake → fix → why) entry under the right category,
then `--agent-reply` and re-poll.

## Images and charts

Use `tweet-craft/HERO_IMAGE_PROCESS.md` for the hook image. The hero should be
conclusion-first and reusable across analyses: different headline, different
facts, same disciplined anatomy.

Use the `benchmark-social-graphics` skill for all chart data. Deterministic
overlay only — never let an image-gen model place chart text or numbers
(it hallucinates them). Image-gen is for styled base cards or craft references
only; final benchmark facts must be rendered by code.

## What NOT to do

- Don't ship a draft that hasn't passed the pre-flight checklist.
- Don't apply reviewer feedback without also appending the lesson to
  FEEDBACK_LOG.md — unlogged feedback is lost to the next agent.
- Don't repeat a mistake already in FEEDBACK_LOG.md.
- Don't generalize claims beyond the experiment.
- Don't optimize for likes; replies (+27×) and bookmarks (+10×) dominate the
  ranking. Likes are nearly worthless by comparison.

## References

- `tweet-craft/FEEDBACK_LOG.md` — the growing lessons ledger (read first)
- `tweet-craft/THREAD_STRATEGY.md` — algorithm weights, hook data, METR template
- `tweet-craft/HERO_IMAGE_PROCESS.md` — reusable conclusion-first hero image process
- `tweet-craft/PONYTAIL_THREAD_REWRITE.md` — a worked example + its review notes
- `clear-writing` skill — Strunk + AI-writing-tell reference
- `benchmark-social-graphics` skill — deterministic chart overlays
- `x-thread-fetch` skill — extract existing threads for reference/templates
