"""The tool layer: every number the agent quotes comes from a function here.

Each tool:
  * takes plain JSON-able arguments,
  * calls the deterministic engine on REAL cached data,
  * returns a dict that always carries `as_of`, `source_url` and `data_label`
    so the answer can say where the number came from.

The same functions are exposed three ways: to the Claude API (TOOL_SCHEMAS +
dispatch, used by the CLI and Streamlit), and to any IDE through the MCP
server in pm_os_mcp/server.py.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from data.connectors import cache, sec_nport, treasury
from data.connectors.http import SourceUnavailable
from engine import guidelines, portfolio, pricing, scenarios, tax

ASSUMPTIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "assumptions.json"


# ---------------------------------------------------------------------------
# Loading data
# ---------------------------------------------------------------------------
def assumptions() -> dict:
    return json.loads(ASSUMPTIONS_PATH.read_text())


def _prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Make raw holdings engine-ready; report anything we had to leave out."""
    df = df.copy()
    notes = []
    cash_like = df["asset_type"].isin(portfolio.CASH_LIKE_TYPES)
    # Cash-like lines (VRDNs, money funds) are carried at market value, duration 0.
    df.loc[cash_like, "par"] = df.loc[cash_like, "market_value"]
    df.loc[cash_like, "price"] = 100.0
    # VRDNs can be put back at par on short notice, so their stated 20-30yr maturity is not their risk.
    df.loc[cash_like, "maturity_years"] = 0.0
    df.loc[cash_like, "coupon"] = df.loc[cash_like, "coupon"].fillna(0.0)
    df.loc[cash_like, "yield"] = df.loc[cash_like, "yield"].fillna(df.loc[cash_like, "coupon"])

    usable = cash_like | ((df["asset_type"].isin(["muni", "treasury"])) & df["yield"].notna()
                          & (df["maturity_years"] > 0))
    dropped = df[~usable]
    if len(dropped):
        notes.append(f"{len(dropped)} lines (${dropped['market_value'].sum():,.0f}) excluded: no fixed coupon/"
                     f"maturity to price (e.g. derivatives, other assets, or unsolvable prices).")
    return df[usable].reset_index(drop=True), notes


def load_portfolio(view: str | None = None, fund: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Real holdings ('fund') or the SMA-sized sample drawn from them ('sma')."""
    cfg = assumptions()
    fund = fund or cfg["defaults"]["fund"]
    view = view or cfg["defaults"]["portfolio_view"]
    raw, meta = sec_nport.load_holdings(fund)
    df, notes = _prepare(raw)
    label = "Real holdings from the fund's public SEC Form N-PORT filing."
    if view == "sma":
        s = cfg["sma_sample"]
        df = sec_nport.sma_sample(df, s["n_bonds"], s["account_size"], s["min_lot"], s["max_lot"])
        label = ("SMA-sized sample of REAL bonds from the fund's public N-PORT filing (real coupons, maturities, "
                 "prices, yields). Par per bond is an equal-weight sizing ASSUMPTION.")
    if df["call_years"].isna().all():
        notes.append("N-PORT has no call schedules: every bond is priced to MATURITY. Premium callable munis would "
                     "have lower yield-to-worst and shorter duration; add calls in data/user/overrides.csv.")
    prov = {
        "as_of": meta.get("as_of"),
        "source_url": meta.get("source_url"),
        "fetched_at": meta.get("fetched_at"),
        "data_label": label,
        "fund": cfg["funds"][fund]["label"],
        "view": view,
        "caveats": notes + ["Sector and state are INFERRED from issuer names (keyword match).",
                            "Independent analysis of public filings; not a Fidelity product."],
    }
    return df, prov


def _strategy(fund: str | None, strategy: str | None) -> tuple[str, dict]:
    cfg = assumptions()
    fund = fund or cfg["defaults"]["fund"]
    key = strategy or cfg["funds"][fund]["default_strategy"]
    return key, cfg["strategies"][key]


def _clean(obj):
    """Make numpy/pandas values JSON-safe (NaN -> None)."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if math.isnan(obj) else round(float(obj), 6)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def get_portfolio(view: str | None = None, fund: str | None = None, max_rows: int = 40) -> dict:
    df, prov = load_portfolio(view, fund)
    valued = portfolio.value_portfolio(df)
    tey_rate = assumptions()["tax"]["tey_rate"]
    cols = ["bond_id", "name", "sector", "state", "coupon", "maturity_date", "maturity_years", "par", "price",
            "market_value", "weight", "yield", "duration", "priced_to", "below_de_minimis", "emma_url"]
    cols = [c for c in cols if c in valued]
    table = valued.sort_values("market_value", ascending=False)[cols]
    return _clean({
        **prov,
        "summary": portfolio.summarize(valued, tax_rate=tey_rate),
        "holdings_shown": min(len(table), max_rows),
        "holdings_total": len(table),
        "holdings": table.head(max_rows).to_dict("records"),
        "maturity_buckets": portfolio.maturity_buckets(valued).to_dict("records"),
        "assumptions_used": {"tey_tax_rate": tey_rate},
    })


def price_bond(coupon: float, yield_pct: float, maturity_years: float, call_years: float | None = None,
               call_price: float = 100.0) -> dict:
    out = pricing.price_bond(coupon, yield_pct, maturity_years, call_years, call_price)
    return _clean({**out, "as_of": None, "source_url": None,
                   "data_label": "Pure calculation on the inputs given (no market data)."})


def run_scenario(type: str, params: dict | None = None, view: str | None = None, fund: str | None = None,
                 strategy: str | None = None) -> dict:
    params = dict(params or {})
    df, prov = load_portfolio(view, fund)
    extra = {}
    scenario_type = type
    if type == "treasury_replay":
        # Turn real Treasury curve moves between two dates into a curve shift.
        curve, tmeta = treasury.load_curve()
        change = treasury.curve_change(curve, params["start_date"], params.get("end_date"))
        params = {"shifts": change["shifts_bp"]}
        scenario_type = "curve"
        extra = {"treasury_replay": {k: change[k] for k in ("start_date", "end_date", "shifts_bp")},
                 "treasury_source_url": tmeta["source_url"]}
    _, limits = _strategy(fund, strategy)
    result = scenarios.run_scenario(df, scenario_type, params, limits)
    if scenario_type in ("curve", "parallel") and df["call_years"].notna().any():
        result["call_option_cost"] = scenarios.call_option_cost(df, scenario_type, params)
    return _clean({**prov, **extra, **result, "guideline_limits_used": limits})


def check_guidelines(view: str | None = None, fund: str | None = None, strategy: str | None = None) -> dict:
    df, prov = load_portfolio(view, fund)
    key, limits = _strategy(fund, strategy)
    out = guidelines.check_guidelines(portfolio.value_portfolio(df), limits)
    return _clean({**prov, "strategy": key, "limits (ASSUMED)": limits, **out})


def tax_loss_screen(threshold: float = 0.0, view: str | None = None, fund: str | None = None) -> dict:
    df, prov = load_portfolio(view, fund)
    rate = assumptions()["tax"]["capital_gains_rate"]
    years_held = float(df["years_held"].dropna().iloc[0]) if "years_held" in df and df["years_held"].notna().any() else 0.0
    out = tax.tax_loss_screen(df, rate, threshold, years_held)
    cost_source = df["cost_source"].dropna().iloc[0] if "cost_source" in df and df["cost_source"].notna().any() else None
    return _clean({**prov, **out, "cost_basis_source (ASSUMPTION)": cost_source,
                   "assumptions_used": {"capital_gains_rate": rate, "years_held": years_held}})


def withdrawal_plan(amount: float, horizon_months: float = 1.0, view: str | None = None,
                    fund: str | None = None, strategy: str | None = None) -> dict:
    df, prov = load_portfolio(view, fund)
    gains = None
    if "cost_price" in df and df["cost_price"].notna().any():
        valued = portfolio.value_portfolio(df)
        gains = dict(zip(valued["bond_id"], valued["price"] - valued["cost_price"].fillna(valued["price"])))
    s = assumptions()["sma_sample"]
    plan = tax.withdrawal_plan(df, amount, s["lot_increment"], s["min_lot"], gains, horizon_months)
    _, limits = _strategy(fund, strategy)
    lo, hi = limits["duration_band"]
    d = plan["duration_after"]
    plan["duration_band_after"] = None if d is None else ("ok" if lo <= d <= hi else "breach")
    return _clean({**prov, **plan, "duration_band (ASSUMED)": limits["duration_band"]})


def convexity_check(bond_id: str, bp: float = 100.0, view: str | None = None, fund: str | None = None) -> dict:
    df, prov = load_portfolio(view, fund)
    match = df[df["bond_id"].astype(str) == str(bond_id)]
    if match.empty:
        return {"error": f"Bond {bond_id} not in this portfolio", **prov}
    return _clean({**prov, **tax.convexity_check(match.iloc[0].to_dict(), bp)})


def muni_treasury_ratio(view: str | None = None, fund: str | None = None, on_date: str | None = None) -> dict:
    """Portfolio muni yield / Treasury yield, by maturity bucket.

    MMD/BVAL AAA curves are licensed, so we use the portfolio's own yields:
    this is a ratio for THESE bonds (mixed credit quality), not a AAA benchmark.
    """
    df, prov = load_portfolio(view, fund)
    curve_all, tmeta = treasury.load_curve()
    curve = treasury.curve_on(curve_all, on_date)
    valued = portfolio.value_portfolio(df[df["asset_type"] == "muni"])
    buckets = portfolio.maturity_buckets(valued)
    tey_rate = assumptions()["tax"]["tey_rate"]
    buckets["treasury_yield_pct"] = buckets["avg_maturity_years"].apply(lambda y: treasury.yield_at(curve, y))
    buckets["muni_treasury_ratio"] = buckets["yield_pct"] / buckets["treasury_yield_pct"]
    buckets["tey_pct"] = buckets["yield_pct"] / (1 - tey_rate)
    buckets["tey_minus_treasury_bp"] = (buckets["tey_pct"] - buckets["treasury_yield_pct"]) * 100
    return _clean({
        **prov,
        "treasury_curve_date": curve["date"].iloc[0],
        "treasury_source_url": tmeta["source_url"],
        "buckets": buckets.to_dict("records"),
        "treasury_curve": curve[["tenor", "years", "yield_pct"]].to_dict("records"),
        "method": "Ratio = MV-weighted yield of portfolio munis in the bucket / Treasury par yield interpolated at "
                  "the bucket's average maturity. Not an MMD/BVAL AAA ratio (those are licensed).",
    })


def fetch_holdings(fund: str | None = None, refresh: bool = False) -> dict:
    """Holdings summary from cache; optionally re-download from EDGAR first."""
    fund = fund or assumptions()["defaults"]["fund"]
    note = None
    if refresh:
        try:
            sec_nport.refresh_holdings(fund, assumptions()["cost_basis"]["prior_filings_back"])
        except SourceUnavailable as exc:
            note = f"Live refresh failed ({exc}); showing last cached copy."
    df, meta = sec_nport.load_holdings(fund)
    return _clean({"as_of": meta["as_of"], "source_url": meta["source_url"], "fetched_at": meta["fetched_at"],
                   "notes": meta.get("notes"), "refresh_note": note, **sec_nport.holdings_summary(df)})


def fetch_treasury_curve(on_date: str | None = None, refresh: bool = False) -> dict:
    note = None
    if refresh:
        try:
            treasury.refresh_curve()
        except SourceUnavailable as exc:
            note = f"Live refresh failed ({exc}); showing last cached copy."
    df, meta = treasury.load_curve()
    curve = treasury.curve_on(df, on_date)
    return _clean({"as_of": curve["date"].iloc[0], "source_url": meta["source_url"], "fetched_at": meta["fetched_at"],
                   "refresh_note": note, "curve": curve[["tenor", "years", "yield_pct"]].to_dict("records")})


def refresh_data(fund: str | None = None) -> dict:
    """Try every live source; report what worked and the cached date of what didn't."""
    fund = fund or assumptions()["defaults"]["fund"]
    report = {}
    jobs = {
        "holdings": lambda: sec_nport.refresh_holdings(fund, assumptions()["cost_basis"]["prior_filings_back"]),
        "treasury_curve": treasury.refresh_curve,
    }
    for name, job in jobs.items():
        try:
            out = job()
            report[name] = {"status": "ok", "as_of": out["meta"]["as_of"], "source_url": out["meta"]["source_url"]}
        except Exception as exc:          # report every failure, never hide it
            cached = cache.load_meta(f"holdings_{fund}" if name == "holdings" else name)
            report[name] = {"status": "failed", "error": str(exc),
                            "last_cached_as_of": cached["as_of"] if cached else None}
    return {"as_of": None, "source_url": None, "refresh": report}


def data_status() -> dict:
    """Provenance of every cached dataset plus the assumptions in force."""
    return {"as_of": None, "source_url": None, "cache": cache.status(), "assumptions": assumptions()}


# ---------------------------------------------------------------------------
# Claude API tool schemas + dispatch
# ---------------------------------------------------------------------------
_VIEW = {"type": "string", "enum": ["sma", "fund"],
         "description": "'sma' = 30-bond SMA-sized sample of real holdings (default); 'fund' = full fund holdings."}
_FUND = {"type": "string", "enum": ["intermediate_muni", "limited_term_muni"],
         "description": "Which public fund filing to use (default intermediate_muni)."}
_STRATEGY = {"type": "string", "enum": ["intermediate_muni", "limited_duration_muni"],
             "description": "Mandate whose (assumed) guideline limits apply."}

TOOL_SCHEMAS = [
    {"name": "get_portfolio",
     "description": "Holdings with price, market value, weight, yield to worst, duration, priced-to date, plus portfolio "
                    "MV, duration, yield, TEY, sector/state mix and maturity buckets. Start here for any portfolio question.",
     "input_schema": {"type": "object", "properties": {"view": _VIEW, "fund": _FUND}}},
    {"name": "price_bond",
     "description": "Price one bond from coupon/yield/maturity (optional call). Returns price, priced-to date, modified "
                    "and Macaulay duration, de minimis line and the full cash-flow table for teaching.",
     "input_schema": {"type": "object", "required": ["coupon", "yield_pct", "maturity_years"], "properties": {
         "coupon": {"type": "number", "description": "Annual coupon in percent, e.g. 5"},
         "yield_pct": {"type": "number", "description": "Yield in percent, e.g. 3.25"},
         "maturity_years": {"type": "number"},
         "call_years": {"type": "number", "description": "Years to first call (optional)"},
         "call_price": {"type": "number"}}}},
    {"name": "run_scenario",
     "description": "Full reprice of every bond under a rate scenario: P&L by bond and total, new duration, call flips, "
                    "guideline breaches. Types: parallel {bp}; curve {preset: bear_steepener|bull_flattener|"
                    "bear_flattener|bull_steepener} or {shifts: {years: bp}}; muni_ratio {bp} (munis move, Treasuries "
                    "flat); credit {sector_bp: {sector: bp}} or {preset: revenue_stress}; custom {parallel_bp, "
                    "bond_bp: {bond_id: bp}, curve_shifts}; treasury_replay {start_date, end_date} replays real "
                    "Treasury curve changes between two dates.",
     "input_schema": {"type": "object", "required": ["type"], "properties": {
         "type": {"type": "string", "enum": ["parallel", "curve", "muni_ratio", "credit", "custom", "treasury_replay"]},
         "params": {"type": "object"}, "view": _VIEW, "fund": _FUND, "strategy": _STRATEGY}}},
    {"name": "check_guidelines",
     "description": "Duration band, sector caps, rating floor and de minimis flags against the (assumed) mandate limits.",
     "input_schema": {"type": "object", "properties": {"view": _VIEW, "fund": _FUND, "strategy": _STRATEGY}}},
    {"name": "tax_loss_screen",
     "description": "Unrealized gain/loss vs. cost basis (premium amortized), harvest candidates above a dollar "
                    "threshold, estimated tax savings at the assumed capital gains rate, wash-sale notes.",
     "input_schema": {"type": "object", "properties": {
         "threshold": {"type": "number", "description": "Minimum loss in dollars to list a bond"},
         "view": _VIEW, "fund": _FUND}}},
    {"name": "withdrawal_plan",
     "description": "Raise cash: coupons/maturities due first, then cash-like lines, then bonds at a loss, then the "
                    "shortest maturities, in $5k odd lots. Returns trades and duration after.",
     "input_schema": {"type": "object", "required": ["amount"], "properties": {
         "amount": {"type": "number"}, "horizon_months": {"type": "number"},
         "view": _VIEW, "fund": _FUND, "strategy": _STRATEGY}}},
    {"name": "convexity_check",
     "description": "For one bond (bond_id = CUSIP): gain if rates fall vs. loss if they rise, and how much upside the "
                    "call option costs versus a non-callable bond.",
     "input_schema": {"type": "object", "required": ["bond_id"], "properties": {
         "bond_id": {"type": "string"}, "bp": {"type": "number"}, "view": _VIEW, "fund": _FUND}}},
    {"name": "muni_treasury_ratio",
     "description": "Portfolio muni yield / Treasury yield by maturity bucket, with TEY vs. Treasury pickup, using the "
                    "real Treasury par curve.",
     "input_schema": {"type": "object", "properties": {
         "view": _VIEW, "fund": _FUND, "on_date": {"type": "string", "description": "YYYY-MM-DD (default latest)"}}}},
    {"name": "fetch_holdings",
     "description": "Summary and provenance of the cached N-PORT holdings (refresh=true re-downloads from EDGAR).",
     "input_schema": {"type": "object", "properties": {"fund": _FUND, "refresh": {"type": "boolean"}}}},
    {"name": "fetch_treasury_curve",
     "description": "The U.S. Treasury par yield curve on a date (default latest cached).",
     "input_schema": {"type": "object", "properties": {"on_date": {"type": "string"}, "refresh": {"type": "boolean"}}}},
    {"name": "refresh_data",
     "description": "Re-download N-PORT holdings and the Treasury curve; reports which sources failed and their last cached date.",
     "input_schema": {"type": "object", "properties": {"fund": _FUND}}},
    {"name": "data_status",
     "description": "As-of dates and source URLs of every cached dataset, plus all assumptions in force.",
     "input_schema": {"type": "object", "properties": {}}},
]

TOOL_FUNCTIONS = {
    "get_portfolio": get_portfolio, "price_bond": price_bond, "run_scenario": run_scenario,
    "check_guidelines": check_guidelines, "tax_loss_screen": tax_loss_screen, "withdrawal_plan": withdrawal_plan,
    "convexity_check": convexity_check, "muni_treasury_ratio": muni_treasury_ratio,
    "fetch_holdings": fetch_holdings, "fetch_treasury_curve": fetch_treasury_curve,
    "refresh_data": refresh_data, "data_status": data_status,
}


def dispatch(name: str, args: dict) -> dict:
    """Run a tool by name. Errors come back as data so the model can say what failed."""
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool {name}"}
    try:
        return fn(**(args or {}))
    except SourceUnavailable as exc:
        return {"error": str(exc), "as_of": None, "source_url": None,
                "instruction": "Data unavailable. Tell the PM which source failed; do not estimate the number."}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "as_of": None, "source_url": None}
