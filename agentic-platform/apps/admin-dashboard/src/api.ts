/** One client for the local agent API. */

export const TOKEN_KEY = "agentic-dev-token";

export type TraceEvent = {
  sequence: number;
  stage: string;
  status: string;
  message: string;
  agent_id: string;
  tool_name: string;
  error_code: string;
  duration_ms: number;
};

export type RunResponse = {
  request_id: string;
  status: string;
  selected_agent: string;
  agents: string[];
  planned_agents: string[];
  workflow: string | null;
  result: { summary?: string; data?: Record<string, unknown> };
  tool_calls: { name: string; ok: boolean; result: unknown }[];
  citations: { source_id: string; location: string; title?: string }[];
  requires_approval: boolean;
  requires_qualified_review: boolean;
  approval_id: string | null;
  learned_from: string;
  session_id: string;
  trace: TraceEvent[];
  errors: TraceEvent[];
  run?: RunResponse;
  feedback?: { id: string; note: string; rating: string }[];
};

export type ExampleRow = { id: string; title: string; group: string; task: string };

export type AgentRow = {
  id: string;
  display_name: string;
  description: string;
  allowed_tools: string[];
  permissions: string[];
  approval_policy: string;
  sample_task: string;
};

export type ApprovalRow = {
  id: string;
  agent_id: string;
  action: string;
  summary: string;
  impact: string;
  status: string;
};

function token(): string {
  return sessionStorage.getItem(TOKEN_KEY) || "local-dev-token-not-for-production";
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Authorization: `Bearer ${token()}`,
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => call<{ status: string }>("/health"),
  agents: () => call<{ agents: AgentRow[] }>("/agents"),
  examples: () => call<{ examples: ExampleRow[] }>("/examples"),
  approvals: () => call<{ approvals: ApprovalRow[] }>("/approvals"),
  run: (body: Record<string, unknown>) =>
    call<RunResponse>("/agent-runs", { method: "POST", body: JSON.stringify(body) }),
  getRun: (id: string) => call<RunResponse>(`/agent-runs/${id}`),
  decide: (id: string, decision: "approved" | "rejected") =>
    call<RunResponse>(`/approvals/${id}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision, actor: "operator" }),
    }),
  feedback: (id: string, note: string) =>
    call(`/agent-runs/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ rating: "not_helpful", note }),
    }),
};

/** n8n responses wrap the run. The screens always read one run object. */
export function unwrap(payload: RunResponse): RunResponse {
  return payload.run ? { ...payload.run, feedback: payload.feedback } : payload;
}
