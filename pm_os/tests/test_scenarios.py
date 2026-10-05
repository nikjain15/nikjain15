"""Scenario P&L checks against hand-verified numbers (toy portfolio only)."""
import pytest

from engine import scenarios, tax
from tests.fixtures.toy_portfolio import GUIDELINES, toy_holdings

DOLLARS = 50
NUMBERS = 0.02


def pnl_by_bond(result):
    return {b["bond_id"]: b["pnl"] for b in result["by_bond"]}


def test_parallel_up_100():
    r = scenarios.run_scenario(toy_holdings(), "parallel", {"bp": 100}, GUIDELINES)
    assert r["total_pnl"] == pytest.approx(-54_009, abs=DOLLARS)
    assert r["total_pnl_pct"] == pytest.approx(-4.95, abs=NUMBERS)
    assert r["duration_after"] == pytest.approx(5.19, abs=NUMBERS)
    assert "duration_band" in r["guidelines_after"]["breaches"]        # 5.19 > 5.0
    assert r["largest_losers"][0]["bond_id"] == "G"
    assert r["largest_losers"][0]["pnl"] == pytest.approx(-9_957, abs=DOLLARS)
    assert "G" in r["call_flips"]                                        # G extends to maturity


def test_parallel_down_100():
    r = scenarios.run_scenario(toy_holdings(), "parallel", {"bp": -100})
    assert r["total_pnl"] == pytest.approx(56_319, abs=DOLLARS)


def test_bear_steepener():
    r = scenarios.run_scenario(toy_holdings(), "curve", {"preset": "bear_steepener"})
    assert r["total_pnl"] == pytest.approx(-28_287, abs=DOLLARS)


def test_bull_flattener_and_call_cost():
    r = scenarios.run_scenario(toy_holdings(), "curve", {"preset": "bull_flattener"})
    assert r["total_pnl"] == pytest.approx(24_152, abs=DOLLARS)
    assert r["duration_after"] == pytest.approx(5.04, abs=NUMBERS)

    cost = scenarios.call_option_cost(toy_holdings(), "curve", {"preset": "bull_flattener"})
    lost = {b["bond_id"]: b["upside_lost"] for b in cost["by_bond"]}
    assert cost["total_upside_lost"] == pytest.approx(-5_056, abs=DOLLARS)
    assert lost["E"] == pytest.approx(-1_240, abs=DOLLARS)
    assert lost["F"] == pytest.approx(-1_240, abs=DOLLARS)
    assert lost["G"] == pytest.approx(-2_576, abs=DOLLARS)


def test_muni_ratio_up_40():
    r = scenarios.run_scenario(toy_holdings(), "muni_ratio", {"bp": 40})
    assert r["total_pnl"] == pytest.approx(-21_463, abs=DOLLARS)


def test_credit_stress():
    r = scenarios.run_scenario(toy_holdings(), "credit", {"preset": "revenue_stress"})
    assert r["total_pnl"] == pytest.approx(-19_199, abs=DOLLARS)
    pnl = pnl_by_bond(r)
    share_e_h = (pnl["E"] + pnl["H"]) / r["total_pnl"]
    assert share_e_h == pytest.approx(0.76, abs=0.01)


def test_convexity_check_bond_e():
    row = toy_holdings().set_index("bond_id").loc["E"].to_dict() | {"bond_id": "E"}
    c = tax.convexity_check(row, bp=100)
    assert c["negative_convexity"] is True or c["upside_lost_to_call"] > 0
    assert c["upside_lost_to_call"] > 0


def test_withdrawal_plan_raises_cash():
    plan = tax.withdrawal_plan(toy_holdings(), 150_000)
    assert plan["proceeds"] + plan["cash_from_coupons"] >= 150_000
    assert plan["trades"][0]["bond_id"] == "A"          # shortest maturity first, no losses on file
    assert all(t["par_sold"] % 5_000 == 0 for t in plan["trades"])


def test_tax_loss_screen():
    h = toy_holdings()
    h["cost_price"] = [100, 100, 100, 100, 100, 100, 110, 100]    # G bought at 110 -> loss
    out = tax.tax_loss_screen(h, cap_gains_rate=0.238)
    assert out["status"] == "ok"
    assert [c["bond_id"] for c in out["candidates"]] == ["G"]
    loss = (103.8165 - 110) * 1250
    assert out["harvestable_loss"] == pytest.approx(loss, abs=DOLLARS)
    assert out["estimated_tax_savings"] == pytest.approx(-loss * 0.238, abs=DOLLARS)
