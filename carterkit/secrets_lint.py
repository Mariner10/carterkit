"""Lint for `secrets[]` and `{{secret:name}}` placeholders (F15, carter-7gve).

Mirrors the app's destination policy (`SecretPolicy` in LayoutSecretStore.swift):

* by default a secret may only be sent to the hosts of the layout's declared
  sources (each http `baseURL` host and mqtt broker host);
* `secrets[].hosts` replaces that set for one secret;
* `secrets[].mesh: true` also allows it in a MeshSocket action payload.

The app refuses a request that breaks the rule (the pipe shows
``secret x not allowed for host h`` / ``... for the mesh``), so every finding here
is a request that would silently not go out. See layout-config.md#Secrets.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from .bind import SECRET_TOKEN, _SECRET_NAME, secret_names

SECRET_KINDS = ("token", "password", "apiKey")
_ACTIONISH = ("action", "longPressAction", "datumAction", "snapshotAction", "nodeAction")
_CRED_WORDS = ("authorization", "token", "key", "secret", "cookie", "password")
_MARK = "\x00secret\x00"


def _f(severity: str, kind: str, where: str, detail: str) -> dict:
    return {"severity": severity, "kind": kind, "where": where, "detail": detail}


def is_placeholder_only(value) -> bool:
    """True when a credential-bearing string carries a `{{secret:…}}` rather than a
    literal (so the `embedded_secret` lint leaves it alone)."""
    return isinstance(value, str) and SECRET_TOKEN.search(value) is not None


def _host(url) -> str | None:
    if not isinstance(url, str) or "://" not in url:
        return None
    try:
        return (urlsplit(SECRET_TOKEN.sub("x", url)).hostname or "").lower() or None
    except ValueError:
        return None


def _secret_in_authority(url: str) -> bool:
    """A placeholder in the scheme, host or port: the app refuses to place it."""
    if not SECRET_TOKEN.search(url):
        return False
    marked = SECRET_TOKEN.sub(_MARK, url)
    if "://" not in marked:
        return marked.split("/", 1)[0].count(_MARK) > 0 and not marked.startswith("/")
    scheme, rest = marked.split("://", 1)
    authority = rest.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    return _MARK in scheme or _MARK in authority


def _declarations(layout: dict, findings: list) -> dict:
    """{name: declaration} for well-formed entries; shape errors become findings.
    The app decodes `secrets` strictly (Codable), so a wrong type fails the layout."""
    raw = layout.get("secrets")
    decls: dict = {}
    if raw is None:
        return decls
    if not isinstance(raw, list):
        findings.append(_f("error", "bad_secrets", "root",
                           "'secrets' must be an array of {name, label?, kind?, hosts?, mesh?}"))
        return decls
    for i, d in enumerate(raw):
        where = f"secrets[{i}]"
        if not isinstance(d, dict):
            findings.append(_f("error", "bad_secrets", where, "a secret declaration must be an object"))
            continue
        name = d.get("name")
        if not isinstance(name, str) or not name:
            findings.append(_f("error", "bad_secrets", where, "a secret declaration needs a string 'name'"))
            continue
        if not _SECRET_NAME.match(name):
            findings.append(_f("warn", "bad_secrets", where,
                               f"secret name {name!r} should be letters, digits, '_', '-' or '.'"))
        if name in decls:
            findings.append(_f("warn", "bad_secrets", where,
                               f"secret '{name}' is declared twice; declare each name once"))
            continue
        for key in ("label", "kind"):
            if key in d and not isinstance(d[key], str):
                findings.append(_f("error", "bad_secrets", f"{where}.{key}", f"'{key}' must be a string"))
        if isinstance(d.get("kind"), str) and d["kind"] not in SECRET_KINDS:
            findings.append(_f("info", "bad_secrets", f"{where}.kind",
                               f"kind {d['kind']!r} is not one of {list(SECRET_KINDS)}; "
                               f"the app loads it but has no special prompt for it"))
        hosts = d.get("hosts")
        if hosts is not None and (not isinstance(hosts, list)
                                  or not all(isinstance(h, str) and h for h in hosts)):
            findings.append(_f("error", "bad_secrets", f"{where}.hosts",
                               "'hosts' must be an array of host names, e.g. [\"api.example.com\"]"))
            hosts = None
        elif isinstance(hosts, list):
            for h in hosts:
                if "://" in h or "/" in h:
                    findings.append(_f("warn", "bad_secrets", f"{where}.hosts",
                                       f"{h!r} is not a bare host; write just the host name "
                                       f"(the app compares hosts, not URLs)"))
        mesh = d.get("mesh")
        if mesh is not None and not isinstance(mesh, bool):
            findings.append(_f("error", "bad_secrets", f"{where}.mesh", "'mesh' must be true or false"))
        decls[name] = {"hosts": ({h.lower() for h in hosts} if isinstance(hosts, list) else None),
                       "mesh": mesh is True}
    return decls


def _source_hosts(layout: dict) -> dict:
    """{source name: (kind, host or None)} for http/mqtt sources."""
    out: dict = {}
    srcs = layout.get("sources")
    if not isinstance(srcs, dict):
        return out
    for name, sd in srcs.items():
        if not isinstance(sd, dict):
            continue
        kind = sd.get("type")
        if kind == "http":
            out[name] = (kind, _host(sd.get("baseURL")))
        elif kind == "mqtt":
            out[name] = (kind, _host(sd.get("url")))
    return out


def _sole(sources: dict, kind: str) -> str | None:
    names = [n for n, (k, _) in sources.items() if k == kind]
    return names[0] if len(names) == 1 else None


def _binding_destination(b: dict, sources: dict, is_action: bool):
    """Where a sync/action's secrets go: ("host", h), ("mesh", None),
    ("unknown", None) when the host can't be worked out statically, or
    ("never", why) when the app does not fill secrets in there at all."""
    method = b.get("method") or "meshsocket"
    if method == "http":
        h = _host(b.get("url"))
        if h:
            return ("host", h)
        name = b.get("source") or _sole(sources, "http")
        entry = sources.get(name) if isinstance(name, str) else None
        return ("host", entry[1]) if entry and entry[1] else ("unknown", None)
    if method == "mqtt":
        name = b.get("source") or _sole(sources, "mqtt")
        entry = sources.get(name) if isinstance(name, str) else None
        return ("host", entry[1]) if entry and entry[1] else ("unknown", None)
    if method == "meshsocket":
        return ("mesh", None) if is_action else ("never", "a MeshSocket sync")
    return ("never", f"a '{method}' binding")


def _uses(layout: dict, sources: dict):
    """Yield (name, where, destination, node) for every placeholder the lint can
    place; placeholders anywhere else come back with destination ("never", why)."""
    srcs = layout.get("sources")
    covered: set = set()
    if isinstance(srcs, dict):
        for sname, sd in srcs.items():
            if not isinstance(sd, dict):
                continue
            covered.add(id(sd))
            kind, host = sources.get(sname, (None, None))
            dest = ("host", host) if host else (("never", f"a '{sd.get('type')}' source")
                                                if kind is None else ("unknown", None))
            for n in secret_names(sd):
                yield n, f"sources.{sname}", dest, sd
    conn = layout.get("connection")
    if isinstance(conn, dict):
        covered.add(id(conn))
        for n in secret_names(conn):
            yield n, "connection", ("never", "the connection block"), conn
    stack = [(layout, "root", None)]
    while stack:
        node, path, parent_key = stack.pop()
        if id(node) in covered:
            continue
        if isinstance(node, dict):
            binding = None
            if parent_key in _ACTIONISH:
                binding = True
            elif parent_key == "sync":
                binding = False
            if binding is not None and isinstance(node.get("method", "meshsocket"), str):
                dest = _binding_destination(node, sources, binding)
                for n in secret_names(node):
                    yield n, path, dest, node
                continue
            for k, v in node.items():
                stack.append((v, f"{path}.{k}", k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                stack.append((v, f"{path}[{i}]", parent_key))
        elif isinstance(node, str):
            for n in secret_names(node):
                yield n, path, ("never", "this field"), node


def _literal_action_headers(layout: dict, findings: list) -> None:
    """A literal credential in an action/sync `headers` (sources are checked by the
    `embedded_secret` pass in validate.py)."""
    stack = [(layout, "root", None)]
    while stack:
        node, path, parent_key = stack.pop()
        if isinstance(node, dict):
            if parent_key in _ACTIONISH or parent_key == "sync":
                headers = node.get("headers")
                if isinstance(headers, dict):
                    for hk, hv in headers.items():
                        if (any(w in str(hk).lower() for w in _CRED_WORDS)
                                and isinstance(hv, str) and hv and not is_placeholder_only(hv)):
                            findings.append(_f(
                                "warn", "embedded_secret", f"{path}.headers.{hk}",
                                "a credential is embedded in the layout — anyone who receives "
                                "this JSON (share, export, MCP readback) receives it; write "
                                "{{secret:name}} and declare it in 'secrets'"))
            for k, v in node.items():
                if not (path == "root" and k in ("sources", "connection")):
                    stack.append((v, f"{path}.{k}", k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                stack.append((v, f"{path}[{i}]", parent_key))


def lint_secrets(layout: dict, findings: list) -> None:
    """Append `bad_secrets`, `secret_host`, `secret_mesh`, `secret_in_url`,
    `secret_not_filled`, `secret_undeclared` and `secret_unused` findings."""
    decls = _declarations(layout, findings)
    sources = _source_hosts(layout)
    default_hosts = {h for _, h in sources.values() if h}
    used: set = set()
    undeclared_reported: set = set()
    for name, where, (kind, detail), node in _uses(layout, sources):
        used.add(name)
        if decls and name not in decls and name not in undeclared_reported:
            undeclared_reported.add(name)
            findings.append(_f("info", "secret_undeclared", where,
                               f"'{{{{secret:{name}}}}}' has no entry in 'secrets'; it still "
                               f"resolves by name under the default rule (source hosts only)"))
        decl = decls.get(name, {"hosts": None, "mesh": False})
        if kind == "never":
            findings.append(_f("warn", "secret_not_filled", where,
                               f"secret '{name}' is not filled in inside {detail}; the phone "
                               f"sends or shows the placeholder text"))
        elif kind == "mesh" and not decl["mesh"]:
            findings.append(_f("warn", "secret_mesh", where,
                               f"secret '{name}' not allowed for the mesh — the action is not "
                               f"sent; set \"mesh\": true on its declaration (every peer in "
                               f"the room can read the payload)"))
        elif kind == "host":
            allowed = decl["hosts"] if decl["hosts"] is not None else default_hosts
            if detail not in allowed:
                fix = ("add it to this secret's 'hosts'" if decl["hosts"] is not None
                       else "list it in the secret's 'hosts' or declare a source on that host")
                findings.append(_f("warn", "secret_host", where,
                                   f"secret '{name}' not allowed for host {detail} — the request "
                                   f"is not sent; {fix}"))
        if isinstance(node, dict):
            for key in ("url", "baseURL", "path"):
                v = node.get(key)
                if isinstance(v, str) and name in secret_names(v) and _secret_in_authority(v):
                    findings.append(_f("warn", "secret_in_url", f"{where}.{key}",
                                       "secret cannot be placed in the url host or port; put it "
                                       "in the path, query or a header"))
    for name in decls:
        if name not in used:
            findings.append(_f("info", "secret_unused", "secrets",
                               f"secret '{name}' is declared but no {{{{secret:{name}}}}} uses it"))
    _literal_action_headers(layout, findings)
