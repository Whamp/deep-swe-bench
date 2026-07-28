# Pi Fabric output telemetry

Stock Pi plus `pi-fabric@0.28.4`, with metadata-only output telemetry added during `npm ci`.

The patch records counts and character lengths in each persisted `fabric_exec` result:

- raw nested-operation result characters;
- nested result characters delivered into the sandbox after Fabric's bound;
- selected final-value, log, raw-output, and returned-text characters;
- nested-operation and truncation counts.

It does not record additional content, alter Fabric's model-visible tool description, add prompt guidance, cap output, or change execution behavior. This is the same-version control for the compact-return comparison.

Install the pinned dependency and apply the checked-in patch with:

```sh
cd 'configs/pi-fabric-output-telemetry@1.0.0/extensions'
npm ci --legacy-peer-deps
```

`apply-output-telemetry.mjs` fails if the published package no longer contains each expected 0.28.4 source block.
