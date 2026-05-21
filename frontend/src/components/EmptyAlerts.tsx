import "./EmptyAlerts.css";

/**
 * Animated empty-state SVG: a row of network nodes connected by a baseline,
 * with a vertical scan-beam sweeping across them. Says "monitoring, all clear".
 */
export default function EmptyAlerts({ height = 160 }: { height?: number }) {
  return (
    <svg
      className="empty-alerts"
      viewBox="0 0 320 160"
      width="100%"
      height={height}
      role="img"
      aria-label="No alerts — scanner is active"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <linearGradient id="ea-line" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0" stopColor="currentColor" stopOpacity="0" />
          <stop offset="0.5" stopColor="currentColor" stopOpacity="0.7" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="ea-beam" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="var(--accent)" stopOpacity="0" />
          <stop offset="0.5" stopColor="var(--accent)" stopOpacity="0.85" />
          <stop offset="1" stopColor="var(--accent)" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* baseline */}
      <line x1="20" y1="80" x2="300" y2="80" stroke="url(#ea-line)" strokeWidth="1.2" />

      {/* network nodes */}
      {[40, 90, 140, 190, 240, 290].map((cx, i) => (
        <g key={cx} className="ea-node" style={{ animationDelay: `${i * 0.18}s` }}>
          <circle cx={cx} cy="80" r="6" className="ea-node-ring" />
          <circle cx={cx} cy="80" r="2.5" className="ea-node-dot" />
        </g>
      ))}

      {/* scan beam */}
      <rect className="ea-beam" x="0" y="20" width="22" height="120" fill="url(#ea-beam)" rx="2" />

      {/* "all clear" check */}
      <g className="ea-check" transform="translate(160, 110)">
        <circle cx="0" cy="0" r="16" className="ea-check-bg" />
        <path d="M -6 0 L -1.5 5 L 7 -5" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </g>
    </svg>
  );
}
