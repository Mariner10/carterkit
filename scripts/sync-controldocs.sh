#!/usr/bin/env bash
# Re-vendor the ControlDocs from the CAR-TER app repo (the canonical source) into
# the package. The docs ARE the library — carterkit ships a pinned snapshot, and
# this script refreshes it. Adjust APP_REPO if your checkout lives elsewhere.
#
# The vendored feature list (carterkit/app_features.json) must move in lockstep:
# a new control doc without its `control.<type>` feature fails
# tests/test_validate.py::test_known_features_come_from_the_vendored_app_list
# (carter-0a69). So when the app checkout root (two levels above ControlDocs) is
# present, this also runs scripts/sync-app-features.py against it. Set
# SKIP_APP_FEATURES=1 to vendor the docs alone.
set -euo pipefail
APP_REPO="${APP_REPO:-$HOME/Desktop/Programming/Swift/CAR-TER/CAR-TER/CAR-TER/ControlDocs}"
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$(cd "$HERE/.." && pwd)/carterkit/controldocs"
[ -d "$APP_REPO" ] || { echo "ControlDocs source not found: $APP_REPO" >&2; exit 1; }
rm -f "$DEST"/*.md
cp "$APP_REPO"/*.md "$DEST"/
echo "vendored $(ls "$DEST"/*.md | wc -l | tr -d ' ') docs into carterkit/controldocs/"

[ "${SKIP_APP_FEATURES:-}" = "1" ] && exit 0
APP_ROOT="$(cd "$APP_REPO/../.." && pwd)"
if [ -f "$APP_ROOT/CAR-TER/Services/DeviceCapabilities.swift" ] || \
   [ -f "$APP_ROOT/CAR-TERTests/Fixtures/device-features.json" ]; then
  PY="$HERE/../.venv/bin/python"
  [ -x "$PY" ] || PY="python3"
  APP_REPO="$APP_ROOT" "$PY" "$HERE/sync-app-features.py" ${APP_FEATURES_LABEL:+--label "$APP_FEATURES_LABEL"}
else
  echo "warning: app checkout not found at $APP_ROOT; carterkit/app_features.json NOT refreshed." >&2
  echo "         run APP_REPO=<app root> scripts/sync-app-features.py before testing." >&2
fi
