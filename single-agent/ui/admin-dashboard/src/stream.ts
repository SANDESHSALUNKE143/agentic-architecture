/** Purpose: read the desk-agent event stream. Used by the chat. */

const TOKEN = "local-dev-token-not-for-production";

export async function streamRun(task: string, sessionId: string, onEvent: (event: Record<string, unknown>) => void) {
  const response = await fetch("/agent-runs/stream", {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ task, session_id: sessionId }),
  });
  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const chunk = await reader.read();
    if (chunk.done) break;
    buffer += decoder.decode(chunk.value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      const line = part.split("\n").find((item) => item.startsWith("data: "));
      if (line) onEvent(JSON.parse(line.slice(6)) as Record<string, unknown>);
    }
  }
}
