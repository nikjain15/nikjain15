"""One polite HTTP helper shared by every connector.

* Sends a descriptive User-Agent (the SEC requires "name email").
* Waits between requests so we stay well under the SEC's 10 requests/second.
* Raises a clear error instead of returning half a response.
"""

from __future__ import annotations

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

MIN_SECONDS_BETWEEN_CALLS = 0.15      # ~6-7 requests/second at most
_last_call = 0.0


class SourceUnavailable(RuntimeError):
    """A data source could not be reached or returned an error."""


def user_agent() -> str:
    name = os.getenv("SEC_USER_AGENT_NAME", "PM-OS research tool")
    email = os.getenv("SEC_USER_AGENT_EMAIL")
    if not email:
        raise SourceUnavailable("Set SEC_USER_AGENT_EMAIL in .env: the SEC requires a contact email in the User-Agent.")
    return f"{name} {email}"


def get(url: str, params: dict | None = None, timeout: int = 30, needs_user_agent: bool = True) -> requests.Response:
    global _last_call
    wait = MIN_SECONDS_BETWEEN_CALLS - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)
    headers = {"User-Agent": user_agent() if needs_user_agent else "PM-OS research tool",
               "Accept-Encoding": "gzip, deflate"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise SourceUnavailable(f"Could not reach {url}: {exc}") from exc
    finally:
        _last_call = time.time()
    if resp.status_code != 200:
        raise SourceUnavailable(f"{url} returned HTTP {resp.status_code}")
    return resp
