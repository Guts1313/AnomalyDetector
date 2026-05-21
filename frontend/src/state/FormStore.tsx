import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Protocol } from "../api/types";

export interface ManualForm {
  protocol: Protocol;
  flow_duration: number;
  total_fwd_packets: number;
  total_bwd_packets: number;
  flow_packets_per_s: number;
  flow_bytes_per_s: number;
  fwd_packet_length_max: number;
  fwd_packet_length_mean: number;
  bwd_packet_length_max: number;
  bwd_packet_length_mean: number;
  flow_iat_mean: number;
  flow_iat_std: number;
  syn_flag_count: number;
  ack_flag_count: number;
  psh_flag_count: number;
  rst_flag_count: number;
  fin_flag_count: number;
  src_ip: string;
  dst_ip: string;
  threshold: number;
  loaded_example?: string;
}

export const DEFAULTS: ManualForm = {
  protocol: "TCP",
  flow_duration: 120_000,
  total_fwd_packets: 10,
  total_bwd_packets: 8,
  flow_packets_per_s: 50,
  flow_bytes_per_s: 20_000,
  fwd_packet_length_max: 800,
  fwd_packet_length_mean: 450,
  bwd_packet_length_max: 900,
  bwd_packet_length_mean: 500,
  flow_iat_mean: 500,
  flow_iat_std: 200,
  syn_flag_count: 1,
  ack_flag_count: 5,
  psh_flag_count: 1,
  rst_flag_count: 0,
  fin_flag_count: 1,
  src_ip: "10.0.0.5",
  dst_ip: "10.0.0.100",
  threshold: 0.5,
};

interface FormCtx {
  form: ManualForm;
  setField: <K extends keyof ManualForm>(k: K, v: ManualForm[K]) => void;
  reset: () => void;
  applyExample: (name: string, flow: Partial<ManualForm>) => void;
}

const Ctx = createContext<FormCtx | null>(null);

export function FormStoreProvider({ children }: { children: ReactNode }) {
  const [form, setForm] = useState<ManualForm>(DEFAULTS);

  const setField = useCallback<FormCtx["setField"]>((k, v) => {
    setForm((prev) => ({ ...prev, [k]: v }));
  }, []);

  const reset = useCallback(() => {
    setForm({ ...DEFAULTS });
  }, []);

  const applyExample = useCallback<FormCtx["applyExample"]>((name, flow) => {
    setForm((prev) => ({ ...prev, ...flow, loaded_example: name }));
  }, []);

  const value = useMemo(() => ({ form, setField, reset, applyExample }), [
    form,
    setField,
    reset,
    applyExample,
  ]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useFormStore(): FormCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useFormStore must be used inside <FormStoreProvider>");
  return v;
}
