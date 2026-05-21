import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { Alert } from "../api/types";
import { SeverityBadge } from "../components/Badge";
import EmptyAlerts from "../components/EmptyAlerts";

type SortKey = "timestamp" | "verdict" | "severity" | "attack_score" | "src_ip" | "dst_ip" | "model_name";
type SortDir = "asc" | "desc";

const SEV_RANK: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1, info: 0 };

function compare(a: Alert, b: Alert, key: SortKey): number {
  const av = a[key];
  const bv = b[key];
  if (key === "severity") return (SEV_RANK[String(av)] ?? -1) - (SEV_RANK[String(bv)] ?? -1);
  if (key === "attack_score") return (Number(av) || 0) - (Number(bv) || 0);
  if (key === "timestamp") return new Date(String(av)).getTime() - new Date(String(bv)).getTime();
  return String(av ?? "").localeCompare(String(bv ?? ""));
}

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("timestamp");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api
      .alerts(200)
      .then((a) => alive && (setAlerts(a), setError(null)))
      .catch((e) => alive && setError(String(e?.message ?? e)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  const sorted = useMemo(() => {
    if (!alerts) return [];
    const dir = sortDir === "asc" ? 1 : -1;
    return [...alerts].sort((a, b) => compare(a, b, sortKey) * dir);
  }, [alerts, sortKey, sortDir]);

  function toggleSort(k: SortKey) {
    if (sortKey === k) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(k);
      setSortDir(k === "timestamp" || k === "attack_score" || k === "severity" ? "desc" : "asc");
    }
  }

  const ariaSort = (k: SortKey): "ascending" | "descending" | "none" =>
    sortKey === k ? (sortDir === "asc" ? "ascending" : "descending") : "none";

  return (
    <section aria-labelledby="alerts-heading">
      <h1 id="alerts-heading">Recent alerts {alerts && <small>({alerts.length})</small>}</h1>

      {loading && <div className="card"><div className="skeleton" style={{ height: 200 }} /></div>}
      {error && <div className="card" role="alert"><p>Could not load alerts: {error}</p></div>}
      {!loading && !error && alerts && alerts.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "32px 16px" }}>
          <EmptyAlerts height={180} />
          <h3 style={{ color: "var(--sev-info)", marginTop: 8 }}>No alerts — system is monitoring</h3>
          <p style={{ color: "var(--text-muted)" }}>
            Score a flow on the <strong>Manual scoring</strong> tab to generate one.
          </p>
        </div>
      )}

      {alerts && alerts.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <Th k="timestamp" label="Time (UTC)" sortKey={sortKey} ariaSort={ariaSort} toggle={toggleSort} />
                <Th k="verdict" label="Verdict" sortKey={sortKey} ariaSort={ariaSort} toggle={toggleSort} />
                <Th k="severity" label="Severity" sortKey={sortKey} ariaSort={ariaSort} toggle={toggleSort} />
                <Th k="attack_score" label="Attack score" sortKey={sortKey} ariaSort={ariaSort} toggle={toggleSort} />
                <Th k="src_ip" label="Src IP" sortKey={sortKey} ariaSort={ariaSort} toggle={toggleSort} />
                <Th k="dst_ip" label="Dst IP" sortKey={sortKey} ariaSort={ariaSort} toggle={toggleSort} />
                <Th k="model_name" label="Model" sortKey={sortKey} ariaSort={ariaSort} toggle={toggleSort} />
              </tr>
            </thead>
            <tbody>
              {sorted.map((a) => (
                <tr key={a.id}>
                  <td className="mono">{new Date(a.timestamp).toISOString().replace("T", " ").slice(0, 19)}</td>
                  <td>{a.verdict}</td>
                  <td><SeverityBadge severity={a.severity} /></td>
                  <td>
                    <div className="progress" aria-label={`attack score ${a.attack_score.toFixed(2)}`}>
                      <span style={{ width: `${Math.round(a.attack_score * 100)}%` }} />
                    </div>
                    <small className="mono">{a.attack_score.toFixed(2)}</small>
                  </td>
                  <td className="mono">{a.src_ip ?? "—"}</td>
                  <td className="mono">{a.dst_ip ?? "—"}</td>
                  <td className="mono">{a.model_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

interface ThProps {
  k: SortKey;
  label: string;
  sortKey: SortKey;
  ariaSort: (k: SortKey) => "ascending" | "descending" | "none";
  toggle: (k: SortKey) => void;
}
function Th({ k, label, sortKey, ariaSort, toggle }: ThProps) {
  return (
    <th
      scope="col"
      aria-sort={ariaSort(k)}
      onClick={() => toggle(k)}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), toggle(k))}
      tabIndex={0}
    >
      {label}{" "}
      <span className="sort-arrow" aria-hidden>
        {sortKey === k ? (ariaSort(k) === "ascending" ? "▲" : "▼") : "↕"}
      </span>
    </th>
  );
}
