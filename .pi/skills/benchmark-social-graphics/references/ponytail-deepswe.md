# Ponytail DeepSWE Reference

Use this only for the completed Ponytail DeepSWE graphics/thread.

## Run identity

- run: `runs/ponytail-full-pilot-w2`
- baseline config: `baseline`
- comparison config: `ponytail-pi-extension`
- model: `deepseek-v4-flash`
- thinking: `high`
- tasks: `113 paired tasks`
- comparison label: `Ponytail full Pi extension`
- comparison color: `#2d2af4`

## README-style mean table

| vs no-skill baseline, mean | patch lines ↓ | tokens ↓ | cost ↓ | time ↓ | partial reward ↑* | full solves ↑* |
|---|--:|--:|--:|--:|--:|--:|
| **ponytail full Pi extension** | **-26%** | **-12%** | **-10%** | **-7%** | **0.709 vs 0.774** | **4/113 vs 2/113** |

Footnote:

```text
↓ lower is better for patch lines, tokens, cost, and time.
↑ higher is better for DeepSWE outcomes.
* partial reward = held-out verifier partial score. full solve = DeepSWE binary reward=1.
```

## Difficulty chart values

Difficulty buckets use baseline partial-reward terciles.

Cost-axis values:

```text
EASY:   baseline 99.1% / $0.149 → ponytail 84.1% / $0.153
MEDIUM: baseline 93.4% / $0.159 → ponytail 85.9% / $0.147
HARD:   baseline 40.1% / $0.143 → ponytail 43.1% / $0.138
```

Token-axis values:

```text
EASY:   baseline 99.1% / 4.69M → ponytail 84.1% / 4.02M
MEDIUM: baseline 93.4% / 3.77M → ponytail 85.9% / 3.46M
HARD:   baseline 40.1% / 3.78M → ponytail 43.1% / 3.34M
```

## Accepted outputs

Cost-axis winner:

- `runs/ponytail-full-pilot-w2/reports/deep-swe-ponytail-twitter-card-fixed-v5.png`
- latest alias: `runs/ponytail-full-pilot-w2/reports/deep-swe-ponytail-twitter-card-fixed.png`
- script: `runs/ponytail-full-pilot-w2/reports/make_twitter_card_fixed.py`

Token-axis winner:

- `runs/ponytail-full-pilot-w2/reports/deep-swe-ponytail-twitter-card-tokens-v4.png`
- latest alias: `runs/ponytail-full-pilot-w2/reports/deep-swe-ponytail-twitter-card-tokens.png`
- script: `runs/ponytail-full-pilot-w2/reports/make_twitter_card_tokens.py`

## Lessons from iteration

- Generated images placed datapoints incorrectly after repeated prompts. Use deterministic overlays for factual regions.
- A 30%–100% y-axis gives hard buckets enough room when partial reward is near 40%.
- Cost-axis chart works with x-axis `$0.13`–`$0.16`.
- Token-axis chart is more readable with x-axis `3.0M`–`5.0M`; move the hard Ponytail label upper-right rather than expanding to `2.5M`.
- EASY label should sit lower-right of the easy baseline point when using token axis.
