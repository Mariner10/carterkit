"""Builder support for group `expand` and the expand/collapse/toggleExpand actions."""
import carterkit
from carterkit import Layout, bind, expand_block



def test_group_expand_and_action_kinds_validate():
    with Layout("P") as ui:
        with ui.tab("T"):
            ui.button("more", label="More", action=bind.toggle_expand("pkg"))
            ui.button("less", label="Less", action=bind.collapse("pkg"))
            with ui.group("Pkg", id="pkg", cols=4, rows=2,
                          expand=expand_block(
                              trigger=["hold", "more"], style="sheet", title="Example",
                              grid={"columns": 4, "rows": 4},
                              children=[bind.place("name", [0, 0], [1, 2]),
                                        {"type": "label", "position": [1, 0], "span": [1, 4],
                                         "text": "Only when expanded"}])) as g:
                g.label("name", position=[0, 0])
            ui.button("open", label="Open", action=bind.expand("pkg"))
    assert ui.validate() == []
    text = repr(ui.layout)
    assert "'toggleExpand': 'pkg'" in text and "'collapse': 'pkg'" in text
    assert "'trigger': ['hold', 'more']" in text and "'ref': 'name'" in text


def test_expand_block_shape_and_checks():
    assert expand_block() == {}
    assert expand_block(trigger="none", style="fullScreen") == {"trigger": "none", "style": "fullScreen"}
    assert bind.place("a", (1, 2), (1, 3), size="large") == \
        {"ref": "a", "position": [1, 2], "span": [1, 3], "size": "large"}
    import pytest
    with pytest.raises(ValueError):
        expand_block(style="popup")


def test_bad_expand_action_flagged():
    with Layout("P") as ui:
        with ui.tab("T"):
            ui.button("b", label="B", action={"expand": 3})
    assert any(f["kind"] == "bad_action" for f in ui.validate())
