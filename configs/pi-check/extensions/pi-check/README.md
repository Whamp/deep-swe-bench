# pi-check

`pi-check` adds a one-shot verification pass to [Pi](https://github.com/earendil-works/pi-mono). The pass asks the current model to re-audit the task with fresh evidence, fix failures or uncertainty, rerun the relevant checks, and briefly report what it verified.

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

Run `/check` before or during a task.

When Pi is idle, `/check` arms verification for the next task without starting an agent turn:

```text
/check
Implement the authentication change.
```

When Pi is working, `/check` queues verification as a follow-up to the current run. It does not steer or interrupt the current response.

A check is one-shot. Repeating `/check` while one is armed, queued, or running does not queue another pass. After the checked run settles, `/check` can target a later task.

## Headless use

Use `--check` with print mode:

```bash
pi --check -p "Implement the authentication change."
```

Pi runs the task, processes the verification follow-up, prints the verifier's final response, and exits.

Use the same flag with JSON output:

```bash
pi --check --mode json -p "Implement the authentication change."
```

JSON mode emits Pi's ordinary event stream for both the task and verification activity.

## Ordering and limits

Verification is an ordinary Pi follow-up at the queue position where it was requested. Messages queued later remain later.

The pass uses the same session, model, tools, working directory, and conversation context as the original task. It gathers fresh evidence, but it is not an independent evaluator or deterministic quality gate.

`pi-check` does not add an LLM-callable tool, a second model, a retry loop, or changes to Pi core.

## Development

```bash
npm install
npm test
npm run typecheck
npm run lint
npm run format:check
```
