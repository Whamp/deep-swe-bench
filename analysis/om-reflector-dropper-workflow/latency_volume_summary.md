# OM observation/reflection volume and latency follow-up

Date: 2026-06-29

Source: fresh scan of `results/**/session/*.jsonl` for `om.observations.recorded` and `om.reflections.recorded`, plus GPT-5.5 low `pi-agent/observational-memory/debug/*.ndjson` events. Machine-readable table: `latency_volume_fresh.csv`.

## Volume: observations vs reflections

Across configs, the memory system records roughly **4–7 observations per reflection**. Reflections are a compression/consolidation layer, not a peer-volume stream.

| config | cells | observations | reflections | obs / reflection |
|---|---:|---:|---:|---:|
| deepseek-v4-flash high OM | 113 | 5,462 | 969 | 5.64 |
| gpt54mini-low | 185 | 2,314 | 426 | 5.43 |
| gpt54mini-off | 185 | 2,788 | 673 | 4.14 |
| glm52-off | 185 | 3,789 | 737 | 5.14 |
| glm52-max | 82 | 1,533 | 183 | 8.38 |
| gpt55-off | 108 | 1,468 | 332 | 4.42 |
| gpt54-off | 108 | 1,408 | 268 | 5.25 |
| xhigh variants | 36 each | 206–538 | 33–77 | 6.0–7.0 |

Interpretation:

- `gpt54mini-off` is the most reflection-heavy relative to observations, but also had the most duplicate/reject/noise mass in the prior reflector audit.
- `glm52-off` records many observations and many reflections; it is high-coverage/high-depth.
- xhigh variants record relatively fewer reflections and a higher observation/reflection ratio, meaning sparser consolidation.

## Latency: observer and reflector

Latency is measured from debug `observer.start` → `observer.records/error`, and `reflector.agent_start` → `reflector.result/error` by `runId`. DeepSeek high has no debug NDJSON under `results/`, so it has volume but no role-latency trace.

| config | observer p95 | reflector p95 | observer errors | reflector errors | reflector result mix |
|---|---:|---:|---:|---:|---|
| gpt54mini-off | 19.2s | 13.2s | 8 | 13 | 181 accepted, 5 filtered, 4 no-tool |
| gpt54mini-low | 19.9s | 14.5s | 14 | 7 | 173 accepted, 2 filtered, 23 no-tool |
| gpt54-off | 22.6s | 10.7s | 10 | 3 | 100 accepted, 100 no-tool |
| gpt54-low | 25.2s | 15.2s | 6 | 1 | 37 accepted, 3 no-tool |
| glm52-off | 42.3s | 30.1s | 39 | 24 | 166 accepted, 14 no-tool |
| gpt55-off | 52.1s | 24.0s | 23 | 5 | 90 accepted, 79 no-tool |
| gpt55-low | 68.1s | 26.6s | 16 | 4 | 29 accepted, 9 no-tool |
| glm52-high | 49.2s | 54.0s | 9 | 4 | 36 accepted |
| glm52-max | 75.8s | 95.4s | 23 | 28 | 72 accepted, 2 no-tool |
| gpt54-xhigh | 219.7s | 164.2s | 19 | 8 | 25 accepted, 7 no-tool |
| gpt54mini-xhigh | 582.2s | 333.5s | 28 | 8 | 16 accepted, 1 no-tool |
| gpt55-xhigh | 741.1s | 135.8s | 28 | 3 | 18 accepted, 1 no-tool |

## How much latency can each role tolerate?

The current data suggests practical bands, not hard limits:

- **Healthy observer latency:** p95 around **20–25s**. This is where GPT-5.4-mini off/low and GPT-5.4 off/low live; append success is high and no-observation cells are low.
- **Usable but expensive observer latency:** p95 around **40–70s**. GLM-off and GPT-5.5 off/low still produce useful memory, but errors/no-observation cells rise.
- **Bad observer latency:** p95 above roughly **2–10 minutes**. xhigh variants produce sparse coverage, many errors, and fewer useful cycles.

Reflector is more latency-sensitive in a different way:

- **Healthy reflector latency:** p95 around **10–15s**.
- **Usable reflector latency:** p95 around **25–55s** if it reliably emits accepted reflections.
- **Bad reflector latency:** p95 above **90s**, especially when paired with high no-tool/error rates or low throughput.

The observer can tolerate moderate slowness better because each observer batch can still append useful raw observations later. The reflector is more vulnerable to slowness because it is a consolidation step; if it arrives late or no-tools, the agent loses the compact constraint memory and the dropper precondition never advances.

## How slow models fail

Slow models do not usually fail by crashing the benchmark directly. They fail by degrading the memory loop:

1. **Late or missing observations** — fewer appended batches, more no-observation/error cells, lower topic coverage.
2. **Sparse or inert reflections** — more `no_tool_call`, fewer accepted reflections, lower coverage transitions.
3. **Stale-context errors** — long-running background workers can finish after the session has moved/reloaded, causing recoverable but wasted work.
4. **No active dropping** — since pools never reach the 10k target, slow reflectors do not trigger better pruning; they simply delay or reduce consolidation.

Observed role difference:

- **Too-slow observer:** loses raw facts and coverage. The memory system has less material.
- **Too-slow reflector:** has material, but fails to turn it into compact durable constraints in time. This shows up as `no_tool_call`, fewer reflections, or lower accepted coverage.

Public-safe summary: the memory worker needs to be fast enough to keep up with the session. In these runs, low/off small models often beat xhigh settings because they produced timely, concrete memory rather than slow, sparse, overthought memory.
