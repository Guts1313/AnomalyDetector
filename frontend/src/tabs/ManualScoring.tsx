import { useState, type FormEventHandler } from "react";
import { api } from "../api/client";
import type { FlowRecord, PredictResponse, Protocol } from "../api/types";
import { EXAMPLES, findExample } from "../data/examples";
import { useFormStore, type ManualForm } from "../state/FormStore";
import VerdictCard from "../components/VerdictCard";
import { CategoryBadge } from "../components/Badge";

const NUMERIC_FIELDS: Array<{ key: keyof ManualForm; label: string; step?: number; group: 1 | 2 | 3 }> = [
  { key: "flow_duration", label: "Flow duration (μs)", step: 10_000, group: 1 },
  { key: "total_fwd_packets", label: "Total fwd packets", step: 1, group: 1 },
  { key: "total_bwd_packets", label: "Total bwd packets", step: 1, group: 1 },
  { key: "flow_packets_per_s", label: "Packets / s", step: 10, group: 1 },
  { key: "flow_bytes_per_s", label: "Bytes / s", step: 1000, group: 1 },

  { key: "fwd_packet_length_max", label: "Fwd pkt length max", group: 2 },
  { key: "fwd_packet_length_mean", label: "Fwd pkt length mean", group: 2 },
  { key: "bwd_packet_length_max", label: "Bwd pkt length max", group: 2 },
  { key: "bwd_packet_length_mean", label: "Bwd pkt length mean", group: 2 },
  { key: "flow_iat_mean", label: "Flow IAT mean", group: 2 },
  { key: "flow_iat_std", label: "Flow IAT std", group: 2 },

  { key: "syn_flag_count", label: "SYN flag count", group: 3 },
  { key: "ack_flag_count", label: "ACK flag count", group: 3 },
  { key: "psh_flag_count", label: "PSH flag count", group: 3 },
  { key: "rst_flag_count", label: "RST flag count", group: 3 },
  { key: "fin_flag_count", label: "FIN flag count", group: 3 },
];

function flowFromForm(form: ManualForm): FlowRecord {
  const total_length_fwd = form.total_fwd_packets * form.fwd_packet_length_mean;
  const total_length_bwd = form.total_bwd_packets * form.bwd_packet_length_mean;
  return {
    protocol: form.protocol,
    flow_duration: form.flow_duration,
    total_fwd_packets: form.total_fwd_packets,
    total_bwd_packets: form.total_bwd_packets,
    total_length_fwd_packets: total_length_fwd,
    total_length_bwd_packets: total_length_bwd,
    fwd_packet_length_max: form.fwd_packet_length_max,
    fwd_packet_length_mean: form.fwd_packet_length_mean,
    bwd_packet_length_max: form.bwd_packet_length_max,
    bwd_packet_length_mean: form.bwd_packet_length_mean,
    flow_bytes_per_s: form.flow_bytes_per_s,
    flow_packets_per_s: form.flow_packets_per_s,
    flow_iat_mean: form.flow_iat_mean,
    flow_iat_std: form.flow_iat_std,
    fwd_iat_total: form.flow_duration * 0.5,
    bwd_iat_total: form.flow_duration * 0.5,
    fin_flag_count: form.fin_flag_count,
    syn_flag_count: form.syn_flag_count,
    rst_flag_count: form.rst_flag_count,
    psh_flag_count: form.psh_flag_count,
    ack_flag_count: form.ack_flag_count,
    src_ip: form.src_ip,
    dst_ip: form.dst_ip,
  };
}

export default function ManualScoring() {
  const { form, setField, reset, applyExample } = useFormStore();
  const [preset, setPreset] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [verdict, setVerdict] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onLoadPreset = () => {
    if (!preset) return;
    const ex = findExample(preset);
    if (!ex) return;
    applyExample(ex.name, ex.flow as Partial<ManualForm>);
  };

  const onSubmit: FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setVerdict(null);
    try {
      const flow = flowFromForm(form);
      const out = await api.predict({ flows: [flow], threshold: form.threshold });
      setVerdict(out);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  const loadedExample = form.loaded_example ? findExample(form.loaded_example) : undefined;

  return (
    <section aria-labelledby="manual-heading">
      <h1 id="manual-heading">Manual flow scoring</h1>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="field-row">
          <div style={{ flex: "1 1 260px" }}>
            <label className="label" htmlFor="preset">
              Load a preset for any category
            </label>
            <select
              id="preset"
              className="select"
              value={preset}
              onChange={(e) => setPreset(e.target.value)}
            >
              <option value="">— pick a category —</option>
              {EXAMPLES.map((e) => (
                <option key={e.name} value={e.name}>
                  {e.name} — {e.tag}
                </option>
              ))}
            </select>
          </div>
          <button type="button" className="btn btn-primary" onClick={onLoadPreset} disabled={!preset}>
            Load preset
          </button>
          <button type="button" className="btn" onClick={reset}>
            Reset
          </button>
        </div>

        {loadedExample && (
          <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Loaded:</span>
            <CategoryBadge category={loadedExample.name} />
            <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
              {loadedExample.why_short}
            </span>
          </div>
        )}
      </div>

      <form className="card" onSubmit={onSubmit}>
        <div className="grid grid-cols-3">
          <div>
            <div className="field">
              <label className="label" htmlFor="protocol">Protocol</label>
              <select
                id="protocol"
                className="select"
                value={form.protocol}
                onChange={(e) => setField("protocol", e.target.value as Protocol)}
              >
                <option>TCP</option>
                <option>UDP</option>
                <option>ICMP</option>
                <option>OTHER</option>
              </select>
            </div>
            {NUMERIC_FIELDS.filter((f) => f.group === 1).map((f) => (
              <NumField
                key={f.key}
                label={f.label}
                step={f.step}
                value={form[f.key] as number}
                onChange={(v) => setField(f.key, v as never)}
              />
            ))}
          </div>

          <div>
            {NUMERIC_FIELDS.filter((f) => f.group === 2).map((f) => (
              <NumField
                key={f.key}
                label={f.label}
                step={f.step}
                value={form[f.key] as number}
                onChange={(v) => setField(f.key, v as never)}
              />
            ))}
          </div>

          <div>
            {NUMERIC_FIELDS.filter((f) => f.group === 3).map((f) => (
              <NumField
                key={f.key}
                label={f.label}
                step={f.step}
                value={form[f.key] as number}
                onChange={(v) => setField(f.key, v as never)}
              />
            ))}
            <div className="field">
              <label className="label" htmlFor="src_ip">Src IP</label>
              <input
                id="src_ip"
                className="input mono"
                value={form.src_ip}
                onChange={(e) => setField("src_ip", e.target.value)}
              />
            </div>
            <div className="field">
              <label className="label" htmlFor="dst_ip">Dst IP</label>
              <input
                id="dst_ip"
                className="input mono"
                value={form.dst_ip}
                onChange={(e) => setField("dst_ip", e.target.value)}
              />
            </div>
            <div className="field">
              <label className="label" htmlFor="threshold">
                Decision threshold: <span className="mono">{form.threshold.toFixed(2)}</span>
              </label>
              <input
                id="threshold"
                className="input"
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={form.threshold}
                onChange={(e) => setField("threshold", Number(e.target.value))}
              />
            </div>
          </div>
        </div>

        <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Scoring…" : "Score flow"}
          </button>
        </div>

        {error && (
          <div className="card" role="alert" style={{ marginTop: 12, borderColor: "var(--sev-critical)" }}>
            <strong>Prediction failed:</strong> {error}
          </div>
        )}
      </form>

      {verdict && (
        <div style={{ marginTop: 16 }}>
          <VerdictCard result={verdict} />
        </div>
      )}
    </section>
  );
}

interface NumFieldProps {
  label: string;
  value: number;
  step?: number;
  onChange: (v: number) => void;
}
function NumField({ label, value, step, onChange }: NumFieldProps) {
  const id = `num-${label.replace(/\s+/g, "-").toLowerCase()}`;
  return (
    <div className="field">
      <label className="label" htmlFor={id}>{label}</label>
      <input
        id={id}
        className="input mono"
        type="number"
        inputMode="decimal"
        step={step ?? "any"}
        value={Number.isFinite(value) ? value : 0}
        onChange={(e) => onChange(e.target.value === "" ? 0 : Number(e.target.value))}
      />
    </div>
  );
}
