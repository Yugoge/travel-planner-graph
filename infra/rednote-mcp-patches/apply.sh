#!/bin/bash
# Apply rednote-mcp patches for XHS proxy support
# Run after: npm install -g rednote-mcp@0.2.3
set -e
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="/usr/lib/node_modules/rednote-mcp/dist"

if [ ! -d "$TARGET" ]; then
  echo "Error: rednote-mcp not found at $TARGET"
  echo "Install first: npm install -g rednote-mcp@0.2.3"
  exit 1
fi

echo "Applying rednote-mcp patches..."
patch -p0 "$TARGET/auth/authManager.js" < "$PATCH_DIR/authManager.patch"
patch -p0 "$TARGET/tools/rednoteTools.js" < "$PATCH_DIR/rednoteTools.patch"
echo "Done. Patches applied to rednote-mcp."
