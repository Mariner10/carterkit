import pytest
import carterkit


def _build(**formkw):
    ui = carterkit.Layout("F")
    ui.tab("A", icon="leaf", cols=4, rows=4)
    with ui.group("New", span=(2, 3), cols=2, rows=3,
                  form=carterkit.form(**formkw)) as g:
        g.textInput("name")
        g.button("save", label="Save", role="submit")
    return ui.layout


GOOD = dict(collection="plants",
            fields={"name": carterkit.form_rules(required=True, max_length=40)},
            submit={"method": "local", "op": "insert", "set": "{{form}}"})


def test_sugar_writes_form_and_validates_clean():
    lay = _build(**GOOD)
    grp = lay["tabs"][0]["children"][0]
    assert grp["form"]["fields"]["name"] == {"required": True, "maxLength": 40}
    assert grp["form"]["collection"] == "plants"
    assert carterkit.validate_layout(lay) == []


def test_after_submit_and_mode_keys():
    f = carterkit.form(mode="edit", collection="p", after_submit="keep")
    assert f == {"mode": "edit", "collection": "p", "afterSubmit": "keep"}


def test_bad_enums_raise():
    with pytest.raises(ValueError):
        carterkit.form(mode="x")
    with pytest.raises(ValueError):
        carterkit.form(after_submit="x")


def test_bad_validator_caught_by_main_lint():
    lay = _build(**dict(GOOD, fields={"name": {"pattern": "^a"}}))
    assert any(f["kind"] == "bad_form" and f["severity"] == "error"
               for f in carterkit.validate_layout(lay))
