# Ponytail full Pi extension on DeepSWE

Run: `ponytail-full-pilot-w2`  
Model: `deepseek-v4-flash`  
Thinking: `high`  
Tasks: 113 paired DeepSWE tasks  
Treatment: real Ponytail Pi extension, full/default mode

## Mean deltas vs no-skill baseline

| vs no-skill baseline, mean | patch lines ↓ | tokens ↓ | cost ↓ | time ↓ | partial reward ↑* | full solves ↑* |
|---|--:|--:|--:|--:|--:|--:|
| **ponytail full Pi extension** | **-26%** | **-12%** | **-10%** | **-7%** | **0.709 vs 0.774** | **4/113 vs 2/113** |

↓ lower is better for patch lines, tokens, cost, and time.  
↑ higher is better for DeepSWE outcomes.  
\* partial reward = held-out verifier partial score. full solve = DeepSWE binary reward=1.

## Cards

- `cost-card.png` — partial reward vs cost by baseline partial-reward tercile.
- `tokens-card-with-solves.png` — partial reward vs tokens, plus full-solve inset.
- `readme-style-benchmark-card.png` — README-style bar chart summary.

The card scripts are deterministic overlays for factual chart regions; generated imagery was used only as a visual shell.
