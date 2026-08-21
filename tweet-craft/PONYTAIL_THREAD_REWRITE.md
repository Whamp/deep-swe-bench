# Ponytail DeepSWE thread — REWRITE v1

Rewritten from the original (`thread/PONYTAIL_THREAD.md`) applying the
`THREAD_STRATEGY.md` principles: surprise-first hook, preview tweet, METR-style
ordering (surprise → setup → mechanism → honest cost → takeaway → close),
de-slopped voice, load-bearing images, reply bait.

Design notes inline. Final text in the code blocks. ~8-9 tweets.

---

## Tweet 1 — HOOK (surprise + tension + number, no question)

Design: drop the yes/no question. Lead with the surprising result and the
tension. Personal pronoun. Specific numbers. Reply bait at the end.

```
I ran the most popular AI coding "skill" on Earth through 113 real engineering tasks.

Ponytail (57k★) wrote 26% less code, used 12% fewer tokens, and solved 2x the problems.

It also made easy tasks worse.

Both are true. Here's what happened 🧵
```

(280 char target. Mentions @DietrichGebert and @datacurve when posted.)

---

## Tweet 2 — PREVIEW (the most-skipped, highest-value tweet)

Design: one-line summary of what the thread covers. Sets up the payoff so
readers know what they get for swiping.

```
I tested the Ponytail skill (full Pi extension, default mode) against a bare
agent on DeepSWE, 113 tasks, DeepSeek V4 Flash, thinking high.

The short version: it's a trade, not a win. Smaller, cheaper, more decisive.
Also more brittle on the tasks you'd expect to be easy.
```

---

## Tweet 3 — SETUP + the surprising number, three ways (METR pattern)

Design: credibility + the headline numbers stated plainly. Image carries the
visual punch.

```
The headline, three ways:

- Full solves: baseline 2  →  Ponytail 4
- Mean partial reward: 0.774  →  0.709  (worse)
- Median patch size: 30.5kB  →  22.1kB  (smaller)

Same model, same tasks, same budget. The only variable was the skill. 👇
```

📎 **Image:** `images/0_ponytail-vs-baseline.jpg`
(caption in tweet: "Baseline vs Ponytail, 113 DeepSWE tasks")

---

## Tweet 4 — THE MECHANISM (why it's a trade, not noise)

Design: this is the core insight tweet. The "two modes" frame is the most
quotable idea in the whole dataset. Make it standalone and punchy.

```
Ponytail isn't "better" or "worse." It has two modes on this benchmark:

✂️ Good pruning: fewer reads, fewer edits, smaller patch, same result.
🔥 Over-pruning: drops the test/fixture/wiring that makes a fix complete.

The benchmark score is the tension between those two.
```

📎 **Image:** `images/5_two-modes.jpg`

---

## Tweet 5 — THE HONEST COST (why easy tasks regressed)

Design: the bad news, framed as the mechanism's consequence. One concrete
example, not a wall of task names. Image shows the difficulty split.

```
Where over-pruning bit: easy and medium tasks.

The pattern was almost always the same. The agent lands the fix in the obvious
core layer, declares done, and never wires up the integration tests or exports
that make it actually pass.

Smaller patch. Missing executable spec.
```

📎 **Image:** `images/1_easy-medium-regression.jpg`

---

## Tweet 6 — EVIDENCE (one concrete example, not a list dump)

Design: one named example beats five. Keep it readable for a public audience.
Avoid the inside-baseball task-name wall from the original.

```
Concrete case: one task Ponytail solved at 100% in the baseline dropped to 0%.

The fix was correct. It just dropped the test files that would have forced the
agent to wire up the rest. "Write less code" became "skip the part that proves
it works."

That's the failure mode in one sentence.
```

📎 **Image:** `images/2_failure-modes.jpg`

---

## Tweet 7 — SYNTHESIS (the generalizable lesson — drives reposts)

Design: the takeaway tweet. This is the one people screenshot. Standalone,
quotable, no jargon.

```
The lesson, for anyone using AI coding skills:

"Write less code" and "stop early" are cheap heuristics. They save tokens. They
also make the agent skip the unglamorous wiring, tests, and exports that turn a
plausible fix into a complete one.

Decisiveness has a cost. Know which mode you're in.
```

---

## Tweet 8 — CLOSE (quotable + CTA + reply bait)

Design: the screenshot tweet. Repo link here (NOT in the hook — links suppress
reach). End with a real question for reply velocity.

```
Repo + full repro: github.com/Whamp/deep-swe-bench
(113 tasks, ~$50, ~1B tokens, all open)

Cost $50 and 1B tokens to answer one question: is this skill worth your time?

Next I'm testing Pi-Observational-Memory and Pi-Advisor.

What skill or extension should I benchmark after that?
```

(Drop the repo link as a reply, or keep it here since it's the close not the
hook. @kunchenguid credit reply below.)

---

## Reply (to post after thread) — CREDIT

```
Inspired by @kunchenguid's ProgramBench TDD tests.
Original post: https://x.com/kunchenguid/status/2064196342248030352
```

---

## What changed vs the original, and why

| Original | Rewrite | Why |
|---|---|---|
| Hook = "is it actually good?" (yes/no question, lowest reach) | Hook = surprising numbers + "both are true" tension | Curiosity/how-to hooks reach 6-40× more than question hooks |
| No preview tweet; jumped to "The good" list | Tweet 2 = one-line result summary | Skipping the preview is the #1 mid-tier thread mistake (Quip data) |
| Order: good → bad → mechanism | Order: surprise → setup → mechanism → cost → takeaway (METR) | METR's viral RCT thread is the genre template |
| Wall of 5 task names (actionlint/adaptix/yjs/textual/true-myth) | One concrete example, "fix was correct, dropped the tests" | Inside-baseball lists read as slop to a public audience |
| Close = "reach out to me" + cost + "what next" | Close = quotable lesson + repo + real question | Last tweet should be the screenshot/share tweet; question drives the +27× reply signal |
| Em-dashes, bullet walls, hedging | Short sentences, present tense, no em-dashes | De-slop per LLM-pattern-filter rules |
| Images attached but never referenced | Each image referenced by what it shows | Images get +30-120% engagement when load-bearing |
| Repo link in hook-adjacent area | Repo link only in close | Links in early tweets suppress reach |
| "What should I test next?" buried | Question is the final line of the close | Reply bait at the end captures the +27× reply weight + author-engagement loop |

## Open decisions for you

1. **Hook length:** v1 is ~4 lines. Want it tighter to 2-3 lines for more dwell
   friction?
2. **The "both are true" framing:** I leaned into the tension (good AND bad).
   Alternative is pure curiosity ("the result surprised me"). Which feels more
   your voice?
3. **Credit placement:** original had a dedicated credit tweet mid-thread. I
   moved it to a reply to avoid breaking the narrative arc. Keep as reply, or
   restore as a tweet?
4. **Numbers in the hook:** I used 26% / 12% / 2x. The original used the same.
   These are the strongest specifics; confirm they're the ones you want lead.
