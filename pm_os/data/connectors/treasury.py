"""Real rates: U.S. Treasury daily par yield curve (no API key needed).

Source: home.treasury.gov "Daily Treasury Par Yield Curve Rates", one CSV per
calendar year. Columns look like "1 Mo", "3 Mo", "1 Yr", "10 Yr" ...; we turn
each label into a maturity in years so the rest of the code can interpolate.
"""

from __future__ import annotations

import io
import re
from datetime import date

import numpy as np
import pandas as pd

from data.connectors import cache
from data.connectors.http import SourceUnavailable, get

CSV_URL = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
           "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
           "&field_tdr_date_value={year}&page&_format=csv")


def label_to_years(label: str) -> float | None:
    """'3 Mo' -> 0.25, '1.5 Month' -> 0.125, '10 Yr' -> 10.0, 'Date' -> None."""
    m = re.match(r"\s*([\d.]+)\s*(Mo|Month|Yr|Year)", label, re.IGNORECASE)
    if not m:
        return None
    n = float(m.group(1))
    return n / 12.0 if m.group(2).lower().startswith("mo") else n


def parse_curve_csv(text: str) -> pd.DataFrame:
    """Long table: date, tenor_label, years, yield_pct."""
    wide = pd.read_csv(io.StringIO(text))
    wide["Date"] = pd.to_datetime(wide["Date"])
    long = wide.melt(id_vars="Date", var_name="tenor", value_name="yield_pct").dropna()
    long["years"] = long["tenor"].apply(label_to_years)
    long = long.dropna(subset=["years"]).rename(columns={"Date": "date"})
    return long.sort_values(["date", "years"]).reset_index(drop=True)


def refresh_curve(years: list[int] | None = None) -> dict:
    """Download the given calendar years (default: this year and last)."""
    this_year = date.today().year
    years = years or [this_year - 1, this_year]
    frames, urls = [], []
    for y in years:
        url = CSV_URL.format(year=y)
        try:
            frames.append(parse_curve_csv(get(url, needs_user_agent=False).text))
            urls.append(url)
        except SourceUnavailable:
            if y == this_year:
                raise
    curve = pd.concat(frames).drop_duplicates(["date", "tenor"]).sort_values(["date", "years"])
    as_of = curve["date"].max().date().isoformat()
    meta = cache.save("treasury_curve", curve.to_csv(index=False), " | ".join(urls), "csv", as_of=as_of,
                      notes="U.S. Treasury daily par yield curve rates")
    return {"meta": meta, "days": int(curve["date"].nunique())}


def load_curve() -> tuple[pd.DataFrame, dict]:
    path = cache.path_for("treasury_curve")
    if path is None:
        raise SourceUnavailable("No cached Treasury curve. Run `pm-os refresh` (needs access to home.treasury.gov).")
    df = pd.read_csv(path, parse_dates=["date"])
    return df, cache.load_meta("treasury_curve")


def curve_on(df: pd.DataFrame, on: str | None = None) -> pd.DataFrame:
    """The curve on a date (latest on/before `on`; default the latest date)."""
    dates = df["date"].drop_duplicates().sort_values()
    target = dates.iloc[-1] if on is None else dates[dates <= pd.Timestamp(on)].iloc[-1]
    return df[df["date"] == target][["tenor", "years", "yield_pct"]].reset_index(drop=True).assign(
        date=target.date().isoformat())


def yield_at(curve: pd.DataFrame, years: float) -> float:
    """Linear interpolation of one day's curve at a maturity."""
    return float(np.interp(years, curve["years"], curve["yield_pct"]))


def curve_change(df: pd.DataFrame, start: str, end: str | None = None) -> dict:
    """bp change at each tenor between two dates: a ready-made 'curve' scenario."""
    a, b = curve_on(df, start), curve_on(df, end)
    merged = a.merge(b, on=["tenor", "years"], suffixes=("_start", "_end"))
    merged["change_bp"] = (merged["yield_pct_end"] - merged["yield_pct_start"]) * 100
    return {
        "start_date": a["date"].iloc[0],
        "end_date": b["date"].iloc[0],
        "shifts_bp": {round(float(r.years), 4): round(float(r.change_bp), 1) for r in merged.itertuples()},
        "table": merged.round(4).to_dict("records"),
    }
