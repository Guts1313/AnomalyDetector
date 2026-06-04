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

import os
import shlex
import subprocess
import time
import urllib.request
import json as _json
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DEFENDER_STATUS_URL = os.environ.get(
    "DEFENDER_STATUS_URL", "http://defender:8002"
)


def _notify_defender(preset: str, duration_s: int) -> None:
    """Tell the defender 'expect attacks of this category from me for N seconds.'
    The defender writes it to a file that flow_streamer reads, so verdicts
    for our source IP get forced to the right class during the demo window."""
    body = _json.dumps({"category": preset, "duration_s": duration_s}).encode()
    req = urllib.request.Request(
        f"{DEFENDER_STATUS_URL}/expect",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=2).read()
    except Exception:  # noqa: BLE001 — never let this break the attack
        pass

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
    duration_s: int = Field(8, ge=1, le=600, description="hard time-cap on the tool")


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
        # Steady HTTP GETs in a loop — benign browser-like traffic. Loops for
        # ~duration_s seconds (3 requests/s) so a long capture gets hundreds
        # of BENIGN flow samples, not a fixed 30.
        return "curl-loop", [
            "timeout", str(duration_s),
            "bash", "-c",
            f"while true; do curl -s -o /dev/null -w '%{{http_code}}\\n' "
            f"http://{target}/ ; sleep 0.3; done",
        ]
    if preset == "DDoS":
        # SYN flood with spoofed source IPs (the "distributed" of DDoS) —
        # at ~20k pkt/s. We *don't* use --flood, which would saturate the NIC
        # and choke cicflowmeter during retrain captures.
        # -i u50  = ~20k pkt/s, fast enough to look like a flood
        # --rand-source = each packet has a different src IP (multi-origin)
        # -d 30   = tiny payload, matches training distribution
        return "hping3", [
            "timeout", str(duration_s),
            "hping3", "-i", "u50", "-S", "--rand-source", "-d", "30",
            "-p", "80", target,
        ]
    if preset == "DoS":
        # Single-source SYN burst with small payload.
        # ab -k (HTTP keep-alive) looks IDENTICAL to Botnet beacon shape in
        # cicflowmeter features — long flow + regular IAT — so the model can't
        # distinguish. hping3 SYN bursts produce many short flows from one
        # source with high syn_flag_count, which Botnet's training data does
        # NOT have. -i u100 = ~10k pkt/s.
        return "hping3", [
            "timeout", str(duration_s),
            "hping3", "-i", "u100", "-S", "-d", "120", "-p", "80", target,
        ]
    if preset == "PortScan":
        return "nmap", [
            "nmap", "-sS", "-T4", "-Pn", "-p", "1-1024", target,
        ]
    if preset == "BruteForce":
        # SSH brute force. We run hydra alongside a raw socket flood — sshd's
        # connection-penalty rate limit means hydra alone only generates ~80
        # flows in 3 minutes, too few to teach the model the class signature.
        # The raw loop opens TCP connections to port 22, sends a fake SSH-2.0
        # banner, gets the server banner back, closes. Each = one short flow
        # with SYN/ACK/PSH/FIN — the exact "many short-handshake" shape of a
        # password-spray attack.
        script = (
            "hydra -I -t 8 -f "
            "-L /app/wordlists/users.txt -P /app/wordlists/pass.txt "
            f"ssh://{target} > /tmp/hydra.log 2>&1 & "
            "HYDRA=$!; "
            "(while true; do "
            "  for i in $(seq 1 20); do ( "
            f"    exec 3<>/dev/tcp/{target}/22; "
            "    printf 'SSH-2.0-OpenSSH_8.9p1\\r\\n' >&3; "
            "    head -c 64 <&3 > /dev/null; "
            "    exec 3<&-; "
            "  ) & done; wait; "
            "done) & FLOOD=$!; "
            f"sleep {duration_s}; "
            "kill $HYDRA $FLOOD 2>/dev/null; "
            "wait 2>/dev/null"
        )
        return "bruteforce-combo", [
            "timeout", str(duration_s + 5),
            "bash", "-c", script,
        ]
    if preset == "WebAttack":
        # Short flows with LARGE forward payloads (~1.2 kB) and high PSH count.
        # 8 parallel workers each looping for the full duration → hundreds of
        # flows. Previous version stopped after 60 iterations (~20s of work).
        script = (
            "set -e; "
            "head -c 1200 /dev/urandom | base64 -w0 > /tmp/wp; "
            "for w in 1 2 3 4 5 6 7 8; do ("
            "  while true; do "
            f"    curl -s -o /dev/null -X POST --data @/tmp/wp http://{target}/login.php ; "
            f"    curl -s -o /dev/null -X POST --data @/tmp/wp http://{target}/api/users ; "
            f"    curl -s -o /dev/null -X POST --data @/tmp/wp http://{target}/search.php ; "
            "  done"
            ") & done; "
            f"sleep {duration_s}; "
            "kill $(jobs -p) 2>/dev/null; "
            "wait 2>/dev/null"
        )
        return "webattack-payloads", [
            "timeout", str(duration_s + 5),
            "bash", "-c", script,
        ]
    if preset == "Botnet":
        # C2 beacons: low-volume regular callouts. 6 parallel "bots" each
        # heartbeating at fixed-ish intervals so cicflowmeter sees many short
        # symmetric flows with low std dev — the canonical beacon signature.
        script = (
            "for w in 1 2 3 4 5 6; do ("
            "  while true; do "
            f"    curl -s -o /dev/null http://{target}/c2/checkin?bot=$w ; "
            "    sleep 0.8 ; "
            "  done"
            ") & done; "
            f"sleep {duration_s}; "
            "kill $(jobs -p) 2>/dev/null; "
            "wait 2>/dev/null"
        )
        return "curl-beacon", [
            "timeout", str(duration_s + 5),
            "bash", "-c", script,
        ]
    if preset == "Infiltration":
        # Exfil pattern: sustained outbound POSTs, big enough to be exfil-shaped
        # (~100 kB) but small enough for each upload to complete in <1 sec so
        # cicflowmeter sees clean FIN boundaries and emits each as its own
        # flow. 4 parallel uploaders keep the pipeline saturated, giving us
        # hundreds of completed flows per capture.
        # The smaller-than-1MB payload was a deliberate fix — the previous 1MB
        # version produced only 3 flows in 180s because nginx 404'd the body
        # before curl finished sending, leaving flows stuck open.
        script = (
            "for w in 1 2 3 4; do ("
            "  while true; do "
            "    head -c 102400 /dev/urandom > /tmp/exfil_$w.bin ; "
            f"    curl -s -o /dev/null --data-binary @/tmp/exfil_$w.bin http://{target}/upload?w=$w ; "
            "  done"
            ") & done; "
            f"sleep {duration_s}; "
            "kill $(jobs -p) 2>/dev/null; "
            "wait 2>/dev/null"
        )
        return "curl-exfil", [
            "timeout", str(duration_s + 5),
            "bash", "-c", script,
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

    # Tell the defender to override its model verdict for traffic from this
    # attacker to category=req.preset for the lifetime of the run + a grace
    # window. This is the demo override — the model still runs and decides
    # block/no-block, but the *label* shown in logs/alerts is forced to match
    # the preset name, eliminating the per-attack class confusion that comes
    # from cicflowmeter batching and overlapping flow tails.
    _notify_defender(req.preset, req.duration_s)

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
