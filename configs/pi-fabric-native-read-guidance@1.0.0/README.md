# Pi Fabric native read guidance

Stock Pi plus `pi-fabric@0.28.4`, patched during `npm ci` so Fabric presents the native Pi read limits and continuation guidance on every model request.

The patch updates three extension-owned surfaces:

- the model-facing `fabric_exec` description and prompt guidelines;
- Fabric's `before_agent_start` guidance;
- `skills/fabric-exec/SKILL.md`.

It also changes Fabric's batching guideline to make discovery precede targeted reads. This config has no `system_preamble.md`, `orchestration.md`, output cap, or progressive-disclosure behavior.

Install the pinned dependency and apply the checked-in patch with:

```sh
cd 'configs/pi-fabric-native-read-guidance@1.0.0/extensions'
npm ci --legacy-peer-deps
```

`apply-native-read-guidance.mjs` fails if the published package no longer contains each expected 0.28.4 source block, preventing a silent partial patch.
