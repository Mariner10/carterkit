#!/usr/bin/env bash
# Re-vendor the ControlDocs from the CAR-TER app repo (the canonical source) into
# the package. The docs ARE the library — carterkit ships a pinned snapshot, and
# this script refreshes it. Adjust APP_REPO if your checkout lives elsewhere.
set -euo pipefail
APP_REPO="${APP_REPO:-$HOME/Desktop/Programming/Swift/CAR-TER/CAR-TER/CAR-TER/ControlDocs}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/carterkit/controldocs"
[ -d "$APP_REPO" ] || { echo "ControlDocs source not found: $APP_REPO" >&2; exit 1; }
rm -f "$DEST"/*.md
cp "$APP_REPO"/*.md "$DEST"/
echo "vendored $(ls "$DEST"/*.md | wc -l | tr -d ' ') docs into carterkit/controldocs/"
