/** Purpose: turn a run result into the sentence and table shown in chat. Used by: views/chat.tsx. */
import { prettyName } from "../labels";
import type { StreamEvent } from "../stream";

export function answerOf(result: Record<string, unknown>, error = "") {
  if (error) return error;
  const products = productRows(result);
  if (products.length === 1) {
    const product = products[0];
    return `${product.name} is ${money(product.price)}, with ${product.stock} in stock.`;
  }
  if (products.length > 1) {
    return products.map((product) => `${product.name} — ${money(product.price)}, ${product.stock} in stock`).join("\n");
  }
  if (typeof result.answer === "string" && result.answer.trim()) return result.answer;
  if (typeof result.explanation === "string" && result.explanation.trim()) return result.explanation;
  return "The agent answered.";
}

function productRows(result: Record<string, unknown>) {
  if (!Array.isArray(result.products)) return [];
  return result.products.map((item) => {
    const product = item as { product_id?: string; name?: string; price?: number; stock?: number };
    return {
      id: product.product_id || product.name || "product",
      name: product.name || product.product_id || "Product",
      price: product.price,
      stock: product.stock ?? "—",
    };
  });
}

function money(value: number | undefined) {
  return value === undefined ? "—" : `$${value}`;
}

export function AnswerBody({ text, result }: { text: string; result?: Record<string, unknown> }) {
  const products = result ? productRows(result) : [];
  const explanation = typeof result?.explanation === "string" ? result.explanation : "";
  const scalars = result
    ? Object.entries(result).filter(([key, value]) => !["products", "sources", "explanation", "answer"].includes(key) && (typeof value === "string" || typeof value === "number" || typeof value === "boolean"))
    : [];
  return (
    <div className="answer-block">
      <p className="answer-text">{text}</p>
      {products.length ? (
        <table className="product-table">
          <thead><tr><th>Product</th><th>Price</th><th>Stock</th></tr></thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}><td>{product.name}</td><td>{money(product.price)}</td><td>{product.stock}</td></tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {explanation && explanation !== text ? <p className="muted">{explanation}</p> : null}
      {scalars.length ? (
        <dl className="result">
          {scalars.map(([key, value]) => (
            <div key={key}><dt>{prettyName(key)}</dt><dd>{String(value)}</dd></div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}

export function sourcesOf(run: NonNullable<StreamEvent["run"]>) {
  const counts = new Map<string, number>();
  for (const step of run.agents) {
    const value = step.result.sources;
    if (!Array.isArray(value)) continue;
    for (const item of value) {
      const id = typeof item === "string" ? item : String((item as { source_id?: string }).source_id || "");
      if (!id) continue;
      counts.set(id, (counts.get(id) || 0) + 1);
    }
  }
  return [...counts.entries()].map(([id, count]) => ({ id, count }));
}
