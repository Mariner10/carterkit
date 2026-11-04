import asyncio

from carterkit.playground import build_playground, live_prompt


def _run(entries, send):
    it = iter(entries)

    def read(_p):
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    out: list[str] = []
    n = asyncio.run(live_prompt(send, read=read, write=out.append))
    return n, out


def test_round_trip_with_stub_transport():
    seen = []

    async def send(text):
        seen.append(text)
        return {"ok": True, "echo": text}

    n, out = _run(["hi", "", "  there  ", "quit", "ignored"], send)
    assert seen == ["hi", "there"]
    assert n == 2
    assert out == ["-> {'ok': True, 'echo': 'hi'}", "-> {'ok': True, 'echo': 'there'}"]


def test_send_error_is_reported_and_prompt_continues():
    async def send(text):
        if text == "bad":
            raise RuntimeError("boom")
        return text

    n, out = _run(["bad", "good"], send)
    assert n == 1
    assert out == ["error: boom", "-> 'good'"]


def test_build_playground_still_builds():
    assert build_playground() is not None
