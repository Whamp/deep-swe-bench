#!/usr/bin/env bash
# Vendor a pruned @optave/codegraph into each codegraph config's bin/.
#
# Why pruned: the full npm install is 254M and bundles native addons for every
# OS/arch. The deep-swe task set spans only 5 language families (TS/Go/Python/
# Rust/JS), so we keep just those tree-sitter grammars + the linux-x64-gnu
# native core (the container is Debian/amd64). Result ~124M.
#
# Why gitignored: matches the existing configs/**/node_modules convention
# (regenerate via this script, not committed). The populate step is the source
# of truth; the smoke gate fails loudly if bin/ is missing.
#
# Usage: scripts/vendor_codegraph.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NODE_DIR="$(dirname "$(dirname "$(readlink -f "$(command -v node)")")")"
SRC="$NODE_DIR/lib/node_modules/@optave/codegraph"

if [ ! -f "$SRC/dist/cli.js" ]; then
  echo "error: @optave/codegraph not found at $SRC" >&2
  echo "install it first:  npm install -g @optave/codegraph" >&2
  exit 1
fi

# Languages present across the 113 deep-swe tasks.
GRAMMARS=(typescript go python rust javascript)

# Where the real pruned copy lives; hardlinked into the other configs to avoid
# a second 124M on disk each.
PRIMARY="$REPO/configs/codegraph-auto/bin/codegraph"
LINKS=(
  "$REPO/configs/codegraph-skill/bin/codegraph"
  "$REPO/configs/codegraph-impact/bin/codegraph"
  "$REPO/configs/codegraph-skill-om/bin/codegraph"
  "$REPO/configs/codegraph-auto-om/bin/codegraph"
  "$REPO/configs/codegraph-impact-om/bin/codegraph"
)

prune_into() {
  local dest="$1"
  rm -rf "$dest"
  mkdir -p "$dest/dist" "$dest/grammars" \
    "$dest/node_modules/@optave/codegraph-linux-x64-gnu" \
    "$dest/node_modules/better-sqlite3/build/Release" \
    "$dest/node_modules/better-sqlite3/lib" \
    "$dest/node_modules/commander" \
    "$dest/node_modules/web-tree-sitter"

  cp -rT "$SRC/dist" "$dest/dist"
  cp "$SRC/package.json" "$dest/"
  cp -rT "$SRC/node_modules/@optave/codegraph-linux-x64-gnu" \
        "$dest/node_modules/@optave/codegraph-linux-x64-gnu"
  cp "$SRC/node_modules/better-sqlite3/build/Release/better_sqlite3.node" \
     "$dest/node_modules/better-sqlite3/build/Release/"
  cp -rT "$SRC/node_modules/better-sqlite3/lib" "$dest/node_modules/better-sqlite3/lib"
  cp "$SRC/node_modules/better-sqlite3/package.json" "$dest/node_modules/better-sqlite3/"
  cp -rT "$SRC/node_modules/commander" "$dest/node_modules/commander"
  cp -rT "$SRC/node_modules/web-tree-sitter" "$dest/node_modules/web-tree-sitter"
  # better-sqlite3 runtime deps (bindings, file-uri-to-path) live at top level
  for d in bindings file-uri-to-path; do
    if [ -d "$SRC/node_modules/$d" ]; then
      cp -rT "$SRC/node_modules/$d" "$dest/node_modules/$d"
    fi
  done
  for g in "${GRAMMARS[@]}"; do
    for f in "$SRC/grammars"/tree-sitter-${g}*.wasm; do
      [ -f "$f" ] && cp "$f" "$dest/grammars/"
    done
  done
}

echo "[vendor] pruning @optave/codegraph -> $PRIMARY"
prune_into "$PRIMARY"
for L in "${LINKS[@]}"; do
  echo "[vendor] hardlinking -> $L"
  mkdir -p "$(dirname "$L")"
  rm -rf "$L"
  cp -rl "$PRIMARY" "$L"
done

# Thin wrapper at bin/cg so callers don't repeat the node path. Lives at
# /arm/bin/cg inside the container (config dir mounted read-only at /arm).
# $1 = the config's bin/ dir (parent of the codegraph/ package).
write_wrapper() {
  local bin_dir="$1"
  cat > "$bin_dir/cg" <<'EOF'
#!/usr/bin/env bash
# cg — invoke the vendored codegraph CLI. Location-independent so it works
# both on the host (configs/<cfg>/bin/cg) and in-container (/arm/bin/cg).
_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec node "$_DIR/codegraph/dist/cli.js" "$@"
EOF
  chmod +x "$bin_dir/cg"
}
write_wrapper "$(dirname "$PRIMARY")"
for L in "${LINKS[@]}"; do write_wrapper "$(dirname "$L")"; done

echo "[vendor] sizes:"
du -sh "$PRIMARY" "${LINKS[@]}" 2>/dev/null | sed 's/^/  /'
echo "[vendor] sanity: version"
node "$PRIMARY/dist/cli.js" --version | sed 's/^/  /'
echo "[vendor] done."
