import { useEffect, useState } from "react";
import { api } from "./api";

type Page = { id: string; title: string; markdown: string };
type Heading = { id: string; title: string; depth: number };

export function DocsView({ onError }: { onError: (message: string) => void }) {
  const [pages, setPages] = useState<Page[]>([]);
  const [current, setCurrent] = useState("");
  const [anchor, setAnchor] = useState("");

  useEffect(() => {
    api<Page[]>("/guide")
      .then((rows) => {
        const order = ["implementation-guide", "architecture-review", "operations", "repository", "architecture", "agent-catalog", "tool-contracts"];
        rows.sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
        setPages(rows);
        setCurrent(rows[0]?.id || "");
      })
      .catch((exc) => onError(String(exc).replace(/^Error:\s*/, "")));
  }, [onError]);

  useEffect(() => {
    if (!anchor) return;
    document.getElementById(anchor)?.scrollIntoView({ block: "start" });
  }, [anchor, current]);

  const page = pages.find((item) => item.id === current);
  if (!page) return <p className="card empty">Loading the repository guide…</p>;

  function open(pageId: string, headingId = "") {
    setCurrent(pageId);
    setAnchor(headingId);
  }

  return (
    <div className="docs-layout">
      <nav className="card docs-nav" aria-label="Documentation">
        {pages.map((item) => (
          <div key={item.id} className="docs-group">
            <button type="button" aria-current={item.id === current && !anchor ? "page" : undefined} onClick={() => open(item.id)}>
              {item.title}
            </button>
            {headingsOf(item.markdown).map((heading) => (
              <button
                key={`${item.id}-${heading.id}`}
                type="button"
                className={heading.depth === 3 ? "docs-section nested" : "docs-section"}
                aria-current={item.id === current && anchor === heading.id ? "true" : undefined}
                onClick={() => open(item.id, heading.id)}
              >
                {heading.title}
              </button>
            ))}
          </div>
        ))}
      </nav>
      <article className="card doc-page">
        <Markdown source={page.markdown} onOpen={(id) => open(id)} />
      </article>
    </div>
  );
}

function headingsOf(markdown: string): Heading[] {
  const found: Heading[] = [];
  for (const line of markdown.split("\n")) {
    const match = /^(#{2,3}) (.+)$/.exec(line);
    if (!match) continue;
    const title = plain(match[2]);
    found.push({ id: slug(title), title, depth: match[1].length });
  }
  return found;
}

function plain(text: string) {
  return text.replace(/`([^`]+)`/g, "$1").replace(/\*\*([^*]+)\*\*/g, "$1").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
}

function slug(text: string) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function Markdown({ source, onOpen }: { source: string; onOpen: (id: string) => void }) {
  const blocks = source.replace(/\r\n/g, "\n").split(/\n{2,}/);
  return (
    <div className="markdown">
      {blocks.map((block, index) => <Block key={index} block={block.trim()} onOpen={onOpen} />)}
    </div>
  );
}

function Block({ block, onOpen }: { block: string; onOpen: (id: string) => void }) {
  if (!block) return null;
  if (block.startsWith("```")) {
    const code = block.replace(/^```[a-z]*\n?/, "").replace(/```$/, "");
    return <pre><code>{code}</code></pre>;
  }
  if (block.startsWith("|")) return <MarkdownTable block={block} />;
  if (block.startsWith("### ")) return heading(block.slice(4), "h4", onOpen);
  if (block.startsWith("## ")) return heading(block.slice(3), "h3", onOpen);
  if (block.startsWith("# ")) return heading(block.slice(2), "h2", onOpen);
  if (/^\d+\.\s/.test(block)) {
    return <ol>{block.split("\n").map((line, index) => <li key={index}>{inline(line.replace(/^\d+\.\s/, ""), onOpen)}</li>)}</ol>;
  }
  if (block.startsWith("- ")) {
    return <ul>{block.split("\n").map((line, index) => <li key={index}>{inline(line.replace(/^- /, ""), onOpen)}</li>)}</ul>;
  }
  if (block.startsWith("![")) {
    const match = block.match(/^!\[([^\]]*)\]\(([^)]+)\)/);
    if (match) {
      const src = match[2].startsWith("http") ? match[2] : `/guide/assets/${match[2].split("/").pop()}`;
      return <img src={src} alt={match[1]} />;
    }
  }
  return <p>{inline(block, onOpen)}</p>;
}

function heading(text: string, level: "h2" | "h3" | "h4", onOpen: (id: string) => void) {
  const id = slug(plain(text));
  const content = inline(text, onOpen);
  if (level === "h2") return <h2 id={id}>{content}</h2>;
  if (level === "h3") return <h3 id={id}>{content}</h3>;
  return <h4 id={id}>{content}</h4>;
}

function MarkdownTable({ block }: { block: string }) {
  const rows = block.split("\n").filter((line) => !/^\|\s*-+/.test(line));
  const cells = rows.map((row) => row.split("|").slice(1, -1).map((cell) => cell.trim()));
  const [head, ...body] = cells;
  return (
    <table className="doc-table">
      <thead><tr>{head.map((cell) => <th key={cell}>{inline(cell, () => undefined)}</th>)}</tr></thead>
      <tbody>
        {body.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{inline(cell, () => undefined)}</td>)}</tr>)}
      </tbody>
    </table>
  );
}

function inline(text: string, onOpen: (id: string) => void) {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g);
  return parts.map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) return <code key={index}>{part.slice(1, -1)}</code>;
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (link) {
      const target = link[2].replace(/^\.\//, "");
      if (target.endsWith(".md")) {
        const id = target.split("/").pop()!.replace(/\.md$/, "");
        return <button key={index} type="button" className="doc-link" onClick={() => onOpen(id)}>{link[1]}</button>;
      }
      return <a key={index} href={link[2]}>{link[1]}</a>;
    }
    return <span key={index}>{part}</span>;
  });
}
