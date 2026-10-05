"""Offline parser checks (synthetic fixtures; no network)."""
from pathlib import Path

import pytest

from data.connectors import sec_nport, treasury
from engine import pricing

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_nport_and_derive_yield():
    info, raw = sec_nport.parse_nport((FIXTURES / "nport_sample.xml").read_text())
    assert info["series_name"] == "Test Intermediate Municipal Income Fund"
    assert info["period_end"] == "2026-06-30"
    df = sec_nport.add_derived_fields(raw, info["period_end"])
    hosp = df.iloc[0]
    assert hosp["asset_type"] == "muni"
    assert hosp["sector"] == "Hospital"
    assert hosp["price"] == pytest.approx(105.0)
    # The solved yield must reprice the bond back to the observed price.
    back = pricing.price_to_worst(5.0, hosp["yield"], hosp["maturity_years"])["price"]
    assert back == pytest.approx(105.0, abs=1e-6)
    assert df.iloc[1]["asset_type"] == "floating"


def test_treasury_csv_parse():
    text = 'Date,"1 Mo","3 Mo","1 Yr","2 Yr","10 Yr"\n10/01/2026,4.1,4.0,3.8,3.6,4.2\n09/30/2026,4.1,4.0,3.7,3.5,4.1\n'
    long = treasury.parse_curve_csv(text)
    assert set(long["years"]) == {1 / 12, 0.25, 1.0, 2.0, 10.0}
    chg = treasury.curve_change(long, "2026-09-30", "2026-10-01")
    assert chg["shifts_bp"][10.0] == pytest.approx(10.0)
    assert treasury.yield_at(treasury.curve_on(long), 6.0) == pytest.approx(3.6 + (4.2 - 3.6) * 0.5)


def test_sma_sample_is_deterministic_and_odd_lot_sized():
    from tests.fixtures.toy_portfolio import toy_holdings
    h = toy_holdings()
    h["market_value"] = h["par"]
    a = sec_nport.sma_sample(h, n_bonds=5, account_size=250_000)
    b = sec_nport.sma_sample(h, n_bonds=5, account_size=250_000)
    assert list(a["bond_id"]) == list(b["bond_id"])
    assert len(a) == 5 and a["sector"].nunique() >= 4          # spread across sectors
    assert (a["par"] == 50_000).all()                            # $250k / 5, a $5k multiple
    assert (a["fund_par"] == 125_000).all()                      # real fund par kept for reference
