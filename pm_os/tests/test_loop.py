"""Agent loop mechanics with a fake Anthropic client (no API key, no network)."""
from types import SimpleNamespace as NS

import pytest

from agent import loop


class FakeMessages:
    """Turn 1: ask for price_bond. Turn 2: answer in text."""

    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return NS(stop_reason="tool_use", content=[
                NS(type="server_tool_use", name="web_search", input={"query": "muni market"}),
                NS(type="web_search_tool_result", content=[NS(url="https://example.com/a", title="A", page_age=None)]),
                NS(type="tool_use", id="t1", name="price_bond",
                   input={"coupon": 5, "yield_pct": 3.25, "maturity_years": 10}),
            ])
        return NS(stop_reason="end_turn", content=[NS(type="text", text="**Headline** 114.84", citations=None)])


def test_loop_runs_tools_and_records_audit(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    agent = loop.PMAgent()
    fake = FakeMessages()
    agent.client = NS(beta=NS(messages=fake))

    result = agent.ask("Price a 5% 10yr at 3.25%")

    assert result.answer.startswith("**Headline**")
    assert result.audit_trail[0]["tool"] == "price_bond"
    assert result.audit_trail[0]["output"]["price"] == pytest.approx(114.8391, abs=1e-3)
    assert result.web_searches == ["muni market"]
    assert result.sources[0]["url"] == "https://example.com/a"
    # The tool result went back to Claude in one user message.
    tool_msg = agent.messages[2]          # user, assistant(tool_use), user(tool_result)
    assert tool_msg["role"] == "user" and tool_msg["content"][0]["tool_use_id"] == "t1"
    assert fake.calls[0]["model"] == "claude-opus-5-5"
