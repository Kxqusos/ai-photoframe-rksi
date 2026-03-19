import { readFileSync } from "node:fs";
import { resolve } from "node:path";

test("frontend entrypoint imports StrictMode explicitly instead of relying on a global React object", () => {
  const entryPath = resolve(__dirname, "main.tsx");
  const source = readFileSync(entryPath, "utf8");

  expect(source).toMatch(/import\s+\{\s*StrictMode\s*\}\s+from\s+"react";/);
  expect(source).toContain("<StrictMode>");
  expect(source).toContain("</StrictMode>");
});
