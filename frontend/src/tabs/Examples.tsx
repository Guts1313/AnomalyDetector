import { useState } from "react";
import { EXAMPLES } from "../data/examples";
import { CategoryBadge } from "../components/Badge";
import { useFormStore, type ManualForm } from "../state/FormStore";
import { api, lab, type AttackResult } from "../api/client";
import type { FlowRecord, PredictResponse } from "../api/types";
import VerdictCard from "../components/VerdictCard";

export default function Examples() {
  const { applyExample } = useFormStore();
  const [busy, setBusy] = useState<string | null>(null);
  const [labBusy, setLabBusy] = useState<string | null>(null);
  const [result, setResult] = useState<{ name: string; res: PredictResponse } | null>(null);
  const [labResult, setLabResult] = useState<{ name: string; res: AttackResult } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const handleLoad = (name: string, flow: Partial<ManualForm>) => {
    applyExample(name, flow);
    setToast(`Loaded ${name} into Manual scoring — switch tabs to see it.`);
    setTimeout(() => setToast(null), 3500);
  };

  const handleSend = async (name: string, flow: FlowRecord) => {
    setBusy(name);
    setError(null);
    setResult(null);
    try {
      const res = await api.predict({ flows: [flow], threshold: 0.5 });
      setResult({ name, res });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const handleRunOnLab = async (name: string) => {
    setLabBusy(name);
    setError(null);
    setLabResult(null);
    try {
      const res = await lab.attack(name, "defender", 8);
      setLabResult({ name, res });
      setToast(
        `Ran ${res.tool} against defender for ${res.duration_s}s — check the Alerts tab for live verdicts.`,
      );
      setTimeout(() => setToast(null), 6000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(
        `Lab attacker unreachable (${msg}). Bring it up with: docker compose -f lab/docker-compose.yml up --build -d`,
      );
    } finally {
      setLabBusy(null);
    }
  };

  return (
    <section aria-labelledby="examples-heading">
      <h1 id="examples-heading">Request examples — one per category</h1>
      <p style={{ color: "var(--text-muted)" }}>
        Each accordion below is a complete <code>POST /predict</code> body the trained model
        is expected to classify as that category. Use <strong>Load into Manual scoring</strong>{" "}
        to copy values into the form, or <strong>Send to /predict</strong> to fire it at the API.
      </p>

      {toast && (
        <div className="card" role="status" aria-live="polite" style={{ borderColor: "var(--sev-info)", marginBottom: 12 }}>
          {toast}
        </div>
      )}

      {EXAMPLES.map((e, i) => (
        <details key={e.name} className="accordion" open={i === 0}>
          <summary>
            <CategoryBadge category={e.name} />
            <span style={{ color: "var(--text-muted)", fontSize: 13 }}>{e.tag} — {e.why_short}</span>
            <span className="chev" aria-hidden>›</span>
          </summary>
          <div className="body">
            <div className="grid grid-cols-2" style={{ marginTop: 12 }}>
              <div>
                <h3>Why these params produce a <code>{e.name}</code> verdict</h3>
                <p>{e.why_full}</p>

                <h3>Key signals the trees split on</h3>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr><th>Feature</th><th>Value</th><th>Why it matters</th></tr>
                    </thead>
                    <tbody>
                      {e.signals.map((s) => (
                        <tr key={s.feature}>
                          <td className="mono">{s.feature}</td>
                          <td className="mono">{s.value}</td>
                          <td>{s.why}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div>
                <h3>Request body</h3>
                <pre className="code"><code>{JSON.stringify({ flows: [e.flow], threshold: 0.5 }, null, 2)}</code></pre>
              </div>
            </div>

            <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn" onClick={() => handleLoad(e.name, e.flow as Partial<ManualForm>)}>
                Load into Manual scoring
              </button>
              <button
                className="btn"
                onClick={() => handleSend(e.name, e.flow as FlowRecord)}
                disabled={busy === e.name}
              >
                {busy === e.name ? "Sending…" : "Send to /predict now"}
              </button>
              <button
                className="btn btn-primary"
                onClick={() => handleRunOnLab(e.name)}
                disabled={labBusy === e.name}
                title="Run the real attack tool against the lab defender container"
              >
                {labBusy === e.name ? "Running on lab…" : "Run on lab"}
              </button>
            </div>

            {labResult && labResult.name === e.name && (
              <div className="card" style={{ marginTop: 12 }}>
                <h3 style={{ margin: 0 }}>
                  Lab attack: <code>{labResult.res.tool}</code>
                </h3>
                <p style={{ color: "var(--text-muted)", fontSize: 13, margin: "6px 0" }}>
                  <code>{labResult.res.command}</code>
                </p>
                <p style={{ color: "var(--text-muted)", fontSize: 12, margin: "6px 0" }}>
                  exit={labResult.res.returncode} · {labResult.res.duration_s}s
                  {labResult.res.timed_out ? " · timed out (expected for flood tools)" : ""}
                </p>
                {labResult.res.stdout && (
                  <pre className="code" style={{ maxHeight: 220 }}>
                    <code>{labResult.res.stdout}</code>
                  </pre>
                )}
                {labResult.res.stderr && (
                  <details>
                    <summary style={{ cursor: "pointer", color: "var(--text-muted)" }}>
                      stderr
                    </summary>
                    <pre className="code" style={{ maxHeight: 180 }}>
                      <code>{labResult.res.stderr}</code>
                    </pre>
                  </details>
                )}
              </div>
            )}

            {result && result.name === e.name && (
              <div style={{ marginTop: 12 }}>
                <VerdictCard result={result.res} title={`Verdict for the ${e.name} preset`} />
              </div>
            )}
          </div>
        </details>
      ))}

      {error && (
        <div className="card" role="alert" style={{ borderColor: "var(--sev-critical)" }}>
          <strong>Prediction failed:</strong> {error}
        </div>
      )}

      <p style={{ color: "var(--text-faint)", fontSize: 12, marginTop: 16 }}>
        Reading the table: <em>feature</em> is the parameter the model is most sensitive to for this
        category, <em>value</em> is the level used in the preset, and <em>why it matters</em>{" "}
        explains the intuition. The same parameters are visualised in{" "}
        <code>docs/anomaly-detector-breakdown.html</code> as a heat map.
      </p>
    </section>
  );
}
