"""FastAPI application for the Network Traffic Anomaly Detector."""
from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from .. import __version__
from ..models.registry import ModelRegistry
from ..schemas.flows import (
    AlertOut,
    FlowRecord,
    FlowVerdict,
    HealthOut,
    MetricsOut,
    PredictRequest,
    PredictResponse,
)
from .store import AlertStore

DEFAULT_THRESHOLD = float(os.environ.get("AD_THRESHOLD", "0.5"))
MODELS_DIR = os.environ.get("AD_MODELS_DIR", "models")
ALERT_DB = os.environ.get("AD_ALERT_DB", "alerts.db")

app = FastAPI(
    title="Network Traffic Anomaly Detector",
    description=(
        "PRP — Angel Rusev (Fontys, Cybersecurity Attack & Defend 2026). "
        "Real-time flow classification with explainable severity scoring."
    ),
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_registry = ModelRegistry(models_dir=MODELS_DIR)
_store = AlertStore(path=ALERT_DB)


def _severity_for(score: float) -> str:
    if score < 0.3:
        return "info"
    if score < 0.5:
        return "low"
    if score < 0.75:
        return "medium"
    if score < 0.9:
        return "high"
    return "critical"


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "service": "anomaly-detector",
        "version": __version__,
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthOut, tags=["meta"])
def health() -> HealthOut:
    try:
        art = _registry.load()
        return HealthOut(
            status="ok",
            model_loaded=True,
            model_name=art.name,
            version=__version__,
        )
    except FileNotFoundError:
        return HealthOut(
            status="degraded",
            model_loaded=False,
            model_name=None,
            version=__version__,
        )


@app.get("/metrics", response_model=MetricsOut, tags=["meta"])
def metrics() -> MetricsOut:
    s = _store.summary()
    return MetricsOut(
        total_predictions=s["total"],
        total_alerts=s["attacks"],
        total_benign=s["benign"],
        attacks_by_class=s["attacks_by_class"],
        severity_breakdown=s["severity_breakdown"],
        avg_latency_ms=s["avg_latency_ms"],
    )


def _predict_payload(flows: list[FlowRecord], threshold: float | None) -> PredictResponse:
    if not flows:
        raise HTTPException(status_code=400, detail="At least one flow is required.")
    try:
        art = _registry.load()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    df = pd.DataFrame([f.model_dump() for f in flows])
    t0 = time.perf_counter()
    out = art.predict(df, threshold=threshold)
    latency_ms = (time.perf_counter() - t0) * 1000

    verdicts_list: list[FlowVerdict] = []
    ts = datetime.utcnow()
    for i, verdict in enumerate(out["verdicts"]):
        score = float(out["attack_scores"][i])
        is_attack = verdict.upper() != "BENIGN"
        severity = _severity_for(score) if is_attack else "info"
        probs = out["class_probabilities"][i] if i < len(out["class_probabilities"]) else {}
        v = FlowVerdict(
            verdict=verdict,
            is_attack=is_attack,
            attack_score=score,
            severity=severity,
            class_probabilities=probs,
            src_ip=flows[i].src_ip,
            dst_ip=flows[i].dst_ip,
            timestamp=ts,
        )
        verdicts_list.append(v)
        _store.log_prediction(
            model_name=art.name,
            verdict=verdict,
            is_attack=is_attack,
            attack_score=score,
            severity=severity,
            src_ip=flows[i].src_ip,
            dst_ip=flows[i].dst_ip,
            latency_ms=latency_ms / max(1, len(flows)),
        )

    return PredictResponse(
        model_name=art.name,
        model_family=art.family,
        threshold_used=threshold,
        verdicts=verdicts_list,
    )


@app.post("/predict", response_model=PredictResponse, tags=["inference"])
def predict(req: PredictRequest) -> PredictResponse:
    """Classify one or more network flows."""
    return _predict_payload(req.flows, req.threshold if req.threshold is not None else None)


@app.post("/predict/csv", response_model=PredictResponse, tags=["inference"])
async def predict_csv(file: UploadFile = File(...), threshold: float | None = None) -> PredictResponse:
    """Classify flows from a CICFlowMeter-style CSV upload."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload must be a .csv file.")
    raw = await file.read()
    import io
    df = pd.read_csv(io.BytesIO(raw))
    # Best-effort column harmonisation: lower-case + strip + replace spaces
    df.columns = [c.strip().lower().replace(" ", "_").replace("/", "_per_") for c in df.columns]
    records = df.to_dict(orient="records")
    flows = [FlowRecord(**{k: v for k, v in r.items() if k in FlowRecord.model_fields or k in ("src_ip", "dst_ip", "src_port", "dst_port")}) for r in records]
    return _predict_payload(flows, threshold)


@app.get("/alerts", response_model=list[AlertOut], tags=["audit"])
def alerts(limit: int = 100) -> list[AlertOut]:
    rows = _store.recent_alerts(limit=limit)
    return [
        AlertOut(
            id=r["id"],
            timestamp=datetime.fromisoformat(r["timestamp"]),
            verdict=r["verdict"],
            is_attack=bool(r["is_attack"]),
            attack_score=r["attack_score"],
            severity=r["severity"],
            src_ip=r["src_ip"],
            dst_ip=r["dst_ip"],
            model_name=r["model_name"],
        )
        for r in rows
    ]


@app.get("/predictions", response_model=list[AlertOut], tags=["audit"])
def predictions(limit: int = 500) -> list[AlertOut]:
    rows = _store.recent_predictions(limit=limit)
    return [
        AlertOut(
            id=r["id"],
            timestamp=datetime.fromisoformat(r["timestamp"]),
            verdict=r["verdict"],
            is_attack=bool(r["is_attack"]),
            attack_score=r["attack_score"],
            severity=r["severity"],
            src_ip=r["src_ip"],
            dst_ip=r["dst_ip"],
            model_name=r["model_name"],
        )
        for r in rows
    ]


@app.post("/admin/reload", tags=["admin"])
def reload_model() -> dict:
    """Reload the model artifact from disk (used after retraining)."""
    art = _registry.reload()
    return {"status": "reloaded", "model_name": art.name, "family": art.family}
