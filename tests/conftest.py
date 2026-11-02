"""Make the MeshSocket package importable when it is not pip-installed.

CI/dev installs it normally; in the CAR-TER workspace it lives under
MeshSocket/Python next to this repo's checkout. Fallback only."""
import importlib.util
import os
import sys

if importlib.util.find_spec("meshsocket") is None:
    for cand in (
        os.environ.get("MESHSOCKET_PATH", ""),
        "/nas/home/Atlas/projects/CAR-TER-workspace/MeshSocket/Python",
        os.path.join(os.path.dirname(__file__), "..", "..", "MeshSocket", "Python"),
    ):
        if cand and os.path.isdir(os.path.join(cand, "meshsocket")):
            sys.path.append(os.path.abspath(cand))
            break
