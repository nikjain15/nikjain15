"""Bond pricing math: price, yield, duration, convexity.

Everything here is deterministic and plain Python, so every number the agent
quotes can be traced back to one of these functions.

Conventions (municipal / Treasury street convention, simplified):
  * Coupons are paid semiannually. A bond with T years left pays coupon/2 at
    times T, T - 0.5, T - 1.0, ... down to the first date after today.
  * Price = sum of CF / (1 + y/2) ** (2 * t), where t is time in years.
  * That sum is the "dirty" (full) price. The quoted "clean" price subtracts
    accrued interest. For whole/half-year maturities accrued is zero, which is
    the case for the unit-test portfolio.
  * Callable bonds are priced to WORST: the lower of the price to the call date
    (redeemed at the call price) and the price to maturity.
  * Modified duration is measured by bumping the yield +/-1bp and repricing
    (so the call option is captured automatically).
"""

from __future__ import annotations

BP = 0.0001          # one basis point in decimal
FREQ = 2             # coupon payments per year (semiannual)


# ---------------------------------------------------------------------------
# Cash flows
# ---------------------------------------------------------------------------
def cash_flow_times(years: float) -> list[float]:
    """Payment times (in years from today), earliest first.

    Counts back from the redemption date in half-year steps, keeping only the
    dates still in the future. A 3.2-year bond pays at 0.2, 0.7, ..., 3.2.
    """
    if years <= 0:
        return []
    times = []
    t = years
    while t > 1e-9:
        times.append(round(t, 10))
        t -= 1.0 / FREQ
    return sorted(times)


def accrued_interest(coupon: float, years: float) -> float:
    """Accrued interest per 100 par since the last coupon date.

    The fraction of the current half-year period already elapsed, times the
    half-year coupon. Zero for whole/half-year maturities.
    """
    times = cash_flow_times(years)
    if not times:
        return 0.0
    time_to_next = times[0]
    elapsed_fraction = 1.0 - time_to_next * FREQ   # share of period gone by
    if elapsed_fraction < 1e-9:
        return 0.0
    return coupon / FREQ * elapsed_fraction


def cash_flow_table(coupon: float, yld: float, years: float, redemption: float = 100.0) -> list[dict]:
    """Every cash flow with its discount factor, PV and running PV total.

    `coupon` and `yld` are in percent (5.0 means 5%). Used by the
    "teach me" view so a PM can see exactly how a price is built.
    """
    rows = []
    running = 0.0
    times = cash_flow_times(years)
    for i, t in enumerate(times):
        cf = coupon / FREQ
        if i == len(times) - 1:
            cf += redemption                      # principal comes back at the end
        df = 1.0 / (1.0 + yld / 100.0 / FREQ) ** (FREQ * t)
        pv = cf * df
        running += pv
        rows.append({
            "period": i + 1,
            "time_years": round(t, 4),
            "cash_flow": round(cf, 6),
            "discount_factor": round(df, 8),
            "present_value": round(pv, 6),
            "running_total": round(running, 6),
        })
    return rows


# ---------------------------------------------------------------------------
# Price to a single redemption date
# ---------------------------------------------------------------------------
def price_to_date(coupon: float, yld: float, years: float, redemption: float = 100.0) -> float:
    """Clean price per 100 par, assuming the bond is redeemed at `years`."""
    dirty = 0.0
    times = cash_flow_times(years)
    for i, t in enumerate(times):
        cf = coupon / FREQ + (redemption if i == len(times) - 1 else 0.0)
        dirty += cf / (1.0 + yld / 100.0 / FREQ) ** (FREQ * t)
    return dirty - accrued_interest(coupon, years)


def macaulay_duration(coupon: float, yld: float, years: float, redemption: float = 100.0) -> float:
    """PV-weighted average time to the cash flows, in years."""
    rows = cash_flow_table(coupon, yld, years, redemption)
    total_pv = sum(r["present_value"] for r in rows)
    if total_pv == 0:
        return 0.0
    return sum(r["time_years"] * r["present_value"] for r in rows) / total_pv


# ---------------------------------------------------------------------------
# Price to worst (handles calls)
# ---------------------------------------------------------------------------
def price_to_worst(coupon: float, yld: float, maturity_years: float,
                   call_years: float | None = None, call_price: float = 100.0) -> dict:
    """Price a bond to the worse (lower) of its call date and its maturity.

    Returns the price and which date it is priced to, because a PM cares a
    lot about whether a callable bond is "priced to call" or "to maturity":
    that flip is what makes durations extend when rates rise.
    """
    to_maturity = price_to_date(coupon, yld, maturity_years, 100.0)
    result = {"price": to_maturity, "priced_to": "maturity", "redemption_years": maturity_years}

    if call_years is not None and 0 < call_years < maturity_years:
        to_call = price_to_date(coupon, yld, call_years, call_price)
        if to_call < to_maturity:
            result = {"price": to_call, "priced_to": "call", "redemption_years": call_years}
    return result


def modified_duration(coupon: float, yld: float, maturity_years: float,
                      call_years: float | None = None, call_price: float = 100.0) -> float:
    """Effective modified duration from a +/-1bp bump-and-reprice.

    D = (P(y - 1bp) - P(y + 1bp)) / (2 * P(y) * 1bp), with every price taken
    to worst, so the call option shortens duration when it is in the money.
    """
    one_bp_in_pct = BP * 100            # yields here are in percent: 1bp = 0.01
    base = price_to_worst(coupon, yld, maturity_years, call_years, call_price)["price"]
    down = price_to_worst(coupon, yld - one_bp_in_pct, maturity_years, call_years, call_price)["price"]
    up = price_to_worst(coupon, yld + one_bp_in_pct, maturity_years, call_years, call_price)["price"]
    return (down - up) / (2.0 * base * BP)


# ---------------------------------------------------------------------------
# Yield from price (used to turn N-PORT market values into yields)
# ---------------------------------------------------------------------------
def yield_to_worst(clean_price: float, coupon: float, maturity_years: float,
                   call_years: float | None = None, call_price: float = 100.0,
                   low: float = -5.0, high: float = 30.0) -> float | None:
    """Solve for the yield (in %) that reproduces `clean_price` priced to worst.

    Price-to-worst falls as yield rises, so plain bisection always converges.
    Solving against the worst price gives the yield to worst directly: at that
    yield one redemption date reprices exactly and the other is no cheaper.
    Returns None if the price is outside what any yield in [low, high] gives.
    """
    def f(y):
        return price_to_worst(coupon, y, maturity_years, call_years, call_price)["price"] - clean_price

    if maturity_years <= 0 or f(low) < 0 or f(high) > 0:
        return None
    for _ in range(200):
        mid = (low + high) / 2.0
        if f(mid) > 0:
            low = mid               # price still too high -> need a higher yield
        else:
            high = mid
        if high - low < 1e-10:
            break
    return (low + high) / 2.0


# ---------------------------------------------------------------------------
# Small helpers used across the engine
# ---------------------------------------------------------------------------
def de_minimis_threshold(years_to_maturity: float) -> float:
    """Market-discount de minimis price: 100 - 0.25 x full years to maturity.

    Buying a muni below this price means the whole discount is taxed as
    ORDINARY income at maturity, not as a capital gain, so these bonds trade
    cheap and are harder to sell. The IRS counts complete years only.
    """
    return 100.0 - 0.25 * int(years_to_maturity)


def tax_equivalent_yield(muni_yield: float, tax_rate: float) -> float:
    """TEY = tax-exempt yield / (1 - tax rate)."""
    return muni_yield / (1.0 - tax_rate)


def price_bond(coupon: float, yld: float, maturity_years: float,
               call_years: float | None = None, call_price: float = 100.0) -> dict:
    """Everything about one bond at one yield: the teaching view."""
    worst = price_to_worst(coupon, yld, maturity_years, call_years, call_price)
    redemption = call_price if worst["priced_to"] == "call" else 100.0
    return {
        "inputs": {"coupon_pct": coupon, "yield_pct": yld, "maturity_years": maturity_years,
                   "call_years": call_years, "call_price": call_price},
        "price": round(worst["price"], 4),
        "priced_to": worst["priced_to"],
        "redemption_years": worst["redemption_years"],
        "price_to_maturity": round(price_to_date(coupon, yld, maturity_years), 4),
        "price_to_call": (round(price_to_date(coupon, yld, call_years, call_price), 4)
                          if call_years and call_years < maturity_years else None),
        "modified_duration": round(modified_duration(coupon, yld, maturity_years, call_years, call_price), 4),
        "macaulay_duration": round(macaulay_duration(coupon, yld, worst["redemption_years"], redemption), 4),
        "accrued_interest": round(accrued_interest(coupon, worst["redemption_years"]), 6),
        "de_minimis_threshold": de_minimis_threshold(maturity_years),
        "cash_flows": cash_flow_table(coupon, yld, worst["redemption_years"], redemption),
        "formula": "Price = sum(CF_t / (1 + y/2)^(2t)) - accrued; callable bonds take the lower of price-to-call and price-to-maturity.",
    }
