"""Investment guideline checks: duration band, sector caps, rating floor, de minimis.

Limits come from data/assumptions.json (they are ASSUMED mandate limits, not
published ones). Each check returns a status of "ok", "breach" or
"not_available" so missing data is never reported as a pass.
"""

from __future__ import annotations

import pandas as pd

# Rating scale, best to worst, for the rating-floor check.
RATING_ORDER = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-",
                "BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"]


def _rating_rank(rating) -> int | None:
    if not isinstance(rating, str):
        return None
    r = rating.strip().upper()
    return RATING_ORDER.index(r) if r in RATING_ORDER else None


def check_guidelines(valued: pd.DataFrame, cfg: dict) -> dict:
    """Run every check on an already-valued portfolio (see portfolio.value_portfolio)."""
    mv = valued["market_value"].sum()
    w = valued["market_value"] / mv
    checks = []

    # 1. Duration band
    duration = float((w * valued["duration"]).sum())
    lo, hi = cfg["duration_band"]
    checks.append({
        "check": "duration_band",
        "value": round(duration, 4),
        "limit": [lo, hi],
        "status": "ok" if lo <= duration <= hi else "breach",
        "detail": f"Portfolio duration {duration:.2f} vs band {lo}-{hi} yrs",
    })

    # 2. Sector caps
    caps = cfg.get("sector_caps", {})
    if "sector" in valued and valued["sector"].notna().any():
        weights = valued.groupby(valued["sector"].fillna("Unknown"))["market_value"].sum() / mv
        for sector, weight in weights.sort_values(ascending=False).items():
            cap = caps.get(sector, caps.get("default"))
            if cap is None:
                continue
            checks.append({
                "check": f"sector_cap:{sector}",
                "value": round(float(weight), 4),
                "limit": cap,
                "status": "ok" if weight <= cap else "breach",
                "detail": f"{sector} {weight:.1%} vs cap {cap:.0%}",
            })
    else:
        checks.append({"check": "sector_caps", "status": "not_available", "detail": "No sector data"})

    # 3. Rating floor
    floor = cfg.get("rating_floor")
    if floor and "rating" in valued and valued["rating"].notna().any():
        floor_rank = _rating_rank(floor)
        ranks = valued["rating"].apply(_rating_rank)
        below = valued[ranks.notna() & (ranks > floor_rank)]
        unrated = valued[ranks.isna()]
        checks.append({
            "check": "rating_floor",
            "limit": floor,
            "status": "breach" if len(below) else "ok",
            "bonds_below_floor": below["bond_id"].tolist(),
            "bonds_without_rating": len(unrated),
            "detail": f"{len(below)} bonds below {floor}; {len(unrated)} without a rating on file",
        })
    else:
        checks.append({"check": "rating_floor", "limit": floor, "status": "not_available",
                       "detail": "No ratings on file (SEC N-PORT does not report credit ratings)."})

    # 4. De minimis: informational flag, not a hard limit
    flagged = valued[valued["below_de_minimis"]]
    checks.append({
        "check": "de_minimis",
        "status": "flag" if len(flagged) else "ok",
        "bonds": [
            {"bond_id": r.bond_id, "price": round(r.price, 3), "threshold": r.de_minimis_threshold}
            for r in flagged.itertuples()
        ],
        "detail": f"{len(flagged)} bonds priced below their de minimis threshold "
                  "(discount would be taxed as ordinary income for a new buyer)",
    })

    breaches = [c["check"] for c in checks if c["status"] == "breach"]
    return {"status": "breach" if breaches else "ok", "breaches": breaches, "checks": checks}
