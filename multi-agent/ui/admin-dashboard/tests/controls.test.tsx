/**
 * Purpose: exercise the shared controls, including the gear and the drawn dropdown.
 * Used by: npm test in apps/admin-dashboard.
 */
import { Checkbox, GearButton, Select, TextField } from "@agentic/controls";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";

afterEach(() => cleanup());

function Harness() {
  const [value, setValue] = useState("local");
  const [checked, setChecked] = useState(false);
  const [text, setText] = useState("");
  return (
    <>
      <Select label="Where this agent stores vectors" value={value} onChange={setValue} options={[{ value: "local", label: "Local index" }, { value: "qdrant", label: "Qdrant" }]} />
      <Checkbox label="Read the index" checked={checked} onChange={setChecked} />
      <TextField label="Direct URL" value={text} onChange={setText} />
    </>
  );
}

describe("controls", () => {
  it("opens a drawn menu instead of the browser dropdown", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    expect(document.querySelector("select")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Where this agent stores vectors" }));
    await user.click(screen.getByRole("option", { name: "Qdrant" }));
    expect(screen.getByRole("button", { name: "Where this agent stores vectors" }).textContent).toContain("Qdrant");
    expect(document.querySelector("[role=listbox]")).toBeNull();
  });

  it("keeps a checkbox beside its label", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const box = screen.getByRole("checkbox", { name: "Read the index" }) as HTMLInputElement;
    expect(box.closest("label")?.textContent).toContain("Read the index");
    await user.click(box);
    expect(box.checked).toBe(true);
  });

  it("edits a text field through the package", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const field = screen.getByRole("textbox", { name: "Direct URL" }) as HTMLInputElement;
    await user.type(field, "https://db.example");
    expect(field.value).toBe("https://db.example");
  });

  it("opens settings from the gear", async () => {
    const user = userEvent.setup();
    let opened = "";
    render(<GearButton label="Settings for Inventory Agent" onClick={() => { opened = "inventory-agent"; }} />);
    const gear = screen.getByRole("button", { name: "Settings for Inventory Agent" });
    expect(gear.querySelector("svg")).toBeTruthy();
    expect(document.querySelector("select")).toBeNull();
    await user.click(gear);
    expect(opened).toBe("inventory-agent");
  });
});
