"""Render the project's research-report Word document.

Reads narrative prose embedded in this script (synthesised from
docs/research/DOT_Research.md, docs/architecture/Threat_Model.md, and the
per-LO dossiers) and the PNG figures in docs/screenshots/, and emits
docs/Research_Report.docx — a self-contained Word document that can be handed
in alongside the repository.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
OUT = ROOT / "docs" / "Research_Report.docx"

# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------


def _set_default_font(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)
    style.paragraph_format.line_spacing = 1.25

    for h, size in [("Heading 1", 18), ("Heading 2", 14), ("Heading 3", 12)]:
        s = doc.styles[h]
        s.font.name = "Calibri"
        s.font.size = Pt(size)
        s.font.bold = True
        s.font.color.rgb = RGBColor(0x1F, 0x2A, 0x44)
        s.paragraph_format.space_before = Pt(14)
        s.paragraph_format.space_after = Pt(6)


def _add_caption(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x55, 0x65, 0x70)
    p.paragraph_format.space_after = Pt(12)


def _add_image(doc: Document, filename: str, caption: str, width_cm: float = 14.0) -> None:
    path = SHOTS / filename
    if not path.exists():
        raise FileNotFoundError(path)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    _add_caption(doc, caption)


def _add_para(doc: Document, text: str) -> None:
    doc.add_paragraph(text)


def _add_quote(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.right_indent = Cm(0.8)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    run.italic = True
    run.font.color.rgb = RGBColor(0x34, 0x44, 0x55)


def _add_meta_table(doc: Document, rows: list[tuple[str, str]]) -> None:
    table = doc.add_table(rows=len(rows), cols=2)
    table.style = "Light Grid Accent 1"
    for (k, v), row in zip(rows, table.rows):
        row.cells[0].text = k
        row.cells[1].text = v
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(10)
        row.cells[0].paragraphs[0].runs[0].bold = True
    # Tighter row height
    for row in table.rows:
        tr = row._tr
        trPr = tr.get_or_add_trPr()
        trHeight = OxmlElement("w:trHeight")
        trHeight.set(qn("w:val"), "300")
        trPr.append(trHeight)
    doc.add_paragraph()


def _add_srq_table(doc: Document) -> None:
    rows = [
        ("SRQ", "Question (abridged)", "DOT strategies"),
        ("SRQ1", "Which flow features are most indicative of anomalous behaviour and how should they be extracted?", "Library + Lab"),
        ("SRQ2", "Which ML algorithms balance accuracy, speed and false-positive rate best?", "Library + Lab + Showroom"),
        ("SRQ3", "How can the system run in real time without unacceptable latency?", "Lab + Workshop"),
        ("SRQ4", "What threshold and tuning strategies minimise false positives?", "Lab"),
        ("SRQ5", "How should anomalies be presented to analysts in an actionable way?", "Library + Field + Showroom"),
        ("SRQ6", "How does the detector perform across the different attack categories?", "Lab"),
    ]
    table = doc.add_table(rows=len(rows), cols=3)
    table.style = "Light Grid Accent 1"
    table.autofit = True
    widths = [Cm(1.6), Cm(11.0), Cm(4.0)]
    for ri, r in enumerate(rows):
        for ci, val in enumerate(r):
            cell = table.cell(ri, ci)
            cell.text = val
            cell.width = widths[ci]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(10)
                    if ri == 0:
                        run.bold = True
    doc.add_paragraph()


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------


def build() -> None:
    doc = Document()
    _set_default_font(doc)

    # ----- Title block --------------------------------------------------------
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Network Traffic Anomaly Detector")
    run.bold = True
    run.font.size = Pt(24)
    run.font.color.rgb = RGBColor(0x1F, 0x2A, 0x44)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run("Personal Research Project — Research Report")
    run.italic = True
    run.font.size = Pt(13)
    run.font.color.rgb = RGBColor(0x55, 0x65, 0x70)

    doc.add_paragraph()  # spacer

    _add_meta_table(
        doc,
        rows=[
            ("Student", "Angel Rusev (i530375)"),
            ("Programme", "BSc ICT & Software Engineering"),
            ("Minor", "Cybersecurity — Attack & Defend"),
            ("Institution", "Fontys University of Applied Sciences"),
            ("Semester", "Spring 2026"),
            ("Document", "Research Report — supersedes PRP v1.0 (March 2026)"),
            ("Repository", "https://github.com/Guts1313/AnomalyDetector"),
        ],
    )

    # ----- Foreword -----------------------------------------------------------
    doc.add_heading("Foreword", level=1)
    _add_para(
        doc,
        "This report is the research deliverable of the Personal Research Project (PRP) "
        "for the Cybersecurity Attack & Defend minor. Where the PRP itself was a proposal, "
        "this document tells the story of the project that was actually built, evaluated, "
        "and reasoned about. Every claim it makes is anchored either in a piece of "
        "literature or in an experiment that can be reproduced in less than two minutes "
        "from the accompanying repository. The objective is not to prove that anomaly "
        "detection works — that has been settled for decades — but to design a defensible "
        "answer to the question of how to do it well, in real time, without drowning a "
        "security analyst in false positives.",
    )

    # ----- 1. The problem and the question -----------------------------------
    doc.add_heading("1. The problem and the question", level=1)
    _add_para(
        doc,
        "Modern organisations process more network traffic in an hour than a SOC analyst "
        "can manually scrutinise in a year. Signature-based intrusion-detection systems "
        "such as Snort and Suricata help, but they are by construction unable to recognise "
        "an attack whose signature has never been seen before. Anomaly-based detection "
        "offers a complementary perspective: rather than asking what malicious traffic "
        "looks like, it learns what normal traffic looks like and flags any deviation. "
        "Its weakness is well documented — false-positive rates that turn an analyst's "
        "console into noise — but its potential to surface zero-day and novel behaviour "
        "is exactly what the signature approach cannot deliver.",
    )
    _add_para(
        doc,
        "The PRP for this project framed that tension in a single main research question:",
    )
    _add_quote(
        doc,
        "How can a machine-learning-based network-traffic anomaly detector be designed "
        "and implemented to accurately identify cyber attacks in real time while "
        "maintaining an acceptable false-positive rate?",
    )
    _add_para(
        doc,
        "Six sub-research questions decompose that ambition into pieces that can be "
        "investigated independently — features, algorithms, latency, tuning, "
        "presentation, and per-category performance. They are summarised in Table 1 "
        "and each is taken up in turn in Section 3.",
    )
    _add_srq_table(doc)
    _add_caption(doc, "Table 1 — Sub-research questions and the DOT strategies used to investigate them.")

    # ----- 2. DOT framework ---------------------------------------------------
    doc.add_heading("2. A methodological compass: the DOT framework", level=1)
    _add_para(
        doc,
        "The Development-Oriented Triangulation (DOT) framework prescribed by Fontys "
        "groups applied-research activities into five method strategies — Library, Lab, "
        "Field, Workshop and Showroom — and asks the researcher to triangulate "
        "conclusions across at least three of them. Triangulation is the antidote to "
        "the most common failure mode in applied research: drawing a strong conclusion "
        "from a single, possibly biased, source of evidence.",
    )
    _add_para(
        doc,
        "For this project Library represents the literature study and the survey of "
        "existing intrusion-detection tools. Lab is the bulk of the work — feature "
        "engineering, training, benchmarking, latency measurement — all performed "
        "against a reproducible synthetic CICIDS-compatible dataset. Field consists of "
        "the SOC-analyst persona modelling that shaped the dashboard, informed by "
        "publicly documented SIEM usability conventions. Workshop is the peer-style "
        "architecture review that scored every design decision against alternatives. "
        "Finally, Showroom is the live demonstration of the working system, which the "
        "screenshots in this report stand in for. Each sub-research question draws on "
        "at least two of these strategies, and the main research question is answered "
        "from three independent angles in Section 4.",
    )

    # ----- 3. Per-SRQ narrative ----------------------------------------------
    doc.add_heading("3. How the project answered each sub-question", level=1)

    # SRQ1
    doc.add_heading("3.1 SRQ1 — Which features matter, and how should they be extracted?", level=2)
    _add_para(
        doc,
        "The literature converges on a small core of flow-level features that carry "
        "most of the discriminative signal for the major CICIDS attack categories. "
        "Sharafaldin and colleagues, in their 2018 paper introducing the CICIDS2017 "
        "dataset, give pride of place to volumetric features (flow duration, packet "
        "and byte counts, bytes per second), distributional features (mean and maximum "
        "packet lengths, inter-arrival time statistics) and protocol semantics — in "
        "particular the TCP flag counters that distinguish a clean handshake from a "
        "scan or a brute-force attempt. Ring and colleagues, surveying the broader "
        "intrusion-detection dataset landscape in 2019, reach a near-identical "
        "conclusion. The Library leg of the triangulation therefore points clearly at "
        "a feature set in the order of twenty flow-level variables.",
    )
    _add_para(
        doc,
        "The Lab leg confirmed that and added a smaller but consequential finding. "
        "Flow metrics are heavily right-skewed: a handful of large flows would "
        "dominate any naïve standardisation. Replacing the project's RobustScaler "
        "(which centres on the median and scales by the inter-quartile range) with a "
        "plain StandardScaler in an ablation run dropped macro F1 by roughly four "
        "percentage points across every algorithm. The pipeline that ships with the "
        "system therefore uses median imputation, RobustScaler for the numeric "
        "features and one-hot encoding for the protocol — packaged together with the "
        "trained model so that train-time and inference-time transformations cannot "
        "diverge. That packaging is not cosmetic: divergence between training and "
        "serving is one of the most commonly cited sources of false positives in "
        "Ring's survey.",
    )

    # SRQ2
    doc.add_heading("3.2 SRQ2 — Which algorithms strike the best balance?", level=2)
    _add_para(
        doc,
        "Chandola's classic survey of anomaly detection partitions the algorithmic "
        "landscape into three families that map naturally onto network-flow detection. "
        "Supervised discriminative methods such as Random Forest and Gradient Boosting "
        "are powerful when labelled benign-versus-attack data is available and they "
        "give per-attack-class output for free. Unsupervised density-based methods "
        "such as Isolation Forest relax the labelling requirement but lose granularity. "
        "One-class boundary methods such as One-Class SVM learn an explicit benign "
        "manifold and flag anything off it. Deep-learning approaches — autoencoders, "
        "LSTMs — were ruled out of scope in the PRP to keep the project tractable, and "
        "remain so here.",
    )
    _add_para(
        doc,
        "The four representatives of the three remaining families were trained on the "
        "same 20 000-flow synthetic dataset with a stratified 75/25 split. The result "
        "(Figure 1) is interesting precisely because it surprised the author. Macro F1 "
        "is essentially tied between One-Class SVM and Gradient Boosting at 0.907, with "
        "Random Forest a half-point behind and Isolation Forest a further nine points "
        "below them.",
    )
    _add_image(doc, "04_algo_comparison.png", "Figure 1 — Macro precision, recall and F1 of the four candidate algorithms on the 20 000-flow synthetic CICIDS-compatible dataset.")
    _add_para(
        doc,
        "The tie hides a critical deployment-time gap. One-Class SVM scores 0.907 over "
        "two classes (benign vs attack) while Gradient Boosting scores 0.907 over "
        "eight — strictly the harder task. Gradient Boosting also predicts about eight "
        "times faster (just under seven microseconds per sample versus around fifty "
        "for OC-SVM) and edges out OC-SVM in ROC-AUC at 0.997 against 0.956. The "
        "production-model selection rule encoded in the trainer therefore prefers the "
        "highest-F1 supervised algorithm whenever its F1 is within two percentage "
        "points of the overall leader. Under that rule, Gradient Boosting is the "
        "model the API actually serves, and it is the model whose detailed behaviour "
        "is examined in Section 3.6 and Section 5.",
    )

    # SRQ3
    doc.add_heading("3.3 SRQ3 — Can it run in real time?", level=2)
    _add_para(
        doc,
        "Per-sample inference time was measured on a thousand-sample slice of the "
        "held-out test set inside the training script. At 6.9 microseconds per sample, "
        "Gradient Boosting sustains roughly 140 000 flows per second on a single "
        "laptop core — orders of magnitude above any realistic ingest rate for an "
        "internal SOC. End-to-end latency adds a JSON-decode, a Pydantic validation "
        "and an asynchronous SQLite append on top of the model call; in the live demo "
        "that overhead measured below one millisecond per request for batches up to "
        "thirty flows. The Workshop leg of the triangulation — a self-applied "
        "architecture-review checklist against published online-inference patterns — "
        "endorsed three decisions that make those numbers possible: keeping the "
        "/predict endpoint stateless, persisting the fitted preprocessor and the model "
        "together in a single joblib bundle, and accepting batches by default so the "
        "vectorised scikit-learn predict path can do its work.",
    )

    # SRQ4
    doc.add_heading("3.4 SRQ4 — How to keep the false-positive rate low?", level=2)
    _add_para(
        doc,
        "The system implements two complementary mechanisms rather than a single hard "
        "cut. The first is a numerical threshold on the attack-probability score, "
        "exposed both through the API and through a slider in the dashboard, so an "
        "operator can dial sensitivity per investigation without retraining anything. "
        "At the default operating point the model raises an attack verdict on twenty-"
        "five out of three thousand five hundred benign test flows — a false-positive "
        "rate of 0.7 per cent, well below the levels Ring and colleagues report as "
        "operationally unsustainable. The second mechanism is severity bucketing: every "
        "verdict is tagged info, low, medium, high or critical, and the dashboard only "
        "surfaces medium-and-above by default. Lower-confidence verdicts are still "
        "written to the audit log, so a post-incident analyst can replay them, but "
        "they do not contribute to alert fatigue. The two layers together turn a "
        "single tunable into an entire FP-control surface.",
    )

    # SRQ5
    doc.add_heading("3.5 SRQ5 — How should the alerts reach the analyst?", level=2)
    _add_para(
        doc,
        "Three conventions recur across the SIEM literature and the published "
        "Splunk, Elastic-SIEM and Wazuh user-experience guidelines. Every alert "
        "should be colour-coded by severity so the eye can triage at a glance. The "
        "audit log must sit alongside the alert queue so an analyst can answer not "
        "just \"why was this flagged?\" but also \"why was that one not flagged?\". And "
        "the attack class drives the response runbook — a port scan does not call "
        "for the same playbook as suspected data exfiltration. The Streamlit "
        "dashboard the project delivers (Figure 2) makes all three concrete. The "
        "overview tab summarises the live state of the system, the alerts tab is a "
        "sortable severity-coloured table with the attack score rendered as a "
        "progress column, and a manual-scoring tab lets the analyst rebuild a "
        "hypothetical flow and read off the class probabilities — explainability "
        "without the weight of a dedicated explainability library.",
    )
    _add_image(doc, "01_dashboard_overview.png", "Figure 2 — Streamlit analyst dashboard after 450 flows have been replayed through the detector. Severity distribution and attacks-by-class are rendered as live Plotly charts.", width_cm=10.5)
    _add_para(
        doc,
        "Underneath the dashboard sits a FastAPI service whose OpenAPI surface "
        "(Figure 3) doubles as the documentation that an ML engineer needs in order "
        "to retrain a model and reload it without bringing the system down — "
        "evidence of the project's bias toward operational integration rather than "
        "stand-alone novelty.",
    )
    _add_image(doc, "02_api_swagger.png", "Figure 3 — FastAPI / Swagger surface, grouped by meta, inference, audit and admin tags.", width_cm=11.5)

    # SRQ6
    doc.add_heading("3.6 SRQ6 — Where does the detector shine, and where does it struggle?", level=2)
    _add_para(
        doc,
        "Macro figures hide more than they reveal. The per-class breakdown (Figure 4) "
        "tells the more honest story. On six of the eight classes — port scan, brute "
        "force, botnet, denial-of-service, distributed denial-of-service and benign — "
        "the model lands at or above 0.99 F1. Web attacks fall a little behind at "
        "0.95, plausibly because encrypted HTTP payloads carry less flow-level signal "
        "than the others. Infiltration, however, sits at 0.35, and the confusion "
        "matrix (Figure 5) shows why: seventy per cent of infiltration flows are "
        "predicted as benign. That is not a defect of the algorithm — it is the "
        "definition of an infiltration attack, which by design seeks to look like "
        "normal traffic. The same gap is visible in Sharafaldin's original report on "
        "the real CICIDS2017 dataset.",
    )
    _add_image(doc, "05_per_class_f1.png", "Figure 4 — Per-class F1 for the deployed Gradient Boosting model on the held-out test set. Class sample sizes are shown above each bar.")
    _add_image(doc, "06_confusion_matrix.png", "Figure 5 — Row-normalised confusion matrix for the deployed model. The infiltration row is the visible weak spot; most infiltration flows are absorbed by the benign class.", width_cm=12.0)
    _add_para(
        doc,
        "The honest framing is therefore: the detector is production-ready for the "
        "high-volume, high-signal attack categories, and it must be paired with "
        "complementary controls — a signature IDS for known infiltration patterns, "
        "or a TLS-metadata sub-classifier as proposed in the open backlog — to cover "
        "the categories that flow-level statistics cannot distinguish. Naming that "
        "limitation explicitly is, in the DOT idiom, an act of triangulation in its "
        "own right.",
    )

    # ----- 4. Triangulation ---------------------------------------------------
    doc.add_heading("4. Triangulation: do the three perspectives agree?", level=1)
    _add_para(
        doc,
        "DOT asks the researcher to triangulate. The main research question — can a "
        "real-time anomaly detector be built that balances accuracy against false "
        "positives — is answered consistently from three independent angles. Library "
        "tells us that flow-level features combined with supervised ensembles are the "
        "right state of the art for CICIDS-style problems. Lab confirms that empirically: "
        "Gradient Boosting reaches 0.99 F1 on six of eight classes, holds the "
        "false-positive rate below one per cent, and runs at sub-millisecond latency. "
        "Showroom, the live demonstration of the working artefact, verifies that the "
        "system meets the analyst-usability and real-time constraints that those "
        "numbers alone could not establish. The three perspectives converge — and the "
        "single point where they almost disagree, the infiltration class, is precisely "
        "where the report has placed its most visible asterisk. That visibility is the "
        "result of triangulation working as intended, not despite it.",
    )

    # ----- 5. Limitations -----------------------------------------------------
    doc.add_heading("5. Limitations and honest caveats", level=1)
    _add_para(
        doc,
        "Four limitations deserve naming. First, every number reported here is "
        "produced against a synthetic CICIDS-shaped dataset of twenty thousand flows. "
        "The pipeline ingests the official CICIDS2017 CSVs unchanged, so the rerun is "
        "mechanical, but the absolute figures will move; the ranking of algorithms is "
        "what the project bets is stable, not the absolute F1. Second, the deep-"
        "learning baseline that the PRP ruled out remains ruled out, and a complete "
        "answer to SRQ2 ultimately requires comparison against at least an autoencoder. "
        "Third, the threshold the system ships with is a defensible default, not the "
        "optimum for any particular SOC; the optimum depends on each operator's "
        "tolerance trade-off between false positives and false negatives. Fourth, the "
        "Field leg of the triangulation rests on indirect persona modelling and SIEM-"
        "usability literature rather than a real analyst interview. Each of these is "
        "tracked as an issue in the project's backlog and is therefore addressable, "
        "not silently buried.",
    )

    # ----- 6. Conclusion ------------------------------------------------------
    doc.add_heading("6. Conclusion", level=1)
    _add_para(
        doc,
        "The project set out to investigate how a machine-learning anomaly detector "
        "could be built to catch real attacks at real-time speed without overwhelming "
        "the analyst it is meant to serve. The answer it arrived at is, with all the "
        "caveats that Section 5 lists honestly, that it can — provided the engineering "
        "is taken as seriously as the modelling. A twenty-feature flow representation "
        "with robust scaling, a Gradient Boosting model with a two-layer threshold-"
        "plus-severity false-positive control, a stateless batch-oriented inference "
        "API, and a severity-coloured dashboard that mirrors established SIEM "
        "conventions together produce a detector that lands above 0.99 F1 on the "
        "high-volume attack classes, runs at sub-millisecond latency per batch, and "
        "is operationally legible to a SOC analyst with no machine-learning background. "
        "Where it falls short — the infiltration class — it falls short for reasons "
        "the literature already named, and the open backlog already sketches the "
        "remediation. The repository that accompanies this report contains everything "
        "needed to reproduce, falsify, or extend any of the claims above.",
    )

    # ----- References ---------------------------------------------------------
    doc.add_heading("References", level=1)
    refs = [
        "Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2018). Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization. ICISSP.",
        "Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). Isolation Forest. IEEE International Conference on Data Mining.",
        "Chandola, V., Banerjee, A., & Kumar, V. (2009). Anomaly Detection: A Survey. ACM Computing Surveys.",
        "Ring, M., Wunderlich, S., Scheuring, D., Landes, D., & Hotho, A. (2019). A Survey of Network-based Intrusion Detection Data Sets. Computers & Security.",
        "scikit-learn documentation: Novelty and Outlier Detection. https://scikit-learn.org/stable/modules/outlier_detection.html",
        "FastAPI documentation. https://fastapi.tiangolo.com/",
        "CICIDS2017 Dataset. https://www.unb.ca/cic/datasets/ids-2017.html",
        "DOT-framework. https://ictresearchmethods.nl/dot-framework/",
    ]
    for i, ref in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.add_run(f"[{i}] ").bold = True
        p.add_run(ref)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"[+] Wrote {OUT}")


if __name__ == "__main__":
    build()
