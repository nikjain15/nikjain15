"""Optional: Treasury constant-maturity yields from FRED (free API key).

Useful for long history (e.g. replaying the 2022 selloff) without pulling
many Treasury CSV years. Needs FRED_API_KEY in .env; skipped if absent.
"""

from __future__ import annotations

import os

import pandas as pd

from data.connectors import cache
from data.connectors.http import SourceUnavailable, get

SERIES = {"DGS1": 1, "DGS2": 2, "DGS5": 5, "DGS10": 10, "DGS30": 30}
URL = "https://api.stlouisfed.org/fred/series/observations"


def refresh_fred(start: str = "2021-01-01") -> dict:
    key = os.getenv("FRED_API_KEY")
    if not key:
        raise SourceUnavailable("FRED_API_KEY not set in .env (optional source).")
    frames = []
    for series, years in SERIES.items():
        resp = get(URL, params={"series_id": series, "api_key": key, "file_type": "json",
                                "observation_start": start}, needs_user_agent=False)
        obs = pd.DataFrame(resp.json()["observations"])
        obs = obs[obs["value"] != "."]
        frames.append(pd.DataFrame({"date": obs["date"], "tenor": series, "years": years,
                                    "yield_pct": obs["value"].astype(float)}))
    df = pd.concat(frames).sort_values(["date", "years"])
    # The public URL (without the key) is what we record as the source.
    meta = cache.save("fred_curve", df.to_csv(index=False), f"{URL}?series_id={','.join(SERIES)}", "csv",
                      as_of=df["date"].max(), notes="FRED constant-maturity Treasury yields")
    return {"meta": meta, "rows": int(len(df))}
