#!/usr/bin/env bash
# Build the three codegraph+OM stacked configs from their codegraph-only bases
# + the observational-memory pieces (extension, worker-usage-trace, settings,
# orchestration line, smoke contract additions).
#
# Each new config = (its codegraph base) + (OM worker gpt-5.4-mini/low):
#   codegraph-skill-om   = skill+binary  + OM
#   codegraph-auto-om    = brief-inject  + OM   (counts, the v1 variant)
#   codegraph-impact-om  = fn-impact     + OM   (names, the v2 variant)
#
# bin/ (the vendored codegraph binary) is NOT copied here — scripts/vendor_codegraph.sh
# hardlinks it into every codegraph config. Run vendor after this.
#
# Usage: scripts/build_codegraph_om_configs.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OM_BASE="$REPO/configs/observational-memory-gpt54mini-low"

declare -A BASE=(
  [codegraph-skill-om]="$REPO/configs/codegraph-skill"
  [codegraph-auto-om]="$REPO/configs/codegraph-auto"
  [codegraph-impact-om]="$REPO/configs/codegraph-impact"
)

# The codegraph extension each OM config loads (empty for skill — skill has none).
declare -A CG_EXT=(
  [codegraph-skill-om]=""
  [codegraph-auto-om]="/arm/extensions/codegraph-auto/index.ts"
  [codegraph-impact-om]="/arm/extensions/codegraph-impact/index.ts"
)

OM_LINE="Observational memory is enabled for this run (observer = gpt-5.4-mini, thinking low). Work normally as a competent engineer; do not change your behavior just because memory is present."

for NEW in "${!BASE[@]}"; do
  SRC="${BASE[$NEW]}"
  DEST="$REPO/configs/$NEW"
  echo "[build] $NEW  <-  $(basename "$SRC")  +  OM"
  rm -rf "$DEST"
  cp -r "$SRC" "$DEST"
  rm -rf "$DEST/bin"   # vendored separately by vendor_codegraph.sh
  rm -f "$DEST/smoke.json"   # base's smoke.json has the wrong config name; generated fresh below

  # OM extension source + worker-usage-trace.
  cp -r "$OM_BASE/extensions/pi-observational-memory" "$DEST/extensions/"
  cp "$OM_BASE/extensions/om-worker-usage-trace.ts" "$DEST/extensions/"

  # OM worker settings into the leaf.
  mkdir -p "$DEST/gpt-5.5/low"
  cp "$OM_BASE/gpt-5.5/low/settings.json" "$DEST/gpt-5.5/low/settings.json"

  # pi-flags: local-vllm preserve, OM usage trace, OM extension, then codegraph ext.
  # printf, not echo: bash `echo "-e"` swallows -e as a flag and prints nothing.
  flags=("-e" "/arm/extensions/local-vllm-preserve-thinking.ts"
         "-e" "/arm/extensions/om-worker-usage-trace.ts"
         "-e" "/arm/extensions/pi-observational-memory/src/index.ts")
  if [ -n "${CG_EXT[$NEW]}" ]; then
    flags+=("-e" "${CG_EXT[$NEW]}")
  fi
  printf '%s\n' "${flags[@]}" > "$DEST/pi-flags"

  # orchestration: append the OM line to whatever the base said.
  printf '\n\n%s\n' "$OM_LINE" >> "$DEST/orchestration.md"
done

echo "[build] done. Run scripts/vendor_codegraph.sh to populate bin/."
