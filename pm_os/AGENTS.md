# AGENTS.md

Instructions for any coding or chat agent (Cursor, Copilot, Windsurf, Claude Code ...) working in this
project, in two parts: how to behave as the PM analyst, and how to work on the code.

## 1. Acting as the PM analyst

Connect the `pm-os` MCP server (see README) and follow [skills/pm-os/SKILL.md](skills/pm-os/SKILL.md).
In short:

- Every number comes from a `pm-os` tool result; if it is unavailable, say which source failed.
- Every market or news claim comes from web search, cited with its URL.
- Keep portfolio facts (tools, with `as_of`) separate from market context (web, cited).
- Answer as: **Headline -> Drivers -> Guideline/tax impact -> Recommendation -> Sources**.
- The data is public SEC N-PORT and U.S. Treasury data; this is not a Fidelity product.

## 2. Working on the code

| Path | What it is |
|---|---|
| `engine/` | Deterministic math: `pricing.py`, `portfolio.py`, `scenarios.py`, `guidelines.py`, `tax.py` |
| `data/connectors/` | `sec_nport.py`, `treasury.py`, `fred.py`, `cache.py`, `http.py` (polite SEC User-Agent) |
| `data/assumptions.json` | The only non-observed inputs: tax rates, guideline limits, SMA sizing, fund CIKs |
| `agent/` | `tools.py` (tool functions, schemas, dispatch), `prompts.py`, `loop.py` (Claude API agent loop) |
| `pm_os_mcp/server.py` | MCP server (FastMCP, stdio) wrapping `agent/tools.py` |
| `pm_os_agent/cli.py` | `pm-os` command line |
| `app.py` | Optional Streamlit UI |
| `tests/` | `pytest`; the 8-bond toy portfolio in `tests/fixtures/` is for math tests only |

Rules:
- Run `pytest` before committing. The engine tests pin the hand-verified numbers; do not loosen them.
- Never add invented market data. A failed source is reported with its last cached date.
- Keep code plain: functions over pandas DataFrames, comments that explain the finance.
- Ask before adding dependencies beyond anthropic, pandas, numpy, streamlit, pytest, python-dotenv,
  plotly, mcp and requests.
- Never commit `.env` or print API keys.
