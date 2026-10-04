#!/usr/bin/env bash
# Re-vendor the ControlDocs from the CAR-TER app repo (the canonical source) into
# the package. The docs ARE the library — carterkit ships a pinned snapshot, and
# this script refreshes it. Adjust APP_REPO if your checkout lives elsewhere.
#
#   sync-controldocs.sh           copy the app's *.md docs over the vendored set
#   sync-controldocs.sh --check   change nothing; list drifted files, exit 1 on drift
#
# tests/test_controldocs_freshness.py runs the same comparison under pytest.
set -euo pipefail
APP_REPO="${APP_REPO:-$HOME/Desktop/Programming/Swift/CAR-TER/CAR-TER/CAR-TER/ControlDocs}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/carterkit/controldocs"

CHECK=0
case "${1:-}" in
  "") ;;
  --check) CHECK=1 ;;
  -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
  *) echo "usage: $0 [--check]" >&2; exit 2 ;;
esac

[ -d "$APP_REPO" ] || { echo "ControlDocs source not found: $APP_REPO" >&2; exit 2; }

if [ "$CHECK" = 1 ]; then
  drift=0
  for src in "$APP_REPO"/*.md; do
    name="$(basename "$src")"
    if [ ! -f "$DEST/$name" ]; then
      echo "missing from carterkit: $name"; drift=$((drift + 1))
    elif ! cmp -s "$src" "$DEST/$name"; then
      echo "differs:                $name"; drift=$((drift + 1))
    fi
  done
  for kit in "$DEST"/*.md; do
    name="$(basename "$kit")"
    if [ ! -f "$APP_REPO/$name" ]; then
      echo "only in carterkit:      $name"; drift=$((drift + 1))
    fi
  done
  if [ "$drift" -gt 0 ]; then
    echo "carterkit/controldocs drifted from $APP_REPO ($drift files); run $0 to re-vendor" >&2
    exit 1
  fi
  echo "carterkit/controldocs matches $APP_REPO"
  exit 0
fi

rm -f "$DEST"/*.md
cp "$APP_REPO"/*.md "$DEST"/
echo "vendored $(ls "$DEST"/*.md | wc -l | tr -d ' ') docs into carterkit/controldocs/"
