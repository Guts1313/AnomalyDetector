export type Protocol = "TCP" | "UDP" | "ICMP" | "OTHER";
export type Severity = "info" | "low" | "medium" | "high" | "critical";

/**
 * All numeric flow features default to 0 server-side, so they are optional
 * here. Only `protocol` is required (matches Pydantic schema).
 */
export interface FlowRecord {
  protocol: Protocol;
  flow_duration?: number;
  total_fwd_packets?: number;
  total_bwd_packets?: number;
  total_length_fwd_packets?: number;
  total_length_bwd_packets?: number;
  fwd_packet_length_max?: number;
  fwd_packet_length_mean?: number;
  bwd_packet_length_max?: number;
  bwd_packet_length_mean?: number;
  flow_bytes_per_s?: number;
  flow_packets_per_s?: number;
  flow_iat_mean?: number;
  flow_iat_std?: number;
  fwd_iat_total?: number;
  bwd_iat_total?: number;
  fin_flag_count?: number;
  syn_flag_count?: number;
  rst_flag_count?: number;
  psh_flag_count?: number;
  ack_flag_count?: number;
  src_ip?: string | null;
  dst_ip?: string | null;
  src_port?: number | null;
  dst_port?: number | null;
}

export interface PredictRequest {
  flows: FlowRecord[];
  threshold?: number;
}

export interface FlowVerdict {
  verdict: string;
  is_attack: boolean;
  attack_score: number;
  severity: Severity;
  class_probabilities: Record<string, number>;
  src_ip?: string | null;
  dst_ip?: string | null;
  timestamp: string;
}

export interface PredictResponse {
  model_name: string;
  model_family: string;
  threshold_used: number | null;
  verdicts: FlowVerdict[];
}

export interface Alert {
  id: number;
  timestamp: string;
  verdict: string;
  is_attack: boolean;
  attack_score: number;
  severity: string;
  src_ip: string | null;
  dst_ip: string | null;
  model_name: string;
}

export interface Health {
  status: "ok" | "degraded";
  model_loaded: boolean;
  model_name: string | null;
  version: string;
}

export interface Metrics {
  total_predictions: number;
  total_alerts: number;
  total_benign: number;
  attacks_by_class: Record<string, number>;
  severity_breakdown: Record<string, number>;
  avg_latency_ms: number;
}
