---
name: benchmark-social-graphics
description: Benchmark graphics. Use when creating social cards, README benchmark tables, chart images, X/Twitter graphics, or visual summaries from eval result artifacts where exact numbers, axes, labels, or datapoint placement matter.
---

# Benchmark Social Graphics

Leading rule: **deterministic facts, generated style**. Image models may make the card shell; code renders numbers, axes, datapoints, tables, and labels.

## Process

1. **Compute**
   - Read paired result artifacts, usually `runs/<run>/<config>/<task>/rep0/result.json`.
   - Include only tasks present in both configs.
   - Use means for README/Twitter summaries unless the user asks for medians.
   - For DeepSWE difficulty buckets, default to baseline partial-reward terciles unless a better out-of-sample difficulty signal exists.
   - Completion: every displayed metric has a computed source.

2. **Separate style from facts**
   - Use image generation for background, card texture, typography mood, and rough layout only.
   - Render final charts/tables with deterministic SVG/HTML/canvas code.
   - If a generated card has good style but wrong geometry, cover only the chart/table region with a code-rendered overlay.
   - Completion: no exact number or datapoint position depends on image-generation output.

3. **Render reproducibly**
   - Save a script beside the output, e.g. `runs/<run>/reports/make_*.py`.
   - Prefer SVG generated in code, rasterized with `rsvg-convert`, composited with `magick`.
   - Version iterations (`-v2`, `-v3`) and preserve winners.
   - Completion: rerunning the script recreates the handed-off PNG.

4. **Place labels deliberately**
   - Labels go near their datapoints, not centered in empty chart bands.
   - Move labels before changing axes; change axes only when points or labels are clipped/cramped.
   - Directionality must be explicit: lower-is-better vs higher-is-better.
   - Completion: read the final image and confirm labels, axes, and values are legible at social-card size.

## Chart Defaults

- y-axis for DeepSWE outcome charts: `partial reward · ↑ better`
- x-axis options:
  - `cost · $ per task → more expensive`
  - `tokens · per task → more tokens`
- black dot: baseline
- blue-purple dot/arrow: comparison config, default `#2d2af4`
- arrows: straight unless the user requests curves
- y-axis: include 30%–100% when hard buckets sit near 40%
- x-axis: tightest readable range that includes all points and label room

Tier label placement defaults:

- EASY near the easy baseline point, often lower-right if there is room
- MEDIUM near/below the medium comparison-config point
- HARD near the hard cluster, clear of the x-axis

## References

Load only when needed:

- Current Ponytail DeepSWE values and accepted output paths: [references/ponytail-deepswe.md](references/ponytail-deepswe.md)
- Card style and image-generation prompts: [references/social-card-style.md](references/social-card-style.md)

## Checklist

Before handoff:

- [ ] every displayed number traces to artifacts or a disclosed reference
- [ ] paired comparisons use the same task set
- [ ] axes include all datapoints without clipping
- [ ] labels do not collide with datapoints, axes, or each other
- [ ] lower/higher-better direction is visible
- [ ] repro script is saved next to the image
- [ ] final PNG path is stated
