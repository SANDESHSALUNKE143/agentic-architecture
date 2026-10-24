/** Purpose: one configuration tab for the selected agent. Used by: ConfigCenter. */
import { Checkbox, NumberField, RadioGroup, Select, TextArea } from "@agentic/controls";
import { prettyName } from "../labels";
import type { EndpointConfig } from "../plugins";
import { ToolChoices } from "../tools/choices";
import { HostBlock, ModelHost } from "./pieces";
import type { Contract, ToolInfo } from "./types";

const RECORD_HOST: Record<string, string> = { otlp: "otlp", log_store: "log_store", grafana: "grafana" };

export function ConfigPanels({
  active,
  contract,
  setContract,
  host,
  onError,
  reloadEndpoints,
  toggleTool,
  details,
  setDetails,
  notesOn,
  keySet,
  waiting,
  availableRecords,
  tools,
  endpoints,
}: {
  active: string;
  contract: Contract;
  setContract: (contract: Contract) => void;
  host: (id: string) => EndpointConfig | undefined;
  onError: (message: string) => void;
  reloadEndpoints: () => Promise<void>;
  toggleTool: (name: string) => void;
  details: string[];
  setDetails: (next: string[]) => void;
  notesOn: boolean;
  keySet: boolean;
  waiting: string[];
  availableRecords: { id: string; title: string }[];
  tools: ToolInfo[];
  endpoints: EndpointConfig[];
}) {
  return (
    <>
          {active === "prompt" ? (
            <section className="config-card">
              <h3>Prompt</h3>
              <TextArea label="One step per line. This is the prompt stored on the agent file." value={contract.instructions.join("\n")} onChange={(value) => setContract({ ...contract, instructions: value.split("\n").filter(Boolean) })} />
            </section>
          ) : null}

          {active === "knowledge" ? (
            <section className="config-card">
              <h3>Knowledge base</h3>
              <Checkbox label="Read the index" checked={contract.rag.retrieve} onChange={(retrieve) => setContract({ ...contract, rag: { ...contract.rag, retrieve } })} />
              <div className="config-fields">
                <Select
                  label="Where this agent stores vectors"
                  value={contract.rag.vector}
                  onChange={(vector) => setContract({ ...contract, rag: { ...contract.rag, vector } })}
                  options={[{ value: "local", label: "Local index" }, { value: "qdrant", label: "Qdrant" }, { value: "aws", label: "AWS" }]}
                />
                <Select
                  label="Embedding for this agent"
                  value={contract.rag.embedding}
                  onChange={(embedding) => setContract({ ...contract, rag: { ...contract.rag, embedding } })}
                  options={[{ value: "local", label: "Local embeddings" }, { value: "openai", label: "OpenAI-compatible" }, { value: "aws", label: "AWS" }]}
                />
              </div>
              {contract.rag.vector === "local" && contract.rag.embedding === "local" ? <p className="muted">This agent uses the index and embeddings in this process.</p> : null}
              {contract.rag.vector === "qdrant" ? <HostBlock endpoint={host("qdrant")} onSaved={reloadEndpoints} onError={onError} /> : null}
              {contract.rag.vector === "aws" ? <HostBlock endpoint={host("aws_vector")} onSaved={reloadEndpoints} onError={onError} /> : null}
              {contract.rag.embedding === "openai" || contract.rag.embedding === "aws" ? <HostBlock endpoint={host("embedding")} onSaved={reloadEndpoints} onError={onError} /> : null}
            </section>
          ) : null}

          {active === "ingestion" ? (
            <section className="config-card">
              <h3>Ingestion</h3>
              <Checkbox
                label="Write a redacted note back after a run"
                checked={contract.rag.capture}
                onChange={(capture) => setContract({
                  ...contract,
                  rag: {
                    ...contract.rag,
                    capture,
                    cadence: capture ? (contract.rag.cadence && contract.rag.cadence !== "off" ? contract.rag.cadence : "each_run") : "off",
                  },
                })}
              />
              {contract.rag.capture ? (
                <Select
                  label="How often"
                  value={contract.rag.cadence || "each_run"}
                  onChange={(cadence) => setContract({ ...contract, rag: { ...contract.rag, cadence } })}
                  options={[{ value: "each_run", label: "After each run" }, { value: "hourly", label: "Hourly" }, { value: "daily", label: "Daily" }]}
                />
              ) : <p>This agent does not write the knowledge base back.</p>}
              <p className="muted">After each run is what this process writes. Hourly and daily are stored on the agent file. There is no separate document pipeline.</p>
            </section>
          ) : null}

          {active === "sql" ? (
            <section className="config-card">
              <h3>SQL</h3>
              <Checkbox label="Read the dataset" checked={contract.tools.includes("analyze_dataset")} onChange={() => toggleTool("analyze_dataset")} />
              <p className="muted">Answers in this build come from the local sales fixture. The address below is this agent's database access.</p>
              {host("sql") ? <HostBlock endpoint={host("sql")} onSaved={reloadEndpoints} onError={onError} /> : null}
            </section>
          ) : null}

          {active === "observability" ? (
            <section className="config-card">
              <h3>Observability</h3>
              <p className="muted">Platform trace and evaluation stay in this process. A remote destination shows its URL, connection string, username, and password after you add it. An address does not mean traces are shipping.</p>
              {["platform_trace", "evaluation"].map((id) => (
                <Checkbox
                  key={id}
                  label={`${prettyName(id)} · in this process`}
                  checked={contract.observability.includes(id)}
                  onChange={(checked) => {
                    const next = checked ? [...contract.observability, id] : contract.observability.filter((item) => item !== id);
                    setContract({ ...contract, observability: next });
                  }}
                />
              ))}
              {contract.observability.filter((id) => RECORD_HOST[id]).map((id) => (
                <div key={id}>
                  <p>{prettyName(id)} for this agent.</p>
                  <HostBlock endpoint={host(RECORD_HOST[id])} onSaved={reloadEndpoints} onError={onError} />
                  <button type="button" className="text-button" onClick={() => setContract({ ...contract, observability: contract.observability.filter((item) => item !== id) })}>Remove {prettyName(id)}</button>
                </div>
              ))}
              {availableRecords.length ? (
                <Select
                  label="Add an observability destination"
                  value=""
                  placeholder="None"
                  onChange={(destination) => { if (destination) setContract({ ...contract, observability: [...contract.observability, destination] }); }}
                  options={availableRecords.map((item) => ({ value: item.id, label: item.title }))}
                />
              ) : null}
            </section>
          ) : null}

          {active === "notes" ? (
            <section className="config-card">
              <h3>Notes</h3>
              <Checkbox label="Keep this conversation" checked={Boolean(contract.memory.conversation_state)} onChange={(conversation_state) => setContract({ ...contract, memory: { ...contract.memory, conversation_state } })} />
              <Checkbox label="Read saved notes" checked={notesOn} onChange={(checked) => setContract({ ...contract, memory: { ...contract.memory, long_term_memory: checked ? "optional" : false } })} />
              <p className="muted">Add as many details as this agent file should keep. Each note is one block.</p>
              {details.map((note, index) => (
                <label key={index} className="ui-field">
                  <span>Note {index + 1}</span>
                  <TextArea value={note} onChange={(value) => setDetails(details.map((item, itemIndex) => itemIndex === index ? value : item))} />
                  <button type="button" className="text-button" onClick={() => setDetails(details.filter((_, itemIndex) => itemIndex !== index))}>Remove note {index + 1}</button>
                </label>
              ))}
              <button type="button" className="secondary" onClick={() => setDetails([...details, ""])}>Add a note</button>
            </section>
          ) : null}

          {active === "model" ? (
            <section className="config-card">
              <h3>Model</h3>
              <p className="muted">The choice belongs to this agent. The model key is reported as set or not set. This form has no key field.</p>
              <RadioGroup
                name="provider"
                value={contract.model.provider || "platform"}
                onChange={(provider) => setContract({ ...contract, model: { provider } })}
                options={[{ value: "platform", label: "Platform" }, { value: "openai", label: "OpenAI-compatible" }, { value: "aws", label: "AWS" }]}
              />
              <p>{keySet ? "Model key is set in the process environment." : "Model key is not set. Mock mode answers without one."}</p>
              {contract.model.provider !== "platform" && host("model") ? (
                <ModelHost endpoint={host("model")!} onSaved={reloadEndpoints} onError={onError} />
              ) : null}
            </section>
          ) : null}

          {active === "tools" ? (
            <section className="config-card">
              <h3>Tools</h3>
              <p className="muted">Every registered tool is listed. A tool can be turned on only when this contract already grants its permission and its connection is saved. Open Plugins to save a host, an allowlist, or an MCP server. A write stays behind approval. This page cannot grant a new permission.</p>
              <ToolChoices tools={tools} selected={contract.tools} permissions={contract.permissions} endpoints={endpoints} labelFor={prettyName} onToggle={toggleTool} />
            </section>
          ) : null}

          {active === "approval" ? (
            <section className="config-card">
              <h3>Approval</h3>
              {waiting.length === 0 && contract.approval.amount_gte === undefined ? <p>This agent has no write. Nothing waits for approval.</p> : null}
              {waiting.map((tool) => <p key={tool}>{prettyName(tool)} stays behind approval.</p>)}
              {contract.approval.amount_gte !== undefined ? (
                <NumberField label="Wait when the amount is at least" value={contract.approval.amount_gte} onChange={(amount_gte) => setContract({ ...contract, approval: { ...contract.approval, amount_gte } })} />
              ) : null}
            </section>
          ) : null}

    </>
  );
}
