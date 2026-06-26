# pi-advisor GLM-5.2 DeepSWE analysis
Compared `pi-advisor-glm52` against the reused DeepSeek baseline symlink `/home/will/evals/deep-swe-bench/runs/ponytail-full-pilot-w2/baseline` over 113 paired tasks.
## Headline
- Mean partial: baseline 0.774 → advisor 0.536 (Δ -0.238).
- Full solves: baseline 2/113 → advisor 5/113.
- Advisor also produced many no-patch failures: skipped-empty-patch 4 → 27.
- Median main tokens fell 3291131 → 1905050; median combined tokens were 1909021.
- Median main cost fell $0.1501 → $0.0997; Z.AI advisor cost is configured as subscription-backed $0 in this harness.

## Difficulty buckets
- hard: partial 0.401 → 0.343 (Δ -0.058), solves 0→0, empty patches 4→12.
- medium: partial 0.934 → 0.559 (Δ -0.375), solves 0→1, empty patches 0→9.
- easy: partial 0.991 → 0.707 (Δ -0.284), solves 2→4, empty patches 0→6.

## Advisor usage
- Advisor was called in 101/113 tasks; call counts {'1': 75, '2': 22, '3': 4, '0': 12}.
- Total advisor tokens 536,450; median 4008; mean per advisor call 4095.
- Provider/model recorded: {'zai': 101, 'None': 12} / {'glm-5.2': 101, 'None': 12}.

## Top wins by partial
- mashumaro-flattened-dataclass-fields (hard): 0.000 → 0.998 (Δ +0.998), binary 0→0, advisor calls 1.
- fastapi-implicit-head-options (hard): 0.000 → 0.987 (Δ +0.987), binary 0→0, advisor calls 1.
- anko-default-function-arguments (hard): 0.000 → 0.983 (Δ +0.983), binary -1→0, advisor calls 1.
- go-critic-doc-link-checker (hard): 0.000 → 0.895 (Δ +0.895), binary 0→0, advisor calls 1.
- goreleaser-retry-publish-auditing (hard): 0.466 → 0.983 (Δ +0.517), binary 0→0, advisor calls 2.
- obsidian-linter-auto-table-of-contents (hard): 0.634 → 0.965 (Δ +0.331), binary 0→0, advisor calls 1.
- aiomonitor-task-snapshots-diff (hard): 0.754 → 0.951 (Δ +0.197), binary 0→0, advisor calls 2.
- scriggo-method-declarations (hard): 0.774 → 0.956 (Δ +0.182), binary 0→0, advisor calls 1.
- etree-xml-diff-patch (hard): 0.791 → 0.910 (Δ +0.119), binary 0→0, advisor calls 2.
- claude-code-by-agents-recursive-delegation (medium): 0.842 → 0.947 (Δ +0.105), binary 0→0, advisor calls 1.

## Top losses by partial
- narwhals-rolling-window-suite (easy): 0.999 → 0.000 (Δ -0.999), binary 0→-1, verifier skipped_empty_patch, advisor calls 0.
- adaptix-name-mapping-aliases (easy): 0.999 → 0.000 (Δ -0.999), binary 0→0, verifier 0, advisor calls 1.
- tomlkit-toml-table-converters (easy): 0.997 → 0.000 (Δ -0.997), binary 0→-1, verifier skipped_empty_patch, advisor calls 0.
- yjs-map-conflict-detection (easy): 0.996 → 0.000 (Δ -0.996), binary 0→-1, verifier skipped_empty_patch, advisor calls 0.
- gql-incremental-graphql-delivery (easy): 0.994 → 0.000 (Δ -0.994), binary 0→0, verifier 0, advisor calls 1.
- dateutil-rfc5545-timezone-interop (easy): 0.993 → 0.000 (Δ -0.993), binary 0→0, verifier 0, advisor calls 1.
- kombu-virtual-queue-dead-lettering (easy): 0.989 → 0.000 (Δ -0.989), binary 0→-1, verifier skipped_empty_patch, advisor calls 0.
- httpx-streaming-json-iteration (easy): 0.983 → 0.000 (Δ -0.983), binary 0→-1, verifier skipped_empty_patch, advisor calls 0.
- sqlfmt-create-table-ddl-formatting (easy): 0.979 → 0.000 (Δ -0.979), binary 0→-1, verifier skipped_empty_patch, advisor calls 1.
- katex-multicolumn-array-spans (medium): 0.978 → 0.000 (Δ -0.978), binary 0→-1, verifier skipped_empty_patch, advisor calls 0.

## Audit
- Result files: 113/113; transient markers: 0 from previous check.
- Nonempty stderr files: 0; structured main-stream errors: 307; advisor tool errors: 3.
