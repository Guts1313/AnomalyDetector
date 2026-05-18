# LO1 — Offensive Security · Evidence Dossier

> **Learning outcome (verbatim):** *You analyse the security of diverse IT
> environments, such as a business environment, a consumer product, or a
> technology, by ethical hacking according to a methodical approach. You also
> analyse security threats and resulting business risks according to a common
> risk-analysis method and advise a client on security improvements of an IT
> environment on a physical, technical and organisational level.*

**Student:** Angel Rusev · **Project:** Network Traffic Anomaly Detector ·
**Minor:** Cybersecurity — Attack & Defend (Fontys, Spring 2026)

---

## 1. Map of evidence

| Sub-criterion of LO1                              | Evidence in this project                                                                                                          | Where to look |
|---------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|----------------|
| Methodical security analysis (ethical hacking)    | STRIDE threat model of the detector itself + emulated attack categories whose flows are scored.                                    | `docs/architecture/Threat_Model.md` (STRIDE table); `scripts/generate_synthetic_dataset.py` (per-attack feature signatures). |
| Common risk-analysis method (Risk = Impact × Likelihood) | PRP §9 risk register extended into the threat-model STRIDE rows with H/M/L impact and likelihood ratings + mitigations.        | This document §3; `docs/architecture/Threat_Model.md` §4. |
| Advice on physical / technical / organisational improvements | Section 4 below — concrete recommendations to the (hypothetical) client, separated into the three layers.                  | This document §4. |

---

## 2. Methodical approach — adopting STRIDE

The project applies **STRIDE** (Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege) — the threat-modelling method standardised by Microsoft and recommended by OWASP — to the detector's own architecture. STRIDE was chosen over PASTA / DREAD because:

* STRIDE is **threat-type oriented** — it maps neatly to MITRE ATT&CK tactics the detector is designed to spot (T1499 Endpoint DoS ↔ T5; T1110 Brute Force ↔ T1; T1071 C2 ↔ T7).
* The artefact's threat surface is small enough that PASTA's seven-stage process would be over-engineered.

The threat model is laid out in `docs/architecture/Threat_Model.md` §4. Eight
threats are inventoried, each with vector, impact, and mitigation.

## 3. Risk analysis — Impact × Likelihood

The PRP §9 risk register is *project-management* risk. For LO1 it is extended
to **security risk** of the running detector:

| ID  | Risk                                            | Impact | Likelihood | Combined | Mitigation (in place)                                                                                       |
|-----|-------------------------------------------------|--------|------------|----------|-------------------------------------------------------------------------------------------------------------|
| SR1 | Model evasion via adversarial flows (Infiltration class) | High   | High       | **Critical** | Per-class F1 reported transparently (SRQ6); recommend pairing with signature-based IDS (Snort).             |
| SR2 | Tampering with the persisted model bundle       | High   | Low        | Medium   | Models mounted read-only in the container; recommended hash-verification step before `/admin/reload`.        |
| SR3 | Information disclosure via the SQLite audit DB  | Medium | Medium     | Medium   | No payloads ever stored; IPs are the only identifying field; volume permissions least-privilege.            |
| SR4 | DoS via oversized batch requests                | Medium | Medium     | Medium   | Recommended upstream rate-limit (issue #11) + max-payload settings in nginx/traefik.                         |
| SR5 | Privilege escalation through the API container  | High   | Low        | Medium   | Non-root user in `Dockerfile.api`; no docker-socket bind-mount; healthcheck enforces container restart.      |
| SR6 | Data poisoning at training time                 | High   | Low        | Medium   | Training is offline; dataset is version-controlled; recommended dataset-hash signing as future work.        |
| SR7 | Encrypted-traffic blind spot                    | Medium | High       | High     | Out-of-scope per PRP §4.2; document the gap; recommended complementary TLS-metadata heuristics layer.       |

## 4. Recommendations to the client — physical / technical / organisational

**Physical**

* Co-locate the detector and the SOC's PCAP capture appliances in the **same security zone** to keep flow features on-LAN and minimise exposure of the audit DB.
* Restrict console access to the host running the API container to dual-control (badge + smart card) per ISO 27002 control 7.2.

**Technical**

1. Deploy the API behind an authenticated reverse proxy (nginx / traefik) — terminates TLS and enforces an API key per analyst.
2. Mount `models/` **read-only** in production; promote model bundles through a separate signed-package channel.
3. Pair the anomaly detector with a **signature-based IDS** (Suricata + ET Open rules) to compensate for the Infiltration F1 gap measured in SRQ6.
4. Enable **rate-limiting** at the proxy layer (issue #11) — caps the DoS risk SR4.
5. Stream the `/alerts` endpoint into the SIEM (Splunk / Elastic) and configure correlation rules for severity = critical.

**Organisational**

1. Document **a procedural response runbook** per severity level — already drafted in `docs/architecture/Threat_Model.md` §6.
2. Schedule **bi-monthly model re-training + drift review** — the operator runs `scripts/train.py` and reviews the new comparison matrix before `POST /admin/reload`.
3. Adopt a **quarterly purple-team exercise** to feed adversarial flows through `/predict` and measure detection-rate decay against the baseline matrix in `models/comparison_matrix.csv`.
4. Document the project's ethical position in the client's privacy register: **no payload inspection**, IPs pseudonymised on egress (§3 of the threat model).

## 5. Mapping to the rubric

* "Methodical approach" ← STRIDE + the DOT-framework triangulation in `docs/research/DOT_Research.md` (Library + Lab + Showroom).
* "Common risk-analysis method" ← Impact × Likelihood × Mitigation matrix in §3 + the PRP risk register.
* "Advise on physical / technical / organisational level" ← Section 4 above.
* "Diverse IT environments" ← The detector is positioned for SOC deployment (business environment), but the threat model also discusses on-prem appliance deployment and Docker-on-laptop demo deployment.
