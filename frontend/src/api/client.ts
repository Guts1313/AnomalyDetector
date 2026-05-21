import type {
  Alert,
  Health,
  Metrics,
  PredictRequest,
  PredictResponse,
} from "./types";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api";
const LAB_ATTACKER =
  (import.meta.env.VITE_LAB_ATTACKER_URL as string | undefined) ??
  "http://localhost:8001";
const LAB_DEFENDER =
  (import.meta.env.VITE_LAB_DEFENDER_URL as string | undefined) ??
  "http://localhost:8002";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE}${path}`;
  const r = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new ApiError(r.status, `${r.status} ${r.statusText} — ${text || path}`);
  }
  return (await r.json()) as T;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export const api = {
  health: () => request<Health>("/health"),
  metrics: () => request<Metrics>("/metrics"),
  alerts: (limit = 200) => request<Alert[]>(`/alerts?limit=${limit}`),
  predict: (body: PredictRequest) =>
    request<PredictResponse>("/predict", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

// ---- Lab control plane (Phase 1+2) ----------------------------------------

export interface AttackResult {
  preset: string;
  tool: string;
  command: string;
  returncode: number;
  stdout: string;
  stderr: string;
  duration_s: number;
  timed_out: boolean;
}

export interface BlocksReport {
  raw: string;
  dropped: { source: string; destination: string }[];
  count: number;
  error?: string;
}

async function rawJson<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new ApiError(r.status, `${r.status} ${r.statusText} — ${text || url}`);
  }
  return (await r.json()) as T;
}

export const lab = {
  attack: (preset: string, target = "defender", duration_s = 8) =>
    rawJson<AttackResult>(`${LAB_ATTACKER}/attack`, {
      method: "POST",
      body: JSON.stringify({ preset, target, duration_s }),
    }),
  blocks: () => rawJson<BlocksReport>(`${LAB_DEFENDER}/blocks`),
  attackerHealth: () => rawJson<{ status: string }>(`${LAB_ATTACKER}/health`),
  defenderHealth: () => rawJson<{ status: string }>(`${LAB_DEFENDER}/health`),
};
