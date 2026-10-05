"""Real portfolio: a Fidelity municipal fund's holdings from SEC Form N-PORT.

How it works
------------
1. Ask EDGAR for the trust's filing list:
       https://data.sec.gov/submissions/CIK##########.json
2. Walk its NPORT-P filings newest first. One trust files a separate N-PORT
   for each fund (series), so we open each filing's primary_doc.xml and keep
   the first whose <seriesName> matches the fund we want. Matching on the name
   means we never hardcode a series id we have not verified.
3. Parse every holding (<invstOrSec>) into one row of holdings.csv.
4. Derive price = market value / par x 100 and solve the yield with the engine.

What N-PORT does NOT contain (so we never pretend it does)
----------------------------------------------------------
* Call schedules: bonds are priced to MATURITY unless you add call dates in
  data/user/overrides.csv. For premium callable munis this overstates both
  yield and duration; the tools flag it.
* Credit ratings: the rating-floor check reports "not_available".
* Sector and state: inferred from the issuer name with a keyword list and
  labelled "inferred".
"""

from __future__ import annotations

import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import pandas as pd

from data.connectors import cache
from data.connectors.http import SourceUnavailable, get
from engine import pricing

ASSUMPTIONS_PATH = Path(__file__).resolve().parents[1] / "assumptions.json"
OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "user" / "overrides.csv"

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
FILING_DOC_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/primary_doc.xml"
FILING_INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/"


def load_fund_config(fund_key: str) -> dict:
    funds = json.loads(ASSUMPTIONS_PATH.read_text())["funds"]
    if fund_key not in funds:
        raise KeyError(f"Unknown fund '{fund_key}'. Options: {list(funds)}")
    return funds[fund_key]


# ---------------------------------------------------------------------------
# EDGAR: find the filings
# ---------------------------------------------------------------------------
def list_nport_filings(cik: int) -> list[dict]:
    """All NPORT-P filings for a registrant, newest first."""
    resp = get(SUBMISSIONS_URL.format(cik=cik))
    recent = resp.json()["filings"]["recent"]
    rows = []
    for i, form in enumerate(recent["form"]):
        if form == "NPORT-P":
            rows.append({
                "accession": recent["accessionNumber"][i],
                "filing_date": recent["filingDate"][i],
                "report_date": recent["reportDate"][i],
            })
    return rows


def _strip_ns(xml_text: str) -> ET.Element:
    """Parse XML and drop namespaces so tags read as plain names."""
    root = ET.fromstring(xml_text)
    for el in root.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def fetch_filing_xml(cik: int, accession: str) -> tuple[str, str]:
    url = FILING_DOC_URL.format(cik=cik, acc=accession.replace("-", ""))
    return get(url).text, url


def find_series_filings(cik: int, series_name_contains: str, how_many: int = 1,
                        exclude_words: list[str] | None = None, max_to_scan: int = 80) -> list[dict]:
    """Newest `how_many` NPORT-P filings whose seriesName matches."""
    needle = series_name_contains.lower()
    exclude = [w.lower() for w in (exclude_words or [])]
    found = []
    for filing in list_nport_filings(cik)[:max_to_scan]:
        xml_text, url = fetch_filing_xml(cik, filing["accession"])
        gen = _strip_ns(xml_text).find(".//genInfo")
        name = (gen.findtext("seriesName") or "") if gen is not None else ""
        if needle in name.lower() and not any(w in name.lower() for w in exclude):
            found.append({**filing, "series_name": name, "xml": xml_text, "url": url,
                          "series_id": gen.findtext("seriesId")})
            if len(found) >= how_many:
                break
    if not found:
        raise SourceUnavailable(f"No NPORT-P filing for a series matching '{series_name_contains}' in CIK {cik}")
    return found


# ---------------------------------------------------------------------------
# Parse holdings
# ---------------------------------------------------------------------------
def parse_nport(xml_text: str) -> tuple[dict, pd.DataFrame]:
    """Return (filing info, one row per holding) from an N-PORT primary_doc.xml."""
    root = _strip_ns(xml_text)
    gen = root.find(".//genInfo")
    info = {
        "registrant": gen.findtext("regName"),
        "cik": gen.findtext("regCik"),
        "series_name": gen.findtext("seriesName"),
        "series_id": gen.findtext("seriesId"),
        "period_end": gen.findtext("repPdEnd"),
        "report_date": gen.findtext("repPdDate"),
        "net_assets": _num(root.findtext(".//fundInfo/netAssets")),
    }
    rows = []
    for sec in root.iter("invstOrSec"):
        debt = sec.find("debtSec")
        rows.append({
            "cusip": sec.findtext("cusip"),
            "name": sec.findtext("name"),
            "title": sec.findtext("title"),
            "par": _num(sec.findtext("balance")),
            "units": sec.findtext("units"),
            "market_value": _num(sec.findtext("valUSD")),
            "pct_of_nav": _num(sec.findtext("pctVal")),
            "asset_cat": sec.findtext("assetCat"),
            "issuer_cat": sec.findtext("issuerCat"),
            "fair_value_level": sec.findtext("fairValLevel"),
            "maturity_date": debt.findtext("maturityDt") if debt is not None else None,
            "coupon_kind": debt.findtext("couponKind") if debt is not None else None,
            "coupon": _num(debt.findtext("annualizedRt")) if debt is not None else None,
            "is_default": debt.findtext("isDefault") if debt is not None else None,
        })
    return info, pd.DataFrame(rows)


def _num(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Derived fields: years, price, yield, sector, state
# ---------------------------------------------------------------------------
SECTOR_KEYWORDS = [
    # (sector, keywords) - first match wins, so specific sectors come before GO.
    ("Hospital", ["HOSP", "HEALTH", "MED CTR", "MEDICAL", "HLTH", "CHILDRENS"]),
    ("HigherEd", ["UNIV", "COLLEGE", "HIGHER ED", "EDL FACS", "EDUCATIONAL FAC", "DORM"]),
    ("Airport", ["AIRPORT", "ARPT", "AVIATION", "AIRPT"]),
    ("Transportation", ["TRANSN", "TRANSIT", "TRANSP", "TPK", "TURNPIKE", "TOLL", "HWY", "BRIDGE", "THRUWAY", "PORT AUTH"]),
    ("Utility", ["WTR", "WATER", "SWR", "SEWER", "ELEC", "PWR", "POWER", "UTIL", "GAS", "ENERGY", "WASTEWATER"]),
    ("Housing", ["HSG", "HOUSING", "MTG FIN", "MORTGAGE"]),
    ("SpecialTax", ["SALES TAX", "SPL TAX", "SPECIAL TAX", "INCOME TAX", "DEDICATED TAX", "TAX ALLOC", "LEASE", "COPS", "CTFS PARTN"]),
    ("Education_K12", ["SCH DIST", "SCHOOL DIST", "ISD", "UNI SCH", "SCH BLDG"]),
    ("GO", ["GO ", "GEN OBLIG", "G.O.", " ST ", "COMWLTH", "COMMONWEALTH", "CNTY", "COUNTY", "CITY", "TOWN", "VILLAGE", "TWP"]),
]

US_STATES = ["ALABAMA", "ALASKA", "ARIZONA", "ARKANSAS", "CALIFORNIA", "COLORADO", "CONNECTICUT", "DELAWARE",
             "DISTRICT OF COLUMBIA", "FLORIDA", "GEORGIA", "HAWAII", "IDAHO", "ILLINOIS", "INDIANA", "IOWA",
             "KANSAS", "KENTUCKY", "LOUISIANA", "MAINE", "MARYLAND", "MASSACHUSETTS", "MICHIGAN", "MINNESOTA",
             "MISSISSIPPI", "MISSOURI", "MONTANA", "NEBRASKA", "NEVADA", "NEW HAMPSHIRE", "NEW JERSEY",
             "NEW MEXICO", "NEW YORK", "NORTH CAROLINA", "NORTH DAKOTA", "OHIO", "OKLAHOMA", "OREGON",
             "PENNSYLVANIA", "PUERTO RICO", "RHODE ISLAND", "SOUTH CAROLINA", "SOUTH DAKOTA", "TENNESSEE",
             "TEXAS", "UTAH", "VERMONT", "VIRGINIA", "WASHINGTON", "WEST VIRGINIA", "WISCONSIN", "WYOMING"]


def infer_sector(name: str, title: str) -> str:
    text = f" {name or ''} {title or ''} ".upper()
    for sector, words in SECTOR_KEYWORDS:
        if any(w in text for w in words):
            return sector
    return "Other"


def infer_state(name: str, title: str) -> str:
    text = f"{name or ''} {title or ''}".upper()
    # Longest names first so "WEST VIRGINIA" wins over "VIRGINIA".
    for state in sorted(US_STATES, key=len, reverse=True):
        if re.search(rf"\b{state}\b", text):
            return state.title()
    return "Unknown"


def classify_asset(row) -> str:
    """muni / treasury / floating / cash / other, from N-PORT categories."""
    if row["coupon_kind"] in ("Floating", "Variable"):
        return "floating"                  # VRDNs and floaters reset near par
    if row["issuer_cat"] == "MUN" and row["asset_cat"] == "DBT":
        return "muni"
    if row["issuer_cat"] in ("UST", "USGA"):
        return "treasury"
    if row["asset_cat"] in ("STIV",) or row["units"] not in ("PA",):
        return "cash"
    return "other"


def add_derived_fields(raw: pd.DataFrame, as_of: str) -> pd.DataFrame:
    df = raw.copy()
    as_of_date = date.fromisoformat(as_of)
    df["asset_type"] = df.apply(classify_asset, axis=1)
    df["maturity_years"] = df["maturity_date"].apply(
        lambda d: (date.fromisoformat(d) - as_of_date).days / 365.25 if isinstance(d, str) and d else None)
    df["price"] = df["market_value"] / df["par"] * 100.0
    df["sector"] = [infer_sector(n, t) for n, t in zip(df["name"], df["title"])]
    df["state"] = [infer_state(n, t) for n, t in zip(df["name"], df["title"])]
    df["call_years"] = None              # not in N-PORT; see overrides.csv
    df["call_price"] = 100.0

    def solve(r):
        if r["asset_type"] != "muni" or not r["maturity_years"] or r["maturity_years"] <= 0 or r["coupon"] is None:
            return r["coupon"] if r["asset_type"] == "floating" else None
        return pricing.yield_to_worst(r["price"], r["coupon"], r["maturity_years"])

    df["yield"] = df.apply(solve, axis=1)
    df["bond_id"] = df["cusip"].fillna(df["name"])
    df["emma_url"] = df["cusip"].apply(
        lambda c: f"https://emma.msrb.org/QuickSearch/Results?quickSearchText={c}" if isinstance(c, str) else None)
    return df


def apply_overrides(df: pd.DataFrame) -> pd.DataFrame:
    """Merge user-supplied call dates / ratings / cost basis by CUSIP, if any."""
    if not OVERRIDES_PATH.exists():
        return df
    ov = pd.read_csv(OVERRIDES_PATH, dtype={"cusip": str})
    df = df.copy()
    as_of = df.attrs.get("as_of")
    for _, o in ov.iterrows():
        mask = df["cusip"] == o["cusip"]
        if not mask.any():
            continue
        if "call_date" in o and isinstance(o["call_date"], str) and as_of:
            df.loc[mask, "call_years"] = (date.fromisoformat(o["call_date"]) - date.fromisoformat(as_of)).days / 365.25
        for col in ("call_price", "rating", "cost_price", "sector", "state"):
            if col in o and pd.notna(o[col]):
                df.loc[mask, col] = o[col]
    # Re-solve yields now that some bonds have calls.
    has_call = df["call_years"].notna() & (df["asset_type"] == "muni")
    for i in df[has_call].index:
        r = df.loc[i]
        df.loc[i, "yield"] = pricing.yield_to_worst(r["price"], r["coupon"], r["maturity_years"],
                                                    r["call_years"], r["call_price"])
    return df


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
def refresh_holdings(fund_key: str = "intermediate_muni", prior_lookback: int = 4) -> dict:
    """Fetch latest N-PORT (and an older one for cost basis); cache holdings.csv.

    `prior_lookback` = how many filings back to take the "purchase" price from
    (4 quarterly filings ~ one year).
    """
    cfg = load_fund_config(fund_key)
    filings = find_series_filings(cfg["cik"], cfg["series_name_contains"], how_many=prior_lookback + 1,
                                  exclude_words=cfg.get("exclude_words"))
    latest = filings[0]
    info, raw = parse_nport(latest["xml"])
    holdings = add_derived_fields(raw, info["period_end"])

    prior_note = "No prior filing found; cost basis unavailable."
    if len(filings) > 1:
        prior = filings[-1]
        prior_info, prior_raw = parse_nport(prior["xml"])
        prior_raw["prior_price"] = prior_raw["market_value"] / prior_raw["par"] * 100.0
        holdings = holdings.merge(prior_raw[["cusip", "prior_price"]].dropna().drop_duplicates("cusip"),
                                  on="cusip", how="left")
        holdings["cost_price"] = holdings["prior_price"]
        holdings["cost_source"] = f"N-PORT price at {prior_info['period_end']}"
        holdings["years_held"] = (date.fromisoformat(info["period_end"]) -
                                  date.fromisoformat(prior_info["period_end"])).days / 365.25
        prior_note = f"Cost basis = price in N-PORT for period ending {prior_info['period_end']} ({prior['url']})."

    holdings.attrs["as_of"] = info["period_end"]
    holdings = apply_overrides(holdings)

    buf = io.StringIO()
    holdings.to_csv(buf, index=False)
    meta = cache.save(f"holdings_{fund_key}", buf.getvalue(), latest["url"], "csv", as_of=info["period_end"],
                      notes=f"{info['registrant']} / {info['series_name']} (series {info['series_id']}), "
                            f"filed {latest['filing_date']}. {prior_note}")
    cache.save(f"nport_{fund_key}_latest", latest["xml"], latest["url"], "xml", as_of=info["period_end"])
    return {"meta": meta, "info": info, "rows": int(len(holdings))}


def load_holdings(fund_key: str = "intermediate_muni") -> tuple[pd.DataFrame, dict]:
    """Cached holdings plus provenance. Raises if nothing has been fetched yet."""
    path = cache.path_for(f"holdings_{fund_key}")
    if path is None:
        raise SourceUnavailable(
            f"No cached holdings for '{fund_key}'. Run `pm-os refresh` (needs access to sec.gov).")
    df = pd.read_csv(path, dtype={"cusip": str})
    meta = cache.load_meta(f"holdings_{fund_key}")
    df.attrs["as_of"] = meta["as_of"]
    return df, meta


def sma_sample(holdings: pd.DataFrame, n_bonds: int = 30, account_size: float = 1_500_000,
               min_lot: float = 25_000, max_lot: float = 125_000, max_maturity: float = 15.0) -> pd.DataFrame:
    """Pick an SMA-sized account from the real holdings.

    Deterministic, so the demo is repeatable: keep fixed-rate munis with a
    solved yield; within each sector, line bonds up so maturity buckets
    alternate (largest position first); then deal one bond per sector in turn,
    biggest sectors first, until we have `n_bonds`. That spreads the account
    across sectors AND maturities, like a laddered SMA.
    Prices, coupons and yields stay REAL; only the par per bond is an
    SMA sizing assumption (equal weight, rounded to $5k odd lots).
    """
    df = holdings[(holdings["asset_type"] == "muni") & holdings["yield"].notna()
                  & (holdings["maturity_years"] > 0.5) & (holdings["maturity_years"] <= max_maturity)].copy()
    df["bucket"] = pd.cut(df["maturity_years"], bins=[0, 2, 4, 6, 8, 10, 15], labels=False)
    df = df.sort_values("market_value", ascending=False)
    df["rank_in_bucket"] = df.groupby(["sector", "bucket"]).cumcount()

    queues = []          # one ordered list of bonds per sector
    for sector in df.groupby("sector")["market_value"].sum().sort_values(ascending=False).index:
        g = df[df["sector"] == sector].sort_values(["rank_in_bucket", "bucket"])
        queues.append([row for _, row in g.iterrows()])

    picks, i = [], 0
    while len(picks) < n_bonds and any(i < len(q) for q in queues):
        for q in queues:
            if i < len(q) and len(picks) < n_bonds:
                picks.append(q[i])
        i += 1
    sample = pd.DataFrame(picks).drop(columns=["bucket", "rank_in_bucket"]).reset_index(drop=True)
    lot = min(max(round(account_size / max(len(sample), 1) / 5_000) * 5_000, min_lot), max_lot)
    sample["fund_par"] = sample["par"]
    sample["par"] = float(lot)
    sample.attrs = holdings.attrs
    return sample


def holdings_summary(df: pd.DataFrame) -> dict:
    """Quick printable summary used by `pm-os refresh`."""
    munis = df[df["asset_type"] == "muni"]
    return {
        "as_of": df.attrs.get("as_of"),
        "lines": int(len(df)),
        "muni_bonds": int(len(munis)),
        "market_value": round(float(df["market_value"].sum()), 0),
        "asset_type_mix": df.groupby("asset_type")["market_value"].sum().div(df["market_value"].sum()).round(4).to_dict(),
        "muni_yield_median_pct": round(float(munis["yield"].median()), 3) if len(munis) else None,
        "sector_mix_inferred": munis.groupby("sector")["market_value"].sum().div(munis["market_value"].sum()).round(4).to_dict(),
    }
