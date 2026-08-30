"""The provider client: what it retries, and what it refuses to retry.

`response_format` is the parameter that varies most between OpenAI-compatible
endpoints, and a provider that rejects it fails in a way that looks exactly
like a broken key from the outside — which is how an empty advisory reading
went unexplained in production for a deploy. These tests pin the distinction.
"""

from __future__ import annotations

import pytest

from app.core import llm

SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}


class BadRequestError(Exception):
    """Shaped like the SDK's 400, matched by name rather than imported."""

    status_code = 400


class AuthenticationError(Exception):
    status_code = 401


def _stub(monkeypatch, responses):
    """Install a fake completion call that plays through *responses*.

    Each entry is either an exception to raise or a string to return. Records
    the kwargs of every attempt so the retry can be inspected.
    """
    calls = []
    queue = list(responses)

    def fake_create(kwargs):
        calls.append(dict(kwargs))
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(llm, "_create", fake_create)
    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "_langfuse_enabled", lambda: False)
    return calls


def call():
    return llm.complete_json(system="s", user="u", schema=SCHEMA, trace_name="t")


def test_the_happy_path_keeps_strict_json_mode(monkeypatch):
    calls = _stub(monkeypatch, ['{"ok": true}'])

    assert call() == {"ok": True}
    assert len(calls) == 1
    assert calls[0]["response_format"] == {"type": "json_object"}


def test_a_rejected_response_format_is_retried_without_it(monkeypatch):
    """The parameter is belt-and-braces: the prompt already demands JSON."""
    calls = _stub(monkeypatch, [BadRequestError("unsupported"), '{"ok": true}'])

    assert call() == {"ok": True}
    assert len(calls) == 2
    assert "response_format" in calls[0]
    assert "response_format" not in calls[1]
    # The retry must still be the same request in every other respect.
    assert calls[1]["messages"] == calls[0]["messages"]
    assert calls[1]["model"] == calls[0]["model"]


def test_a_bad_key_is_not_retried(monkeypatch):
    """Retrying an auth failure just doubles the wait before the same answer."""
    calls = _stub(monkeypatch, [AuthenticationError("invalid api key")])

    assert call() is None
    assert len(calls) == 1


def test_a_network_failure_is_not_retried(monkeypatch):
    calls = _stub(monkeypatch, [ConnectionError("dns")])

    assert call() is None
    assert len(calls) == 1


def test_a_retry_that_also_fails_gives_up_quietly(monkeypatch):
    calls = _stub(monkeypatch, [BadRequestError("a"), BadRequestError("b")])

    assert call() is None
    assert len(calls) == 2


def test_non_json_output_is_refused_rather_than_guessed_at(monkeypatch):
    _stub(monkeypatch, ["Here you go!\n```json\n{\"ok\": true}\n```"])

    assert call() is None


def test_no_key_configured_makes_no_call_at_all(monkeypatch):
    calls = _stub(monkeypatch, ['{"ok": true}'])
    monkeypatch.setattr(llm, "is_enabled", lambda: False)

    assert call() is None
    assert calls == []


@pytest.mark.parametrize(
    "exc",
    [BadRequestError("x"), type("UnprocessableEntityError", (Exception,), {})("x")],
)
def test_bad_request_is_recognised_by_status_or_class_name(monkeypatch, exc):
    """The client class is chosen at call time — it may be the LangFuse-wrapped
    one — so the SDK's exception types cannot simply be imported and caught."""
    calls = _stub(monkeypatch, [exc, '{"ok": true}'])

    assert call() == {"ok": True}
    assert len(calls) == 2
