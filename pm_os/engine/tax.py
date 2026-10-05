"""SMA tax logic: tax-loss harvesting, withdrawals, convexity.

In a separately managed account the client owns each bond directly, so every
sale realizes a taxable gain or loss for that client. These functions make
those trade-offs explicit.

Tax rates and cost basis are ASSUMPTIONS (see data/assumptions.json); the fund
filings we use do not publish lot-level cost.
"""

from __future__ import annotations

import math

import pandas as pd

from engine import portfolio, pricing


# ---------------------------------------------------------------------------
# Cost basis
# ---------------------------------------------------------------------------
def amortized_basis(cost_price: float, coupon: float, years_held: float, maturity_years_now: float,
                    call_years_now: float | None = None) -> float:
    """Tax basis today for a muni bought at `cost_price`.

    Premium on a tax-exempt bond MUST be amortized (no deduction), which lowers
    basis every year. We do it on a constant-yield basis: find the yield the
    client bought at, then reprice at that yield with today's remaining term.
    Discount bonds keep their cost basis here (market-discount accretion is
    taxed at sale/maturity, not added to basis, unless elected).
    """
    if cost_price is None or (isinstance(cost_price, float) and math.isnan(cost_price)) or cost_price <= 100:
        return cost_price
    maturity_at_purchase = maturity_years_now + years_held
    call_at_purchase = call_years_now + years_held if call_years_now else None
    purchase_yield = pricing.yield_to_worst(cost_price, coupon, maturity_at_purchase, call_at_purchase)
    if purchase_yield is None:
        return cost_price
    return max(100.0, pricing.price_to_worst(coupon, purchase_yield, maturity_years_now, call_years_now)["price"])


# ---------------------------------------------------------------------------
# Tax-loss harvesting
# ---------------------------------------------------------------------------
def tax_loss_screen(holdings: pd.DataFrame, cap_gains_rate: float, threshold: float = 0.0,
                    years_held: float = 0.0) -> dict:
    """Unrealized gain/loss vs. cost and the harvestable losses.

    `threshold` is the minimum loss in dollars for a bond to be a candidate
    (small losses are not worth an odd-lot round trip).
    """
    if "cost_price" not in holdings or holdings["cost_price"].isna().all():
        return {"status": "not_available",
                "detail": "No cost basis on file. Enter or upload cost, or load a prior N-PORT filing as the purchase price."}

    valued = portfolio.value_portfolio(holdings)
    rows = []
    for _, r in valued.iterrows():
        cost = r.get("cost_price")
        if cost is None or (isinstance(cost, float) and math.isnan(cost)):
            continue
        call_years = r.get("call_years") if "call_years" in r else None
        if isinstance(call_years, float) and math.isnan(call_years):
            call_years = None
        basis = amortized_basis(cost, r["coupon"], years_held, r["maturity_years"], call_years)
        gain = (r["price"] - basis) * r["par"] / 100.0
        rows.append({
            "bond_id": r["bond_id"], "name": r.get("name"), "par": r["par"],
            "price": round(r["price"], 4), "cost_price": round(cost, 4), "tax_basis": round(basis, 4),
            "unrealized_gain": round(gain, 2),
        })
    table = pd.DataFrame(rows)
    losses = table[table["unrealized_gain"] < -abs(threshold)].sort_values("unrealized_gain")
    total_loss = float(losses["unrealized_gain"].sum())
    return {
        "status": "ok",
        "cap_gains_rate": cap_gains_rate,
        "total_unrealized_gain": round(float(table["unrealized_gain"].sum()), 2),
        "harvestable_loss": round(total_loss, 2),
        "estimated_tax_savings": round(-total_loss * cap_gains_rate, 2),
        "candidates": losses.to_dict("records"),
        "all_positions": table.to_dict("records"),
        "wash_sale_notes": [
            "Do not buy back the same or a 'substantially identical' bond within 30 days before or after the sale.",
            "Swap instead into a different issuer, or the same issuer with a clearly different coupon/maturity.",
            "Check the client's other accounts too: a repurchase anywhere in the household can trigger a wash sale.",
            "Premium munis: basis is amortized (shown above), so the realizable loss is smaller than price vs. original cost.",
        ],
    }


# ---------------------------------------------------------------------------
# Withdrawal plan
# ---------------------------------------------------------------------------
def coupons_due(holdings: pd.DataFrame, months: float) -> list[dict]:
    """Coupons (and maturities) paid within the next `months`.

    Payment dates are rebuilt by stepping back from maturity in half-years,
    which matches how most munis pay; floating-rate notes are skipped.
    """
    horizon = months / 12.0
    asset = holdings.get("asset_type", pd.Series("muni", index=holdings.index)).fillna("muni")
    due = []
    for (_, r), kind in zip(holdings.iterrows(), asset):
        if kind in portfolio.CASH_LIKE_TYPES:
            continue
        for t in pricing.cash_flow_times(r["maturity_years"]):
            if t > horizon:
                break
            amount = r["coupon"] / pricing.FREQ * r["par"] / 100.0
            if abs(t - r["maturity_years"]) < 1e-6:
                amount += r["par"]
            due.append({"bond_id": r["bond_id"], "in_years": round(t, 3), "amount": round(amount, 2)})
    return due


def withdrawal_plan(holdings: pd.DataFrame, amount: float, lot_increment: float = 5_000,
                    min_lot: float = 25_000, gains: dict | None = None, horizon_months: float = 1.0) -> dict:
    """Raise `amount` dollars: coupons and cash first, then losses, then the shortest maturities.

    Partial sales are rounded UP to `lot_increment` of par and never leave a
    position smaller than `min_lot` (the rest is sold too), mimicking odd-lot
    trading. `gains` optionally maps bond_id -> unrealized gain per 100 par.
    """
    valued = portfolio.value_portfolio(holdings)
    valued["gain_per_100"] = valued["bond_id"].map(gains or {}).fillna(0.0)
    asset = valued.get("asset_type", pd.Series("muni", index=valued.index)).fillna("muni")

    # Priority: 0 = cash/floating, 1 = losses (largest first), 2 = everything else by maturity
    valued["priority"] = 2
    valued.loc[valued["gain_per_100"] < 0, "priority"] = 1
    valued.loc[asset.isin(portfolio.CASH_LIKE_TYPES), "priority"] = 0
    order = valued.sort_values(["priority", "gain_per_100", "maturity_years"])

    # Step 1: coupons and maturities landing before the client needs the money.
    incoming = coupons_due(holdings, horizon_months)
    incoming_cash = sum(c["amount"] for c in incoming)
    remaining = amount - incoming_cash
    trades = []
    for _, r in order.iterrows():
        if remaining <= 0:
            break
        price = r["price"]
        par_needed = math.ceil(remaining / (price / 100.0) / lot_increment) * lot_increment
        par_sold = min(par_needed, r["par"])
        if 0 < r["par"] - par_sold < min_lot:
            par_sold = r["par"]                          # don't leave an unsellable stub
        proceeds = par_sold * price / 100.0
        remaining -= proceeds
        reason = {0: "cash / floating-rate first", 1: "harvests a loss", 2: "shortest maturity"}[r["priority"]]
        trades.append({"bond_id": r["bond_id"], "name": r.get("name"), "par_sold": par_sold,
                       "price": round(price, 4), "proceeds": round(proceeds, 2),
                       "maturity_years": round(r["maturity_years"], 2), "reason": reason})

    after = holdings.copy()
    for t in trades:
        after.loc[after["bond_id"] == t["bond_id"], "par"] -= t["par_sold"]
    after = after[after["par"] > 0]
    before_summary = portfolio.summarize(valued)
    after_summary = portfolio.summarize(portfolio.value_portfolio(after)) if len(after) else {}
    return {
        "amount_requested": amount,
        "coupons_and_maturities_due": incoming,
        "cash_from_coupons": round(incoming_cash, 2),
        "proceeds": round(sum(t["proceeds"] for t in trades), 2),
        "shortfall": round(max(remaining, 0.0), 2),
        "trades": trades,
        "duration_before": before_summary["duration"],
        "duration_after": after_summary.get("duration"),
        "market_value_after": after_summary.get("market_value"),
        "note": "Sale prices are the current valuation prices; real odd-lot bids are typically lower.",
    }


# ---------------------------------------------------------------------------
# Convexity / call option check for one bond
# ---------------------------------------------------------------------------
def convexity_check(row: dict, bp: float = 100.0) -> dict:
    """Gain if rates fall `bp` vs. loss if they rise `bp`, with and without the call."""
    c, y, m = row["coupon"], row["yield"], row["maturity_years"]
    call = row.get("call_years")
    call = None if (call is None or (isinstance(call, float) and math.isnan(call))) else call
    cp = row.get("call_price", 100.0) or 100.0
    par = row.get("par", 100.0)
    step = bp / 100.0

    def px(yy, callable_=True):
        return pricing.price_to_worst(c, yy, m, call if callable_ else None, cp)["price"]

    base, down, up = px(y), px(y - step), px(y + step)
    base_nc, down_nc, up_nc = px(y, False), px(y - step, False), px(y + step, False)
    to_dollars = par / 100.0
    return {
        "bond_id": row.get("bond_id"),
        "shift_bp": bp,
        "price": round(base, 4),
        "gain_if_rates_fall": round((down - base) * to_dollars, 2),
        "loss_if_rates_rise": round((up - base) * to_dollars, 2),
        "asymmetry": round(((down - base) + (up - base)) * to_dollars, 2),
        "negative_convexity": (down - base) < -(up - base),
        "noncallable_gain_if_rates_fall": round((down_nc - base_nc) * to_dollars, 2),
        "upside_lost_to_call": round(((down_nc - base_nc) - (down - base)) * to_dollars, 2) if call else 0.0,
        "priced_to_now": pricing.price_to_worst(c, y, m, call, cp)["priced_to"],
        "priced_to_if_rates_rise": pricing.price_to_worst(c, y + step, m, call, cp)["priced_to"],
    }
