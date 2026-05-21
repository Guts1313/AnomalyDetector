import type { ReactNode } from "react";
import "./KPI.css";

interface KPIProps {
  label: string;
  value: ReactNode;
  delta?: string;
  hint?: string;
  accent?: string;
}

export default function KPI({ label, value, delta, hint, accent }: KPIProps) {
  return (
    <div className="kpi card" style={accent ? { borderTopColor: accent } : undefined}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value mono">{value}</div>
      {delta && <div className="kpi-delta">{delta}</div>}
      {hint && <div className="kpi-hint">{hint}</div>}
    </div>
  );
}
