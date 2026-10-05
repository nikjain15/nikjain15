"""Value a whole portfolio: price, market value, weight, duration, yield.

A portfolio is a pandas DataFrame with one row per bond. Required columns:

    bond_id         short id shown to the PM (CUSIP for real holdings)
    par             face amount in dollars
    coupon          annual coupon in percent (5.0 = 5%)
    maturity_years  years from the as-of date to final maturity
    yield           yield to worst in percent

Optional columns (used when present):

    call_years, call_price   first call date (years) and call price
    sector, rating, state    descriptive fields for guidelines
    asset_type               "muni", "treasury", "cash", "floating" ...
    cost_price               client cost per 100 par (tax-loss screen)
    name                     issuer / description

Everything is plain functions over DataFrames so it is easy to follow.
"""

from __future__ import annotations

import math

import pandas as pd

from engine import pricing

# Bonds that are cash-like: no repricing, zero duration (VRDNs, money funds).
CASH_LIKE_TYPES = {"cash", "floating"}


def _opt(row, col, default=None):
    """Read an optional column, treating NaN/blank as missing."""
    if col not in row or row[col] is None:
        return default
    value = row[col]
    if isinstance(value, float) and math.isnan(value):
        return default
    return value


def value_bond(row, yld: float | None = None) -> dict:
    """Price, duration and priced-to date for one bond row at `yld` (default: its own yield)."""
    y = row["yield"] if yld is None else yld
    asset_type = _opt(row, "asset_type", "muni")

    if asset_type in CASH_LIKE_TYPES:
        # Cash and floating-rate notes reset to par: no rate sensitivity.
        price = _opt(row, "price", 100.0)
        return {"price": price, "priced_to": "reset", "duration": 0.0, "yield": y}

    call_years = _opt(row, "call_years")
    call_price = _opt(row, "call_price", 100.0)
    worst = pricing.price_to_worst(row["coupon"], y, row["maturity_years"], call_years, call_price)
    duration = pricing.modified_duration(row["coupon"], y, row["maturity_years"], call_years, call_price)
    return {"price": worst["price"], "priced_to": worst["priced_to"], "duration": duration, "yield": y}


def value_portfolio(holdings: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of `holdings` with price, market value, weight and duration added."""
    df = holdings.copy()
    results = [value_bond(row) for _, row in df.iterrows()]
    df["price"] = [r["price"] for r in results]
    df["priced_to"] = [r["priced_to"] for r in results]
    df["duration"] = [r["duration"] for r in results]
    df["market_value"] = df["price"] * df["par"] / 100.0
    df["weight"] = df["market_value"] / df["market_value"].sum()
    df["de_minimis_threshold"] = df["maturity_years"].apply(pricing.de_minimis_threshold)
    df["below_de_minimis"] = (df["price"] < df["de_minimis_threshold"]) & (
        df.get("asset_type", pd.Series("muni", index=df.index)) == "muni")
    return df


def summarize(valued: pd.DataFrame, tax_rate: float | None = None) -> dict:
    """Portfolio-level numbers: MV, MV-weighted duration and yield, TEY, mixes."""
    mv = valued["market_value"].sum()
    w = valued["market_value"] / mv
    port_yield = float((w * valued["yield"]).sum())
    summary = {
        "bond_count": int(len(valued)),
        "market_value": round(float(mv), 2),
        "par": round(float(valued["par"].sum()), 2),
        "duration": round(float((w * valued["duration"]).sum()), 4),
        "yield_to_worst_pct": round(port_yield, 4),
        "average_maturity_years": round(float((w * valued["maturity_years"]).sum()), 3),
    }
    if tax_rate is not None:
        summary["tax_equivalent_yield_pct"] = round(pricing.tax_equivalent_yield(port_yield, tax_rate), 4)
        summary["tey_tax_rate"] = tax_rate
    for col in ("sector", "rating", "state", "asset_type"):
        if col in valued and valued[col].notna().any():
            mix = valued.groupby(valued[col].fillna("Unknown"))["market_value"].sum() / mv
            summary[f"{col}_mix"] = {k: round(float(v), 4) for k, v in mix.sort_values(ascending=False).items()}
    summary["priced_to_call_count"] = int((valued["priced_to"] == "call").sum())
    summary["below_de_minimis_count"] = int(valued["below_de_minimis"].sum())
    return summary


def maturity_buckets(valued: pd.DataFrame, edges=(0, 1, 3, 5, 7, 10, 15, 100)) -> pd.DataFrame:
    """MV-weighted yield and weight by maturity bucket (the portfolio's own curve)."""
    labels = [f"{a}-{b}y" for a, b in zip(edges[:-1], edges[1:])]
    df = valued.copy()
    df["bucket"] = pd.cut(df["maturity_years"], bins=list(edges), labels=labels, right=False)
    rows = []
    for bucket, g in df.groupby("bucket", observed=True):
        mv = g["market_value"].sum()
        rows.append({
            "bucket": str(bucket),
            "bonds": int(len(g)),
            "weight": float(mv / df["market_value"].sum()),
            "avg_maturity_years": float((g["market_value"] * g["maturity_years"]).sum() / mv),
            "yield_pct": float((g["market_value"] * g["yield"]).sum() / mv),
        })
    return pd.DataFrame(rows)
