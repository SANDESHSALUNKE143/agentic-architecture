/** Purpose: the configuration sections for one agent. Used by: the agent workspace. */
import { Checkbox, NumberField, Select, TextArea } from "@agentic/controls";
import { EndpointForm, type EndpointConfig } from "../plugins";
import { ToolChoices } from "../tools/choices";
import { label } from "./text";
import type { Contract, PlatformSettings, RagOption, Sequence, ToolInfo } from "./types";

const SINK_HOST: Record<string, string> = { otlp: "otlp", log_store: "log_store", grafana: "grafana" };

export function Instructions({ contract, onChange }: { contract: Contract; onChange: (contract: Contract) => void }) {
  return (
    <>
      <TextArea label="Instructions, one step per line" value={contract.instructions.join("\n")} onChange={(value) => onChange({ ...contract, instructions: value.split("\n").filter(Boolean) })} />
      <h3>Approval</h3>
      {contract.approval.amount_gte !== undefined ? (
        <NumberField label="Ask for approval when the amount is at least" value={contract.approval.amount_gte} onChange={(amount_gte) => onChange({ ...contract, approval: { ...contract.approval, amount_gte } })} />
      ) : <p className="muted">This agent has no amount threshold.</p>}
      {(contract.approval.required_for || []).length ? (
        <div className="check-grid">
          {(contract.approval.required_for || []).map((tool) => (
            <Checkbox key={tool} label={`${label(tool)} stays behind approval`} checked disabled />
          ))}
        </div>
      ) : <p className="muted">No write tools on this contract.</p>}
    </>
  );
}

export function Memory({ contract, endpoints, onChange, onSaved, onError }: { contract: Contract; endpoints: EndpointConfig[]; onChange: (contract: Contract) => void; onSaved: () => Promise<void>; onError: (message: string) => void }) {
  const longTerm = String(contract.memory.long_term_memory || "optional") !== "false";
  const neo4j = endpoints.find((item) => item.id === "neo4j");
  return (
    <>
      <Checkbox label="Short-term memory keeps this conversation" checked={Boolean(contract.memory.conversation_state)} onChange={(conversation_state) => onChange({ ...contract, memory: { ...contract.memory, conversation_state } })} />
      <Select
        label="Long-term memory"
        value={String(contract.memory.long_term_memory || "optional")}
        onChange={(long_term_memory) => onChange({ ...contract, memory: { ...contract.memory, long_term_memory } })}
        options={[{ value: "optional", label: "May read saved notes" }, { value: "false", label: "Off" }]}
      />
      {longTerm ? (
        <>
          <p className="muted">Saved notes stay in this API process. The address is this agent's notes host. This build does not open a Neo4j session.</p>
          {neo4j ? <EndpointForm embedded endpoint={neo4j} onSaved={onSaved} onError={onError} /> : null}
        </>
      ) : <p className="muted">Long-term memory is off, so this agent does not read saved notes.</p>}
    </>
  );
}

export function Observability({ contract, platform, endpoints, onChange, onSaved, onError }: { contract: Contract; platform: PlatformSettings; endpoints: EndpointConfig[]; onChange: (contract: Contract) => void; onSaved: () => Promise<void>; onError: (message: string) => void }) {
  return (
    <>
      <p className="muted">Choose what this agent records. Platform trace and evaluation stay in this process. OpenTelemetry, the log store, and Grafana open the address where the record is pushed. This reference still keeps the record here and does not send the raw question. A password is not shown again.</p>
      {(platform.observability || []).map((tool) => {
        const selected = contract.observability.includes(tool.id);
        const host = endpoints.find((item) => item.id === SINK_HOST[tool.id]);
        return (
          <div key={tool.id} className="stack">
            <Checkbox
              label={tool.title}
              checked={selected}
              onChange={() => {
                const next = selected ? contract.observability.filter((item) => item !== tool.id) : [...contract.observability, tool.id];
                onChange({ ...contract, observability: next });
              }}
            />
            {selected && host ? (
              <>
                <p className="muted">This address is for this agent. Saving it does not start shipping traces.</p>
                <EndpointForm embedded endpoint={host} onSaved={onSaved} onError={onError} />
              </>
            ) : null}
          </div>
        );
      })}
    </>
  );
}

export function Retrieval({ contract, platform, endpoints, onChange, onSaved, onError }: { contract: Contract; platform: PlatformSettings; endpoints: EndpointConfig[]; onChange: (contract: Contract) => void; onSaved: () => Promise<void>; onError: (message: string) => void }) {
  const hosts = retrievalHosts(contract).map((id) => endpoints.find((item) => item.id === id)).filter((item): item is EndpointConfig => Boolean(item));
  return (
    <>
      <p className="muted">A host address appears only when this agent selects that store. A password is not shown again.</p>
      <Checkbox label="Read from the index" checked={Boolean(contract.rag?.retrieve)} onChange={(retrieve) => onChange({ ...contract, rag: { ...contract.rag, retrieve } })} />
      <Checkbox label="Capture this turn as a redacted note" checked={Boolean(contract.rag?.capture)} onChange={(capture) => onChange({ ...contract, rag: { ...contract.rag, capture } })} />
      <Choice label="Vector database" value={contract.rag?.vector || "local"} options={platform.rag?.vector || []} onChange={(vector) => onChange({ ...contract, rag: { ...contract.rag, vector } })} />
      <Choice label="Embedding model" value={contract.rag?.embedding || "local"} options={platform.rag?.embedding || []} onChange={(embedding) => onChange({ ...contract, rag: { ...contract.rag, embedding } })} />
      <Choice label="Chat model" value={contract.model?.provider || "platform"} options={platform.rag?.model || []} onChange={(provider) => onChange({ ...contract, model: { provider } })} />
      {hosts.map((endpoint) => (
        <EndpointForm key={endpoint.id} embedded endpoint={endpoint} onSaved={onSaved} onError={onError} />
      ))}
      {hosts.length === 0 ? <p className="muted">The index, the embedding, and the chat model stay in this process.</p> : null}
    </>
  );
}

export function Tools({ contract, tools, endpoints, onChange }: { contract: Contract; tools: ToolInfo[]; endpoints: EndpointConfig[]; onChange: (contract: Contract) => void }) {
  const writes = new Set(tools.filter((tool) => tool.write).map((tool) => tool.name));
  function toggle(name: string) {
    const next = contract.tools.includes(name) ? contract.tools.filter((item) => item !== name) : [...contract.tools, name];
    const required = new Set(contract.approval.required_for || []);
    if (writes.has(name) && next.includes(name)) required.add(name);
    onChange({ ...contract, tools: next, approval: { ...contract.approval, required_for: [...required] } });
  }
  return (
    <>
      <p className="muted">Every registered tool is listed. A tool can be turned on only when this contract already grants its permission and its connection is saved.</p>
      <ToolChoices tools={tools} selected={contract.tools} permissions={contract.permissions} endpoints={endpoints} labelFor={label} onToggle={toggle} />
    </>
  );
}

export function Workflows({ agent, sequences }: { agent: string; sequences: Sequence[] }) {
  const mine = sequences.filter((item) => item.agents.includes(agent));
  if (!mine.length) {
    return <p className="muted">This agent runs on its own. The planner can still choose it from the brief. An n8n webhook is the invoke_n8n tool on a contract, and that call waits for approval.</p>;
  }
  return (
    <>
      <p className="muted">The planner runs one of these sequences in this order. An n8n webhook is the invoke_n8n tool on a contract, and that call waits for approval.</p>
      {mine.map((item) => (
        <article key={item.id} className="collapse">
          <div className="body">
            <strong>{label(item.id)}</strong>
            <ol>
              {item.agents.map((step, index) => <li key={step}>{index + 1}. {label(step)}</li>)}
            </ol>
          </div>
        </article>
      ))}
    </>
  );
}

export function Choice({ label: name, value, options, onChange }: { label: string; value: string; options: RagOption[]; onChange: (value: string) => void }) {
  const current = options.find((option) => option.id === value);
  return (
    <Select
      label={name}
      value={value}
      hint={current?.detail}
      onChange={onChange}
      options={options.map((option) => ({ value: option.id, label: option.title }))}
    />
  );
}

export function retrievalHosts(contract: Contract) {
  const ids: string[] = [];
  if (contract.rag?.vector === "qdrant") ids.push("qdrant");
  if (contract.rag?.vector === "aws") ids.push("aws_vector");
  if (contract.rag?.embedding === "openai" || contract.rag?.embedding === "aws") ids.push("embedding");
  if (contract.model?.provider === "openai" || contract.model?.provider === "aws") ids.push("model");
  return ids;
}
