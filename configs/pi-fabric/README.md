# pi-fabric

Clean stock Pi plus the pinned `pi-fabric` extension.

The config loads the published package root at
`/arm/extensions/node_modules/pi-fabric`, using its package manifest unchanged.
This installs the extension and all bundled skills with their upstream defaults: `fabric-exec` is
model-invocable, while the other Fabric workflows remain user-invoked. The
harness adds no unrelated skill or extension and no config-authored
prompt, model override, advisor, or environment setting.

The dependency is pinned in `extensions/package-lock.json`. On a fresh
checkout, install it with:

```sh
cd configs/pi-fabric/extensions
npm ci --legacy-peer-deps
```
