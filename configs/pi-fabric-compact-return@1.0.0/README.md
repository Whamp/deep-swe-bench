# Pi Fabric compact return

Stock Pi plus `pi-fabric@0.28.4`, with the same metadata-only telemetry as `pi-fabric-output-telemetry@1.0.0` and one extension-owned compact-return guideline.

The guideline preserves Fabric's intended loops, branches, retries, `Promise.all`, and sequential awaits. It asks the model to keep intermediate tool results inside the sandbox and return the smallest sufficient decision-ready value rather than raw source or command-output bundles.

This config does not prescribe search/read ordering, add a system preamble or orchestration prompt, cap output, or alter executor behavior beyond telemetry.

Install the pinned dependency and apply the checked-in patch with:

```sh
cd 'configs/pi-fabric-compact-return@1.0.0/extensions'
npm ci --legacy-peer-deps
```

`apply-compact-return.mjs` fails if the published package no longer contains each expected 0.28.4 source block.
