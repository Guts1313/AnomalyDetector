# Advisory report

**Phase:** Sprint 4 · Final delivery

Advice to the (hypothetical) client deploying the Network Traffic Anomaly
Detector in a SOC/NOC, separated — per the offensive-security learning outcome —
into physical, technical and organisational improvements. The full risk basis is
in `evidence/LO1_Offensive_Security.md` and the Research Report's threat model.

## Executive summary

The detector is **production-ready for high-volume, high-signal attack classes**
(DoS, DDoS, PortScan, BruteForce, Botnet — all ≥0.99 F1) at sub-millisecond
latency and a <1% analyst-visible false-positive rate. It has one **named blind
spot — infiltration** (F1 0.35) — intrinsic to flow-level detection. The advice
below makes the system deployable and closes that gap with complementary
controls.

## Physical

- Co-locate the detector and the PCAP-capture appliances in the **same security
  zone** to keep flow features on-LAN and limit exposure of the audit store.
- Restrict console access to the host to **dual-control** (badge + smart card),
  per ISO 27002 control 7.2.

## Technical

1. Deploy the API behind an **authenticated reverse proxy** (nginx/traefik) that
   terminates TLS and enforces a per-analyst API key.
2. Mount `models/` **read-only** in production and promote model bundles through
   a **signed** package channel (mitigates model-tampering, STRIDE T2).
3. **Pair with a signature IDS** (Suricata + ET Open) to cover the infiltration
   gap measured in SRQ6.
4. Enable **rate-limiting** at the proxy to cap the oversized-batch DoS risk (T5).
5. Stream the `/alerts` feed into the **SIEM** (Splunk/Elastic) with a
   correlation rule on `severity = critical`.

## Organisational

1. Document a **per-severity response runbook** (drafted in the threat model §6).
2. Schedule **bi-monthly retraining + drift review**: run `scripts/train.py`,
   review the comparison matrix, then `POST /admin/reload`.
3. Run a **quarterly purple-team exercise** feeding adversarial flows through
   `/predict` and measure detection-rate decay against the baseline matrix.
4. Record the ethical posture in the privacy register: **no payload inspection**,
   IPs pseudonymised — supporting GDPR/AVG compliance.

## Residual risk to accept or treat

| Risk | Severity | Recommended treatment |
|---|---|---|
| Model evasion / infiltration blind spot | Critical | Pair with signature IDS + TLS-metadata sub-classifier |
| Encrypted-traffic blind spot | High | Complementary TLS-metadata heuristics |
| Oversized-batch DoS | Medium | Upstream rate-limit |
| Model/dataset tampering | Medium | Read-only mount + signed hashes |

The detector should be positioned as the **detect** layer of a defence-in-depth
stack — combined with prevention (firewall) and response (SOAR) controls — not as
a standalone solution.
