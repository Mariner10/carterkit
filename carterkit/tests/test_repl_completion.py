from carterkit.repl import _Handle, completions, make_completer


class _Hub:
    layout = {}


def _ns():
    return {"hub": _Hub(), "temp": _Handle(_Hub(), {"id": "temp", "type": "gauge"}), "tempo": 1}


def test_names_complete():
    assert completions(_ns(), "te") == ["temp", "tempo"] or set(completions(_ns(), "te")) >= {"temp", "tempo"}
    assert completions(_ns(), "hu") == ["hub"]


def test_methods_complete():
    out = completions(_ns(), "temp.pu")
    assert out == ["temp.push("]


def test_no_match_and_callable():
    assert completions(_ns(), "zzz") == []
    assert make_completer(_ns())("hu", 0) == "hub"
