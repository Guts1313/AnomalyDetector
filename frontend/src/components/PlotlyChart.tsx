import { useEffect, useMemo, useState } from "react";
import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";
import type { Data, Layout, Config } from "plotly.js";
import { useTheme } from "../theme/ThemeProvider";

// Bind react-plotly to the minified Plotly bundle to keep payload reasonable.
const Plot = createPlotlyComponent(Plotly as unknown as typeof import("plotly.js"));

interface PlotlyChartProps {
  data: Data[];
  layout?: Partial<Layout>;
  config?: Partial<Config>;
  height?: number;
  title?: string;
  className?: string;
}

function readCssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

export default function PlotlyChart({
  data,
  layout,
  config,
  height = 300,
  title,
  className,
}: PlotlyChartProps) {
  const { theme } = useTheme();
  // re-read tokens whenever theme flips
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = requestAnimationFrame(() => setTick((n) => n + 1));
    return () => cancelAnimationFrame(id);
  }, [theme]);

  const computedLayout = useMemo<Partial<Layout>>(() => {
    const fontColor = readCssVar("--text", "#e5e7eb");
    const axisColor = readCssVar("--axis", "#94a3b8");
    const gridColor = readCssVar("--grid", "rgba(148,163,184,0.18)");
    return {
      title: title ? { text: title, font: { size: 14, color: fontColor } } : undefined,
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: "'Inter', system-ui, sans-serif", color: fontColor, size: 12 },
      margin: { t: title ? 40 : 16, b: 32, l: 48, r: 16 },
      height,
      xaxis: {
        gridcolor: gridColor,
        linecolor: axisColor,
        tickcolor: axisColor,
        zerolinecolor: gridColor,
        automargin: true,
        ...(layout?.xaxis ?? {}),
      },
      yaxis: {
        gridcolor: gridColor,
        linecolor: axisColor,
        tickcolor: axisColor,
        zerolinecolor: gridColor,
        automargin: true,
        ...(layout?.yaxis ?? {}),
      },
      legend: { font: { color: fontColor } },
      hoverlabel: { font: { color: fontColor } },
      ...layout,
    };
  }, [theme, layout, height, title]);

  const mergedConfig: Partial<Config> = {
    displaylogo: false,
    responsive: true,
    modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"],
    ...config,
  };

  return (
    <div className={className} style={{ width: "100%", height }}>
      <Plot
        data={data}
        layout={computedLayout}
        config={mergedConfig}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
