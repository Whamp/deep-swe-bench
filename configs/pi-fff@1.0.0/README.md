# pi-fff@1.0.0

Stock Pi plus `@ff-labs/pi-fff@0.10.3` in its default `tools-and-ui` mode.
The extension adds the `fffind` and `ffgrep` tools and its extension-owned tool
guidance. Interactive FFF-backed `@` completion is part of the selected mode but
does not affect RPC benchmark cells.

This release does not add config-authored prompt text, enable the environment-
gated multi-grep tool, or configure persistent frecency or query-history
databases. Each isolated benchmark cell therefore starts without search memory
from another cell. Agents may still use shell search through Pi's `bash` tool.

Install the pinned package and its Pi peer dependencies with:

```sh
cd 'configs/pi-fff@1.0.0/extensions'
npm ci
```

The `gpt-5.6-luna/high` leaf targets the current `pi@0.84.1` harness subject.
Comparisons may use the existing `baseline@1.0.0` Luna/high results produced by
`pi@0.83.0`; that subject-version difference should be reported as a comparison
caveat rather than treated as matched provenance.
