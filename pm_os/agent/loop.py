"""The agent loop: Claude calls tools until it has what it needs, then answers.

Plain manual loop (no framework) so every step is visible:

    1. Send the conversation + tool list to Claude.
    2. If Claude asks for our tools, run them, send the results back, repeat.
    3. Web search runs on Anthropic's servers; its results come back inline.
    4. When Claude stops asking for tools, return the answer plus an audit
       trail of every tool call and every web source.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import anthropic
from dotenv import load_dotenv

from agent import tools
from agent.prompts import SYSTEM_PROMPT

load_dotenv()

MODELS = {"best": "claude-opus-5-5", "cheap": "claude-sonnet-5-5"}
WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}
MAX_STEPS = 12                     # safety cap on tool round trips per question


@dataclass
class AgentResult:
    answer: str
    audit_trail: list = field(default_factory=list)    # our tool calls: name, input, output
    web_searches: list = field(default_factory=list)   # queries Claude ran
    sources: list = field(default_factory=list)        # {title, url} from search results / citations
    stop_reason: str | None = None


class PMAgent:
    """Holds one PM conversation; call .ask() repeatedly for follow-ups."""

    def __init__(self, model: str | None = None, effort: str = "high", web_search: bool = True):
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.")
        self.client = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY; never printed
        self.model = model or os.getenv("PM_OS_MODEL", MODELS["best"])
        self.effort = effort
        self.tools = tools.TOOL_SCHEMAS + ([WEB_SEARCH_TOOL] if web_search else [])
        self.messages: list = []

    def _call_claude(self):
        return self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=self.tools,
            messages=self.messages,
            output_config={"effort": self.effort},
            # If a safety classifier declines, retry on Anthropic's recommended fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )

    def ask(self, question: str, on_step=None) -> AgentResult:
        """Answer one question. `on_step(event_dict)` lets a UI show progress live."""
        self.messages.append({"role": "user", "content": question})
        result = AgentResult(answer="")

        for _ in range(MAX_STEPS):
            response = self._call_claude()
            result.stop_reason = response.stop_reason
            self.messages.append({"role": "assistant", "content": response.content})
            self._collect_web_activity(response, result, on_step)

            if response.stop_reason == "refusal":
                result.answer = "The model declined this request. Try rephrasing the question."
                return result
            if response.stop_reason == "pause_turn":
                continue                              # server-side search paused; resend to resume
            if response.stop_reason != "tool_use":
                result.answer = "".join(b.text for b in response.content if b.type == "text")
                return result

            # Run every tool Claude asked for and return all results in ONE user message.
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                output = tools.dispatch(block.name, block.input)
                entry = {"tool": block.name, "input": block.input, "output": output}
                result.audit_trail.append(entry)
                if on_step:
                    on_step({"type": "tool", **entry})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output, default=str),
                    "is_error": "error" in output,
                })
            self.messages.append({"role": "user", "content": tool_results})

        result.answer = "Stopped after the maximum number of tool steps without a final answer."
        return result

    @staticmethod
    def _collect_web_activity(response, result: AgentResult, on_step):
        """Record web search queries, result URLs and citations for the audit panel."""
        seen = {s["url"] for s in result.sources}
        for block in response.content:
            if block.type == "server_tool_use" and block.name == "web_search":
                query = (block.input or {}).get("query")
                result.web_searches.append(query)
                if on_step:
                    on_step({"type": "web_search", "query": query})
            elif block.type == "web_search_tool_result" and isinstance(block.content, list):
                for item in block.content:
                    url = getattr(item, "url", None)
                    if url and url not in seen:
                        seen.add(url)
                        result.sources.append({"title": getattr(item, "title", url), "url": url,
                                               "page_age": getattr(item, "page_age", None), "cited": False})
            elif block.type == "text" and getattr(block, "citations", None):
                for c in block.citations:
                    url = getattr(c, "url", None)
                    for s in result.sources:
                        if s["url"] == url:
                            s["cited"] = True
