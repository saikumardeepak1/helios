const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ACCESS_TOKEN_KEY = "helios_access_token";
const REFRESH_TOKEN_KEY = "helios_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_URL}${path}`, { ...init, headers });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? "Request failed");
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export interface RunSummary {
  id: string;
  agent_name: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  span_count: number;
  risk_score: number;
}

export interface ToolCall {
  id: string;
  tool_name: string;
  arguments: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
}

export interface Span {
  id: string;
  parent_span_id: string | null;
  kind: string;
  input: Record<string, unknown> | null;
  output: Record<string, unknown> | null;
  prompt_tokens: number;
  completion_tokens: number;
  started_at: string;
  ended_at: string | null;
  tool_calls: ToolCall[];
}

export interface RunDetail {
  id: string;
  agent_name: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  risk_score: number;
  spans: Span[];
}

export function listRuns(): Promise<RunSummary[]> {
  return apiFetch<RunSummary[]>("/v1/runs");
}

export function getRun(runId: string): Promise<RunDetail> {
  return apiFetch<RunDetail>(`/v1/runs/${runId}`);
}

export interface AgentCost {
  agent_name: string;
  cost_usd: string;
}

export interface DailyCost {
  day: string;
  cost_usd: string;
}

export interface CostSummary {
  total_usd: string;
  by_agent: AgentCost[];
  by_day: DailyCost[];
}

export function getCostSummary(days = 30): Promise<CostSummary> {
  return apiFetch<CostSummary>(`/v1/cost/summary?days=${days}`);
}
