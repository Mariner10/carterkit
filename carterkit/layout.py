"""A fluent layout builder — the ergonomic front door over LayoutBuffer.

    from carterkit import Layout, build, bind

    layout = (Layout("Dashboard", columns=4, rows=4)
              .connect("ws://192.168.1.50:8765", channel="home")
              .tab("Main", icon="gauge")
              .add(build.gauge(id="cpu", min=0, max=100,
                               sync=[bind.listen("cpu")]), default_span=[2, 2])
              .add(build.button(id="refresh", action=bind.action("refresh")))
              .layout)

Auto-placement, id de-duplication, and grid bookkeeping come from LayoutBuffer;
`.validate()` lints against the bundled catalog. Chainable: every mutator returns self.
"""
from __future__ import annotations

import json

from . import bind as _bind
from . import validate as _validate
from .buffer import LayoutBuffer


class Layout:
    def __init__(self, name: str = "Layout", *, columns: int = 4, rows: int = 6,
                 accent: str = "#667eea"):
        self._buf = LayoutBuffer.blank(name=name, columns=columns, rows=rows, accent=accent)
        self._tab = 0
        self._first_tab_used = False

    def connect(self, url: str, **identity) -> "Layout":
        """Attach a `connection` block (see bind.connection for the identity kwargs)."""
        self._buf.layout["connection"] = _bind.connection(url, **identity)
        return self

    def tab(self, title: str, *, icon: str = "square.grid.2x2",
            columns: int = 4, rows: int = 6) -> "Layout":
        """Start a tab and make it current. The first call configures the default tab;
        later calls append new tabs."""
        if not self._first_tab_used:
            t = self._buf.tabs[0]
            t["title"], t["icon"] = title, icon
            t["grid"] = {"columns": columns, "rows": rows}
            self._tab = 0
            self._first_tab_used = True
        else:
            self._tab = self._buf.add_tab(title, icon=icon, columns=columns, rows=rows)
        return self

    def add(self, control: dict, *, position=None, span=None, default_span=None) -> "Layout":
        """Add a control to the current tab (auto-placed unless `position` is given)."""
        self._buf.add_control(control, tab_index=self._tab, position=position,
                              default_span=default_span or span)
        return self

    def group(self, group: dict, *, position=None) -> "Layout":
        """Add a group container to the current tab."""
        self._buf.add_group(group, tab_index=self._tab, position=position)
        return self

    @property
    def layout(self) -> dict:
        """The composed layout dict (ready to push/save)."""
        return self._buf.layout

    @property
    def buffer(self) -> LayoutBuffer:
        """The underlying LayoutBuffer, for advanced ops (update/move/remove)."""
        return self._buf

    def validate(self) -> list:
        """Lint against the bundled control catalog."""
        import carterkit
        return carterkit.validate_layout(self.layout)

    def findings(self) -> str:
        """Human-readable lint report."""
        return _validate.format_findings(self.validate())

    def json(self, indent: int = 2) -> str:
        return json.dumps(self.layout, indent=indent)

    def __repr__(self) -> str:
        n = sum(len(t.get("children", [])) for t in self._buf.tabs)
        return (f"<Layout {self.layout.get('name')!r}: "
                f"{len(self._buf.tabs)} tab(s), {n} control(s)>")
