# Confirmed-launch smoke contracts

A versioned config's leaf-local `smoke.json` defines the evidence that one
subject cell must produce before batch fan-out. It is a validation contract, not
a behavior input, so it does not change the config lock. Launch planning
validates the contract without model use and stores its assertions in the launch
plan. Execution evaluates that stored copy rather than rereading a mutable file.
Preflight records structured diagnostics for every failed requirement.

A corrected contract may be applied to saved artifacts without another subject
or model call when the config behavior and exact result evidence are unchanged.
A new rep is required when behavior changed or the saved cell lacks evidence
needed by the corrected contract.

Versioned contracts must use stable fields, parsed records, files, counters, or
extension-owned machine markers. They cannot use README wording, source prose,
line breaks, output lengths, character counts, or arbitrary text fragments.

## Structured JSON records

Use `requireJsonRecords` when the required evidence lives in a JSON object or a
JSONL stream:

```json
{
  "requireJsonRecords": [
    {
      "equals": {
        "model": "gpt-5.6-sol",
        "reasoning.effort": "low"
      },
      "format": "json",
      "globs": [
        "initial_context/provider_request_*.json"
      ],
      "minimum": 2
    },
    {
      "equals": {
        "thinkingLevel": "low",
        "type": "thinking_level_change"
      },
      "format": "jsonl",
      "globs": [
        "session/*.jsonl"
      ],
      "minimum": 1
    }
  ]
}
```

Each assertion has four fields:

- `globs`: one or more safe paths relative to the result cell;
- `format`: `json` for one object per file or `jsonl` for one object per line;
- `equals`: non-empty dotted fields and their required JSON values;
- `minimum`: the positive number of matching records required across all
  matching files.

A JSON object counts only when every dotted field matches. Missing files and
mismatched records do not count. Unreadable files, malformed JSON or JSONL
lines, arrays, and scalar values produce an artifact-specific diagnostic and
fail preflight. If the valid matching count is below `minimum`, preflight fails
before batch fan-out.

Use this assertion to prove request shape, thinking level, model selection, or
other structured runtime evidence. Do not substitute `requireFiles`; file
existence alone does not prove file contents.

## Other durable assertions

- `equalsResultValues`: exact structured `result.json` fields.
- `minResultValues`: positive counters or numeric result thresholds.
- `requireFiles`: required result-cell artifacts.
- `requireRepoFiles`: required model/config validation artifacts.
- `requireUsageRecords`: compact secondary-role usage records selected by
  dotted-field equality and minimum count.
- `requireExtensionMarkers` and `forbidExtensionMarkers`: one stable token
  deliberately emitted by a config-owned extension.

Generic preflight also requires a successful subject exit, no timeout, positive
executor usage, a native session file, and Pi RPC lifecycle evidence.
