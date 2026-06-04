import type { PredictResponse } from "../api/types";
import { SeverityBadge, CategoryBadge, CATEGORY_COLOR } from "./Badge";
import PlotlyChart from "./PlotlyChart";

const PROB_BAR = "#3b82f6";

interface Props {
  result: PredictResponse;
  title?: string;
}

export default function VerdictCard({ result, title = "Verdict" }: Props) {
  const v = result.verdicts[0];
  if (!v) return null;
  const probs = Object.entries(v.class_probabilities ?? {})
    .sort((a, b) => b[1] - a[1]);
  // Show probability of the predicted class, not attack_score. For BENIGN
  // verdicts attack_score is the *complement* (~1 - p(BENIGN)), which reads
  // as a confusingly low number next to a confident BENIGN bar in the chart.
  const verdictProb = v.class_probabilities?.[v.verdict] ?? v.attack_score;

  return (
    <div className="card">
      <header style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 10, marginBottom: 8 }}>
        <h2 style={{ margin: 0 }}>{title}:</h2>
        <CategoryBadge category={v.verdict} />
        <SeverityBadge severity={v.severity} />
        <span className="mono" style={{ color: "var(--text-muted)" }}>
          score {verdictProb.toFixed(3)}
        </span>
      </header>

      {probs.length > 0 && (
        <PlotlyChart
          height={300}
          title="Class probabilities"
          data={[
            {
              type: "bar",
              x: probs.map(([k]) => k),
              y: probs.map(([, p]) => p),
              marker: {
                color: probs.map(([k]) => CATEGORY_COLOR[k] ?? PROB_BAR),
              },
              hovertemplate: "<b>%{x}</b><br>p = %{y:.3f}<extra></extra>",
            },
          ]}
          layout={{ yaxis: { range: [0, 1] }, showlegend: false }}
        />
      )}

      <small style={{ color: "var(--text-muted)" }}>
        Model: <code>{result.model_name}</code> ({result.model_family}) · threshold used:{" "}
        <code>{result.threshold_used ?? "—"}</code>
      </small>
    </div>
  );
}
