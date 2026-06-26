# OM public / research framing notes

Source set: `runs/om-memory-pilot-w10/reports/paired_manifest.json`, `runs/om-memory-pilot-w10/reports/initial_summary.md`, `runs/om-memory-pilot-w10/results.jsonl`, and the paired writeups in `runs/om-memory-pilot-w10/reports/pair_*.md`.

## Safe headline

On this paired replay (`113` task pairs, `rep0` only), `pi-observational-memory` improved mean partial reward from `0.774167` to `0.856332` (`+0.082165`, about `+10.6%` relative) and raised binary solves from `2/113` to `10/113` (`+8` solves).

## What the run actually shows

- Partial reward improved on `69/113` rows, worsened on `33/113`, and tied on `11/113`.
- Hard tasks improved the most on average: `0.401454 -> 0.709870` (`+0.308417`), with solves `0 -> 1`.
- Medium and easy buckets were mixed on average (`0.934380 -> 0.912542` and `0.990884 -> 0.948064`), even though both buckets gained more binary solves.
- The run looks more like a quality lift than a cost win: OM used more tokens on `89/113` rows, higher direct cost on `80/113`, and more wall time on `72/113`.
- Median resource use moved up too: total tokens `3.29M -> 5.45M`, turns `57 -> 80`, wall time `776.4s -> 929.2s`.

## Caveats to keep explicit

- Baseline was reused from `runs/ponytail-full-pilot-w2/baseline`; this is a paired replay, not a fresh baseline rerun.
- There is only one rep per task (`rep0` across all `113` pairs), so this is directional, not variance-bounded.
- The per-row manifest reports agent-side metrics only; OM worker overhead is not a separate column, so do not present this as a full system-cost comparison.
- The only nonzero verifier outcomes were `opa-rego-rule-profiling` (`skipped_empty_patch`) and `boa-hierarchical-evaluation-cancellation` (`timeout`) in `runs/om-memory-pilot-w10/results.jsonl`; those are benchmark outcomes, not API false-failure evidence.
- OM debug logs show stale extension-context worker errors in `22/113` tasks (`9` `observer.error` + `13` `reflector.error`), all with the same message: `This extension ctx is stale after session replacement or reload...`. Example traces: `runs/om-memory-pilot-w10/pi-observational-memory/narwhals-rolling-window-suite/rep0/pi-agent/observational-memory/debug/019f00f0-dc16-7427-9fe3-f64cb9266b0d.ndjson` and `runs/om-memory-pilot-w10/pi-observational-memory/actionlint-action-pinning-lint/rep0/pi-agent/observational-memory/debug/019f0069-1079-7264-bef3-b4927100afeb.ndjson`.

## Good follow-up assets

1. **Scatter**: baseline partial vs OM partial, with a 45° line and color by difficulty bucket.
2. **Waterfall / lollipop**: per-task partial delta, sorted, with labels for top wins and top losses.
3. **Tradeoff scatter**: partial delta vs token delta (or wall-time delta) to show where the lift cost more search.
4. **Table**: top wins/losses with task name, baseline->OM partial, and file-path evidence from `pair_0_top_wins.md` / `pair_1_top_losses.md`.
5. **Error table**: tasks with stale-context debug errors, grouped by outcome, to show the internal worker issue is orthogonal to benchmark success.

## Recommended public wording

Use phrasing like: “In a paired replay of 113 tasks, OM improved average partial reward and binary solves, but the gain came with higher search cost and a small number of internal worker lifecycle errors. The result is promising, but it is not a multi-seed, full-cost, or provider-failure study.”