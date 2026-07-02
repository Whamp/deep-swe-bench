#!/usr/bin/env bash
# Remove large, regenerable local CodeGraph/codebase-memory artifacts.
#
# This script only targets paths that should be ignored by git:
#   - .codegraph/                         local CodeGraph index
#   - cache/codegraph-repos/              cached third-party repos + their indexes
#   - configs/codegraph*/bin/             vendored codegraph payloads
#   - configs/codebase-memory*/bin/       vendored codebase-memory-mcp payloads
#
# Dry-run by default. Pass --yes to delete.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

YES=0
case "${1:-}" in
  --yes|-y) YES=1 ;;
  "") ;;
  --help|-h)
    sed -n '1,18p' "$0"
    exit 0
    ;;
  *)
    echo "usage: scripts/clean_local_codegraph_artifacts.sh [--yes]" >&2
    exit 2
    ;;
esac

paths=()
[ -e .codegraph ] && paths+=(".codegraph")
[ -e cache/codegraph-repos ] && paths+=("cache/codegraph-repos")
while IFS= read -r -d '' path; do paths+=("$path"); done < <(
  find configs -mindepth 2 -maxdepth 2 -type d -name bin \
    \( -path 'configs/codegraph*/bin' -o -path 'configs/codebase-memory*/bin' \) \
    -print0 2>/dev/null | sort -z
)

if [ "${#paths[@]}" -eq 0 ]; then
  echo "[clean] no local CodeGraph/codebase-memory artifacts found"
  exit 0
fi

printf '[clean] candidates:\n'
for path in "${paths[@]}"; do
  if ! git check-ignore -q -- "$path"; then
    echo "error: refusing to remove non-ignored path: $path" >&2
    exit 1
  fi
  du -sh "$path" 2>/dev/null | sed 's/^/  /'
done

if [ "$YES" -ne 1 ]; then
  echo "[clean] dry run only; pass --yes to remove these ignored/regenerable paths"
  exit 0
fi

for path in "${paths[@]}"; do
  echo "[clean] removing $path"
  rm -rf -- "$path"
done

echo "[clean] done. Regenerate config binaries with:"
echo "  scripts/vendor_codegraph.sh"
echo "  scripts/vendor_codebase_memory.sh"
