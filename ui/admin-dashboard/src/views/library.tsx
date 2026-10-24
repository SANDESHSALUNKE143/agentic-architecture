/** Purpose: the agent cards that open a chat. Used by: the console shell. */
import { GearButton } from "@agentic/controls";
import { initials, prettyName, type AgentCard } from "../labels";

export function LibraryView({ agents, onOpen, onOpenSettings }: { agents: AgentCard[]; onOpen: (agent: string) => void; onOpenSettings: (agent: string) => void }) {
  return (
    <div className="library-view">
      <div className="library-intro">
        <p className="eyebrow">Agent library</p>
        <h2>Choose the agent for the job</h2>
        <p>Names, descriptions, and tools come from the contracts this process loaded.</p>
      </div>
      <div className="library-grid">
        {agents.map((agent) => (
          <article key={agent.name} className="library-card">
            <div className="library-card-head">
              <div className="hero-icon" aria-hidden="true">{initials(agent.name)}</div>
              <GearButton label={`Settings for ${prettyName(agent.name)}`} onClick={() => onOpenSettings(agent.name)} />
            </div>
            <h3>{prettyName(agent.name)}</h3>
            <p>{agent.description}</p>
            <div className="capability-row">
              {agent.tools.map((tool) => <span className="chip" key={tool}>{prettyName(tool)}</span>)}
            </div>
            <button type="button" onClick={() => onOpen(agent.name)}>Open chat</button>
          </article>
        ))}
      </div>
    </div>
  );
}

