"""CAR-TER links, per the CAR-TER repo's contract/links.json (docs/LINKS.md).

Anything shown outside the app (QR codes, printed links) uses the https form so the iPhone
Camera and desktop taps work and Beta can be targeted; ``scheme=True`` gives the in-app form.
"""
from __future__ import annotations

import urllib.parse
from typing import Mapping, Optional

HOSTS = {False: "links.carterbeaudoin.net", True: "go-beta.carterbeaudoin.net"}
SCHEMES = {False: "carter", True: "carter-beta"}


def app_link(route: str, path: str = "", query: Optional[Mapping[str, object]] = None,
             beta: bool = False, scheme: bool = False, fragment: str = "") -> str:
    """``route`` + optional ``path`` segment + query (None/empty values dropped, order kept)."""
    rest = route + (f"/{urllib.parse.quote(path, safe='')}" if path else "")
    q = [(k, str(v)) for k, v in (query or {}).items() if v not in (None, "")]
    if q:
        rest += "?" + urllib.parse.urlencode(q, quote_via=urllib.parse.quote, safe="")
    if fragment:
        rest += "#" + fragment
    return f"{SCHEMES[beta]}://{rest}" if scheme else f"https://{HOSTS[beta]}/{rest}"
