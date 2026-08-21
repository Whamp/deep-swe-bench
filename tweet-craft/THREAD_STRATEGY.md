# Benchmark thread strategy: viral without slop

Synthesis of research on what makes developer/AI benchmark threads spread on X
while staying high-signal. Source: X open-source algorithm weights, 3,700- and
10.2M-thread analyses, METR's viral RCT thread, Simon Willison's eval voice, and
LLM-slop pattern filters. This is the basis for a future `tweet-craft` skill.

## The ranking weights (from X's open-sourced `the-algorithm`)

This is the ground truth. Everything else is downstream of it.

| Signal | Weight | Implication |
|---|---|---|
| **Reply** | **+27.0×** | #1 signal. End posts with a real question or debatable claim. |
| **Bookmark** | **+10.0×** | Save-worthy content. Make the thread a reference, not a hot take. |
| Follow | +4.0× | "I want more of this." The career signal. |
| Dwell time | +2.0× / +1.5× | Multi-line posts + real content earn read time. |
| `reply_engaged_by_author` | **+75** | Author replies to repliers → triples the reply score. **Engage in the first hour.** |
| Like (fav) | +0.5× | Worthless relative to replies/bookmarks. Stop optimizing for likes. |
| Report | −369× | One report erases ~500 likes. |
| Not Interested | −74× | Off-topic = algorithmic death. Stay on-niche. |
| Scrolled Past | −11× | Weak hook triggers this. The hook is everything. |

**Hard takeaway:** replies + bookmarks >> likes. One mute from an off-topic
follower-of-follower erases the upside of 150 likes, so **stay on-niche for the
audience you're reaching through shares** — don't bait a broader audience that
will mute you.

## Thread anatomy (converges across all sources)

1. **Hook (tweet 1) — 80-90% of performance.** Specific number, bold claim, or
   counterintuitive statement. Never "A thread:" or a yes/no question. Lead with
   the payoff/tension, not the setup.
2. **Preview (tweet 2) — the most-skipped, highest-value tweet.** One line: "I
   tested X across Y tasks. The result: Z. Here's what I found." Skipping this is
   the #1 mistake mid-tier threads make; it kills mid-thread completion.
3. **Body (tweets 3 to N-2) — one idea per tweet, each standalone-readable.** If a
   tweet only makes sense after reading 3 prior tweets, cut it.
4. **Synthesis (tweet N-1) — pulls body into one observation.** This drives
   reposts. The "here's the generalizable lesson" tweet.
5. **Close (tweet N) — quotable, standalone, most-screenshotted.** Where reposts
   and follows compound. Often the single most-engaged tweet in the chain.

**Length sweet spot: 7-10 tweets.** Our 9-post ponytail thread is in range.

## Hook data (3,700 threads, twitter10k)

| Hook type | Avg likes | Avg views |
|---|---|---|
| **How-To** | **534** | 90,981 |
| Question | 259 | 7,467 (low reach) |
| Shocking/Curiosity | 183 | **54,465** (high reach) |
| Story-Based | 158 | 39,073 |
| Numbered List | **13** | 869 (worst) |

- Personal pronouns (I/my/we) → **2.2× more likes** than impersonal. "I built
  this" beats "here is how to build this."
- Numbered-list hooks ("5 things...") are the worst performer despite being the
  most recommended. Avoid them.
- Curiosity-gap hooks pull reach (views) harder than engagement (likes). For
  follower growth, curiosity > how-to.

## The METR template (the closest analog to our work)

METR's viral thread on their RCT (devs 19% slower with AI tools than they
thought) is the genre template for benchmark/experiment threads:

1. **Hook names the surprising result + the tension:** "We ran an RCT. The
   results surprised us: devs thought they were 20% faster but were 19% slower."
2. **Setup (credibility):** 16 devs, 246 real tasks, randomized.
3. **The surprising number, stated three ways:** forecast +24%, felt +20%, actual
   -19%.
4. **Mechanism (why):** less time coding, more time prompting/waiting.
5. **Robustness:** persists across measures, estimators, subsets. Not a fluke.
6. **Motivation:** why this matters beyond the benchmark.

The pattern: **surprising number → setup → mechanism → robustness → why it
matters.** This is the skeleton for our benchmark threads.

## Anti-slop rules (from LLM-pattern-filter + voicemoat + dev voice guides)

LLM tells that mark text as AI-generated (detect and remove):

- **Em-dashes (—) in every clause** → the #1 dead giveaway. Use periods or commas.
- "Furthermore / Moreover / Additionally" openers → essay filler.
- "straightforward" / "worth noting that" / "It's important to note" → hedges.
- "I'd be happy to" / "Let me..." → servile / stalling.
- Exclamation marks on mundane technical claims → forced enthusiasm.
- Walls of text (5+ sentences, no line breaks).

Developer voice principles (from shippost.lol, social-writer style guide):

- **Direct, zero fluff.** The point IS the first sentence. No "Hey everyone."
- **Confident without hedging.** State what you found. Don't apologize.
- Short sentences (10-15 words). Active, present tense.
- Specific > generic ("30 min to ship" not "way faster").
- "use" not "utilize." "help" not "facilitate."
- Name specific tools via @mentions.
- No italics-emulating formatting tricks on X.

## Diagnosis of the current ponytail thread

| Problem | Evidence | Fix |
|---|---|---|
| Hook is a yes/no question | "is it actually good?" = lowest-reach hook type | Lead with the surprising tension + number |
| No preview/promise tweet | Jumps hook → "The good" list | Add tweet 2: one-line result summary |
| Order buries the surprise | good → bad → mechanism | surprise → mechanism → honest cost → takeaway |
| Inside-baseball task lists | actionlint/adaptix/yjs names mean nothing publicly | One "evidence" tweet with the chart, no raw task dump |
| Weak close | "reach out to me" + cost, then "what next" | Quotable standalone insight as the final tweet |
| Slop tells | em-dashes, bullet-walls, hedging | De-slop per rules above |
| Images not load-bearing | 4 images, text never references them | Reference each chart by what it shows |

## Image/chart rules

- Charts > text tables for reach. Images get +30-120% engagement.
- One chart = one thesis. If the audience can't read the takeaway in 3 seconds,
  it's chart design, not chart storytelling.
- Lead with the most interesting number visually, then guide to context.
- Use the `benchmark-social-graphics` deterministic-overlay skill for all
  numbers/datapoints. Never let an image-gen model place chart text or numbers
  (it hallucinates them). Image-gen only for styled base cards.
- Reference every image in the text of the tweet it attaches to.

## Reply-velocity (the distribution lever)

- First 30-60 min engagement decides whether the thread spreads. The algorithm
  weights early reply velocity above all later activity.
- **Author must reply to repliers in the first hour** (+75 weight on
  `reply_engaged_by_author`). This is the single biggest legal lever.
- End the hook (and ideally the close) with a genuine question to provoke
  replies, not just likes.
- Keep links OUT of the hook tweet (links suppress reach). Drop the repo link in
  the close or a reply.

## Pre-flight checklist

Also enforced by the `write-benchmark-thread` skill (model-invoked). See
`FEEDBACK_LOG.md` for the growing list of concrete (mistake → fix → why)
entries captured from real reviews — those are hard constraints, not
abstractions. Read the log before every draft.

- [ ] Hook is a specific number / bold claim / tension, not a question or list
- [ ] Tweet 2 is a one-line preview of the result
- [ ] Every body tweet is standalone-readable
- [ ] Tweet N-1 is the synthesis (generalizable lesson)
- [ ] Tweet N is quotable + standalone (the screenshot tweet)
- [ ] No em-dashes, no "furthermore/moreover," no hedges
- [ ] No numbered-list hook
- [ ] Personal pronouns in the hook (I/my/we)
- [ ] Each image is referenced by the tweet it attaches to
- [ ] Hook + close end with a real question (reply bait)
- [ ] Repo link is in the close or a reply, NOT the hook
- [ ] Author plans to reply to every replier in the first hour
