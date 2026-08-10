# pi-check

`pi-check` adds a one-shot verification pass to [Pi](https://github.com/earendil-works/pi). The pass asks the current model—or a model chosen for one check—to re-audit the task with fresh evidence, fix failures or uncertainty, rerun the relevant checks, and briefly report what it verified.

## Install

Install from GitHub:

```bash
pi install git:github.com/Whamp/pi-check
```

Install a local checkout:

```bash
pi install /absolute/path/to/pi-check
```

To try the extension without installing the package:

```bash
pi -e ./extensions/checkExtension.ts
```

Pi packages run with your full system permissions. Review the extension before installing it.

## Interactive use

Run `/check` without an argument to use Pi's current model and thinking level:

```text
/check
Implement the authentication change.
```

When Pi is idle, the command arms the next task without starting an agent turn. When Pi is working, it queues verification as a normal follow-up without steering or interrupting the response.

Pass an exact `provider/model:thinking` value to use a different model for one check:

```text
/check openai-codex/gpt-5.4:xhigh
Implement the authentication change.
```

Pi runs the task with the current model. At the next point with no queued messages, it switches to the requested model, queues verification, then restores the previous model and thinking level.

A model-specific `/check` entered while Pi is working is rejected if another message is already queued. Work submitted after an accepted command may finish before verification because the model-specific check waits for the next empty queue.

A check is one-shot. Repeating `/check` while one is armed, waiting, queued, running, or restoring does not add or replace a pass. After restoration and settlement, `/check` can target another task.

### Preflight before changes

Run `/check-preflight` with no arguments to arm a one-task architecture checkpoint before Pi's first detected file change:

```text
/check-preflight
Implement the authentication change.
```

At idle, the command arms the next task. During active work, it arms the current unsettled task. Invoke it again before it triggers to disarm it. The first detected `edit` or `write` is blocked before execution and Pi steers the same model in the same session through the fixed checkpoint. The blocked call is never replayed; after the checkpoint, the model must reissue any still-needed change on a later response.

After preflight triggers, it is unavailable until the targeted task settles. Other detected mutations from the same assistant response are also blocked, while read-only siblings may finish. The latch clears for the next response, so the model can reissue the change. A task that settles without a detected mutation simply expires the unused preflight.

The target is one unsettled task, not one low-level model run. Automatic retries, overflow-compaction retries, steering, and queued continuations keep the same armed or spent state. Terminal errors and user aborts end it through normal settlement. Reload, new/resumed sessions, forks/clones, and quit discard all runtime-local preflight state. Preflight does not write session entries or reconstruct earlier mutation attempts from history.

Preflight always detects `edit` and `write`. Its Bash matcher deliberately recognizes only a narrow positive set: in-place `sed`/`perl`/`ruby`, ordinary-file redirects, `tee`, `truncate`, `dd of=`, `patch`, `git apply`, and common direct filesystem commands such as `rm`, `mv`, `cp`, and `touch`. Redirects to `/dev/null`, stdout, stderr, and descriptor duplication do not trigger it. Unknown or ambiguous commands—including package managers, formatters, generators, arbitrary scripts and interpreters, and Git checkout/reset/restore—remain allowed.

This matcher is incomplete by design. Preflight is a planning aid, not a shell parser, sandbox, permission boundary, or security control.

## Headless use

Use `--check-preflight` to arm preflight for the first task in TUI, print, JSON, or RPC mode:

```bash
pi --check-preflight -p "Implement the authentication change."
pi --check-preflight --mode json -p "Implement the authentication change."
pi --check-preflight --mode rpc
```

RPC clients may also send `/check-preflight` through the normal `prompt` command while idle or streaming. The command runs immediately through Pi's ordinary extension-command path. Print and JSON emit no substitute status record; JSON and RPC expose only Pi's existing user messages, tool results, queue updates, and lifecycle events. Preflight adds no custom recap event, schema, or exit status.

`--check` requires an exact `provider/model:thinking` value. Bare `--check` is no longer supported.

```bash
pi --check openai-codex/gpt-5.4:xhigh -p "Implement the authentication change."
```

Pi runs the task with the original model, verifies it with the requested model, restores the original model and thinking level, prints the verifier's final response, and exits.

Use the same value with JSON output:

```bash
pi --check openai-codex/gpt-5.4:xhigh --mode json -p "Implement the authentication change."
```

JSON mode emits Pi's ordinary events for the task and verification.

The value must name an exact provider, model ID, and Pi thinking level. `pi-check` does not resolve aliases, bare model IDs, partial matches, or fallback lists. Pi may adjust a valid thinking level to one supported by the selected model.

If the value is malformed, unknown, unavailable, or unauthenticated, Pi still runs the original task after accepting the complete flag value. It skips verification, writes the reason to stderr, and exits non-zero. Text mode prints the original task's final response; JSON mode emits the original task's events. A missing flag value is a CLI error and may stop before the task starts.

## Ordering and limits

Preflight and final verification are independent one-shots: `/check-preflight`, `--check-preflight`, `/check`, and `--check` retain separate state in every mode. When both are armed and preflight triggers, Pi's normal queue ordering delivers its `steer` checkpoint before the verification `followUp`. If preflight is still unused when the expected verification prompt actually starts, it expires and remains unavailable until settlement, so verifier `edit`, `write`, and classified Bash calls proceed. A failure, expiry, or abort in either lifecycle does not cancel or re-arm the other.

Preflight relies on Pi's native first-blocker-wins order. An earlier extension block prevents pi-check from seeing or consuming the call. If pi-check blocks first, later blockers do not see that call. Pi-check does not arbitrate, override, or replay blocks.

Plan mode needs no special integration. Preflight remains armed while mutation tools are hidden and can trigger if queued execution starts before the task settles. Planning that settles without execution expires it normally.

Classifier and synchronous steering-delivery failures fail open: the current mutation is allowed, preflight closes for that run, and pi-check emits a best-effort warning without changing the exit status. Pi's public `sendUserMessage()` API returns `void`; an asynchronous steering rejection cannot be observed retroactively, so only synchronous delivery throws can be handled at the blocking boundary.

A same-model `/check` uses Pi's normal follow-up queue position. A model-specific check waits to add its prompt until the temporary model switch succeeds and no other messages are queued. This prevents a failed switch from silently running verification on the original model.

The pass uses the same session, tools, working directory, and conversation context as the original task. Temporary model and thinking changes may appear in session history, but the prior selection is restored after verification succeeds, fails, or is aborted. A restoration failure is reported and makes headless execution exit non-zero.

A selected model gives the verification turn different capabilities, but not an independent context. The result is not a deterministic quality gate.

`pi-check` does not add an LLM-callable tool, a second session, a direct provider call, a retry loop, or changes to Pi core.

## Development

```bash
npm install
npm test
npm run typecheck
npm run lint
npm run format:check
```
