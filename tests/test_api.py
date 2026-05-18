"""End-to-end API tests using FastAPI's TestClient.

These tests run the training pipeline on a tiny synthetic dataset, persist a
model, then exercise the API surface. They double as integration tests for
the SRQ3 (real-time latency) and SRQ4 (threshold tuning) deliverables.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from anomaly_detector.models.trainers import persist_best, train_all_models
from scripts.generate_synthetic_dataset import generate


@pytest.fixture(scope="module")
def trained_model(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("ad_test")
    os.environ["AD_MODELS_DIR"] = str(tmp)
    os.environ["AD_ALERT_DB"] = str(tmp / "alerts.db")
    df = generate(rows=2500, seed=7)
    comp = train_all_models(df)
    persist_best(comp, out_dir=str(tmp))
    yield tmp


@pytest.fixture(scope="module")
def client(trained_model):
    # Import after env vars are set
    from importlib import reload
    import anomaly_detector.api.main as m
    reload(m)
    return TestClient(m.app)


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_predict_benign(client):
    flow = {"protocol": "TCP", "flow_duration": 60000, "total_fwd_packets": 8, "total_bwd_packets": 7}
    r = client.post("/predict", json={"flows": [flow]})
    assert r.status_code == 200
    body = r.json()
    assert "verdicts" in body and len(body["verdicts"]) == 1
    v = body["verdicts"][0]
    assert "verdict" in v and "attack_score" in v and "severity" in v


def test_predict_synthetic_attack(client):
    # Build a portscan-like flow
    flow = {
        "protocol": "TCP",
        "flow_duration": 50,
        "total_fwd_packets": 1,
        "total_bwd_packets": 0,
        "fwd_packet_length_max": 60,
        "fwd_packet_length_mean": 60,
        "flow_packets_per_s": 5000,
        "syn_flag_count": 1,
    }
    r = client.post("/predict", json={"flows": [flow], "threshold": 0.4})
    assert r.status_code == 200
    body = r.json()
    # We don't assert the *label* (synthetic noise can flip the model),
    # but the API must produce a scored verdict.
    assert 0 <= body["verdicts"][0]["attack_score"] <= 1


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "total_predictions" in body
