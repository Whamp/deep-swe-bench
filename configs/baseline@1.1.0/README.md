# baseline@1.1.0

Versioned stock-Pi baseline for the read-long-lines pilot on Pi `0.84.1`.

This release adds no config-authored extension, skill, system preamble,
`orchestration.md`, or appended system prompt. Its only model role is the main
Pi executor, and usage comes from native `session/*.jsonl` assistant messages.

The release adds these tested leaves while preserving the stock-Pi behavior of
`baseline@1.0.0`:

- `gpt-5.6-sol/low`
- `gpt-5.6-terra/low`
- `gpt-5.6-luna/low`
- `glm-5.2/max`

Codex leaves use OAuth subscription quota. GLM uses direct Z.ai subscription
quota. Leaf-local smoke contracts verify the exact model, provider request,
thinking level, Pi subject version, native session usage, and RPC lifecycle.

The release declares `baseline@1.0.0` as its previous release and uses
`versionImpact=rerun`. Historical `baseline@1.0.0` locks and results remain
unchanged.
