import type { Health } from "../api/types";
import { useTheme } from "../theme/ThemeProvider";
import type { TabDef } from "./Tabs";
import BrandMark from "./BrandMark";
import "./Navbar.css";

interface NavbarProps {
  tabs: TabDef[];
  activeTab: string;
  onTabChange: (id: string) => void;
  health: Health | null;
}

const STATUS_COLOR: Record<string, string> = {
  ok: "var(--sev-info)",
  degraded: "var(--sev-medium)",
  down: "var(--sev-critical)",
};

export default function Navbar({ tabs, activeTab, onTabChange, health }: NavbarProps) {
  const { theme, toggle } = useTheme();
  const status = health?.status ?? "down";
  const color = STATUS_COLOR[status] ?? STATUS_COLOR.down;

  return (
    <header className="navbar" role="banner">
      <a className="sr-only" href="#main">Skip to main content</a>
      <div className="navbar-inner container">
        <div className="brand">
          <BrandMark size={36} />
          <div className="brand-text">
            <strong>Network Anomaly Detector</strong>
            <small>PRP · Fontys Cybersecurity (Attack &amp; Defend)</small>
          </div>
        </div>

        <nav className="tabs" role="tablist" aria-label="Primary">
          {tabs.map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={activeTab === t.id}
              tabIndex={activeTab === t.id ? 0 : -1}
              className={`tab ${activeTab === t.id ? "active" : ""}`}
              onClick={() => onTabChange(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="navbar-meta">
          <div
            className="status-pill"
            title={
              health
                ? `Model: ${health.model_name ?? "—"} · v${health.version}`
                : "API offline"
            }
          >
            <span className="dot" style={{ background: color, color, boxShadow: `0 0 8px ${color}` }} />
            <span className="status-label">{status.toUpperCase()}</span>
          </div>
          <button
            type="button"
            className="theme-toggle"
            onClick={toggle}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          >
            {theme === "dark" ? <MoonIcon /> : <SunIcon />}
          </button>
        </div>
      </div>
    </header>
  );
}

function MoonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}
