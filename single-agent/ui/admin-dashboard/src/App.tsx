/** Purpose: harness settings and one chat bound to desk-agent. Used by main.tsx. */
import { useState } from "react";
import { AgentRun } from "./agent/run";
import { HarnessSettings } from "./settings";

export function App() {
  const [harness, setHarness] = useState("");
  return (
    <main>
      <h1>Desk agent</h1>
      <HarnessSettings onChange={setHarness} />
      <AgentRun harness={harness} />
    </main>
  );
}
