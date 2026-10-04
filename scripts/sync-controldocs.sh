#!/usr/bin/env bash
# Re-vendor the ControlDocs from the CAR-TER app repo (the canonical source) into
# the package. The docs ARE the library — carterkit ships a pinned snapshot, and
# this script refreshes it. Adjust APP_REPO if your checkout lives elsewhere.
#
#   sync-controldocs.sh           copy the app's *.md docs over the vendored set
#   sync-controldocs.sh --check   change nothing; list drifted files, exit 1 on drift
#   APP_REF=<ref> sync-controldocs.sh --check   compare against a git ref of the
#                                 app repo (branch/tag) instead of its working tree
#
# Exit codes: 0 in sync / vendored, 1 drift (--check), 2 usage or source not found.
# tests/test_controldocs_freshness.py runs the same comparison under pytest.
set -euo pipefail
APP_REPO="${APP_REPO:-$HOME/Desktop/Programming/Swift/CAR-TER/CAR-TER/CAR-TER/ControlDocs}"
APP_REF="${APP_REF:-${CARTER_APP_CONTROLDOCS_REF:-}}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/carterkit/controldocs"

CHECK=0
case "${1:-}" in
  "") ;;
  --check) CHECK=1 ;;
  -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
  *) echo "usage: $0 [--check]" >&2; exit 2 ;;
esac

[ -d "$APP_REPO" ] || { echo "ControlDocs source not found: $APP_REPO" >&2; exit 2; }

if [ "$CHECK" = 1 ]; then
  shopt -s nullglob
  if [ -n "$APP_REF" ]; then
    # Read the docs straight out of git so the app's working tree (which may hold
    # someone's uncommitted edits) doesn't matter.
    TOP="$(git -C "$APP_REPO" rev-parse --show-toplevel 2>/dev/null)" \
      || { echo "APP_REF needs a git checkout: $APP_REPO" >&2; exit 2; }
    REL="$(cd "$APP_REPO" && git rev-parse --show-prefix)"
    REL="${REL%/}"
    git -C "$TOP" rev-parse --verify -q "$APP_REF^{commit}" >/dev/null \
      || { echo "unknown app ref: $APP_REF" >&2; exit 2; }
    app_names() { git -C "$TOP" ls-tree --name-only "$APP_REF:$REL" | grep '\.md$' || true; }
    app_has() { git -C "$TOP" cat-file -e "$APP_REF:$REL/$1" 2>/dev/null; }
    app_cat() { git -C "$TOP" show "$APP_REF:$REL/$1"; }
    SOURCE="$APP_REPO @ $APP_REF"
  else
    app_names() { for f in "$APP_REPO"/*.md; do basename "$f"; done; }
    app_has() { [ -f "$APP_REPO/$1" ]; }
    app_cat() { cat "$APP_REPO/$1"; }
    SOURCE="$APP_REPO"
  fi

  drift=0
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    if [ ! -f "$DEST/$name" ]; then
      echo "missing from carterkit: $name"; drift=$((drift + 1))
    elif ! app_cat "$name" | cmp -s - "$DEST/$name"; then
      echo "differs:                $name"; drift=$((drift + 1))
    fi
  done < <(app_names)
  for kit in "$DEST"/*.md; do
    name="$(basename "$kit")"
    if ! app_has "$name"; then
      echo "only in carterkit:      $name"; drift=$((drift + 1))
    fi
  done
  if [ "$drift" -gt 0 ]; then
    echo "carterkit/controldocs drifted from $SOURCE ($drift files); run $0 to re-vendor" >&2
    exit 1
  fi
  echo "carterkit/controldocs matches $SOURCE"
  exit 0
fi

[ -z "$APP_REF" ] || { echo "APP_REF only applies to --check" >&2; exit 2; }
rm -f "$DEST"/*.md
cp "$APP_REPO"/*.md "$DEST"/
echo "vendored $(ls "$DEST"/*.md | wc -l | tr -d ' ') docs into carterkit/controldocs/"
