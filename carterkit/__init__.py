"""carterkit — build and drive CAR-TER layouts from Python.

The control vocabulary *is* the bundled documentation: every control's schema,
fields, and examples are parsed at runtime from the ControlDocs markdown shipped
inside this package (``carterkit/controldocs/``) — the same docs the CAR-TER app
renders. So the docs never drift from the definitions; they are one and the same.

Quick map:
  - ``controls()`` / ``doc()`` / ``examples()`` — the docs-as-catalog surface
  - ``Layout`` / ``Fragment`` — the flat builder: controls as methods, live handles,
    context-manager tabs/groups (``declare.Screen`` is the declarative-class veneer)
  - ``LayoutBuffer`` — incrementally build a layout (auto-placement, dedupe)
  - ``validate_layout()`` — schema + grid lint against the bundled catalog
  - ``lint_dynamic_traffic()`` — check ``dynamic=`` groups against observed broadcasts
  - ``infer`` / ``codegen`` / ``theming`` / ``tune`` — generate layouts, servers, themes
  - ``Connection`` — ONE parser for every connection artifact (relay URL, pairing
    QR JSON, Connect+ Add-Device credential, layout connection block)
  - ``Hub`` / ``Layout.serve()`` — drive the layout you built: ``ctrl.push(value)``
    and ``@ctrl.on`` derived from the very sync/action bindings you authored
  - ``CarterClient`` / ``notify_http`` — the lower-level client: connect, push, alerts
"""
from importlib.resources import files
from pathlib import Path

from . import catalog, grid, codegen, infer, theming, tune, dynamic, contract
from .contract import extract_contract
from .buffer import LayoutBuffer, BufferError
from .validate import validate_layout as _validate_layout, format_findings
from .client import (CarterClient, notify_http, CarterNotifyError,
                     device_refresh_http, CarterDeviceRevoked)
from .relay import LocalRelay, port_in_use, lan_ip
from . import bind
from .controls import build, control
from .layout import Layout, Fragment, Control, Condition
from .connection import Connection
from .hub import Hub, HubError

try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version
    __version__ = _pkg_version("carterkit")          # single source of truth: pyproject
except (ImportError, PackageNotFoundError):            # source tree without an install
    __version__ = "0+unknown"

#: The layout/wire protocol version carterkit emits and understands. The JSON
#: contract — not this Python API — is the real compatibility boundary across the
#: app, the relay, and this library; unknown fields are tolerated on read.
PROTOCOL_VERSION = 1


def controldocs_dir() -> Path:
    """Filesystem path to the bundled ControlDocs markdown (the source of truth)."""
    return Path(files(__package__) / "controldocs")


def controls(types=None, include_theme: bool = False) -> dict:
    """Machine-readable schema for every placeable control, keyed by layout ``type``."""
    return catalog.build_catalog(controldocs_dir(), types=types, include_theme=include_theme)


def doc(control: str):
    """Full parsed doc (fields, themeFields, body, examples) for a control type or node_id."""
    return catalog.resolve_doc(controldocs_dir(), control)


def doc_markdown(control: str):
    """The control's human/AI documentation prose (the rendered markdown body)."""
    d = doc(control)
    return d["body"] if d else None


def examples(control: str):
    """Documented example snippets for a control: ``[{"name", "json"}, ...]``."""
    return catalog.get_examples(controldocs_dir(), control)


def validate_layout(layout: dict, catalog_: dict = None) -> list:
    """Lint a layout (schema + grid). Defaults to the bundled control catalog."""
    return _validate_layout(layout, catalog_ if catalog_ is not None else controls(include_theme=True))


def lint_dynamic_traffic(layout: dict, observed, catalog_: dict = None) -> list:
    """Lint a layout's `dynamic=` groups against observed broadcast payloads. Returns
    `validate`-style findings (see `dynamic.lint_dynamic_traffic`)."""
    return dynamic.lint_dynamic_traffic(layout, observed, catalog=catalog_)


__all__ = [
    "__version__", "PROTOCOL_VERSION",
    "CarterClient", "notify_http", "CarterNotifyError",
    "device_refresh_http", "CarterDeviceRevoked",
    "LayoutBuffer", "BufferError",
    "controls", "doc", "doc_markdown", "examples", "validate_layout",
    "lint_dynamic_traffic", "format_findings", "controldocs_dir",
    "build", "control", "bind", "Layout", "Fragment", "Control", "Condition",
    "Connection", "Hub", "HubError",
    "catalog", "grid", "codegen", "infer", "theming", "tune", "dynamic",
    "contract", "extract_contract",
]
