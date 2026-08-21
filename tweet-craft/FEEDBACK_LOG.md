# Benchmark thread feedback log

Append-only ledger of concrete lessons learned from reviewing real benchmark
threads. **Read this before drafting any new thread** — every entry below is a
mistake a reviewer caught on a real draft. Grouped by category. Each entry:
the bad pattern, the fix, and why.

A fresh-context agent that skips this file will repeat these mistakes.

## How to use this log

- **Before drafting:** read the whole file. These are known failure modes.
- **After a review round:** append new (mistake → fix → why) entries under the
  right category. Date and source-thread each entry.
- **When drafting:** treat every entry as a hard constraint, not a suggestion.

Categories: [Accuracy](#accuracy) · [Voice / anti-slop](#voice--anti-slop) ·
[False certainty & over-generalization](#false-certainty--over-generalization) ·
[Precise language](#precise-language) · [Credits & distribution](#credits--distribution) · [Process](#process)

---

## Accuracy

Never over-claim. Credibility is lost faster than it is earned, and one
overstatement makes the whole thread suspect.

### 2026-06-26 · Ponytail DeepSWE thread (round 1)

**Bad:** "I ran the most popular AI coding skill on Earth through 113 tasks."
**Fix:** "I tested a 'write less code' AI skill on 113 tasks." State only what
the benchmark actually measured. Star count is a verifiable fact; "most popular"
is an unverifiable superlative.
**Why:** Over-claiming signals hype and costs credibility with the technical
audience we want. The hook's job is surprise + tension, not puffery. If a claim
isn't something the reader can verify in one click, cut it.

### 2026-06-26 · Ponytail DeepSWE thread (round 1)

**Bad:** "The only variable was the skill."
**Fix:** "The only variable was the Ponytail Pi extension."
**Why:** Accuracy. The arm under test was the full Pi *extension*, not just the
skill prompt. "Skill" is a different (narrower) thing in Pi. Get the noun right.
When two terms could describe the treatment, use the one that matches what was
actually loaded.

---

## Voice / anti-slop

LLM prose regressions to statistical means. These are the tells a reviewer
flags as "feels written by an AI." Cut them on sight.

### 2026-06-26 · Ponytail DeepSWE thread (round 1)

**Bad:** "The headline, three ways:" as a setup line for three bullet stats.
**Fix:** State the numbers plainly, no meta-setup. e.g. "Full solves: 2 → 4.
Mean partial reward: 0.774 → 0.709."
**Why:** "The X, N ways" / "Let me show you" / "Here's the thing" setup lines are
the #1 AI-prose tell. Real benchmark accounts (Artificial Analysis, METR) state
numbers directly with no preamble. Compare against the voice you're imitating
before keeping any setup phrase.

### 2026-06-26 · Ponytail DeepSWE thread (round 1)

**Bad:** "Where over-pruning bit:" — strained metaphor phrasing.
**Fix:** "Over-pruning hit on easy and medium tasks." Plain verb, plain noun.
**Why:** If a phrase makes the reader pause to parse it, rewrite it. Metaphors
that sound clever in the writer's head read as AI-generated. Prefer the boring
active verb.

### 2026-06-26 · Ponytail DeepSWE thread (round 1)

**Bad:** "That's the failure mode in one sentence." (closing flourish)
**Fix:** Deleted. End on the concrete quote/example, not a meta-comment about
how well you just summarized.
**Why:** Self-referential closers ("in one sentence", "that's the takeaway",
"the lesson is clear") are a reliable slop signature. The reader can tell when
you've made your point; announcing that you have is filler.

### 2026-06-26 · standing rule

Always run the `writing-clearly-and-concisely` skill on published prose (tweets,
blogs, READMEs, reports). Load its `elements-of-style/03-elementary-principles-of-composition.md`
for the active-voice / concrete-language / omit-needless-words rules. The
`signs-of-ai-writing.md` reference in that skill documents further tells.

---

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 7)

**Bad:** Leaving "handles unverified" after the user has confirmed handles.
**Fix:** Update the handles and remove the caveat. Current confirmed handles for
this thread include @earendilworks, @badlogicgames, @datacurve, @kunchenguid,
and @elpapi42.
**Why:** Once verified, the caveat makes the draft look unfinished and reduces
confidence.

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 4)

**Bad:** Using insider task ids in public evidence tweets.
**Fix:** Replace task slugs like `mashumaro-flattened-dataclass-fields` with a
short plain-English task description, e.g. "a Python dataclass-serialization
task with flattened fields."
**Why:** Slugs are precise for us but opaque to readers. The tweet should carry
the meaning without making the reader decode a benchmark id.

**Bad:** Leaving an AI-sounding summary sentence after already making the point.
**Fix:** Delete the sentence. If a line feels like "This is the punchline," the
thread probably already said it.
**Why:** Explaining the structure sounds synthetic. End with the concrete teaser
or result instead.

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 2)

**Bad:** Writing "Why that is scandalous:" before the context-purist joke.
**Fix:** Remove the explanation and let the joke work: "Nobody tell the context
engineering purists." Then state the belief system plainly in the next tweet.
**Why:** Explaining the joke is never funny. A strong hook should create the
frame; the next tweet should provide evidence, not explain the punchline.

## False certainty & over-generalization

Don't generalize beyond what you measured. Don't assert necessity when you mean
possibility.

### 2026-06-26 · Ponytail DeepSWE thread (round 1)

**Bad:** "The lesson, for anyone using AI coding skills:" (generalizes from one
skill to all skills).
**Fix:** "The lesson from testing Ponytail:" (scoped to what was tested).
**Why:** The benchmark tested one skill. Generalizing the lesson to all AI
coding skills overclaims. Scope claims to the experiment. The reader trusts
honest scope more than confident reach.

### 2026-06-26 · Ponytail DeepSWE thread (round 1)

**Bad:** "They also make the agent skip the wiring…" (asserts inevitability).
**Fix:** "They can also make the agent skip the wiring…" (possibility).
**Why:** False certainty. Minimalist heuristics *can* cause over-pruning; they
don't *always*. "Can" is accurate and honest. Don't trade precision for force.

---

## Precise language

Vague nouns ("the system", "the skill", "the agent") blur what was actually
tested. Use the precise noun a reader needs to reproduce the experiment.

### 2026-06-26 · Ponytail DeepSWE thread (round 1)

**Bad:** "against a bare agent"
**Fix:** "against an unmodified Pi agent"
**Why:** "Bare agent" is vague and slightly pejorative. The actual control was
an unmodified Pi install — the same harness, same tools, same model, just
without the treatment. Name the control precisely so a reader can reproduce it.

### 2026-06-26 · standing rule

When naming the control and treatment, use the exact configuration strings. For
this harness: "unmodified Pi agent" (baseline, `--no-skills --no-extensions`)
vs. the named extension/skill (e.g. "the Ponytail Pi extension", "the
pi-observational-memory extension"). Never shorthand to "baseline agent" or
"the agent" in the setup tweet.

---

## Credits & distribution

Credit the creators of the tools and benchmarks you build on. It costs nothing
and is the single highest-upside distribution lever after the hook.

### 2026-06-26 · Ponytail DeepSWE thread (round 1)

**Bad:** Single credit tweet to @kunchenguid only.
**Fix:** Dedicated credit tweet tagging @DietrichGebert (Ponytail),
@datacurveai (DeepSWE), @badlogic / @earendilworks (Pi), @kunchenguid
(ProgramBench, format inspiration).
**Why:** A creator @mention notifies them. If any engages (like/RT/reply), the
algorithm weights it heavily (reply_engaged_by_author +75, follow +4×). Worst
case they ignore it. **Tagging creators helps reach; it never hurts.** Verify
handles on X before posting (org handles are inferred from GitHub and may
differ). Keep credits in a dedicated tweet or reply, never the hook — @s and
links in the hook suppress reach.

### 2026-06-27 · pi-observational-memory DeepSWE thread (round 1)

**Bad:** Repeating user shorthand that pi-observational-memory was a "port" of
Mastra's implementation without checking the extension's own README.
**Fix:** Ground attribution in the source. The package README says it is
"Inspired by Mastra's Observational Memory research" and identifies `elpapi42`
as the author. Use "inspired by" unless the repo itself says "port".
**Why:** Creator attributions are public factual claims. A subtle word like
"port" vs "inspired by" can miscredit the work and damage trust.

### Standing — handle verification

Known-good handles (verified 2026-06-26):
- Ponytail: **@DietrichGebert** (Dietrich Gebert)
- DeepSWE / Datacurve: **@datacurveai** (verify on X before first post)
- Pi: **@badlogic** (Mario Zechner) and **@earendilworks** (org)
- ProgramBench: **@kunchenguid** (Kun Chen)

### 2026-06-26 · Ponytail DeepSWE thread (round 2)

**Bad:** Dropping the image from the hook tweet.
**Fix:** The hook tweet must have an image. Images boost engagement
+30-120% and the hook is where it matters most. The fix is NOT to dump a
dense analytical chart back in — it's to generate a dedicated scroll-stopping
hero image that conveys the thesis in one glance. Queue hook-image generation
as a distinct task once the text/format is locked.
**Why:** A hook without an image leaves the single highest-engagement slot
unarmed. Dense charts fail as hero images because they require study; a hero
image must read in under a second. Separating "text/format" from "image asset
generation" as phases is correct, but the hook slot must not ship empty.

## Visual assets

### 2026-06-26 · Ponytail DeepSWE thread (round 3)

**Bad:** Treating a first deterministic concept render as review-ready when it
had sloppy margins, overflowing text, cramped edges, and a mismatched dark
background.
**Fix:** Separate the visual process into three passes: (1) concept/thesis,
(2) craft/layout/color, (3) factual deterministic rebuild. If an image-gen model
cleans up the layout well, use it as a style reference, not the final factual
asset. Re-render exact text, numbers, and labels with code.
**Why:** Benchmark images need both scroll-stop appeal and factual trust. Image
generation can improve composition, but it can also silently alter numbers,
handles, captions, or labels. The final card must have exact deterministic facts
and a deliberate craft pass before review.

**Bad:** Leaving body-image slots mismatched with the tweet text while focusing
only on the hook.
**Fix:** Work cohesively at the slot level: hook first, then verify every body
image matches its tweet purpose and caption. Do not redesign all cards at once,
but do replace obviously wrong/mismatched slots before asking for thread-level
review.
**Why:** A strong hook image cannot rescue a thread if the body cards say a
different thing than the tweet they attach to. Cohesion matters more than making
every body card perfect in the same pass.

**Bad:** Treating the successful Ponytail hero card as a reusable conclusion
instead of a reusable structure.
**Fix:** Preserve the anatomy, not the wording: kicker, two-line conclusion,
2-3 exact fact panels, verdict labels, punchline footer, provenance footer. Each
analysis needs its own hero conclusion and supporting facts.
**Why:** Future threads will have different core claims: OM may be "hard tasks
improved, cost rose"; advisor may be "diagnostic, not publishable efficacy";
model comparisons may be about quality/cost tradeoffs. A good process must make
fresh-context agents find the new surprise rather than copy `Smaller. And worse.`
onto unrelated data.

### 2026-06-27 · pi-observational-memory DeepSWE thread (round 1)

**Bad:** Interpreting "the triangles are confusing" as permission to remove the
hook image entirely.
**Fix:** Fix the confusing element, keep the hook image. If the reviewer flags a
specific visual detail, preserve the surrounding slot unless they explicitly ask
to remove it.
**Why:** The hook image is a distribution requirement and a logged process rule.
Dropping it silently repeats an earlier Ponytail mistake. Reviewer feedback is
usually local; do not broaden it without asking.

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 3)

**Bad:** Mixing mental units in a hero image: "5× solves" versus "66% more
tokens".
**Fix:** Use comparable units when the reader needs quick cost/benefit: "5×
solves" versus "1.66× tokens".
**Why:** Same-unit contrasts reduce arithmetic. A reader can compare tradeoffs
faster when both sides use multipliers.

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 2)

**Bad:** Framing memory only as "remembering more".
**Fix:** Explain the more interesting mechanism: useful observations are kept
and noisy context can fall away. In this implementation, memory can act as
context hygiene, not context bloat.
**Why:** The strongest argument answers the context-purist objection directly.
The point is not "stuff more into context"; it is "preserve the valuable parts
and forget the unimportant parts automatically."

**Bad:** Trying to fit every newer experiment into the current thread.
**Fix:** Tease later GPT-5.5 / observer / thinking-level experiments without
spilling their results. Keep the current thread about the DeepSeek-v4-flash OM
run and the mechanism it surfaced.
**Why:** Threads need one spine. New results can raise curiosity, but dumping
multiple campaigns into one thread dilutes the proof and invites overclaiming.

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 8)

**Bad:** Putting a tilde in a hero-image headline number (`~8%`).
**Fix:** Use the clean rounded number in the visual (`8%`) and explain estimate
status in the supporting tweet or report.
**Why:** A tilde on a hero card visually megaphones uncertainty. It makes the
image feel less confident without adding useful precision.

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 6)

**Bad:** Hero image framed treatment cost as "1.66× tokens," implying all extra
tokens were extension overhead.
**Fix:** For the hero, contrast the benefit with true extension overhead:
"5× solves" vs "~8% observer overhead." Keep the broader main-agent token
increase in the cost tweet where it can be explained as unlocked task work.
**Why:** Hero images compress the story. If they compress the wrong cost, they
teach the wrong takeaway.

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 5)

**Bad:** Treating the whole treatment cost delta as the cost of the extension.
**Fix:** Separate extension overhead from unlocked task work. For OM, observer
work was about +8% tokens, while much of the remaining spend came from the main
agent continuing useful task work it otherwise failed to complete.
**Why:** If the extension helps the agent keep going, extra main-agent tokens
are not pure memory overhead. They are part of the work required to finish the
task. Public cost framing should distinguish bookkeeping cost from unlocked
progress.

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 4)

**Bad:** Over-describing the provenance of an estimate inside the tweet body.
**Fix:** Use reader-facing language: "Observers add about 8% more tokens for
their work." Keep the detailed source in internal notes or a linked report.
**Why:** A tweet needs the conclusion and enough caveat to be honest. Too much
measurement provenance slows the reader down.

### 2026-06-29 · pi-observational-memory DeepSWE thread (round 3)

**Bad:** Reporting cost as "$0.15 → $0.20 per task" when the benchmark artifact
is a full run.
**Fix:** Show total run dollars for the benchmark: baseline total → treatment
main-agent total, then add any estimated extension-worker overhead separately.
**Why:** Total cost is easier to reason about for a benchmark campaign. Per-task
figures can hide whether the run was cheap, expensive, or worth repeating.

**Bad:** Leaving a vague caveat that worker tokens were excluded.
**Fix:** When later instrumentation exists, convert the caveat into a bounded
estimate. For OM, GPT-5.4-mini-low observer traces showed about +8.3% worker
tokens; apply that as an estimate and label it clearly.
**Why:** Readers can use an estimate. They cannot use an unquantified caveat.

## Metrics framing

### 2026-06-26 · Ponytail DeepSWE thread (round 2)

**Bad:** Listing "mean partial reward" with no reader context, alongside solves
and patch size, leaving readers unsure which number to weight.
**Fix:** Label partial reward as the main metric inline: "Partial reward (our
main metric, less noisy): 0.774 → 0.709 (worse)." Keep the parenthetical short.
**Why:** At our sample sizes (113 tasks, 1 rep), binary solves are extremely
noisy (2 vs 4 is within n=1 sampling variance). Partial reward is the less
noisy, more continuous signal, so it is the honest primary metric for our
runs. Readers don't know that unless we tell them. Always flag which number
matters most, briefly.

### Standing — DeepSWE official metric (verified 2026-06-26)

DeepSWE's official leaderboard headline metric is **pass@1 (binary)**, e.g.
"GPT-5.5 [medium]: 54%±3% pass@1." Mean task partial is a secondary stat they
report alongside it. Do NOT claim DeepSWE uses partial reward as their primary
metric — they don't. We use partial as OUR primary for a different, valid
reason: lower noise at our sample size.

---

## Process

### 2026-06-26 · standing rule — the iteration loop

The thread you are rewriting is a **vehicle for the learning process**, not a
product to ship. Every round of reviewer feedback must be:

1. Applied to the current draft.
2. **Appended to this log** as a durable rule (mistake → fix → why).
3. Folded into the next draft and every future thread.

A fresh-context agent drafting the next thread (e.g. pi-observational-memory)
must read this log first. If they repeat a logged mistake, the loop failed.

### 2026-06-26 · standing rule — review loop setup

To run the human review loop on a draft over Tailscale without the Pi Annotate
extension:

1. Put the rendered HTML + relative assets under `.lavish/` in the working dir
   (Lavish serves the file's directory; relative asset paths only).
2. Bind lavish-axi to the Tailnet IP:
   `LAVISH_AXI_HOST=100.112.72.93 LAVISH_AXI_LINK_HOST=100.112.72.93 npx -y lavish-axi .lavish/<file>.html`
3. Share the session URL with the reviewer (laptop browser over Tailnet).
4. Run `lavish-axi poll` (background) to receive annotations + queued prompts.
5. Apply feedback, append to this log, reply via `--agent-reply`, re-poll.

This avoids the `pi-annotate` MV3 service-worker sleep problem entirely.
