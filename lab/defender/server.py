"""Small read-only HTTP service on the defender container.

Exposes /health, /blocks (active iptables DROP rules), /alerts-recent (a thin
proxy to the api for FE convenience). Doesn't expose any write endpoints —
mutations are owned by flow_streamer.py."""
from __future__ import annotations

import os
import re
import subprocess
from typing import Any

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

API_URL = os.environ.get("AD_API_URL", "http://api:8000")

app = FastAPI(title="AnomalyDetector defender status", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"]
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


_DROP_RE = re.compile(
    r"^\s*\d+\s+DROP\s+(?:\w+)\s+--\s+(?P<src>[\d./]+)\s+(?P<dst>[\d./]+)",
    re.MULTILINE,
)


@app.get("/blocks")
def blocks() -> dict[str, Any]:
    """Returns the raw INPUT chain + a parsed list of DROP sources.

    For the LO demo this is the "proof" page — assessor can see the rule
    landed in the kernel firewall and the attacker IP is in there."""
    try:
        r = subprocess.run(
            ["iptables", "-L", "INPUT", "-n", "--line-numbers"],
            capture_output=True, text=True, check=True, timeout=5,
        )
        raw = r.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc), "raw": "", "dropped": []}

    drops: list[dict[str, str]] = []
    for m in _DROP_RE.finditer(raw):
        drops.append({"source": m.group("src"), "destination": m.group("dst")})
    return {"raw": raw, "dropped": drops, "count": len(drops)}


@app.get("/alerts-recent")
def alerts_recent(limit: int = 50) -> Any:
    """Thin proxy to the api's /alerts so the FE can poll one origin if needed."""
    try:
        r = requests.get(f"{API_URL}/alerts", params={"limit": limit}, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        return {"error": str(exc), "items": []}
