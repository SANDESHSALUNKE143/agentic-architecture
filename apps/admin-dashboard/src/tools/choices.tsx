/** Purpose: the tool list on an agent, including tools that cannot be turned on yet. Used by: configuration. */
import { Checkbox } from "@agentic/controls";
import type { EndpointConfig } from "../plugins";
import { connectionState, type ToolConnection } from "../tools";

export function ToolChoices({
  tools,
  selected,
  permissions,
  endpoints,
  labelFor,
  onToggle,
}: {
  tools: ToolConnection[];
  selected: string[];
  permissions: Record<string, boolean>;
  endpoints: EndpointConfig[];
  labelFor: (value: string) => string;
  onToggle: (name: string) => void;
}) {
  return (
    <div className="tool-list">
      {tools.map((tool) => {
        const connection = connectionState(tool, endpoints);
        const allowed = Boolean(permissions[tool.permission]);
        const ready = allowed && connection.ready;
        const detail = allowed ? connection.detail : `This contract does not grant ${tool.permission}.`;
        return (
          <div key={tool.name} className="tool-choice">
            <Checkbox label={labelFor(tool.name)} checked={ready && selected.includes(tool.name)} disabled={!ready} onChange={() => onToggle(tool.name)} />
            <small>{tool.summary}</small>
            <small>{detail}</small>
          </div>
        );
      })}
    </div>
  );
}
