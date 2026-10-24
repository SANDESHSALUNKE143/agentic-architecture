/**
 * Purpose: open POST /agent-runs/stream and yield each server-sent event.
 * Used by: Agent chat. The body is RunBody.
 */
import { token } from "./api";

export type StreamEvent = {
  type: string;
  message?: string;
  workflow?: string;
  agents?: string[];
  agent_id?: string;
  tool?: string;
  status?: string;
  detail?: string;
  result?: Record<string, unknown>;
  tool_calls?: { name: string; status: string }[];
  run?: {
    request_id: string;
    workflow: string;
    status: string;
    error: string;
    approval_id: string;
    agents: { agent_id: string; status: string; result: Record<string, unknown>; tool_calls: { name: string; status: string }[] }[];
    trace: { stage: string; agent_id?: string; tool?: string; status?: string }[];
  };
};

export async function streamRun(body: object, onEvent: (event: StreamEvent) => void): Promise<void> {
  const response = await fetch("/agent-runs/stream", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const line = chunk.split("\n").find((item) => item.startsWith("data: "));
      if (line) onEvent(JSON.parse(line.slice(6)) as StreamEvent);
    }
  }
}
