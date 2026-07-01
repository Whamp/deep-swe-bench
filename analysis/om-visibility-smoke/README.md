# OM visibility smoke

Cheap local smoke for the pi-observational-memory visibility question.

It does **not** call a paid model. `run-smoke.mjs` starts a local fake OpenAI-compatible provider, runs Pi in RPC mode, and records the final provider payloads through a `before_provider_request` extension.

## Run

```bash
node analysis/om-visibility-smoke/run-smoke.mjs
```

## What it tests

1. **Positive control**: put a sentinel in `--append-system-prompt` and prove the payload capture sees it.
2. **OM projection**:
   - turn 1 creates a large session;
   - `/seedom` appends a valid `om.observations.recorded` custom ledger entry containing the sentinel;
   - Pi compacts before the next executor turn;
   - turn 2's actual executor provider payload is captured;
   - the smoke asserts the payload contains the sentinel, `abc123abc123`, and the OM rendered-summary header.

## Interpretation

Passing result means:

- the capture layer sees the real outbound executor payload;
- `type:"custom"` OM ledger entries are **not** visible before compaction;
- after compaction, OM's compaction hook can project the folded ledger into executor-visible context.

That supports the current working model: benchmark `pi -p` runs only test semantic OM memory if compaction happens before a later useful executor turn. One-shot runs where compaction happens at/after `agent_end` do not exercise the main memory-projection path.
