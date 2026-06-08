# Attack scenarios

**Phase:** Design & Implement · **Sprint 2**

Each scenario is one attack category the detector must recognise. In the
attack/defend lab (`lab/`), a preset on the frontend's Request-examples tab
launches the matching **real** offensive tool against the defender container;
the traffic shape it produces is what the model must classify back into the same
category. This is what makes the lab an end-to-end test rather than a scripted
animation. See `flowcharts/attack_defend_sequence.png` for the runtime loop.

## Scenario catalogue

| # | Category | Tool | Argv (essence) | Flow signature the model keys on | MITRE / STRIDE |
|---|---|---|---|---|---|
| 1 | BENIGN | curl (loop) | steady HTTP GETs, ~3/s | balanced rates, normal packet sizes, healthy handshake | baseline |
| 2 | DDoS | hping3 | `-S --rand-source -p 80` | very high packets/s, spoofed sources, high SYN-flag count | T1498/T1499 · DoS |
| 3 | DoS | hping3 | `-S -p 80` (single source) | high SYN burst from one source, lower total volume | T1499 · DoS |
| 4 | PortScan | nmap | `-sS -T4 -Pn -p 1-1024` | many short SYN-scan flows to sequential ports | T1046 · Recon |
| 5 | BruteForce | hydra + raw SSH banner loop | `ssh://target` :22 | many short SSH handshakes (SYN/ACK/PSH/FIN), password spray | T1110 · Spoofing/EoP |
| 6 | WebAttack | curl POST payloads / sqlmap | large fwd payloads to `/login.php`, `/search.php` | short flows, large forward payload, high PSH count | T1190 · Tampering |
| 7 | Botnet | curl beacon (6 "bots") | `/c2/checkin` every ~0.8s | low-rate, regular call-outs, low inter-arrival variance | T1071 · C2 |
| 8 | Infiltration | curl --data-binary exfil | sustained outbound POST (~100 kB) | sustained outbound data, otherwise benign-shaped | T1041 · Exfiltration |

## Expected detector behaviour

- **High-signal categories** (DDoS, DoS, PortScan, BruteForce, Botnet) are
  expected to be recognised with high confidence (≥0.99 F1 in evaluation).
- **WebAttack** is harder (encrypted/variable payloads) — ~0.95 F1.
- **Infiltration** is *by design* hard: it mimics normal traffic, so flow-level
  statistics alone are weak (≈0.35 F1). The recommended control is to pair the
  detector with a signature IDS — documented honestly rather than hidden.

## Defensive response (in the lab)

When a flow is classified as an attack with score ≥ 0.7, the defender installs
an `iptables -A INPUT -s <attacker_ip> -j DROP` rule; subsequent probes from
that source time out (observable proof) and the verdict appears as a
severity-coloured row in the analyst's Alerts tab. The block has a short TTL —
a demo safety net, not a production persistence policy.

## Trust boundary

The defender needs `NET_RAW` (tcpdump) and `NET_ADMIN` (iptables), scoped to the
container's own network namespace so the host firewall is never touched. Full
threat analysis is in [Threat_Model.md](Threat_Model.md).
