"""MCP server: exposes the PM-OS tools to any MCP client over stdio.

Claude Code, Claude Desktop, Cursor, VS Code (Copilot agent mode), Windsurf
and other MCP clients start this process and call the tools below. Each tool
is a thin wrapper over agent/tools.py, so the IDE agent and the CLI agent
share exactly the same numbers.

Run directly:   pm-os-mcp      (or: python -m pm_os_mcp.server)
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from agent import tools

mcp = FastMCP(
    "pm-os",
    instructions=(
        "Fixed income SMA analytics on REAL public data (SEC N-PORT holdings of a Fidelity muni fund, U.S. "
        "Treasury curve). Every number you quote must come from these tools; cite as_of and source_url. "
        "Use web search for market context and cite URLs. Answer: Headline -> Drivers -> Guideline/tax impact "
        "-> Recommendation -> Sources. Independent analysis, not a Fidelity product."
    ),
)


@mcp.tool()
def get_portfolio(view: str = "sma", fund: str = "intermediate_muni") -> dict:
    """Holdings with price, MV, weight, yield to worst, duration and priced-to date, plus portfolio MV,
    duration, yield, TEY, sector/state mix and maturity buckets. view: 'sma' (30 real bonds, SMA-sized) or 'fund'."""
    return tools.dispatch("get_portfolio", {"view": view, "fund": fund})


@mcp.tool()
def price_bond(coupon: float, yield_pct: float, maturity_years: float, call_years: float | None = None,
               call_price: float = 100.0) -> dict:
    """Price one bond (coupon and yield in %). Returns price, priced-to date, durations, de minimis line and
    the cash-flow table with discount factors, PVs and running total."""
    return tools.dispatch("price_bond", {"coupon": coupon, "yield_pct": yield_pct, "maturity_years": maturity_years,
                                         "call_years": call_years, "call_price": call_price})


@mcp.tool()
def run_scenario(type: str, params: dict | None = None, view: str = "sma", fund: str = "intermediate_muni",
                 strategy: str | None = None) -> dict:
    """Full reprice under a scenario; P&L by bond and total, new duration, call flips, guideline breaches.
    type: parallel {bp} | curve {preset: bear_steepener|bull_flattener|bear_flattener|bull_steepener, or shifts:
    {years: bp}} | muni_ratio {bp} | credit {sector_bp: {sector: bp}} or {preset: revenue_stress} |
    custom {parallel_bp, bond_bp, curve_shifts} | treasury_replay {start_date, end_date}."""
    return tools.dispatch("run_scenario", {"type": type, "params": params or {}, "view": view, "fund": fund,
                                           "strategy": strategy})


@mcp.tool()
def check_guidelines(view: str = "sma", fund: str = "intermediate_muni", strategy: str | None = None) -> dict:
    """Duration band, sector caps, rating floor, de minimis flags vs. the assumed mandate limits."""
    return tools.dispatch("check_guidelines", {"view": view, "fund": fund, "strategy": strategy})


@mcp.tool()
def tax_loss_screen(threshold: float = 0.0, view: str = "sma", fund: str = "intermediate_muni") -> dict:
    """Unrealized gains/losses vs. cost (premium amortized), harvest candidates, tax savings, wash-sale notes."""
    return tools.dispatch("tax_loss_screen", {"threshold": threshold, "view": view, "fund": fund})


@mcp.tool()
def withdrawal_plan(amount: float, horizon_months: float = 1.0, view: str = "sma",
                    fund: str = "intermediate_muni", strategy: str | None = None) -> dict:
    """Sell order to raise `amount`: coupons/cash first, then losses, then shortest maturities; duration after."""
    return tools.dispatch("withdrawal_plan", {"amount": amount, "horizon_months": horizon_months, "view": view,
                                              "fund": fund, "strategy": strategy})


@mcp.tool()
def convexity_check(bond_id: str, bp: float = 100.0, view: str = "sma", fund: str = "intermediate_muni") -> dict:
    """One bond (CUSIP): gain if rates fall vs. loss if they rise, and the upside the call option costs."""
    return tools.dispatch("convexity_check", {"bond_id": bond_id, "bp": bp, "view": view, "fund": fund})


@mcp.tool()
def muni_treasury_ratio(view: str = "sma", fund: str = "intermediate_muni", on_date: str | None = None) -> dict:
    """Portfolio muni yield / Treasury yield by maturity bucket, and TEY pickup over Treasuries."""
    return tools.dispatch("muni_treasury_ratio", {"view": view, "fund": fund, "on_date": on_date})


@mcp.tool()
def fetch_holdings(fund: str = "intermediate_muni", refresh: bool = False) -> dict:
    """Summary + provenance of the N-PORT holdings; refresh=True re-downloads from SEC EDGAR."""
    return tools.dispatch("fetch_holdings", {"fund": fund, "refresh": refresh})


@mcp.tool()
def fetch_treasury_curve(on_date: str | None = None, refresh: bool = False) -> dict:
    """U.S. Treasury par yield curve on a date (default latest); refresh=True re-downloads."""
    return tools.dispatch("fetch_treasury_curve", {"on_date": on_date, "refresh": refresh})


@mcp.tool()
def refresh_data(fund: str = "intermediate_muni") -> dict:
    """Re-download every live source; reports failures and the last cached as-of date."""
    return tools.dispatch("refresh_data", {"fund": fund})


@mcp.tool()
def data_status() -> dict:
    """As-of dates and source URLs of all cached data, plus every assumption in force."""
    return tools.dispatch("data_status", {})


def main():
    mcp.run()              # stdio transport by default


if __name__ == "__main__":
    main()
