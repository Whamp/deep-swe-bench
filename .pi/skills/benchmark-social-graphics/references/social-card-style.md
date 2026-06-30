# Social Card Style Reference

## Accepted style

Use this visual language for benchmark social cards:

- square 1080–1254px card
- vivid blue/purple outer background
- off-white paper card with subtle dot/grid texture
- large editorial serif headline
- small monospace metadata labels
- black baseline datapoints
- blue-purple comparison-config datapoints and arrows (`#2d2af4`)
- subtle gray axes/grid
- footer can include `x.com/hampsonw`, `github.com/Whamp`, `thinking: High`, and task count

Keep text sparse. Put nuance in the thread, not the image.

## Hook hero card pattern

A hook hero card is **not** a miniature report. It is the visual version of the
thread hook: one surprising conclusion, backed by exact facts, readable in under
one second.

Use a conclusion-first anatomy:

1. kicker: corpus + config scope
2. two-line headline: the analysis-specific conclusion
3. two fact panels (three max): exact values plus verdict labels
4. punchline footer: one short synthesis line
5. provenance footer: handle/repo/task count/model if relevant

Keep this structure general. Do not reuse Ponytail's conclusion for other runs.
For each analysis, choose a fresh headline and supporting metrics:

- Ponytail example: `Smaller. / And worse.` with partial reward and patch size.
- OM example shape: likely hard-task quality gain vs extra tokens/cost.
- Advisor example shape: likely diagnostic/run-health caveat, not efficacy claim.
- Model comparison shape: quality or pass@1 gap vs cost/time tradeoff.

Hero charts must read in one second. If a visual needs axis study, it belongs in
the body of the thread, not the hook.

## Image-generation prompt pattern

Use image generation for the shell only:

```text
Create a square benchmark social-card infographic.
Vivid blue-purple outer background. Centered off-white paper card with subtle dot-grid texture and soft shadow.
Editorial serif headline, small monospace metadata labels, sober research-poster aesthetic.
Leave the chart area clean and suitable for deterministic overlay.
No extra text. No fake numbers. No fake logos. No rendered datapoints.
```

Then render chart/table text with code.

Image generation may also be used as a **craft reference**: generate a cleaned-up
version of a deterministic concept to improve spacing, hierarchy, or mood. Do
not use the generated raster as the final factual layer. Rebuild exact numbers,
labels, and geometry deterministically afterward.

## README-style card pattern

For wide README cards:

- white background
- GitHub-ish sans-serif
- grouped bars where baseline is 100%
- gray baseline, blue-purple comparison config
- column names carry direction arrows, e.g. `tokens ↓`, `partial reward ↑`
- footnote explains directionality and benchmark-specific outcome definitions

## Deterministic overlay pattern

Preferred tools:

```bash
rsvg-convert -w 1254 -h 1254 overlay.svg -o overlay.png
magick base.png overlay.png -composite output.png
```

In code:

- define raw values in one `points` mapping
- define `X()` and `Y()` transforms
- draw grid/axes first, arrows second, dots third, labels last
- keep all chart constants near the top of the script
- write the SVG and final PNG beside the script
