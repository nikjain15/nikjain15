"""Pricing math checks against hand-verified numbers (toy portfolio only)."""
import pytest

from engine import pricing, portfolio
from tests.fixtures.toy_portfolio import toy_holdings

DOLLARS = 50      # tolerance for dollar amounts
NUMBERS = 0.02    # tolerance for prices, durations, yields


@pytest.fixture
def valued():
    return portfolio.value_portfolio(toy_holdings())


def test_baseline_portfolio(valued):
    s = portfolio.summarize(valued, tax_rate=0.37 + 0.038)
    assert s["market_value"] == pytest.approx(1_090_955, abs=DOLLARS)
    assert s["duration"] == pytest.approx(4.99, abs=NUMBERS)
    assert s["yield_to_worst_pct"] == pytest.approx(2.94, abs=NUMBERS)
    assert s["tax_equivalent_yield_pct"] == pytest.approx(4.96, abs=NUMBERS)


def test_bond_g_priced_to_call_at_345():
    b = pricing.price_bond(4.0, 3.45, 12, call_years=8)
    assert b["priced_to"] == "call"
    assert b["redemption_years"] == 8
    assert b["price"] == pytest.approx(103.82, abs=NUMBERS)
    assert b["modified_duration"] == pytest.approx(6.83, abs=NUMBERS)


def test_bond_g_extends_to_maturity_at_445():
    b = pricing.price_bond(4.0, 4.45, 12, call_years=8)
    assert b["priced_to"] == "maturity"
    assert b["price"] == pytest.approx(95.85, abs=NUMBERS)
    assert b["modified_duration"] == pytest.approx(9.38, abs=NUMBERS)
    # ...and it falls below the de minimis line of 100 - 0.25 x 12 = 97.00
    assert b["de_minimis_threshold"] == 97.0
    assert b["price"] < b["de_minimis_threshold"]


def test_bond_e_noncallable_comparison():
    before = pricing.price_to_date(5.0, 3.25, 10)
    after = pricing.price_to_date(5.0, 2.70, 10)
    assert before == pytest.approx(114.84, abs=NUMBERS)
    assert after == pytest.approx(120.04, abs=NUMBERS)
    assert (after - before) * 125_000 / 100 == pytest.approx(6_500, abs=DOLLARS)


def test_cash_flow_table_sums_to_price():
    rows = pricing.price_bond(5.0, 3.0, 8)["cash_flows"]
    assert len(rows) == 16
    assert rows[-1]["running_total"] == pytest.approx(pricing.price_to_date(5.0, 3.0, 8), abs=1e-4)


def test_yield_solver_round_trips():
    for coupon, y, mat, call in [(5.0, 3.25, 10, 8), (4.0, 4.45, 12, 8), (3.0, 2.1, 3.37, None)]:
        price = pricing.price_to_worst(coupon, y, mat, call)["price"]
        assert pricing.yield_to_worst(price, coupon, mat, call) == pytest.approx(y, abs=1e-6)


def test_tey():
    assert pricing.tax_equivalent_yield(3.0, 0.408) == pytest.approx(5.0676, abs=1e-3)
