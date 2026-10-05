"""8-bond HYPOTHETICAL portfolio used ONLY to unit-test the pricing math.

It is never shown in the demo. Each bond yields the curve rate at its final
maturity; all bonds are $125k par munis.
"""
import pandas as pd

CURVE = {1: 2.50, 3: 2.58, 4: 2.65, 6: 2.80, 8: 3.00, 10: 3.25, 12: 3.45}

BONDS = [
    # bond_id, coupon, maturity, call (yrs), sector
    ("A", 5.0, 1, None, "GO"),
    ("B", 5.0, 3, None, "GO"),
    ("C", 5.0, 4, None, "GO"),
    ("D", 5.0, 6, None, "GO"),
    ("E", 5.0, 10, 8, "Hospital"),
    ("F", 5.0, 10, 8, "Airport"),
    ("G", 4.0, 12, 8, "Utility"),
    ("H", 5.0, 8, None, "HigherEd"),
]

GUIDELINES = {"duration_band": [3.0, 5.0], "sector_caps": {"default": 0.30, "GO": 0.60}, "rating_floor": "BBB-"}


def toy_holdings() -> pd.DataFrame:
    rows = []
    for bond_id, coupon, mat, call, sector in BONDS:
        rows.append({"bond_id": bond_id, "par": 125_000, "coupon": coupon, "maturity_years": float(mat),
                     "call_years": float(call) if call else None, "call_price": 100.0,
                     "yield": CURVE[mat], "sector": sector, "asset_type": "muni"})
    return pd.DataFrame(rows)
