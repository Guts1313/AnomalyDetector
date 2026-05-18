"""Pydantic v2 request/response models for the FastAPI surface."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class FlowRecord(BaseModel):
    """A single network flow expressed in CICIDS-compatible features.

    Only `protocol` is required; all numeric features default to 0.0 so that
    callers can submit partial records (the pipeline will handle missing
    features). For production use, supplying all features yields the best
    accuracy.
    """

    model_config = ConfigDict(extra="allow")

    protocol: Literal["TCP", "UDP", "ICMP", "OTHER"] = Field("TCP")

    flow_duration: float = 0.0
    total_fwd_packets: float = 0.0
    total_bwd_packets: float = 0.0
    total_length_fwd_packets: float = 0.0
    total_length_bwd_packets: float = 0.0
    fwd_packet_length_max: float = 0.0
    fwd_packet_length_mean: float = 0.0
    bwd_packet_length_max: float = 0.0
    bwd_packet_length_mean: float = 0.0
    flow_bytes_per_s: float = 0.0
    flow_packets_per_s: float = 0.0
    flow_iat_mean: float = 0.0
    flow_iat_std: float = 0.0
    fwd_iat_total: float = 0.0
    bwd_iat_total: float = 0.0
    fin_flag_count: float = 0.0
    syn_flag_count: float = 0.0
    rst_flag_count: float = 0.0
    psh_flag_count: float = 0.0
    ack_flag_count: float = 0.0

    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None


class PredictRequest(BaseModel):
    flows: list[FlowRecord]
    threshold: Optional[float] = Field(
        None,
        description=(
            "Optional decision threshold on the attack-probability score "
            "(supervised) or normalised anomaly score (one-class). Lower = "
            "more sensitive."
        ),
        ge=0.0,
        le=1.0,
    )


class FlowVerdict(BaseModel):
    verdict: str = Field(..., description="Predicted class label (e.g. BENIGN, DDoS, PortScan, ATTACK).")
    is_attack: bool
    attack_score: float = Field(..., ge=0.0, le=1.0)
    severity: Literal["info", "low", "medium", "high", "critical"]
    class_probabilities: dict[str, float] = Field(default_factory=dict)
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    timestamp: datetime


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_name: str
    model_family: str
    threshold_used: Optional[float]
    verdicts: list[FlowVerdict]


class AlertOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: int
    timestamp: datetime
    verdict: str
    is_attack: bool
    attack_score: float
    severity: str
    src_ip: Optional[str]
    dst_ip: Optional[str]
    model_name: str


class HealthOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    status: Literal["ok", "degraded"]
    model_loaded: bool
    model_name: Optional[str]
    version: str


class MetricsOut(BaseModel):
    total_predictions: int
    total_alerts: int
    total_benign: int
    attacks_by_class: dict[str, int]
    severity_breakdown: dict[str, int]
    avg_latency_ms: float
