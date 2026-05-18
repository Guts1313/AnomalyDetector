"""SQLite store for predictions/alerts.

A deliberately tiny persistence layer — the goal is auditability of every
flow seen by the detector (LO2 monitoring + procedural response), not a
production-grade event store.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

_DDL = """
CREATE TABLE IF NOT EXISTS predictions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT NOT NULL,
    model_name    TEXT NOT NULL,
    verdict       TEXT NOT NULL,
    is_attack     INTEGER NOT NULL,
    attack_score  REAL NOT NULL,
    severity      TEXT NOT NULL,
    src_ip        TEXT,
    dst_ip        TEXT,
    latency_ms    REAL
);
CREATE INDEX IF NOT EXISTS idx_predictions_ts ON predictions(timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_attack ON predictions(is_attack);
"""


class AlertStore:
    def __init__(self, path: str = "alerts.db") -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(_DDL)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def log_prediction(
        self,
        *,
        model_name: str,
        verdict: str,
        is_attack: bool,
        attack_score: float,
        severity: str,
        src_ip: Optional[str],
        dst_ip: Optional[str],
        latency_ms: float,
    ) -> int:
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO predictions
                (timestamp, model_name, verdict, is_attack, attack_score, severity, src_ip, dst_ip, latency_ms)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    datetime.utcnow().isoformat(timespec="seconds"),
                    model_name,
                    verdict,
                    int(is_attack),
                    float(attack_score),
                    severity,
                    src_ip,
                    dst_ip,
                    float(latency_ms),
                ),
            )
            return cur.lastrowid or 0

    def recent_alerts(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM predictions
                   WHERE is_attack = 1
                   ORDER BY id DESC LIMIT ?""",
                (int(limit),),
            ).fetchall()
        return [dict(r) for r in rows]

    def recent_predictions(self, limit: int = 500) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM predictions ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [dict(r) for r in rows]

    def summary(self) -> dict:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) c FROM predictions").fetchone()["c"]
            attacks = conn.execute(
                "SELECT COUNT(*) c FROM predictions WHERE is_attack=1"
            ).fetchone()["c"]
            benign = total - attacks
            sev_rows = conn.execute(
                "SELECT severity, COUNT(*) c FROM predictions GROUP BY severity"
            ).fetchall()
            class_rows = conn.execute(
                "SELECT verdict, COUNT(*) c FROM predictions WHERE is_attack=1 GROUP BY verdict"
            ).fetchall()
            lat = conn.execute(
                "SELECT AVG(latency_ms) avg FROM predictions"
            ).fetchone()["avg"]
        return {
            "total": total,
            "attacks": attacks,
            "benign": benign,
            "severity_breakdown": {r["severity"]: r["c"] for r in sev_rows},
            "attacks_by_class": {r["verdict"]: r["c"] for r in class_rows},
            "avg_latency_ms": float(lat or 0.0),
        }
