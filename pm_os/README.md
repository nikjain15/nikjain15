# PM-OS: a fixed income SMA analyst on real public data

Ask a bond portfolio question in plain English ("what happens if rates rise 100bp?") and get a
PM-style answer built from **computed numbers** (a deterministic Python engine), **real data** (SEC
N-PORT holdings of a Fidelity municipal bond fund and the U.S. Treasury yield curve) and **cited
research** (web search).

> Independent analysis of **publicly filed** fund holdings. Not a Fidelity product, and no Fidelity
> branding.

PM-OS has three front ends, and all of them share one engine:

| Layer | What it is | Use it from |
|---|---|---|
| MCP server (`pm-os-mcp`) | Every analytics tool over stdio | Claude Code, Claude Desktop, Cursor, VS Code, Windsurf, any MCP client |
| Skill / agent instructions | `skills/pm-os/SKILL.md`, `AGENTS.md`, `CLAUDE.md` | Tells the IDE's agent to act like a PM analyst |
| CLI agent (`pm-os`) | Anthropic SDK agent loop + server-side web search | Any terminal |
| Streamlit UI (`app.py`) | Optional thin front end over the same agent | Browser |

## Setup (about 2 minutes)

```bash
git clone <this repo> && cd pm_os
pip install -e ".[ui,dev]"
cp .env.example .env          # add ANTHROPIC_API_KEY and SEC_USER_AGENT_EMAIL
pytest                        # 30 tests: the engine math must pass first
pm-os refresh                 # pulls N-PORT holdings + Treasury curve, prints a summary
pm-os ask "What happens if rates rise 100bp?"
```

`pm-os refresh` needs outbound access to `data.sec.gov`, `www.sec.gov` and `home.treasury.gov`
(and `api.stlouisfed.org` if you use FRED). Everything is cached in `data/cache/` with its source URL
and fetch time, so the demo runs offline afterwards.

## Connect it to your IDE (MCP)

After `pip install -e .`, the `pm-os-mcp` command is on your PATH. If your IDE does not see your
virtualenv, replace `"pm-os-mcp"` with its absolute path (`which pm-os-mcp`).

**Claude Code**: `.mcp.json` in this folder is picked up automatically. The skill is at
`.claude/skills/pm-os` (a link to `skills/pm-os`).
```json
{ "mcpServers": { "pm-os": { "command": "pm-os-mcp" } } }
```

**Cursor**: `.cursor/mcp.json` (same shape as above, already included). Cursor reads `AGENTS.md`.

**VS Code (Copilot agent mode)**: `.vscode/mcp.json` (included):
```json
{ "servers": { "pm-os": { "type": "stdio", "command": "pm-os-mcp" } } }
```

**Claude Desktop**: Settings → Developer → Edit Config (`claude_desktop_config.json`):
```json
{ "mcpServers": { "pm-os": { "command": "/absolute/path/to/pm-os-mcp" } } }
```

**Windsurf**: `~/.codeium/windsurf/mcp_config.json`, same `mcpServers` shape as Claude Desktop.

Every tool returns JSON with `as_of` and `source_url`, so the IDE agent can cite them.

## What's real, what's assumed

| Input | Source | Status |
|---|---|---|
| Holdings (CUSIP, issuer, par, market value, coupon, maturity) | SEC Form N-PORT, Fidelity Intermediate Municipal Income Fund (CIK 215829) or Limited Term Municipal Income Fund (CIK 35373). The series is matched by name inside the trust's filings, so no series ID is hardcoded. | **Real** |
| Bond price | market value ÷ par × 100 | **Real (derived)** |
| Yield | Solved by the engine from that price | **Real (derived)** |
| Treasury curve | home.treasury.gov daily par yield curve (FRED optional) | **Real** |
| Market/news context | Claude server-side web search, cited | **Real, cited** |
| Sector, state | Keyword match on issuer name | **Inferred**, and labelled as such |
| Call schedules, ratings | Not in N-PORT. Add them in `data/user/overrides.csv` (template included). | **Missing unless you supply them** |
| Tax rates, guideline limits, SMA lot sizes, cost basis | `data/assumptions.json`. Cost defaults to the bond's price in an N-PORT filing about a year earlier. | **Assumptions**, shown in every tool result |

What the data can't tell you:
- **Calls.** N-PORT has no call dates, so bonds are priced to maturity until you add calls. For premium
  5% munis that overstates yield and duration. The tools say this every time.
- **No MMD/BVAL.** Those AAA curves are licensed. The muni/Treasury ratio here is the portfolio's own
  yield ÷ Treasury yield by maturity bucket, not a AAA benchmark.
- **EMMA.** The MSRB's terms of use prohibit scraping and automated download, so PM-OS only links out
  to EMMA per CUSIP (`emma_url` in the holdings table).
- If a source fails, the tools return an error naming it plus the last cached date. They never fill in a
  number.

## Engine conventions

- Price = Σ CF / (1 + y/2)^(2t), semiannual; clean price = dirty − accrued.
- Callable bonds use yield to worst: the lower of price-to-call and price-to-maturity.
- Modified duration by a ±1bp bump-and-reprice, so call flips are captured. Macaulay = PV-weighted time.
- Dollar P&L = (new price − old price) × par / 100. Scenarios fully reprice every bond.
- De minimis threshold = 100 − 0.25 × full years to maturity. TEY = yield / (1 − 40.8%).
- Tax-loss screen amortizes premium (required for tax-exempt bonds) before measuring the loss.

The math is pinned by `tests/test_pricing.py` and `tests/test_scenarios.py` against a hypothetical
8-bond portfolio (`tests/fixtures/`). That portfolio is only a test fixture and never appears in the demo.

## Project layout

```
engine/            pricing.py, portfolio.py, scenarios.py, guidelines.py, tax.py
data/connectors/   sec_nport.py, treasury.py, fred.py, cache.py, http.py
data/assumptions.json   tax rates, guideline limits, SMA sizing, fund CIKs
data/cache/        fetched files + .meta.json (source URL, fetched_at, as_of)
agent/             tools.py (tools + schemas + dispatch), prompts.py, loop.py (agent loop)
pm_os_mcp/         server.py (MCP)
pm_os_agent/       cli.py (pm-os command)
skills/pm-os/      SKILL.md
app.py             optional Streamlit UI
tests/             pytest
```

## CLI

```bash
pm-os ask "Are we inside our duration band?"     # one question
pm-os chat                                       # follow-ups keep context
pm-os --cheap ask "..."                          # claude-sonnet-5-5 instead of claude-opus-5-5
pm-os tool run_scenario '{"type":"curve","params":{"preset":"bear_steepener"}}'   # one tool, no LLM
pm-os status                                     # cached data, as-of dates, sources
streamlit run app.py                             # optional UI
```

The agent uses `claude-opus-5-5` by default (`PM_OS_MODEL` in `.env` overrides it). It also uses Anthropic's
server-side web search (`web_search_20260209`) and server-side refusal fallback. The API key is read
from `.env` and is never printed.

## 5-minute demo script

Before the meeting, run `pm-os refresh` and `pytest`. Open the Streamlit UI, or Claude Code in this
folder.

1. **"Walk me through the portfolio: what do we own, what's it yield, and what's that worth to a
   top-bracket client?"** (`get_portfolio`)
   Shows that the data is real (CUSIPs, the N-PORT as-of date and the filing link) and shows SMA
   thinking (TEY at 40.8%). Also shows the honesty layer: inferred sectors and no call data.
2. **"What happens if rates rise 100bp? Are we still inside our duration band?"** (`run_scenario`,
   `check_guidelines`)
   Full repricing, P&L by bond, duration after the shock and band status. Open the audit trail
   to show that every number came from a tool call.
3. **"Replay the last 3 months of Treasury curve moves on this book."** (`run_scenario` with
   `treasury_replay`)
   Uses the real Treasury curve, not a made-up shock. Shows how key-rate moves feed into the P&L.
4. **"What's the muni/Treasury ratio doing, and why does it matter for us?"** (`muni_treasury_ratio`
   + web search)
   Ratios by maturity bucket from real data, plus cited market commentary. This is where you explain
   why MMD/BVAL aren't used (they're licensed).
5. **"Which bonds should we harvest for tax losses? Mind wash sales."** (`tax_loss_screen`)
   This is where SMA expertise shows: premium amortization of basis, savings at 23.8%, swap ideas that
   avoid "substantially identical" bonds, and the de minimis risk on discount bonds.
6. **"A client needs $150k next month. What do we sell?"** (`withdrawal_plan`)
   Coupons first, then losses, then short maturities. Shows odd-lot sizing and duration after the sale,
   which is the kind of trade-off a PM makes every week.

Bonus, in the "Teach me" tab: price a 4% 12-year bond callable in 8 at 3.45% and then at 4.45%. The
bond flips from priced-to-call (103.82, duration 6.83) to priced-to-maturity (95.85, duration 9.38) and
drops below de minimis (97.00). This is negative convexity in one picture.
