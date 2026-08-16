# Leaderboard token efficiency

The leaderboard reports **Solves / 1M adjusted tokens** as a secondary efficiency metric. Solve rate remains the primary quality metric.

## `cache-read-10pct-v1`

Version 1 gives cache-read tokens 10% of the weight of other model tokens:

```text
adjusted tokens = reported total tokens - (0.90 × known cache-read tokens)
solves / 1M adjusted tokens = solved cells × 1,000,000 / adjusted tokens
```

`reported total tokens` uses `combined_total_tokens` when available, so the denominator includes the main executor and declared secondary model roles. It falls back to `total_tokens` for older artifacts.

Known cache reads are the sum of:

- main executor `cache_read_tokens`
- advisor `advisor_cache_read_tokens`
- observational-memory worker `om_worker_cache_read_tokens`
- recursive child `recursive_child_cache_read_tokens`
- workflow agent `workflow_cache_read_tokens`

Tokens without a component breakdown remain in the denominator at full weight. The policy never infers unreported cache usage or drops unclassified secondary-role tokens.

The run-level metric divides total solves by the sum of adjusted tokens across every selected cell, including failed cells. It does not average per-cell ratios. A run with no reported tokens has no efficiency value.

The leaderboard also shows aggregate cache-read share:

```text
cache-read share = known cache-read tokens / reported total tokens
```

Cache-read share describes the token composition; it is not the cache discount.

## Historical results

The dashboard derives these fields when it reads existing `result.json` artifacts. Historical leaderboard rows are therefore backfilled without modifying official result artifacts. The API includes the policy name and cache-read weight with every comparison row so the denominator remains auditable if a later policy version changes.
