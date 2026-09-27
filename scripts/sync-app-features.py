#!/usr/bin/env python3
"""Vendor the app's feature set (what get-device-info reports as `features`) into
carterkit/app_features.json, the list `requires.features` is linted against.

Source, in order of preference:
  1. <app>/CAR-TERTests/Fixtures/device-features.json: the app's own golden of
     DeviceCapabilities.features, once carter-5sn.4 lands it. Copied as-is.
  2. Otherwise, derived from the Swift the feature list is built from:
     ControlDefinition.ControlType (authorable = every case except `unsupported`) and
     DeviceCapabilities' syncMethods / actionMethods / layoutFeatures.

Usage: APP_REPO=<app checkout root> scripts/sync-app-features.py [--label "master 72b75d34"]
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "carterkit" / "app_features.json"
APP = Path(os.environ.get("APP_REPO") or HERE.parents[1] / "CAR-TER")


def _label(argv):
    if "--label" in argv:
        return argv[argv.index("--label") + 1]
    try:
        sha = subprocess.run(["git", "-C", str(APP), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        return f"app {sha}"
    except (OSError, subprocess.CalledProcessError):
        return "app (unknown revision)"


def _from_fixture():
    p = APP / "CAR-TERTests" / "Fixtures" / "device-features.json"
    if not p.is_file():
        return None
    data = json.loads(p.read_text())
    feats = data["features"] if isinstance(data, dict) else data
    return sorted(feats), "CAR-TERTests/Fixtures/device-features.json"


def _swift_list(text, name):
    m = re.search(rf"static let {name}\s*=\s*\[([^\]]*)\]", text)
    if not m:
        raise SystemExit(f"DeviceCapabilities.{name} not found")
    return re.findall(r'"([^"]+)"', m.group(1))


def _from_swift():
    caps = (APP / "CAR-TER" / "Services" / "DeviceCapabilities.swift").read_text()
    model = (APP / "CAR-TER" / "Models" / "ControlDefinition.swift").read_text()
    m = re.search(r"enum ControlType\b[^{]*\{(.*?)static var authorable", model, re.S)
    if not m:
        raise SystemExit("ControlDefinition.ControlType / authorable not found")
    body = re.sub(r"//[^\n]*", "", m.group(1))
    types = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("case ") and "(" not in line and "=" not in line:
            types += [t.strip() for t in line[5:].split(",") if t.strip()]
    types = [t for t in types if t != "unsupported"]
    feats = [f"control.{t}" for t in types]
    feats += [f"sync.{m}" for m in _swift_list(caps, "syncMethods")]
    feats += [f"action.{m}" for m in _swift_list(caps, "actionMethods")]
    feats += _swift_list(caps, "layoutFeatures")
    return sorted(set(feats)), "derived from DeviceCapabilities.swift + ControlDefinition.swift"


def main(argv):
    got = _from_fixture() or _from_swift()
    feats, source = got
    OUT.write_text(json.dumps({"app": _label(argv), "source": source, "features": feats},
                              indent=1) + "\n")
    print(f"vendored {len(feats)} features ({source}) into {OUT.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main(sys.argv[1:])
