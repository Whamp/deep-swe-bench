# Benchmark thread hero images

A hook image is not a miniature report. It is the visual version of the hook:
one surprising conclusion, backed by exact facts, readable in under one second.

## Principle

**Conclusion first; facts second; style last.**

For every benchmark thread, the hero conclusion will change. Preserve the
repeatable structure, not the specific Ponytail message.

Good hero cards answer:

1. What is the surprising conclusion?
2. What two or three facts make it undeniable?
3. What emotion should the reader feel: surprise, tension, skepticism, urgency,
   curiosity?

Bad hero cards try to summarize the whole analysis.

## Reusable anatomy

Use this structure unless there is a strong reason not to:

1. **Kicker** — corpus + treatment scope
   - Example: `PONYTAIL · 113 REAL ENGINEERING TASKS`
   - Future examples: `PI OBSERVATIONAL MEMORY · DEEPSWE`,
     `GPT-5.5 · 36-TASK FAST-ITER SUBSAMPLE`
2. **Two-line headline** — the conclusion in plain words
   - Keep it specific and non-generic.
   - It may be a tension: `Smaller. And worse.`
   - It may be a result: `Memory helped the hard tasks.`
   - It may be a caveat: `More solves. More cost.`
3. **Fact panels** — 2 panels by default, 3 max
   - Each panel gets one metric, one baseline/treatment comparison, and one
     verdict word.
   - Use exact values from artifacts.
   - Label directionality: `worse`, `better`, `smaller`, `more expensive`, etc.
4. **Punchline footer** — one short synthesis line
   - Example: `both true at once`
   - Future examples: `hard tasks carried the gain`, `better, but not cheaper`
5. **Small provenance footer**
   - Author/repo, task count, model/thinking level if relevant.

## What stays general

- Full-bleed or card-shell pseudo-scientific visual style.
- Off-white dot/grid paper texture.
- Editorial serif headline.
- Monospace metadata labels.
- Treatment color `#2d2af4` unless the thread has a different accepted accent.
- Black or gray baseline values.
- Exact deterministic rendering of all facts.
- Sparse text. Put nuance in the thread, not the image.

## What changes per analysis

- Headline conclusion.
- Chosen metrics.
- Direction labels.
- Treatment/control names.
- Emotion/tension.
- Whether the visual uses comparison panels, a one-point chart, or a simple
  before/after split.

## Choosing metrics

Pick metrics that support the hook, not every metric you computed.

Use two panels when possible:

- One **quality/outcome** metric: partial reward, pass@1, full solves, failure
  rate, regression rate.
- One **cost/shape** metric: tokens, wall time, cost, patch size, tool calls.

If the conclusion is about a distribution, use one compact chart instead:

- difficulty buckets
- scatter around a diagonal
- waterfall of task deltas

But a hero chart must still read in one second. If it needs axis study, it is a
body image, not the hook image.

## Image generation policy

Use image generation for **craft reference or shell only**:

- spacing
- mood
- paper texture
- rough composition
- lighting/contrast

Never use image generation as the final factual layer for benchmark numbers.
Image models can silently alter values, labels, handles, or chart geometry.

Safe workflow:

1. Render a deterministic concept image.
2. Optionally give it to an image model for a cleanup/style reference.
3. Rebuild the final image deterministically from code using the improved
   layout as reference.
4. Verify every number and label.

## Hero card checklist

Before review:

- [ ] The conclusion is clear in under one second.
- [ ] The hero is not a dense analytical chart.
- [ ] Every displayed value traces to a run artifact or disclosed source.
- [ ] Text has generous margins and no overflow.
- [ ] Background/color matches the accepted visual system for the thread.
- [ ] Directionality is explicit (`better`, `worse`, `smaller`, etc.).
- [ ] The image is legible at mobile feed size.
- [ ] The final asset is deterministic SVG/PNG with a repro script.

## Ponytail worked example

Conclusion: Ponytail made patches smaller but reduced mean partial reward.

Hero headline:

```text
Smaller.
And worse.
```

Fact panels:

- `PARTIAL REWARD`: `0.774 → 0.709`, verdict `worse`
- `PATCH SIZE`: `30.5k → 22.1k`, verdict `27% smaller`

Punchline footer:

```text
both true at once
```

Final deterministic script:

- `tweet-craft/assets/make_hook_hero_v2.py`
- output: `tweet-craft/assets/hook-hero-v2.png`
