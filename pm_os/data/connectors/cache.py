"""Disk cache for every fetched dataset.

Each dataset is stored as two files in data/cache/:

    <name>.<ext>        the content (CSV, XML, JSON ...)
    <name>.meta.json    {"source_url", "fetched_at", "as_of", "notes"}

so the UI and the agent can always say WHERE a number came from and WHEN.
If a live fetch fails we fall back to the last cached copy and say so; we
never fill a gap with made-up data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[1] / "cache"


def _paths(name: str, ext: str) -> tuple[Path, Path]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{name}.{ext}", CACHE_DIR / f"{name}.meta.json"


def save(name: str, content: str | bytes, source_url: str, ext: str,
         as_of: str | None = None, notes: str | None = None) -> dict:
    """Write content plus its provenance; returns the metadata."""
    data_path, meta_path = _paths(name, ext)
    mode = "wb" if isinstance(content, bytes) else "w"
    with open(data_path, mode) as f:
        f.write(content)
    meta = {
        "name": name,
        "file": data_path.name,
        "source_url": source_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": as_of,
        "notes": notes,
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta


def load_meta(name: str) -> dict | None:
    meta_path = CACHE_DIR / f"{name}.meta.json"
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text())


def path_for(name: str) -> Path | None:
    """Path of the cached content file, or None if nothing is cached."""
    meta = load_meta(name)
    if not meta:
        return None
    p = CACHE_DIR / meta["file"]
    return p if p.exists() else None


def status() -> list[dict]:
    """Provenance of everything in the cache (for the 'as of' panel)."""
    if not CACHE_DIR.exists():
        return []
    return [json.loads(p.read_text()) for p in sorted(CACHE_DIR.glob("*.meta.json"))]
