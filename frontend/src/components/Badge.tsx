import type { Severity } from "../api/types";

/**
 * Severity and category colors are semantic across themes — keep the raw hex
 * so they can be passed straight to Plotly (which won't resolve CSS variables).
 */
export const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#3b82f6",
  info: "#10b981",
};

export const CATEGORY_COLOR: Record<string, string> = {
  BENIGN: "#10b981",
  DDoS: "#ef4444",
  DoS: "#f97316",
  PortScan: "#06b6d4",
  BruteForce: "#f59e0b",
  WebAttack: "#eab308",
  Botnet: "#a855f7",
  Infiltration: "#ec4899",
};

interface BadgeProps {
  label: string;
  color?: string;
  withDot?: boolean;
}

export function Badge({ label, color = "var(--accent)", withDot = false }: BadgeProps) {
  return (
    <span className="badge" style={{ background: color }} aria-label={label}>
      {withDot && <span className="dot" aria-hidden />}
      {label}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: Severity | string }) {
  const sev = (severity as Severity) in SEVERITY_COLOR ? (severity as Severity) : "info";
  return <Badge label={String(severity).toUpperCase()} color={SEVERITY_COLOR[sev]} withDot />;
}

export function CategoryBadge({ category }: { category: string }) {
  const color = CATEGORY_COLOR[category] ?? "var(--accent)";
  return <Badge label={category} color={color} />;
}
