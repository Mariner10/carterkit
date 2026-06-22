"""Typed control constructors, generated at runtime from the bundled ControlDocs.

Because the catalog *is* the docs, every placeable control type is available as a
builder whose validation and `help()` come straight from its documentation:

    from carterkit import build
    build.gauge(id="cpu", min=0, max=100, sync=[bind.listen("cpu")])
    build.color_picker(id="tint")             # snake_case maps to the catalog type
    help(build.gauge)                          # prints the gauge documentation

Unknown control types and bad enum values raise; unknown props are allowed
(forward-compatible — the device ignores props it doesn't understand).
"""
from __future__ import annotations

from functools import lru_cache

from . import catalog


@lru_cache(maxsize=1)
def _catalog() -> dict:
    from . import controldocs_dir
    return catalog.build_catalog(controldocs_dir())


def _resolve_type(name: str) -> str | None:
    """Map an attribute name to a catalog control type: exact, or snake_case→camelCase."""
    cat = _catalog()
    if name in cat:
        return name
    head, *rest = name.split("_")
    camel = head + "".join(p.title() for p in rest)
    return camel if camel in cat else None


def control(type: str, *, id: str, position=None, span=None, **props) -> dict:
    """Build and validate one control dict. `id` is required; `position`/`span` are
    optional. Raises on an unknown control type or an out-of-range enum value."""
    cat = _catalog()
    if type not in cat:
        raise ValueError(f"unknown control type {type!r}. Known: {', '.join(sorted(cat))}")
    spec = cat[type]
    enums = {f["name"]: f["values"] for f in spec.get("fields", [])
             if f.get("type") == "enum" and f.get("values")}
    for key, val in props.items():
        if key in enums and val not in enums[key]:
            raise ValueError(
                f"{type}.{key}={val!r} is not a valid option; choose one of {enums[key]}")
    out: dict = {"type": type, "id": id}
    if position is not None:
        out["position"] = list(position)
    if span is not None:
        out["span"] = list(span)
    out.update(props)
    return out


class _Controls:
    """Attribute access returns a builder bound to a catalog control type."""

    def __getattr__(self, name: str):
        ctype = _resolve_type(name)
        if ctype is None:
            raise AttributeError(
                f"no control type {name!r}. Available: {', '.join(self.__dir__())}")

        def make(*, id: str, position=None, span=None, **props) -> dict:
            return control(ctype, id=id, position=position, span=span, **props)

        doc = catalog.resolve_doc(_catalog_dir(), ctype)
        make.__name__ = ctype
        make.__qualname__ = f"controls.{ctype}"
        make.__doc__ = (doc or {}).get("body") or f"Build a {ctype} control."
        return make

    def __dir__(self):
        return sorted(_catalog())

    def types(self) -> list[str]:
        """All placeable control types available as builders."""
        return sorted(_catalog())


def _catalog_dir():
    from . import controldocs_dir
    return controldocs_dir()


build = _Controls()
