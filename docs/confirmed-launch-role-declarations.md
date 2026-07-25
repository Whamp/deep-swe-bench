# Confirmed-launch model role declarations

A versioned config lock must declare every LLM role before launch planning can
produce a receipt. Planning stops before subject execution when a role, model
selection, call bound, credential route, usage source, subject version, required
capability, or extension surface is unresolved.

## Role schema

Each object in `declaredRoles` contains:

- `name`: unique role name used by launch surfaces and usage accounting.
- `roleKind`: descriptive pattern such as `executor`, `advisor`,
  `observational-memory`, `recursive`, or `workflow`. The compiler does not
  branch on this value.
- `modelSelection`: one of the model-selection forms below.
- `credentialRoute`: a route name also listed in `credentialRoutes`.
- `billingCategory`: `subscription quota`, `paid API`, or `local compute`.
- `usageSource`: a `path` listed in `usageSources` and a compact `format`.
  Every non-executor source also declares a structured `recordSelector` and a
  `resultAccounting` mapping with `calls` and `totalTokens` result fields.
- `callBehavior`: fixed or bounded calls per rep plus finite concurrency.

The supported compact usage formats are `native-session`,
`filtered-tool-events`, `compact-worker-trace`, and `compact-jsonl`. Raw
`pi.jsonl` event streams are invalid.

The executor is mandatory. Its fixed model and thinking must match the launch
request.

### Secondary usage accounting

A secondary role must connect its compact trace to both preflight evidence and
`result.json` accounting:

```json
{
  "format": "filtered-tool-events",
  "path": "tool-usage.jsonl",
  "recordSelector": {
    "type": "tool_execution_end",
    "toolName": "advisor"
  },
  "resultAccounting": {
    "calls": "advisor_calls",
    "totalTokens": "advisor_total_tokens"
  }
}
```

The versioned smoke contract must contain a `requireUsageRecords` assertion for
the same path and selector, plus positive `minResultValues` assertions for both
mapped result fields. Planning rejects a secondary role when any link is
missing. Preflight therefore cannot pass merely because executor-native session
usage exists.

### Fixed model

```json
{
  "kind": "fixed",
  "provider": "openai-codex",
  "model": "openai-codex/gpt-5.5",
  "thinking": "xhigh"
}
```

### Inherited model

```json
{
  "kind": "inherited",
  "role": "executor"
}
```

Planning resolves inherited roles into the referenced role's exact model list.
Inheritance cycles and missing role names fail planning.

### Bounded dynamic models

```json
{
  "kind": "bounded-dynamic",
  "models": [
    {
      "provider": "example",
      "model": "example/worker-a",
      "thinking": "medium"
    },
    {
      "provider": "example",
      "model": "example/worker-b",
      "thinking": "high"
    }
  ]
}
```

The list must be non-empty and finite. Arbitrary or unbounded selection returns
`LaunchClarificationRequired` with structured evidence.

### Call behavior

A fixed role declares its exact calls per rep:

```json
{
  "kind": "fixed",
  "callsPerRep": 1,
  "maxConcurrency": 1
}
```

A dynamic role declares upper bounds:

```json
{
  "kind": "bounded",
  "maxCallsPerRep": 4,
  "maxConcurrency": 2
}
```

All bounds must be positive integers. Unbounded call behavior requires
clarification.

## Extension launch surfaces

Every locked behavior input of kind `extension` must be covered by a
`launchSurfaces` entry. A surface path may name one file or a directory prefix.
`modelRoles` lists every declared role the surface can call; an empty list states
that the reviewed surface makes no model call.

```json
{
  "path": "extensions/advisor",
  "modelRoles": ["advisor"]
}
```

Unknown extension paths stop planning with the config identity and uncovered
path. Launch planning reports the evidence but never invokes a workflow,
research agent, or grilling process.

## Model-free compatibility checks

Planning checks the lock's `testedSubjectVersions` against the resolved subject
version and `requiredCapabilities` against runtime capability evidence. It also
checks every declared credential route by name. The plan and receipt contain
route names only; credential values never enter either artifact.

The receipt renders resolved models, inheritance or bounded-selection details,
billing routes, compact usage paths, call bounds, tested subject versions, and
required capabilities for operator review.
