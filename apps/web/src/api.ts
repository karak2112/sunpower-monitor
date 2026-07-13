export type MetricPoint = {
  value: number;
  unit: string;
  time: string;
  collected_at: string;
  quality: string;
  source: string;
};

export type CurrentResponse = {
  site_id: string;
  livedata: Record<string, MetricPoint>;
  meters: Array<{
    pvs_path_id: string;
    name: string;
    model: string | null;
    last_seen_at: string;
    power_kw: number | null;
    power_time: string | null;
  }>;
  inverters: Array<{
    pvs_path_id: string;
    name: string;
    model: string | null;
    last_seen_at: string;
    power_kw: number | null;
    power_time: string | null;
    collected_at: string | null;
  }>;
  inverter_power_kw_sum: number;
};

export type HealthResponse = {
  status: string;
  database_ok: boolean;
  latest_measurement_at: string | null;
  inverter_devices: number;
  last_collector_run: {
    status: string;
    source: string;
    finished_at: string | null;
    meter_count: number | null;
    inverter_count: number | null;
    measurement_rows: number | null;
    message: string | null;
  } | null;
};

export type Device = {
  id: string;
  device_type: string;
  pvs_path_id: string;
  model: string | null;
  name: string | null;
  rated_watts: number | null;
  grid_row: number | null;
  grid_col: number | null;
  enabled: boolean;
  first_seen_at: string;
  last_seen_at: string;
};

export type HistoryResponse = {
  metric: string;
  start: string;
  end: string;
  count: number;
  points: Array<{
    time: string;
    value: number;
    unit: string;
    quality: string;
    source: string;
    device_type: string;
    pvs_path_id: string;
    name: string | null;
  }>;
};

const API_BASE = "/api";
const TOKEN_KEY = "solar_monitor_api_token";

export function getApiToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function setApiToken(token: string): void {
  if (token.trim()) localStorage.setItem(TOKEN_KEY, token.trim());
  else localStorage.removeItem(TOKEN_KEY);
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const token = getApiToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => apiFetch<HealthResponse>("/health"),
  current: () => apiFetch<CurrentResponse>("/v1/current"),
  devices: () => apiFetch<{ devices: Device[] }>("/v1/devices"),
  history: (metric: string, hours = 24) =>
    apiFetch<HistoryResponse>(
      `/v1/history?metric=${encodeURIComponent(metric)}&device_type=site&pvs_path_id=livedata&hours=${hours}`,
    ),
  updateLayout: (deviceId: string, body: { grid_row?: number; grid_col?: number; name?: string }) =>
    apiFetch<{ device: Device }>(`/v1/devices/${deviceId}/layout`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  exportCsvUrl: (hours = 24) =>
    `${API_BASE}/v1/export.csv?metric=pv_power_kw&device_type=site&pvs_path_id=livedata&hours=${hours}`,
};

const CACHE_KEY = "solar_monitor_last_current";

export function cacheCurrent(data: CurrentResponse): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ savedAt: Date.now(), data }));
  } catch {
    /* ignore quota */
  }
}

export function readCachedCurrent(): { savedAt: number; data: CurrentResponse } | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as { savedAt: number; data: CurrentResponse };
  } catch {
    return null;
  }
}
