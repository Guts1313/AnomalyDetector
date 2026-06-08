# Trend & literature analysis (Library strategy)

**Phase:** Define & Analyse · **Sprint 1**

The Library leg of the DOT triangulation surveys the state of the art to fix the
feature set and the algorithm families *before* the Lab work begins. Full
substantiation is in `docs/research/DOT_Research.md` and the Research Report.

## 1. Flow-level features are the right abstraction

Sharafaldin et al. (2018, CICIDS2017) and Ring et al. (2019) converge on a small
core of flow-level features carrying most of the discriminative signal:

- **Volumetric** — flow duration, packet/byte counts, bytes-per-second.
- **Distributional** — packet-length mean/max, inter-arrival-time statistics.
- **Protocol semantics** — TCP flag counters that separate a clean handshake from a scan or brute-force.

Conclusion: a feature set on the order of twenty flow-level variables — not raw
payloads — is the right input. This directly answers SRQ1's direction.

## 2. Algorithm families

Chandola et al. (2009) partition anomaly detection into three families that map
onto network-flow detection:

| Family | Examples | Trade-off |
|---|---|---|
| Supervised / discriminative | Random Forest, Gradient Boosting | Best with labels; per-class output for free |
| Unsupervised / density | Isolation Forest, LOF | No labels needed; loses granularity |
| One-class boundary | One-Class SVM | Learns a benign manifold; binary only |

Deep-learning approaches (autoencoders, LSTMs) are noted but ruled out of scope
to keep the project tractable and energy-efficient. This frames SRQ2.

## 3. Existing tools (product analysis)

Signature IDS (Snort, Suricata, Zeek) catch known attacks but miss novel ones —
the gap an anomaly detector fills. SIEM UX conventions (Splunk, Elastic SIEM,
Wazuh) inform the analyst-facing design (SRQ5): severity colour-coding, an audit
log beside the alert queue, and attack-class-driven runbooks.

## 4. Implication for the design

Use ~20 flow-level features + a supervised tree ensemble, control false positives
with a threshold plus severity bucketing, present results with SIEM-style
severity coding, and pair with a signature IDS where flow statistics are blind
(infiltration). These hypotheses are tested in the Lab in Sprints 2–3.

## References

Sharafaldin et al. (2018); Liu, Ting & Zhou (2008, Isolation Forest);
Chandola, Banerjee & Kumar (2009); Ring et al. (2019). Full list in the
Research Report.
