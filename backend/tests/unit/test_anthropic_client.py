"""AnthropicAIClient adapter tests (T034) using a fake SDK client — no network.

Covers the three branches: parsed text block, API error -> None (fail-safe, C-4), and a
response with no text block -> None.
"""

from __future__ import annotations

from types import SimpleNamespace

import anthropic
import httpx

from aegis.ai.anthropic_client import AnthropicAIClient


class _FakeClient:
    def __init__(self, behavior) -> None:
        self.messages = SimpleNamespace(create=lambda **kw: behavior(kw))


def test_returns_parsed_json_from_text_block():
    def behavior(_kw):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text='{"decision": "emit"}')])

    client = AnthropicAIClient(_FakeClient(behavior))
    assert client.complete(model="claude-opus-4-8", system="s", user="u", schema={}) == {
        "decision": "emit"
    }


def test_api_error_maps_to_none():
    def behavior(_kw):
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))

    client = AnthropicAIClient(_FakeClient(behavior))
    assert client.complete(model="m", system="s", user="u", schema={}) is None


def test_no_text_block_returns_none():
    def behavior(_kw):
        return SimpleNamespace(content=[SimpleNamespace(type="thinking", thinking="...")])

    client = AnthropicAIClient(_FakeClient(behavior))
    assert client.complete(model="m", system="s", user="u", schema={}) is None
