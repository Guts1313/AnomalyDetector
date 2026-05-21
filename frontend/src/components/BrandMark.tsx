import "./BrandMark.css";

/**
 * Animated radar / network-pulse logo mark.
 * - Center node "breathes" (scale)
 * - Three concentric rings pulse outward with staggered delay
 * - SVG strokes pick up the current --accent via currentColor
 */
export default function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <svg
      className="brand-mark"
      width={size}
      height={size}
      viewBox="0 0 40 40"
      aria-hidden
      role="img"
    >
      <defs>
        <radialGradient id="bm-core" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="currentColor" stopOpacity="1" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </radialGradient>
      </defs>

      <circle className="bm-ring bm-ring-1" cx="20" cy="20" r="6" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle className="bm-ring bm-ring-2" cx="20" cy="20" r="6" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle className="bm-ring bm-ring-3" cx="20" cy="20" r="6" fill="none" stroke="currentColor" strokeWidth="1.5" />

      <circle className="bm-halo" cx="20" cy="20" r="9" fill="url(#bm-core)" />
      <circle className="bm-core" cx="20" cy="20" r="4" fill="currentColor" />
    </svg>
  );
}
