# Social Card Style Reference

## Accepted style

Use this visual language for benchmark social cards:

- square 1080–1254px card
- vivid blue/purple outer background
- off-white paper card with subtle dot/grid texture
- large editorial serif headline
- small monospace metadata labels
- black baseline datapoints
- blue-purple treatment datapoints and arrows (`#2d2af4`)
- subtle gray axes/grid
- footer can include `x.com/hampsonw`, `github.com/Whamp`, `thinking: High`, and task count

Keep text sparse. Put nuance in the thread, not the image.

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

## README-style card pattern

For wide README cards:

- white background
- GitHub-ish sans-serif
- grouped bars where baseline is 100%
- gray baseline, blue-purple treatment
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
