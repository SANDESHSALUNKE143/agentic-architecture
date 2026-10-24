/** Purpose: approve or reject a paused write. The actor must differ from the agent. Used by: the console shell. */
import { GearButton, TextField } from "@agentic/controls";
import { useEffect, useState } from "react";
import { api } from "../api";

type Approval = { id: string; agent_id: string; tool: string; status: string; arguments: Record<string, unknown> };

export function ApprovalsView({ onError, onOpenSettings }: { onError: (message: string) => void; onOpenSettings: (agent: string) => void }) {
  const [items, setItems] = useState<Approval[] | null>(null);
  const [actor, setActor] = useState("local-operator");

  async function load() {
    setItems(await api<Approval[]>("/approvals"));
  }

  useEffect(() => {
    load().catch((exc) => onError(readableError(exc)));
  }, [onError]);

  async function decide(id: string, decision: string) {
    onError("");
    try {
      await api(`/approvals/${id}/decision`, { method: "POST", body: JSON.stringify({ decision, actor }) });
      await load();
    } catch (exc) {
      onError(readableError(exc));
    }
  }

  return (
    <div className="pane">
      <div className="pane-scroll stack">
      <section className="card">
        <header>
          <div>
            <p className="eyebrow">Operator</p>
            <h2>Who is deciding</h2>
          </div>
        </header>
        <div className="body">
            <TextField label="The actor cannot approve a request from their own agent." value={actor} onChange={setActor} />
        </div>
      </section>
      {!items ? <p className="card empty">Loading approvals…</p> : null}
      {items && items.length === 0 ? <p className="card empty">No approvals yet. A write above the order threshold will appear here.</p> : null}
      {items?.map((item) => (
        <article key={item.id} className="card">
          <header>
            <div>
              <p className="eyebrow">{label(item.tool)}</p>
              <h2>{label(item.agent_id)}</h2>
              <p className="mono">{item.id}</p>
            </div>
            <div className="row-actions">
              <GearButton label={`Settings for ${label(item.agent_id)}`} onClick={() => onOpenSettings(item.agent_id)} />
              <Status value={item.status} />
            </div>
          </header>
          <div className="body">
            <ResultBody result={item.arguments} />
          </div>
          {item.status === "pending" ? (
            <div className="foot">
              <button className="danger" type="button" onClick={() => decide(item.id, "reject")}>Reject</button>
              <button className="primary" type="button" onClick={() => decide(item.id, "approve")}>Approve</button>
            </div>
          ) : null}
        </article>
      ))}
      </div>
    </div>
  );
}

function Status({ value }: { value: string }) {
  return <span className={`badge ${value}`}>{label(value)}</span>;
}

function ResultBody({ result }: { result: Record<string, unknown> }) {
  const entries = Object.entries(result).filter(([, value]) => value !== "" && value !== null && value !== undefined);
  if (!entries.length) return <p className="muted">No structured result.</p>;
  return (
    <dl className="result">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{label(key)}</dt>
          <dd>{renderValue(key, value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function renderValue(key: string, value: unknown) {
  if (key === "products" && Array.isArray(value)) {
    return (
      <table className="product-table">
        <thead>
          <tr><th>Product</th><th>Price</th><th>Stock</th></tr>
        </thead>
        <tbody>
          {value.map((item) => {
            const product = item as { product_id?: string; name?: string; price?: number; stock?: number };
            return (
              <tr key={product.product_id}>
                <td>{product.name || product.product_id}</td>
                <td>{product.price ?? "—"}</td>
                <td>{product.stock ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  }
  if (key === "sources" && Array.isArray(value)) {
    return (
      <ul>
        {value.map((item, index) => {
          const source = item as { source_id?: string; location?: string };
          return <li key={index}>{source.source_id}{source.location ? ` · ${source.location}` : ""}</li>;
        })}
      </ul>
    );
  }
  if (Array.isArray(value)) {
    if (!value.length) return <span className="muted">None</span>;
    return <span>{value.map((item) => typeof item === "object" ? JSON.stringify(item) : String(item)).join(", ")}</span>;
  }
  if (typeof value === "object" && value) return <span>{JSON.stringify(value)}</span>;
  return <span>{String(value)}</span>;
}

function label(value: string) {
  const known: Record<string, string> = {
    "product-discovery": "Product discovery",
    "customer-support": "Customer support",
    "order-processing": "Order processing",
    "data-analysis": "Data analysis",
    needs_approval: "Needs approval",
    completed: "Completed",
    failed: "Failed",
    pending: "Pending",
    approved: "Approved",
    rejected: "Rejected",
    load_instructions: "The agent loaded its instructions",
    reason: "The agent chose its next step",
    tool: "The agent used a tool",
    persist: "The agent saved its answer",
    product_id: "Product",
    order_id: "Order",
    mean_amount: "Mean amount",
  };
  if (known[value]) return known[value];
  return value.replaceAll("-", " ").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function readableError(exc: unknown) {
  const text = String(exc);
  if (text.includes("401")) return "The access token was rejected.";
  return text.replace(/^Error:\s*/, "");
}
