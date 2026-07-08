# omp (Oh My Pi) harness vs Pi baseline on 12_v2

Run: `gpt55-low-baseline-omp-12v2-r3-w12` — 36 cells (12 tasks × 3 reps), **omp v16.3.5
harness** (`/home/will/.cache/.bun/bin/omp`), executor `openai-codex/gpt-5.5` low, tools
`read,bash,edit,write,grep,glob`, no skills/extensions/rules. Compared against the **Pi
harness** baseline (`baseline`) at the same model/thinking/prompt on the same 12_v2 cells.

This is a **harness head-to-head**: only the agent runtime differs (omp vs Pi). Model,
thinking level (low), DeepSWE task container, verifier, and appended prompt text
(`harness/system_preamble.md` + `configs/baseline/orchestration.md`) are identical.

## Headline

**The omp harness underperforms the Pi harness.** Fewer solves, lower partial, and it
burns ~3× more tokens for worse results. The harness is not interchangeable with Pi at
this model level.

## Aggregate (36 paired cells)

| metric | Pi baseline | omp baseline | delta (omp−Pi) |
|---|---|---|---|
| solves | 11/36 (30.6%) | 9/36 (25.0%) | **−2** |
| mean partial | 0.9739 | 0.9537 | **−0.020** |
| median tokens | 591k | **1,916k** | **+1,181k (~3.2×)** |
| median cost | $0.84 | $1.80 | +$0.85 (~2.1×) |
| median wall | 199s | 281s | +82s |
| median turns | 40 | 50 | +10 |
| median tool calls | 38 | 50 | +12 |
| median patch | 10.8kB | 15.7kB | +4.9kB |
| reward_binary=−1 (crash/empty) | 0 | 1 | +1 |

omp does more work on every axis — more turns, more tool calls, bigger patches, 3× the
tokens — and still solves fewer tasks at lower quality. That is the opposite of an
efficiency win.

## Solve agreement

both=8 · Pi-only=3 · omp-only=1 · neither=24. omp crosses the threshold on 1 task Pi
missed and drops 3 Pi hit. Thin signal at n=36, but it points the same way as the
partial and token gaps.

## Per-task (3-rep mean partial / solves out of 3)

omp worse: `mobly-grouped-test-barriers` 0.983→0.661 (−0.32), `go-critic-doc-link-checker`
0.965→0.930 (2/3→1/3), `langchain-request-coalescing` (1/3→0/3), `sql-formatter-bigquery-pipe-formatting`
(1/3→0/3).

omp better: `participle-grammar-conflict-analysis` 0.892→0.980, `tengo-callable-instance-isolation`
0.936→0.979, `obsidian-linter-link-format-conversion` (2/3→3/3).

The wins and losses are task-specific and roughly balance on partial, but the losses
cost more binary solves (3 lost vs 1 gained).

## Context — all gpt-5.5 low configs on 12_v2

| config | solves | % | meanP | med tok | med cost |
|---|---|---|---|---|---|
| codebase-memory-max-pi-codex-goal | 17/36 | 47.2% | 0.982 | 1.75M | $2.14 |
| pi-codex-goal | 16/36 | 44.4% | 0.978 | 1.42M | $1.86 |
| pi-recursive | 13/36 | 36.1% | 0.982 | 0.97M | $1.13 |
| **Pi baseline** | **11/36** | **30.6%** | **0.974** | **0.59M** | **$0.84** |
| baseline-wf | 10/36 | 27.8% | 0.986 | 0.62M | $0.92 |
| advisor-gpt55-xhigh | 10/36 | 27.8% | 0.973 | 0.98M | $0.98 |
| **omp baseline** | **9/36** | **25.0%** | **0.954** | **1.92M** | **$1.80** |
| codebase-memory-max | 8/36 | 22.2% | 0.976 | 0.80M | $1.01 |
| ponytail-full | 7/36 | 19.4% | 0.976 | 0.93M | $1.06 |

omp sits below the Pi baseline and every Pi-based low config except the extension arms
that themselves lose solves, while spending more tokens than all of them. It is the most
token-expensive config in this slice for the second-fewest solves.

## Bottom line

On 12_v2 with gpt-5.5 low, **omp is Pareto-dominated by the Pi harness** (9 vs 11 solves
at ~3× the token cost and ~2× the dollar cost). The harness is a real variable: a minimal
omp run is materially worse, not equivalent, to a minimal Pi run at the same model.

Caveats:
- Small slice (12 tasks × 3 reps). The solve delta (−2) and agreement (3 vs 1) are thin;
  the token gap is large and consistent but the binary signal would benefit from 36_v2.
- omp had one `reward_binary=−1` cell (crash/empty patch); Pi had none — a minor reliability
  marker at this sample size.
- Both arms run on the same Codex subscription, so cost reflects token volume, not cash.
