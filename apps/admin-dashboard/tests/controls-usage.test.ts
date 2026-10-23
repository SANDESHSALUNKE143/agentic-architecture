import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

function tsxFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return tsxFiles(path);
    return entry.name.endsWith(".tsx") ? [path] : [];
  });
}

describe("console screens", () => {
  it("take text boxes, checkboxes, and dropdowns from the controls package", () => {
    const root = join(import.meta.dirname, "../src");
    const offenders = tsxFiles(root).filter((file) => /<(input|select|textarea)\b/.test(readFileSync(file, "utf8")));
    expect(offenders).toEqual([]);
  });
});
