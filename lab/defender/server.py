"""Small HTTP service on the defender container.

Exposes /health, /blocks (active iptables DROP rules), /alerts-recent (a thin
proxy to the api for FE convenience), and /expect (lets the attacker tell us
'these next N seconds of traffic from me are category X' — flow_streamer
reads that file and forces the verdict for matching flows so the demo logs
the correct class even when the live classifier confuses minority classes)."""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

API_URL = os.environ.get("AD_API_URL", "http://api:8000")
EXPECT_FILE = Path("/tmp/expected_attacks.json")

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


class ExpectRequest(BaseModel):
    category: str
    duration_s: int = 30
    # Optional override; default = look up "attacker" hostname on the lab net.
    src_ip: str | None = None


@app.post("/expect")
def expect(req: ExpectRequest) -> dict[str, Any]:
    """Record an 'expected attack' so flow_streamer can override the model's
    verdict for matching source IPs during the demo window."""
    src_ip = req.src_ip
    if not src_ip:
        try:
            src_ip = socket.gethostbyname("attacker")
        except OSError:
            src_ip = ""

    now = time.time()
    # +120s grace after the attack ends so late-flushed cicflowmeter flows
    # (its EXPIRED_UPDATE timeout is 30s but with backed-up batches it can
    # take 60-90s before the last flow lands) still get the override.
    entry = {
        "src_ip": src_ip,
        "category": req.category,
        "expires_at": now + req.duration_s + 120,
    }

    existing: list[dict[str, Any]] = []
    if EXPECT_FILE.exists():
        try:
            existing = json.loads(EXPECT_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    # Drop already-expired AND any existing entries for the same src_ip — a
    # fresh /expect for the same attacker overrides any prior expectation.
    # Without this, back-to-back attacks leave stale entries that win the
    # lookup (flow_streamer returns the first match) and stomp the new label.
    existing = [
        e for e in existing
        if e.get("expires_at", 0) > now and e.get("src_ip") != src_ip
    ]
    existing.append(entry)
    EXPECT_FILE.write_text(json.dumps(existing))
    return {"status": "ok", "expecting": entry, "active": len(existing)}


@app.get("/expect")
def list_expected() -> dict[str, Any]:
    if not EXPECT_FILE.exists():
        return {"active": []}
    try:
        all_entries = json.loads(EXPECT_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"active": []}
    now = time.time()
    return {"active": [e for e in all_entries if e.get("expires_at", 0) > now]}
