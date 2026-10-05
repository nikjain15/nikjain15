"""Optional Streamlit front end over the same tools and agent as the CLI.

    streamlit run app.py

Left: portfolio + guideline lights. Center: PM chat. Right: audit trail.
Tabs for scenario presets, the "teach me" pricing walk-through and the data
provenance / assumptions panel.
"""

from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from agent import tools

st.set_page_config(page_title="PM-OS: Fixed Income SMA Analyst", layout="wide")

GAIN, LOSS = "#2a78d6", "#e34948"         # validated diverging pair (blue gain / red loss)
SUGGESTED = [
    "What happens if rates rise 100bp?",
    "Are we inside our duration band?",
    "Which bonds should we harvest for tax losses?",
    "A client needs $150k next month. What do we sell?",
    "What's the muni/Treasury ratio doing, and why does it matter for us?",
    "Replay the last 3 months of Treasury curve moves on this portfolio.",
]
SCENARIOS = {
    "+100bp parallel": ("parallel", {"bp": 100}),
    "-100bp parallel": ("parallel", {"bp": -100}),
    "Bear steepener": ("curve", {"preset": "bear_steepener"}),
    "Bull flattener": ("curve", {"preset": "bull_flattener"}),
    "Muni ratio +40bp": ("muni_ratio", {"bp": 40}),
    "Credit stress": ("credit", {"preset": "revenue_stress"}),
}

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("PM-OS")
    st.caption("Independent analysis of PUBLIC filings. Not a Fidelity product.")
    fund = st.selectbox("Fund filing", ["intermediate_muni", "limited_term_muni"])
    view = st.radio("Portfolio", ["sma", "fund"],
                    format_func=lambda v: "SMA sample (30 real bonds)" if v == "sma" else "Full fund")
    cheap = st.toggle("Cheaper model", value=False)
    teach = st.toggle("Teach me (show the math)", value=False)
    if st.button("Refresh data from SEC / Treasury"):
        st.json(tools.refresh_data(fund))

portfolio_out = tools.dispatch("get_portfolio", {"view": view, "fund": fund})
if "error" in portfolio_out:
    st.error(f"Portfolio data unavailable: {portfolio_out['error']}")
    st.info("Run `pm-os refresh` (needs access to sec.gov and home.treasury.gov). PM-OS never fills gaps with invented numbers.")

tab_ask, tab_scen, tab_teach, tab_data = st.tabs(["Ask", "Scenarios", "Teach me", "Data & assumptions"])


def guideline_lights():
    g = tools.dispatch("check_guidelines", {"view": view, "fund": fund})
    if "error" in g:
        return
    icon = {"ok": "🟢", "breach": "🔴", "flag": "🟡", "not_available": "⚪"}
    for c in g["checks"]:
        st.write(f"{icon.get(c['status'], '⚪')} {c['detail']}")


# ---------------------------------------------------------------- ask tab
with tab_ask:
    left, center, right = st.columns([1.2, 1.6, 1.0])

    with left:
        st.subheader("Portfolio")
        if "error" not in portfolio_out:
            s = portfolio_out["summary"]
            st.caption(f"As of {portfolio_out['as_of']} · [source]({portfolio_out['source_url']})")
            a, b, c = st.columns(3)
            a.metric("Market value", f"${s['market_value']:,.0f}")
            b.metric("Duration", f"{s['duration']:.2f}")
            c.metric("YTW / TEY", f"{s['yield_to_worst_pct']:.2f}% / {s['tax_equivalent_yield_pct']:.2f}%")
            cols = ["bond_id", "name", "sector", "market_value", "weight", "yield", "duration", "priced_to"]
            st.dataframe(pd.DataFrame(portfolio_out["holdings"])[cols], hide_index=True, height=320)
            st.markdown("**Guidelines** (assumed limits)")
            guideline_lights()
            for note in portfolio_out.get("caveats", []):
                st.caption(f"⚠ {note}")

    with center:
        st.subheader("Ask the analyst")
        chip_cols = st.columns(2)
        clicked = None
        for i, q in enumerate(SUGGESTED):
            if chip_cols[i % 2].button(q, key=f"chip{i}"):
                clicked = q
        question = st.chat_input("Ask about the portfolio...") or clicked

        if "agent" not in st.session_state or st.session_state.get("cheap") != cheap:
            try:
                from agent.loop import MODELS, PMAgent
                st.session_state.agent = PMAgent(model=MODELS["cheap"] if cheap else None)
                st.session_state.cheap = cheap
                st.session_state.history = []
            except RuntimeError as exc:
                st.warning(str(exc))
        context = f"(Use view='{view}', fund='{fund}' in tool calls.) "
        if teach:
            context += ("(Teach mode: after the answer, walk through how the key number was derived, using "
                        "price_bond's cash-flow table for one representative bond.) ")
        if question and "agent" in st.session_state:
            with st.spinner("Running tools and searching..."):
                result = st.session_state.agent.ask(context + question)
            st.session_state.history.append((question, result))
        for q, r in reversed(st.session_state.get("history", [])):
            st.chat_message("user").write(q)
            st.chat_message("assistant").markdown(r.answer)

    with right:
        st.subheader("Audit trail")
        history = st.session_state.get("history", [])
        if history:
            r = history[-1][1]
            for step in r.audit_trail:
                with st.expander(f"🔧 {step['tool']}  ·  as of {step['output'].get('as_of')}"):
                    st.code(json.dumps(step["input"], indent=1), language="json")
                    st.json(step["output"], expanded=False)
            for q in r.web_searches:
                st.write(f"🔎 {q}")
            st.markdown("**Sources**")
            for src in r.sources:
                mark = "✅" if src["cited"] else "·"
                st.markdown(f"{mark} [{src['title']}]({src['url']})")
        else:
            st.caption("Tool calls, inputs, outputs and web sources appear here.")

# ---------------------------------------------------------------- scenario tab
with tab_scen:
    st.subheader("Scenario presets (full reprice of every bond)")
    choice = st.radio("Scenario", list(SCENARIOS), horizontal=True)
    stype, params = SCENARIOS[choice]
    res = tools.dispatch("run_scenario", {"type": stype, "params": params, "view": view, "fund": fund})
    if "error" in res:
        st.error(res["error"])
    else:
        a, b, c = st.columns(3)
        pnl = res["total_pnl"]
        a.metric("Total P&L", f"{'-' if pnl < 0 else '+'}${abs(pnl):,.0f}", f"{res['total_pnl_pct']:.2f}%")
        b.metric("Duration", f"{res['duration_after']:.2f}", f"{res['duration_after'] - res['duration_before']:+.2f}")
        c.metric("Guideline breaches", len(res["guidelines_after"]["breaches"]) or "None")
        bonds = pd.DataFrame(res["by_bond"]).sort_values("pnl")
        fig = go.Figure(go.Bar(
            x=bonds["pnl"], y=bonds["bond_id"].astype(str), orientation="h",
            marker_color=[GAIN if v >= 0 else LOSS for v in bonds["pnl"]],
            hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
        ))
        fig.update_layout(title=f"P&L by bond: {choice}", xaxis_title="P&L ($)", height=max(320, 18 * len(bonds)),
                          margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
        fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", zerolinecolor="rgba(128,128,128,0.5)")
        st.plotly_chart(fig, width="stretch")
        st.markdown("**Before / after**")
        st.dataframe(bonds[["bond_id", "sector", "shift_bp", "price_before", "price_after", "priced_to_before",
                            "priced_to_after", "duration_before", "duration_after", "pnl", "below_de_minimis_after"]],
                     hide_index=True)
        if res.get("call_flips"):
            st.warning(f"Call flips (priced-to date changed): {', '.join(map(str, res['call_flips']))}")
        st.caption(f"As of {res['as_of']} · {res['data_label']}")

# ---------------------------------------------------------------- teach tab
with tab_teach:
    st.subheader("How a bond price is built")
    st.caption("Price = Σ CF / (1 + y/2)^(2t). Callable bonds take the LOWER of price-to-call and price-to-maturity.")
    c1, c2, c3, c4 = st.columns(4)
    coupon = c1.number_input("Coupon %", value=4.0, step=0.125)
    yld = c2.number_input("Yield %", value=3.45, step=0.05)
    mat = c3.number_input("Maturity (yrs)", value=12.0, step=0.5)
    call = c4.number_input("Call (yrs, 0 = none)", value=8.0, step=0.5)
    out = tools.dispatch("price_bond", {"coupon": coupon, "yield_pct": yld, "maturity_years": mat,
                                        "call_years": call or None})
    a, b, c, d = st.columns(4)
    a.metric("Price", f"{out['price']:.4f}")
    b.metric("Priced to", f"{out['priced_to']} ({out['redemption_years']}y)")
    c.metric("Modified duration", f"{out['modified_duration']:.3f}")
    d.metric("De minimis line", f"{out['de_minimis_threshold']:.2f}")
    st.dataframe(pd.DataFrame(out["cash_flows"]), hide_index=True)
    st.caption(f"Price to maturity {out['price_to_maturity']} vs. price to call {out['price_to_call']}: "
               "the lower one is the price a buyer will pay.")

# ---------------------------------------------------------------- data tab
with tab_data:
    status = tools.dispatch("data_status", {})
    st.subheader("Data provenance")
    st.dataframe(pd.DataFrame(status["cache"]), hide_index=True)
    st.subheader("Assumptions (the only non-observed inputs)")
    st.json(status["assumptions"])
