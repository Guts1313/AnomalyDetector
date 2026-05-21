import { useEffect, useState } from "react";
import KPI from "../components/KPI";
import PlotlyChart from "../components/PlotlyChart";
import { api } from "../api/client";
import type { Metrics } from "../api/types";
import { SEVERITY_COLOR, CATEGORY_COLOR } from "../components/Badge";

const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"] as const;

export default function Overview() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api
      .metrics()
      .then((m) => {
        if (!alive) return;
        setMetrics(m);
        setError(null);
      })
      .catch((e) => alive && setError(String(e?.message ?? e)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  if (loading) {
    return (
      <section>
        <div className="grid grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card" aria-hidden>
              <div className="skeleton" style={{ height: 14, width: "40%", marginBottom: 12 }} />
              <div className="skeleton" style={{ height: 32, width: "60%" }} />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (error || !metrics) {
    return (
      <div className="card" role="alert">
        <h2>Metrics not available</h2>
        <p>{error ?? "Make some predictions first, then refresh."}</p>
      </div>
    );
  }

  const alertRate = metrics.total_alerts / Math.max(1, metrics.total_predictions);
  const sevEntries = SEVERITY_ORDER.filter((s) => metrics.severity_breakdown[s] != null).map(
    (s) => ({ severity: s, count: metrics.severity_breakdown[s] ?? 0 }),
  );
  const classEntries = Object.entries(metrics.attacks_by_class).sort((a, b) => b[1] - a[1]);

  return (
    <section aria-labelledby="overview-heading">
      <h1 id="overview-heading">Overview</h1>

      <div className="grid grid-cols-4">
        <KPI
          label="Total flows scored"
          value={metrics.total_predictions.toLocaleString()}
          accent="#3b82f6"
        />
        <KPI
          label="Alerts raised"
          value={metrics.total_alerts.toLocaleString()}
          delta={`${(alertRate * 100).toFixed(1)}% of all flows`}
          accent="var(--sev-critical)"
        />
        <KPI
          label="Benign flows"
          value={metrics.total_benign.toLocaleString()}
          accent="var(--sev-info)"
        />
        <KPI
          label="Avg latency"
          value={`${metrics.avg_latency_ms.toFixed(2)} ms`}
          accent="var(--sev-medium)"
        />
      </div>

      <div className="divider" />

      <div className="grid grid-cols-2">
        <div className="card">
          <h3>Severity distribution</h3>
          {sevEntries.length === 0 ? (
            <p className="kpi-hint">No severities recorded yet.</p>
          ) : (
            <PlotlyChart
              height={280}
              data={[
                {
                  type: "bar",
                  x: sevEntries.map((e) => e.severity.toUpperCase()),
                  y: sevEntries.map((e) => e.count),
                  marker: {
                    color: sevEntries.map(
                      (e) => SEVERITY_COLOR[e.severity] ?? "#3b82f6",
                    ),
                  },
                  hovertemplate: "<b>%{x}</b><br>%{y} alerts<extra></extra>",
                },
              ]}
              layout={{ showlegend: false }}
            />
          )}
        </div>

        <div className="card">
          <h3>Attacks by class</h3>
          {classEntries.length === 0 ? (
            <p className="kpi-hint">No attacks classified yet.</p>
          ) : (
            <PlotlyChart
              height={280}
              data={[
                {
                  type: "pie",
                  hole: 0.55,
                  labels: classEntries.map(([k]) => k),
                  values: classEntries.map(([, v]) => v),
                  marker: {
                    colors: classEntries.map(
                      ([k]) => CATEGORY_COLOR[k] ?? "#3b82f6",
                    ),
                  },
                  textinfo: "label+percent",
                  hovertemplate: "<b>%{label}</b><br>%{value} flows<extra></extra>",
                } as never,
              ]}
              layout={{ showlegend: false }}
            />
          )}
        </div>
      </div>
    </section>
  );
}
