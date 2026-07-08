#!/usr/bin/env bash
# Vendor codebase-memory-mcp into every codebase-memory config's bin/.
#
# The binary is intentionally gitignored (configs/**/bin/) and regenerated on
# demand, like the codegraph binary. Keep one primary copy in this repo and
# hardlink it into the sibling configs so the seven apparent copies consume only
# one binary's worth of disk space.
#
# Usage:
#   scripts/vendor_codebase_memory.sh
#   CODEBASE_MEMORY_MCP_BIN=/path/to/codebase-memory-mcp scripts/vendor_codebase_memory.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${CODEBASE_MEMORY_MCP_BIN:-$(command -v codebase-memory-mcp || true)}"

if [ -z "$SRC" ] || [ ! -x "$SRC" ]; then
  echo "error: codebase-memory-mcp not found or not executable" >&2
  echo "set CODEBASE_MEMORY_MCP_BIN=/path/to/codebase-memory-mcp or put it on PATH" >&2
  exit 1
fi
SRC="$(readlink -f "$SRC")"
case "$SRC" in
  "$REPO"/configs/*/bin/codebase-memory-mcp)
    echo "error: source points at an existing vendored copy: $SRC" >&2
    echo "use the original binary, e.g. /home/will/.local/bin/codebase-memory-mcp" >&2
    exit 1
    ;;
esac

PRIMARY="$REPO/configs/codebase-memory/bin/codebase-memory-mcp"
LINKS=(
  "$REPO/configs/codebase-memory-bash-hook/bin/codebase-memory-mcp"
  "$REPO/configs/codebase-memory-max/bin/codebase-memory-mcp"
  "$REPO/configs/codebase-memory-max-pi-codex-goal/bin/codebase-memory-mcp"
  "$REPO/configs/codebase-memory-om/bin/codebase-memory-mcp"
  "$REPO/configs/codebase-memory-om-bash-hook/bin/codebase-memory-mcp"
  "$REPO/configs/codebase-memory-om-reindex/bin/codebase-memory-mcp"
  "$REPO/configs/codebase-memory-reindex/bin/codebase-memory-mcp"
)

install_primary() {
  mkdir -p "$(dirname "$PRIMARY")"
  rm -f "$PRIMARY"
  cp "$SRC" "$PRIMARY"
  chmod +x "$PRIMARY"
}

hardlink_to_primary() {
  local link="$1"
  mkdir -p "$(dirname "$link")"
  rm -f "$link"
  if ! ln "$PRIMARY" "$link"; then
    echo "error: failed to hardlink $link -> $PRIMARY" >&2
    echo "hardlinks are required here to avoid local disk duplication" >&2
    exit 1
  fi
}

echo "[vendor] source: $SRC"
echo "[vendor] primary: $PRIMARY"
install_primary
for link in "${LINKS[@]}"; do
  echo "[vendor] hardlinking -> $link"
  hardlink_to_primary "$link"
done

echo "[vendor] apparent size of each hardlink:"
for path in "$PRIMARY" "${LINKS[@]}"; do
  du -sh "$path" 2>/dev/null | sed 's/^/  /'
done
echo "[vendor] combined disk usage accounting hardlinks once:"
du -shc "$(dirname "$PRIMARY")" "${LINKS[@]%/codebase-memory-mcp}" 2>/dev/null | tail -1 | sed 's/^/  /'
echo "[vendor] sanity: version"
"$PRIMARY" --version | sed 's/^/  /'
echo "[vendor] done."
