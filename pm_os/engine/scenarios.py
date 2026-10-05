"""Rate scenarios: shift yields, fully reprice every bond, report P&L.

A scenario is just "how many bp does each bond's yield move". Each scenario
type below is a different rule for that number:

    parallel    every bond moves the same bp
    curve       bp depends on the bond's maturity (interpolated key-rate shifts)
    muni_ratio  every muni moves; Treasuries stay flat
    credit      bp depends on the bond's sector (spread widening)
    custom      any mix: per-bond shifts on top of an optional parallel move

The bonds are then fully repriced (to worst, so calls can flip on or off),
which is why the P&L is not just -duration x shift.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine import guidelines, portfolio

# Preset curve shapes in bp at key maturities (years). Steepener/flattener
# values are the stress definitions used in the unit tests; the other two are
# their mirror images for completeness.
CURVE_PRESETS = {
    "bear_steepener": {1: 10, 3: 20, 4: 25, 6: 35, 8: 50, 10: 65, 12: 75},
    "bull_flattener": {1: -5, 3: -15, 4: -20, 6: -30, 8: -40, 10: -55, 12: -65},
    "bear_flattener": {1: 75, 3: 65, 4: 50, 6: 35, 8: 25, 10: 20, 12: 10},
    "bull_steepener": {1: -65, 3: -55, 4: -40, 6: -30, 8: -20, 10: -15, 12: -5},
}

CREDIT_PRESETS = {
    # Revenue-sector stress: hospitals and higher-ed widen most, GO flat.
    "revenue_stress": {"Hospital": 90, "HigherEd": 70, "Airport": 40, "Utility": 10, "GO": 0},
}


def interpolate_shift(curve_shift: dict, years: float) -> float:
    """Linear interpolation of a {years: bp} shift; flat beyond the ends."""
    points = sorted((float(k), float(v)) for k, v in curve_shift.items())
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return float(np.interp(years, xs, ys))


def shifts_for(holdings: pd.DataFrame, scenario_type: str, params: dict) -> pd.Series:
    """Return the bp shift for each bond (indexed like `holdings`)."""
    params = params or {}
    idx = holdings.index
    asset = holdings.get("asset_type", pd.Series("muni", index=idx)).fillna("muni")

    if scenario_type == "parallel":
        return pd.Series(float(params.get("bp", 0)), index=idx)

    if scenario_type == "curve":
        curve = params.get("shifts") or CURVE_PRESETS[params.get("preset", "bear_steepener")]
        return holdings["maturity_years"].apply(lambda y: interpolate_shift(curve, y))

    if scenario_type == "muni_ratio":
        bp = float(params.get("bp", 0))
        return pd.Series(np.where(asset == "muni", bp, 0.0), index=idx)

    if scenario_type == "credit":
        by_sector = params.get("sector_bp") or CREDIT_PRESETS[params.get("preset", "revenue_stress")]
        sector = holdings.get("sector", pd.Series("Unknown", index=idx)).fillna("Unknown")
        return sector.map(lambda s: float(by_sector.get(s, by_sector.get("default", 0))))

    if scenario_type == "custom":
        base = float(params.get("parallel_bp", 0))
        per_bond = params.get("bond_bp", {})
        curve = params.get("curve_shifts")
        out = pd.Series(base, index=idx)
        if curve:
            out += holdings["maturity_years"].apply(lambda y: interpolate_shift(curve, y))
        out += holdings["bond_id"].map(lambda b: float(per_bond.get(str(b), 0)))
        return out

    raise ValueError(f"Unknown scenario type: {scenario_type}")


def run_scenario(holdings: pd.DataFrame, scenario_type: str, params: dict | None = None,
                 guideline_cfg: dict | None = None) -> dict:
    """Reprice every bond under the scenario and summarize P&L and breaches."""
    before = portfolio.value_portfolio(holdings)
    shifts = shifts_for(holdings, scenario_type, params or {})

    shocked = holdings.copy()
    shocked["yield"] = holdings["yield"] + shifts / 100.0       # bp -> percent
    after = portfolio.value_portfolio(shocked)

    by_bond = pd.DataFrame({
        "bond_id": before["bond_id"],
        "sector": before.get("sector"),
        "shift_bp": shifts.round(2),
        "price_before": before["price"].round(4),
        "price_after": after["price"].round(4),
        "priced_to_before": before["priced_to"],
        "priced_to_after": after["priced_to"],
        "duration_before": before["duration"].round(3),
        "duration_after": after["duration"].round(3),
        "pnl": ((after["price"] - before["price"]) * before["par"] / 100.0).round(2),
        "below_de_minimis_after": after["below_de_minimis"],
    })
    total_pnl = float(by_bond["pnl"].sum())
    mv_before = float(before["market_value"].sum())

    result = {
        "scenario": {"type": scenario_type, "params": params or {}},
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(100.0 * total_pnl / mv_before, 4),
        "market_value_before": round(mv_before, 2),
        "market_value_after": round(float(after["market_value"].sum()), 2),
        "duration_before": portfolio.summarize(before)["duration"],
        "duration_after": portfolio.summarize(after)["duration"],
        "largest_losers": by_bond.nsmallest(5, "pnl")[["bond_id", "pnl"]].to_dict("records"),
        "call_flips": by_bond[by_bond["priced_to_before"] != by_bond["priced_to_after"]]["bond_id"].tolist(),
        "by_bond": by_bond.to_dict("records"),
    }
    if guideline_cfg is not None:
        result["guidelines_after"] = guidelines.check_guidelines(after, guideline_cfg)
    return result


def call_option_cost(holdings: pd.DataFrame, scenario_type: str, params: dict | None = None) -> dict:
    """Effect of the call options: actual P&L minus P&L if no bond were callable.

    Negative in a rally (upside given up because prices are capped near the
    call price); positive in a selloff (the bond was priced to a short call
    date, so it lost less, although its duration extends).
    """
    actual = run_scenario(holdings, scenario_type, params)
    no_calls = holdings.copy()
    no_calls["call_years"] = None
    bullet = run_scenario(no_calls, scenario_type, params)
    rows = []
    for a, b in zip(actual["by_bond"], bullet["by_bond"]):
        lost = a["pnl"] - b["pnl"]
        if abs(lost) > 0.005:
            rows.append({"bond_id": a["bond_id"], "pnl_callable": a["pnl"], "pnl_if_noncallable": b["pnl"],
                         "upside_lost": round(lost, 2)})
    return {"total_upside_lost": round(sum(r["upside_lost"] for r in rows), 2), "by_bond": rows,
            "sign_convention": "negative = P&L given up to calls; positive = calls cushioned the move"}
