# pi-recursive config research handoff

This directory is intentionally **not yet a runnable deep-swe-bench config**. It is a fresh config directory created to preserve research/context from a ypi/pi-recursive investigation so another agent session can build the real config files later.

Do not treat this as complete until a later session adds the usual config artifacts such as `orchestration.md`, `pi-flags`, model leaf directories, `env`, and/or `smoke.json` as appropriate.

## Source context

Research came from inspecting `/home/will/projects/ypi` on 2026-07-02 plus local Pi docs:

- ypi repo current `master` at `8753ce4` (`2026-06-22`, `ci: local-first test/release flow; hermetic pinned CI; drop scheduled drift workflow`).
- npm registry currently has `ypi@0.6.1` and `pi-recursive@0.6.1`.
- `pi-recursive` is the new pure Pi extension package split out of ypi.
- Relevant ypi files inspected:
  - `/home/will/projects/ypi/CHANGELOG.md`
  - `/home/will/projects/ypi/README.md`
  - `/home/will/projects/ypi/pi-recursive/README.md`
  - `/home/will/projects/ypi/extensions/recursive.ts`
  - `/home/will/projects/ypi/extensions/ypi/env.ts`
  - `/home/will/projects/ypi/extensions/ypi/native-tool.ts`
  - `/home/will/projects/ypi/extensions/ypi/prompt.ts`
  - `/home/will/projects/ypi/extensions/ypi/runtime.ts`
  - `/home/will/projects/ypi/SYSTEM_PROMPT.md`
- Relevant Pi docs inspected:
  - `docs/extensions.md`
  - `docs/packages.md`
  - `docs/settings.md`
  - `docs/security.md`

## Main conclusion

For a plain Pi-based config, prefer installing/loading **`pi-recursive`** as a Pi package/extension rather than running the `ypi` CLI wrapper.

`pi-recursive` gives Pi a native recursive `rlm_query` tool. The `ypi` CLI remains useful only when the shell wrapper ergonomics are needed (`rlm_query` binary, pipes, async shell jobs, `rlm_cost`, `rlm_sessions`, `rlm_cleanup`, etc.).

Minimal install/use:

```bash
pi install npm:pi-recursive
pi
```

One-shot test/use:

```bash
pi -e npm:pi-recursive "Use rlm_query to ask a child what 2 + 2 is."
```

Project-local install:

```bash
pi install -l npm:pi-recursive
```

Equivalent Pi settings entry:

```json
{
  "packages": ["npm:pi-recursive"]
}
```

Global installs write `~/.pi/agent/settings.json`; project-local installs write `.pi/settings.json` and are subject to Pi project trust.

## What changed in ypi recently

The project was quiet after March 2026, then got a substantial June refresh.

Important timeline:

- `v0.5.1` fixed macOS portability (`mktemp`, Bash 3.2 array behavior).
- npm-only `ypi@0.5.2` added the `pi-package` keyword for gallery discoverability; that commit was not reachable from current remote history when checked.
- `v0.6.0` introduced the major architecture shift:
  - `extensions/recursive.ts` became the canonical Pi extension.
  - Native Pi `rlm_query` tool added.
  - Extension implementation split under `extensions/ypi/`.
  - Pure extension companion package `pi-recursive` added.
  - `ypi` became the batteries-included CLI wrapper around the same extension.
- `v0.6.1` aligned npm package keywords with Pi package gallery conventions and verified registry install of `pi-recursive`.

Important hardening in 0.6.x:

- Fixed `RLM_MAX_CALLS` off-by-one.
- Sanitized `RLM_TRACE_ID` before path use.
- Anchored `RLM_START_TIME` per depth-0 recursion tree to avoid stale timeout failures in long-running root sessions.
- Made malformed depth config fail closed.
- Fixed async notify JSON escaping/TMPDIR handling in shell helper path.
- Expanded provider credential env allowlist, including `COPILOT_GITHUB_TOKEN` and `HF_TOKEN`.
- Added native tool tests, provider allowlist tests, pack tests, registry install smoke, pure-extension parity/e2e checks.

## Native extension behavior

`extensions/recursive.ts` does three important things:

1. Ensures recursive environment defaults.
2. Registers native Pi tool `rlm_query` when current depth is below max depth.
3. Patches Pi's system prompt before agent start.

Native tool behavior from `extensions/ypi/native-tool.ts`:

- Tool name: `rlm_query`.
- Parameters:
  - `prompt` string, required.
  - `context` string, optional exact child context.
  - `fork` boolean, optional copy of current session into child session.
- Spawns child `pi` with the same extension path where possible.
- Uses JSON mode by default (`RLM_JSON=1`) so child cost can be parsed.
- Uses jj workspace isolation automatically when available and `RLM_JJ != 0`.
- If jj is unavailable/disabled, child tools are read-only by default (`read,grep,find,ls,rlm_query`) unless `RLM_UNSAFE_NO_JJ_WRITE=1`.
- Child Pi disables skill/prompt/theme/context-file discovery by default unless `RLM_CHILD_DISCOVERY=1`.
- Shared child sessions are enabled by default (`RLM_SHARED_SESSIONS=1`).

## Configuration surface

`pi-recursive` configuration is currently environment-variable based, not Pi `settings.json` based. Pi settings install/load the package; runtime behavior comes from env vars in the Pi process.

Primary knobs:

| Env var | Default | Meaning |
| --- | --- | --- |
| `RLM_MAX_DEPTH` | `3` | Maximum recursion depth. |
| `RLM_MAX_CALLS` | unset | Maximum total `rlm_query` invocations in the tree. |
| `RLM_TIMEOUT` | unset | Wall-clock seconds for the recursive tree. |
| `RLM_BUDGET` | unset | Dollar budget for the recursive tree; native mode requires `RLM_JSON=1`. |
| `RLM_CHILD_PROVIDER` | parent provider | Provider for child calls at depth > 0. |
| `RLM_CHILD_MODEL` | parent model | Model for child calls at depth > 0. |
| `RLM_JJ` | `1` | Use jj workspace isolation automatically when available; set `0` to disable. |
| `RLM_SHARED_SESSIONS` | `1` | Share child sessions in the active Pi session dir; set `0` for `--no-session`. |
| `RLM_CHILD_DISCOVERY` | `0` | Set `1` to let child Pi load skills, prompt templates, themes, context files, and approval prompts. |
| `YPI_EXTENSION_PROMPT_MODE` | `append` | `append` ypi prompt to Pi prompt, or `replace` Pi prompt with ypi prompt. |
| `YPI_EXTENSION_DEBUG` | unset | Set `1` to emit debug sentinels on stderr. |
| `RLM_UNSAFE_NO_JJ_WRITE` | `0` | Set `1` to allow write tools when jj isolation is unavailable/disabled. Use carefully. |

Secondary/advanced env vars observed in source:

| Env var | Notes |
| --- | --- |
| `RLM_EXTENSIONS` | Defaults `1`; if `0`, disables recursion extension loading. |
| `RLM_CHILD_EXTENSIONS` | Overrides extension loading for child depths. |
| `RLM_JSON` | Defaults `1`; set `0` for plain `-p` child output, but budget enforcement cannot measure cost. |
| `RLM_PROVIDER` / `RLM_MODEL` | Usually filled from active Pi model; can force parent/child provider-model. |
| `RLM_TRACE_ID` | Auto-generated, sanitized; used in temp/session filenames. |
| `RLM_CALL_COUNTER_FILE` | Auto-created counter file for total calls. |
| `RLM_COST_FILE` | Auto-created when `RLM_BUDGET` is set. |
| `RLM_SESSION_DIR` / `RLM_SESSION_FILE` | Session plumbing for children. |
| `RLM_SYSTEM_PROMPT` | Defaults to package `SYSTEM_PROMPT.md`. |
| `RLM_PROMPT_FILE` | Child prompt file path; set internally. |
| `YPI_PI_BIN` | Override the child Pi binary. |
| `YPI_EXTENSION_ROOT` / `YPI_EXTENSION_PATH` | Extension runtime paths; normally managed internally. |
| `YPI_SHELL_HELPER` | Off in pure extension mode; ypi wrapper sets `1` to expose shell helper/source. |

## Where to expose config for deep-swe-bench

Future config-building session should likely use the existing deep-swe-bench pattern:

- Use a config-local `env` file for `RLM_*` / `YPI_*` knobs.
- Use Pi package settings/flags to load `npm:pi-recursive`.
- Do not use the `ypi` binary if the comparison is intended to test Pi with the extension installed.
- Do not enable `YPI_SHELL_HELPER=1` unless intentionally testing ypi shell-helper behavior.
- Do not add runnable launch artifacts without running the project’s config validation workflow/skill first.

Possible starting env for a benchmark-safe out-of-box config:

```bash
YPI_EXTENSION_PROMPT_MODE=append
YPI_EXTENSION_DEBUG=1
RLM_MAX_CALLS=8
RLM_TIMEOUT=900
RLM_CHILD_THINKING=low
RLM_COST_FILE=/out/pi-recursive-cost.jsonl
RLM_CALL_COUNTER_FILE=/out/pi-recursive-calls.counter
```

Do not set `RLM_BUDGET` for the first scored comparison. It is too sensitive to
model price and would turn cost into a hard stop instead of an observed metric.

Model routing should be decided explicitly. If child model differs from parent, set both:

```bash
RLM_CHILD_PROVIDER=<provider>
RLM_CHILD_MODEL=<model-id>
```

For benchmark integrity, make the child model choice part of the config identity/documentation.

## Prompt content appended by pi-recursive

By default, `pi-recursive` appends `/home/will/projects/ypi/SYSTEM_PROMPT.md` to Pi's normal system prompt.

Default behavior:

```text
Pi normal system prompt
+
ypi recursive prompt
```

If set:

```bash
YPI_EXTENSION_PROMPT_MODE=replace
```

then the extension replaces Pi's normal prompt with the ypi recursive prompt.

The appended ypi prompt contains these sections:

1. **Core Identity**
   - Agent is a recursive LLM with native `rlm_query`.
   - Current depth comes from `RLM_DEPTH`; respect `RLM_MAX_DEPTH`.
   - Sub-agents get fresh context windows.
   - Context is finite/non-renewable.

2. **Recursive Decomposition**
   - Core pattern: size up → search → delegate → combine.
   - Use `$CONTEXT` as a file when present.
   - Use `$RLM_PROMPT_FILE` for exact original prompt access.
   - Prefer direct work for small tasks.
   - Includes examples for small direct tasks, multi-file refactors, chunking large files, and async shell-helper usage.

3. **Coding and File Editing**
   - Directly modify files when asked; don't only describe changes.
   - Check for jj workspace.
   - Child agents use jj workspaces when available/enabled.
   - Without jj, children are read-only unless `RLM_UNSAFE_NO_JJ_WRITE=1`.

4. **Guardrails & Cost Awareness**
   - Explains `RLM_TIMEOUT`, `RLM_MAX_CALLS`, `RLM_BUDGET`.
   - Mentions optional shell-suite helpers (`rlm_cost`, `rlm_sessions`, `rlm_cleanup`) only when available.
   - Warns not to run foreground `rlm_query` loops; use async shell helper when available for parallel work.

5. **Rules**
   - Search before reading.
   - Size up before delegating.
   - Validate sub-agent output.
   - Use computation for counts/dates/math.
   - Act, don’t describe.
   - Keep sub-agent tasks small.
   - At deeper depths, prefer direct actions.

Optional Section 6:

- The full shell `rlm_query` implementation is appended only when `YPI_SHELL_HELPER=1` and the shell file exists.
- Plain `pi-recursive` normally does **not** include this section.

## ypi vs pi-recursive split

Use `pi-recursive` when:

- You want recursion inside ordinary Pi.
- You want native `rlm_query` as a tool.
- You do not need shell piping/async wrappers or ypi helper binaries.

Use `ypi` when:

- You want a preconfigured recursive CLI wrapper.
- You need shell-compatible `rlm_query` on PATH.
- You need pipes/async shell jobs or helper commands (`rlm_cost`, `rlm_sessions`, `rlm_cleanup`).

For this benchmark config, current preference is **`pi-recursive`**, not `ypi`, unless the experiment is explicitly about shell-helper behavior.

## Current GitHub/open-work context from ypi

When checked, ypi had open PRs that may affect future behavior but were not merged into master:

- PR #16: dynamic depth/call counter meter.
- PR #14: sync model/provider into child calls after interactive model switch.
- PR #13: unicode arrow parsing and macOS temp path test.
- PR #9: resolve Pi binary from `node_modules` instead of bare PATH.
- PR #3: macOS Bash 3.2 launcher fix.

Relevant open issues:

- Windows support request.
- `pi: not found` when installed via bun.
- Old upstream compatibility bot issues likely made stale by the local-first CI change.

## Validation notes for later session

Before turning this into a runnable config, use the repo’s `benchmark-config-validation` guidance as required by `AGENTS.md`.

Likely things to prove:

- Pi package install/load path for `npm:pi-recursive` works in the harness environment.
- Native tool `rlm_query` is registered in the smoke run.
- `RLM_*` env vars are visible to the Pi process.
- Child calls use intended provider/model and record usage in a compact/accountable source.
- If secondary/child model differs from executor model, get explicit user confirmation before benchmark launch per repo rules.
- Avoid persisting raw per-cell `--mode json` streams; use native session usage or a compact secondary usage source.

## Proposed deep-swe-bench config design (2026-07-02)

Design goal: test the ordinary `pi-recursive` Pi package experience, not the `ypi`
CLI wrapper and not a custom curated recursive-agent prompt. Use defaults wherever
benchmark safety/accounting does not require an override.

### Recommended config identity

Use one config first:

```text
configs/pi-recursive
```

Meaning: Pi with the `pi-recursive` package installed/loaded, native `rlm_query`
tool available, no shell helper, no hand-authored workflow prompt beyond the
package's own default prompt patch.

Do **not** fold `jj` setup or unsafe child-write mode into this config. If we later
want writable child workspaces, make a separate config such as
`pi-recursive-jj`, because that is not the same out-of-box experience.

### Package loading

Use a vendored package directory under the config and load it explicitly with
`pi-flags`, because `harness/run.py` always passes `--no-extensions` before
config-authored flags. Relying on `settings.json` `packages` would be less clear
and may be suppressed by `--no-extensions`; relying on `npm:pi-recursive` would
also require runtime network/package install inside the benchmark container.

Proposed files:

```text
configs/pi-recursive/pi-flags
configs/pi-recursive/orchestration.md
configs/pi-recursive/env
configs/pi-recursive/extensions/pi-recursive/package.json
configs/pi-recursive/extensions/pi-recursive/extensions/recursive.ts
configs/pi-recursive/extensions/pi-recursive/extensions/ypi/*.ts
configs/pi-recursive/extensions/pi-recursive/SYSTEM_PROMPT.md
configs/pi-recursive/gpt-5.5/low/settings.json
configs/pi-recursive/gpt-5.5/low/smoke.json
```

Proposed `pi-flags`:

```text
-e
/arm/extensions/pi-recursive
```

This uses Pi package directory loading so the package manifest, not a custom
entrypoint path, selects `./extensions/recursive.ts`.

### Orchestration prompt

Use neutral orchestration, matching extension-backed configs such as Ponytail:

```text
No extra task guidance. The installed pi-recursive Pi package controls recursive delegation.
```

Do **not** add extra instructions like "always call rlm_query". That would test a
curated benchmark prompt rather than what a user gets after installing the
extension.

### System prompt mode

Use `YPI_EXTENSION_PROMPT_MODE=append`.

Rationale:

- `append` is the package default.
- It preserves Pi's normal system prompt, the deep-swe-bench system preamble,
  task context, tool descriptions, and config orchestration.
- `replace` would remove core Pi/harness instructions and would not represent a
  normal `pi install npm:pi-recursive` user experience.

Even though `append` is default, put it in `env` for auditability because result
artifacts currently do not record config env files.

### `jj` decision

For the first config, do **not** install or initialize `jj`.

Important nuance: installing the `jj` binary alone is insufficient. The extension
calls `jj root` in `/app`; DeepSWE task checkouts are Git repos, not jj repos, so
`jj root` will still fail unless we also run something like
`jj git init --colocate` inside each task repo before Pi starts. That setup would
be an extra benchmark intervention.

Out-of-box behavior with no jj workspace is:

- `RLM_JJ` defaults to `1`, but `jj root` fails.
- child `rlm_query` agents run in the current checkout with read-only tools
  (`read,grep,find,ls,rlm_query`) unless `RLM_UNSAFE_NO_JJ_WRITE=1`.
- the parent executor still does all final edits.

That is the correct first-pass behavior for `configs/pi-recursive`. A later
`pi-recursive-jj` config can intentionally add jj binary + per-cell `jj git init
--colocate` + child usage/accounting smoke checks.

### Environment defaults and benchmark guardrails

Use light recursion guardrails plus audit/smokeability fields:

```text
YPI_EXTENSION_PROMPT_MODE=append
YPI_EXTENSION_DEBUG=1
RLM_MAX_CALLS=8
RLM_TIMEOUT=900
RLM_CHILD_THINKING=low
RLM_COST_FILE=/out/pi-recursive-cost.jsonl
RLM_CALL_COUNTER_FILE=/out/pi-recursive-calls.counter
```

`RLM_MAX_CALLS=8` and `RLM_TIMEOUT=900` are reasonable benchmark safety limits:
they still allow several bounded child delegations, while preventing one cell
from spending the whole harness timeout in recursive children. The normal harness
`agent_timeout` still bounds the whole cell.

Do **not** set `RLM_BUDGET=1.00`. A fixed one-dollar cap is arbitrary,
model-price-dependent, and can prematurely cut off expensive-but-valid cells. Cost
should be measured, not used as a hard stopper, for this first config.

`YPI_EXTENSION_DEBUG=1` emits stderr sentinels such as
`__YPI_NATIVE_TOOL_REGISTERED__` for smoke checks. The two `/out` files make
call/cost sidecars durable for audit and parser cross-checks. The authoritative
scored usage still comes from parsed session JSONL.

Leave these unset to use package defaults:

```text
RLM_MAX_DEPTH        # default 3
RLM_BUDGET           # unset = no package dollar cap; benchmark accounting still records usage
RLM_JJ               # default 1, but no jj workspace means read-only children
RLM_SHARED_SESSIONS  # default 1
RLM_CHILD_DISCOVERY  # default 0
RLM_CHILD_PROVIDER   # inherit parent provider
RLM_CHILD_MODEL      # inherit parent model
RLM_CHILD_THINKING   # set to low in this config so child Pi calls match parent thinking
RLM_UNSAFE_NO_JJ_WRITE # default 0; do not enable in this config
YPI_SHELL_HELPER     # default off in pure pi-recursive package
```

### Child model and thinking

Use the same provider/model as the parent by default. Do not set
`RLM_CHILD_PROVIDER` or `RLM_CHILD_MODEL` unless making a separate child-model
config.

The vendored `pi-recursive` copy has been patched to support
`RLM_CHILD_THINKING`. When set, child Pi calls add `--thinking <level>` to their
spawned `pi` command and propagate that value as `RLM_THINKING` to deeper
children. This config sets `RLM_CHILD_THINKING=low`, so GPT-5.5-low executor and
recursive child calls use the same thinking level. The leaf also keeps:

```json
{
  "defaultThinkingLevel": "low"
}
```

as a fallback for Pi processes that resolve a default thinking level from
settings. For other executor thinking levels, use a matching leaf-local env and
settings file.

### Usage/accounting status before launch

Parser support is now implemented in `harness/parse_usage.py` and covered by
`tests/test_parse_usage.py`.

With default `RLM_SHARED_SESSIONS=1`, child Pi sessions are written under the same
`/out/session` directory as the parent. The parser now:

1. Treats the newest non-`*_d<depth>_c<call>.jsonl` file as the root executor
   session for normal `total_tokens`/`turns`.
2. Parses current-attempt `*_d<depth>_c<call>.jsonl` child sessions separately
   into `recursive_child_*` fields, including `recursive_child_calls`,
   `recursive_child_total_tokens`, and `recursive_child_cost_usd`.
3. Adds recursive child totals into `combined_total_tokens` and
   `combined_cost_usd`.
4. Keeps `RLM_COST_FILE=/out/pi-recursive-cost.jsonl` as an audit cross-check,
   not the primary scored usage source.

Remaining requirement before scored fan-out: run a one-task smoke/preflight that
actually invokes `rlm_query` and proves nonzero `recursive_child_*` fields in the
result cell. Do not use `RLM_SHARED_SESSIONS=0` for scored comparisons because it
hides child transcripts and weakens usage auditing.

### Smoke contract shape

A config-authored smoke contract should prove package load and prompt/tool
registration without requiring the benchmark task agent to actually choose
`rlm_query` on the smoke task.

Suggested checks:

- `equalsResultValues`: config/model/thinking.
- `minResultValues`: `combined_total_tokens >= 1`.
- `requireFiles`: `session/*.jsonl`, `logs/pi.stderr.txt`.
- `requireText` in `logs/pi.stderr.txt`:
  - `__YPI_EXTENSION_LOADED__`
  - `__YPI_NATIVE_TOOL_REGISTERED__`
  - `__YPI_EXTENSION_PROMPT_PATCHED__`
- `requireRepoFiles` for `orchestration.md`, `pi-flags`, `env`, vendored
  package files, `SYSTEM_PROMPT.md`, and relevant model docs.
- `requireRepoText` proving:
  - `pi-flags` loads `/arm/extensions/pi-recursive`
  - `env` uses append mode and audit sidecars
  - vendored `package.json` is `"name": "pi-recursive"`
  - vendored source registers `rlm_query`
  - `RLM_UNSAFE_NO_JJ_WRITE=1` is absent
- `forbidText`: `model_unavailable`, `Previous response with id`, and other
  known provider-corruption strings.

A separate manual preflight should run a direct Pi prompt like "Use `rlm_query`
to ask a child what 2 + 2 is" to prove child calls, usage parsing, and read-only
fallback before any 12/36-task fan-out.

## Post-run failure mode found on 2026-07-02

The first GPT-5.5-low `pi-recursive` 12_v2 run found a validation failure that the
initial smoke should have caught before fan-out.

### What failed

Children did **not** fail to return answers to the parent. The parent received
non-empty `rlm_query` results for every top-level cell.

The actual handicap was the read-only child tool surface when no `jj` workspace
was available:

```ts
const READ_ONLY_TOOLS = "read,grep,find,ls,rlm_query";
```

Pi's `grep` and `find` are built-in Pi tools, but their default implementations
call external `rg` and `fd` binaries. In the DeepSWE task containers these were
not available/downloadable for child Pi processes, so child search repeatedly
failed with:

```text
ripgrep (rg) is not available and could not be downloaded
fd is not available and could not be downloaded
```

This was an obviously bad benchmark handicap: children were asked to audit real
code changes but had no working recursive search and no `bash` fallback because
`bash` was excluded from the read-only tool list. They could still use `ls` and
`read`, so the treatment was not mechanically broken, but it was compromised and
wasted compute.

### Smoke lesson

For configs with nested workers/subagents, a smoke must prove the child agent's
actual tool surface works, not just that the extension registered and returned a
non-empty answer.

The pi-recursive smoke contract now forbids the exact child failure strings above
and requires durable child artifacts (`session/*_d1_c*.jsonl`,
`pi-recursive-cost.jsonl`, `pi-recursive-calls.counter`). A future clean smoke
should also force a child to exercise its intended retrieval path before any
multi-task fan-out.

### Debug setting

`YPI_EXTENSION_DEBUG=1` is useful only for local registration probes. It pollutes
parent-visible child answers with stderr markers such as
`__YPI_EXTENSION_LOADED__` because the native tool appends child stderr to the
returned tool text. Scored configs should use:

```bash
YPI_EXTENSION_DEBUG=0
```

and rely on result fields/session artifacts/smoke contracts for validation.

### Updated guardrail

The benchmark env has been changed from:

```bash
YPI_EXTENSION_DEBUG=1
RLM_MAX_CALLS=8
```

to:

```bash
YPI_EXTENSION_DEBUG=0
RLM_MAX_CALLS=12
```

`RLM_MAX_CALLS=12` gives a little more room for recursive audit branches while
still bounding runaway recursion.

### Open fix decision

There are three plausible fixes, each a different treatment and therefore a
separate config or explicit config revision:

1. **Make read-only tools actually work.** Provide `rg` and `fd` to child Pi
   processes, or ship reliable wrapper binaries/scripts. This preserves the
   intended read-only child model.
2. **Allow child `bash` without edit/write.** This restores search/test/diff
   capability but is not truly read-only because shell commands can mutate `/app`.
   It should be treated as a different, less isolated config unless guarded by a
   workspace or filesystem policy.
3. **Use `jj` workspaces.** Install/initialize `jj` so `maybeCreateJjWorkspace()`
   succeeds and children can safely get full tools in isolated workspaces. This
   is the cleanest recursive-agent treatment, but it is not the same out-of-box
   no-jj config and needs its own smoke proving child edits/tests do not mutate
   the parent checkout.

Do not rerun a scored pi-recursive comparison until one of these paths has a
passing smoke that demonstrates child retrieval/search works.

### Selected immediate fix: make Pi read-only tools functional

Correction after review: the right first fix is not to work around broken child
search by changing child behavior. It is to make Pi's built-in read-only tools
fully functional in the benchmark image.

`harness/Dockerfile.pi-agent` now installs:

```bash
apt-get install -y --no-install-recommends ripgrep fd-find
ln -sf /usr/bin/fdfind /usr/local/bin/fd
```

and `harness/lib.py` now tags pi images with `PI_IMAGE_REV = "v2-tools"` so
cached `deep-swe-pi:*` images built before this fix are not silently reused.
Future pi-recursive smokes should verify no child session contains the missing
`rg`/`fd` failure strings. This preserves the intended no-jj treatment: child
agents are read-only, but their `grep` and `find` tools actually work.

### Decision correction: keep git-worktree behavior out of this config

After review, the jj→git-worktree instruction changes were judged too extensive
for `configs/pi-recursive`. This config should now test the upstream
`pi-recursive` prompt plus fixed Pi read-only tool dependencies (`rg`/`fd`) only.

The vendored `SYSTEM_PROMPT.md` has been restored to the upstream
`pi-recursive/SYSTEM_PROMPT.md` text. The smoke contract no longer pins the
temporary "parent-writes, child-audits" Git/no-jj wording.

If we want Git-worktree-backed writable children, make that a separate config
such as `pi-recursive-git-worktree`. That config should implement actual
launcher support for `git worktree add`, child execution in the temporary
worktree, patch/diff collection, and cleanup. Do not simulate that treatment by
changing only prompt text in the baseline `pi-recursive` config.
