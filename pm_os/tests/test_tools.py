"""Every agent tool runs end to end and carries provenance.

Uses the toy fixture in place of the N-PORT cache (no network needed).
"""
import pandas as pd
import pytest

from agent import tools
from data.connectors import sec_nport, treasury
from tests.fixtures.toy_portfolio import toy_holdings


@pytest.fixture(autouse=True)
def fake_sources(monkeypatch):
    h = toy_holdings()
    h["asset_type"] = "muni"
    h["market_value"] = 0.0
    h["name"] = h["bond_id"]
    h["cost_price"] = 100.0
    monkeypatch.setattr(sec_nport, "load_holdings",
                        lambda fund: (h.copy(), {"as_of": "2026-06-30", "source_url": "test://fixture", "fetched_at": "x"}))
    curve = pd.DataFrame({"date": pd.Timestamp("2026-10-01"), "tenor": ["1 Yr", "10 Yr"],
                          "years": [1.0, 10.0], "yield_pct": [3.5, 4.0]})
    monkeypatch.setattr(treasury, "load_curve", lambda: (curve, {"source_url": "test://curve"}))


@pytest.mark.parametrize("name,args", [
    ("get_portfolio", {"view": "fund"}),
    ("price_bond", {"coupon": 5, "yield_pct": 3, "maturity_years": 10, "call_years": 8}),
    ("run_scenario", {"type": "parallel", "params": {"bp": 100}, "view": "fund"}),
    ("check_guidelines", {"view": "fund"}),
    ("tax_loss_screen", {"view": "fund"}),
    ("withdrawal_plan", {"amount": 150000, "view": "fund"}),
    ("convexity_check", {"bond_id": "G", "view": "fund"}),
    ("muni_treasury_ratio", {"view": "fund"}),
])
def test_tool_runs_with_provenance(name, args):
    out = tools.dispatch(name, args)
    assert "error" not in out, out.get("error")
    assert "as_of" in out and "source_url" in out


def test_scenario_matches_engine_through_tool():
    out = tools.dispatch("run_scenario", {"type": "parallel", "params": {"bp": 100}, "view": "fund"})
    assert out["total_pnl"] == pytest.approx(-54_009, abs=50)
    # In a selloff the calls cushion the loss (positive), the opposite of a rally.
    assert out["call_option_cost"]["total_upside_lost"] > 0


def test_missing_data_is_reported_not_invented(monkeypatch):
    def boom(fund):
        raise sec_nport.SourceUnavailable("No cached holdings")
    monkeypatch.setattr(sec_nport, "load_holdings", boom)
    out = tools.dispatch("get_portfolio", {})
    assert "error" in out and "do not estimate" in out["instruction"]


def test_every_schema_has_a_function():
    assert {s["name"] for s in tools.TOOL_SCHEMAS} == set(tools.TOOL_FUNCTIONS)
