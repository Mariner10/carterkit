"""``carterkit tutorial``: the CAR-TER tutorials in the terminal, with checks you can run.

The tutorials are authored in the CAR-TER workspace (``dev-guide/tutorials/<id>.md``) and
vendored here like the ControlDocs (``carterkit/tutorials/``, pinned by its SOURCE file,
refreshed by ``carterkit/scripts/sync_controldocs.py --dest carterkit/tutorials``).
carterkit renders them; it never authors them.

    carterkit tutorial                          list
    carterkit tutorial steps first-hub          the steps: goal, code, what you should see
    carterkit tutorial --start first-hub dir    scaffold the starter kit as it stands before step 1
    carterkit tutorial --check first-hub --step 4 [--dir dir]
                                                run steps 1 to 4's checks against FakeHub

A code tutorial's finished state is a starter kit (``carterkit new --template <kit>``). The
kit's ``hub.py`` marks each step's code with ``# tutorial: <name>`` ... ``# end: <name>``; the
start state is the kit with those regions removed.
"""
from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import os
import re
from importlib.resources import files
from typing import Any, Optional

_FENCE = re.compile(r"^```([^\n]*)\n(.*?)^```[ \t]*$", re.S | re.M)
_SECTION = re.compile(r"^## (.+?)(?:\s*\{#([\w-]+)\})?\s*$", re.M)
_REF = re.compile(r"\[\[([^\]\n]+)\]\]")
_REGION = re.compile(r"^# tutorial: (\w+)\n(.*?)^# end: \1\n", re.S | re.M)


class TutorialError(Exception):
    """A user-facing problem (unknown id, wrong audience, bad folder)."""


def _root():
    return files("carterkit") / "tutorials"


def index() -> dict:
    """{id: frontmatter} for every vendored tutorial."""
    return json.loads((_root() / "index.json").read_text(encoding="utf-8"))


def get(tid: str) -> dict:
    idx = index()
    if tid not in idx:
        raise TutorialError(f"no tutorial {tid!r}; carterkit tutorial lists them: {', '.join(sorted(idx))}")
    return idx[tid]


def _body(tid: str) -> str:
    raw = (_root() / f"{tid}.md").read_text(encoding="utf-8")
    m = re.match(r"---\n.*?\n---\n", raw, re.S)
    return raw[m.end():] if m else raw


def blocks(text: str) -> list[tuple[str, set, Optional[str], str]]:
    """Fenced blocks as (lang, flags, name, code); a block's name is its last bare token."""
    out = []
    for m in _FENCE.finditer(text):
        toks = m.group(1).split()
        lang, flags, name = (toks[0] if toks else ""), set(), None
        for t in toks[1:]:
            if t in ("run", "layout"):
                flags.add(t)
            else:
                name = t[5:] if t.startswith("name=") else t
        out.append((lang, flags, name, m.group(2).rstrip("\n")))
    return out


def sections(tid: str) -> dict[str, str]:
    """{step id: the step's body text}."""
    body = _body(tid)
    masked = _FENCE.sub(lambda m: "\0" * len(m.group(0)), body)
    hits = list(_SECTION.finditer(masked))
    return {h.group(2): body[h.end(): hits[i + 1].start() if i + 1 < len(hits) else len(body)]
            for i, h in enumerate(hits) if h.group(2)}


# ---- rendering -------------------------------------------------------------

def _kit_ref(name: str) -> Optional[str]:
    import carterkit
    parts = name.split(".")[1:]
    obj = next((getattr(carterkit, n) for n in getattr(carterkit, "__all__", [])
                if n.lower() == parts[0]), None)
    for p in parts[1:]:
        obj = getattr(obj, p, None)
    if obj is None:
        return None
    try:
        sig = str(inspect.signature(obj))
    except (TypeError, ValueError):
        sig = ""
    doc = (inspect.getdoc(obj) or "").split("\n\n")[0].replace("\n", " ").strip()
    label = ".".join(parts) + sig
    return f"{label}: {doc}" if doc else label


def render_ref(target: str) -> str:
    """What a ``[[target]]`` reference shows in the terminal (id -> a doc hint)."""
    name, _, alias = target.partition("|")
    name = name.strip()
    if alias:
        return alias.strip()
    if name.startswith("control."):
        return f"{name[8:]} (carterkit doc {name[8:]})"
    if name.startswith("doc."):
        return f"the {name[4:]} doc"
    if name.startswith("kit."):
        return _kit_ref(name) or name
    if name.startswith("tutorial:"):
        return f"carterkit tutorial steps {name[9:]}"
    if re.fullmatch(r"[\w-]+\.[\w.-]+", name):
        ctl, field = name.split(".", 1)
        return f"{field} (carterkit doc {ctl} --field {field})"
    return name


def render_text(text: str) -> str:
    return _REF.sub(lambda m: render_ref(m.group(1)), text)


def _prose(section: str) -> str:
    return render_text(_FENCE.sub("", section)).strip()


def list_lines() -> list[str]:
    idx = index()
    width = max((len(i) for i in idx), default=0)
    return [f"{i.ljust(width)}  {m['kind']:<10} {m['time']:>2} min  {m['builds']}" for i, m in sorted(idx.items())]


def steps_text(tid: str) -> str:
    """The whole tutorial for a terminal: header, then each step."""
    meta = get(tid)
    secs = sections(tid)
    steps = meta["steps"]
    out = [f"{meta['title']}  ({meta['kind']}, {meta['time']} min, {meta['level']})", meta["builds"]]
    if meta.get("prerequisites"):
        out.append("First: " + ", ".join(f"carterkit tutorial steps {p}" for p in meta["prerequisites"]))
    if meta["audience"] == "app":
        out.append("This one is done in the app: open Learn > Guides in CAR-TER, or read it on the website.")
    elif meta.get("starterKit"):
        out.append(f"Start: carterkit tutorial --start {tid} my-{meta['starterKit']}   "
                   f"Finished: carterkit new my-{meta['starterKit']} --template {meta['starterKit']}")
    for n, st in enumerate(steps, 1):
        out += ["", f"Step {n} of {len(steps)}: {st['goal']}", "-" * 40]
        text = secs.get(st["id"], "")
        do = st.get("do", {})
        if "app" in do:
            out.append(re.sub(r"\*\*(.*?)\*\*", r"\1", do["app"]))
        prose = _prose(text)
        if prose:
            out.append(prose)
        for lang, flags, name, code in blocks(text):
            if lang in ("python", "json", "bash") and name != "none":
                out += ["", f"[{name or lang}]", code]
        if st.get("check"):
            out += ["", "You should see: " + render_text(st["check"])]
    if meta.get("next"):
        out += ["", "Next: " + ", ".join(f"carterkit tutorial steps {x}" for x in meta["next"])]
    return "\n".join(out)


# ---- --start ---------------------------------------------------------------

def strip_regions(source: str) -> str:
    """The kit's hub.py with every ``# tutorial:`` region removed."""
    out = _REGION.sub("", source)
    return re.sub(r"\n{4,}", "\n\n\n", out)


def start(tid: str, dest: str) -> list[str]:
    """Scaffold the starter kit as it stands before step 1 into ``dest``; returns files written."""
    from . import scaffold
    meta = get(tid)
    kit = meta.get("starterKit")
    if meta["audience"] == "app" or not kit:
        raise TutorialError(f"{tid} is done in the app; there is no project to start "
                            f"(carterkit tutorial steps {tid})")
    written = scaffold.scaffold(dest, template=kit)
    hub = os.path.join(dest, "hub.py")
    with open(hub, encoding="utf-8") as f:
        src = f.read()
    doc_end = src.index('"""', 3) + 3
    rest = strip_regions(src[doc_end:]).lstrip("\n")
    skeleton = f"{src[:doc_end]}\n# Build this file step by step: carterkit tutorial steps {tid}\n\n{rest}"
    with open(hub, "w", encoding="utf-8") as f:
        f.write(skeleton)
    lay = os.path.join(dest, "layout.json")
    with open(lay, encoding="utf-8") as f:
        layout = json.load(f)
    for tab in layout.get("tabs", []):
        tab["children"] = []
    with open(lay, "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2)
        f.write("\n")
    return written


# ---- --check ---------------------------------------------------------------

def _hit(frame, want: dict) -> bool:
    return isinstance(frame, dict) and all(k in frame and frame[k] == v for k, v in want.items())


async def run_expect(mod, fake, ex: dict) -> list[str]:
    """Apply one code step's ``expect`` to a loaded hub module and its FakeHub; returns failures.

    Keys: ``set`` {NAME: v} override a module global first; ``module`` {NAME: v} must equal;
    ``calls`` [{fn, args, returns | between}] call module functions ("@hub" in args is the hub;
    when present ``run`` is not started); ``when`` [frame] sent by the phone to a running
    ``run``; ``wait`` seconds to let it work; ``sent`` [frame] the hub must have broadcast
    (a frame matches on the keys given); ``at_least`` {msg_type: n}.
    """
    bad = []
    for k, v in (ex.get("set") or {}).items():
        setattr(mod, k, v)
    for k, v in (ex.get("module") or {}).items():
        if getattr(mod, k, None) != v:
            bad.append(f"{k} is {getattr(mod, k, None)!r}, expected {v!r}")
    calls = ex.get("calls") or []
    for c in calls:
        fn = getattr(mod, c["fn"], None)
        if fn is None:
            bad.append(f"hub.py defines no {c['fn']}")
            continue
        args = [fake.hub if a == "@hub" else a for a in c.get("args") or []]
        out = fn(*args)
        if inspect.isawaitable(out):
            out = await out
        shown = ", ".join(repr(a) for a in c.get("args") or [])
        if "returns" in c and out != c["returns"]:
            bad.append(f"{c['fn']}({shown}) returned {out!r}, expected {c['returns']!r}")
        if "between" in c and not (isinstance(out, (int, float)) and c["between"][0] <= out <= c["between"][1]):
            bad.append(f"{c['fn']}() returned {out!r}, outside {c['between'][0]} to {c['between'][1]}")
    if not calls and callable(getattr(mod, "run", None)) and (ex.get("when") or ex.get("sent") or ex.get("at_least")):
        task = asyncio.create_task(mod.run(fake.hub))
        await asyncio.sleep(0.02)
        for frame in ex.get("when") or []:
            await fake.dispatch(frame)
        await asyncio.sleep(float(ex.get("wait", 0.02)))
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    elif not calls and (ex.get("when") or ex.get("sent")):
        bad.append("hub.py defines no run(hub) yet")
    frames = fake.frames()
    for want in ex.get("sent") or []:
        if not any(_hit(f, want) for f in frames):
            bad.append("the hub never broadcast " + ", ".join(f"{k}={v!r}" for k, v in want.items()))
    for mt, n in (ex.get("at_least") or {}).items():
        got = len(fake.frames(mt))
        if got < n:
            bad.append(f"{got} {mt} frames broadcast, expected at least {n}")
    return bad


def check(tid: str, step: int, folder: str = ".") -> list[tuple[int, str, list[str]]]:
    """Run steps 1..``step``'s checks on the project in ``folder``.

    Returns [(step number, goal, failures)], one row per step (empty failures = pass)."""
    from . import validate_layout
    from .layout import Layout
    from .testing import FakeHub, load_hub_module
    meta = get(tid)
    if meta["audience"] == "app":
        raise TutorialError(f"{tid} is done in the app, so there is nothing to check here")
    steps = meta["steps"]
    if not 1 <= step <= len(steps):
        raise TutorialError(f"{tid} has {len(steps)} steps; --step takes 1 to {len(steps)}")
    hub_py, lay = os.path.join(folder, "hub.py"), os.path.join(folder, "layout.json")
    rows = []
    for n, st in enumerate(steps[:step], 1):
        bad: list[str] = []
        try:
            with open(lay, encoding="utf-8") as f:
                findings = validate_layout(json.load(f))
            bad += [f"layout.json: {x['where']}: {x['detail']}" for x in findings if x["severity"] == "error"]
        except (OSError, ValueError) as e:
            bad.append(f"layout.json: {e}")
        mod = None
        if os.path.isfile(hub_py):
            try:
                mod = load_hub_module(hub_py, f"tutorial_{tid.replace('-', '_')}")
            except Exception as e:  # noqa: BLE001 - the learner's file; say what broke
                bad.append(f"hub.py does not load: {type(e).__name__}: {e}")
        else:
            bad.append(f"no hub.py in {folder}")
        if mod is not None and not isinstance(getattr(mod, "ui", None), Layout):
            bad.append("hub.py defines no `ui` (a Layout)")
        elif mod is not None and st.get("expect"):
            fake = FakeHub(mod.ui)
            try:
                bad += asyncio.run(run_expect(mod, fake, st["expect"]))
            except Exception as e:  # noqa: BLE001
                bad.append(f"{type(e).__name__}: {e}")
        rows.append((n, st["goal"], bad))
    return rows


def check_text(tid: str, step: int, folder: str = ".") -> tuple[str, bool]:
    """``check`` formatted for the terminal; (text, all passed)."""
    meta = get(tid)
    rows = check(tid, step, folder)
    out, ok = [], True
    for n, goal, bad in rows:
        if not bad:
            out.append(f"ok    step {n}: {goal}")
            continue
        ok = False
        out.append(f"FAIL  step {n}: {goal}")
        out.append("      You should see: " + render_text(meta["steps"][n - 1].get("check", "")))
        out += [f"      - {b}" for b in bad]
    return "\n".join(out), ok
