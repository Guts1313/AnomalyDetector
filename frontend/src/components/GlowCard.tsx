import type { CSSProperties, HTMLAttributes, ReactNode } from "react";

interface GlowCardProps extends Omit<HTMLAttributes<HTMLDivElement>, "children"> {
  children: ReactNode;
  /** Seconds for one full revolution of the snake border. Default: 5s. */
  speed?: number;
  /** Snake border thickness. Default: 1.5px. */
  thickness?: number;
  /** Override the gradient colors (3 stops). Defaults to dark-blue → red → white. */
  colors?: [string, string, string];
}

/**
 * Wrapper component for cards/grid items that adds a rotating conic-gradient
 * "snake" border on top of the existing .card glass surface. Pure CSS — the
 * heavy lifting lives in global.css (.card::before + @property --gradient-angle).
 *
 * Pass props to tune speed/thickness/colors per instance:
 *   <GlowCard speed={3} colors={["#22c55e", "#3b82f6", "#ffffff"]}>...</GlowCard>
 */
export default function GlowCard({
  children,
  speed,
  thickness,
  colors,
  className,
  style,
  ...rest
}: GlowCardProps) {
  const cssVars: CSSProperties = {
    ...(speed != null ? { "--snake-duration": `${speed}s` } : {}),
    ...(thickness != null ? { "--snake-thickness": `${thickness}px` } : {}),
    ...(colors
      ? {
          "--snake-blue": colors[0],
          "--snake-red": colors[1],
          "--snake-white": colors[2],
        }
      : {}),
    ...style,
  } as CSSProperties;

  return (
    <div className={`card${className ? ` ${className}` : ""}`} style={cssVars} {...rest}>
      {children}
    </div>
  );
}
