/** Purpose: choose which harness the next run uses. Used by App. */
import { RadioGroup } from "@agentic/controls";
import { useEffect, useState } from "react";
import { api } from "./api";

type Option = { id: string; label: string; detail: string };
type Settings = { harness: string; options: Option[] };

export function HarnessSettings({ onChange }: { onChange: (harness: string) => void }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Settings>("/settings/harness")
      .then((loaded) => {
        setSettings(loaded);
        onChange(loaded.harness);
      })
      .catch((exc: unknown) => setError(exc instanceof Error ? exc.message : "Settings did not load."));
  }, [onChange]);

  async function choose(harness: string) {
    setError("");
    try {
      const saved = await api<Settings>("/settings/harness", {
        method: "PUT",
        body: JSON.stringify({ harness }),
      });
      setSettings(saved);
      onChange(saved.harness);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "The harness was not saved.");
    }
  }

  if (!settings) return <p>{error || "Loading harness settings."}</p>;
  const detail = settings.options.find((option) => option.id === settings.harness)?.detail || "";
  return (
    <section>
      <h2>Harness</h2>
      <RadioGroup
        name="harness"
        value={settings.harness}
        options={settings.options.map((option) => ({ value: option.id, label: option.label }))}
        onChange={choose}
      />
      <p>{detail}</p>
      {error ? <p>{error}</p> : null}
    </section>
  );
}
