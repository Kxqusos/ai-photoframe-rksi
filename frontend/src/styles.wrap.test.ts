import { readFileSync } from "node:fs";
import { resolve } from "node:path";

test("capture style description allows breaking long tokens without overflowing card width", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.capture-style-item__description\s*\{[^}]*min-width:\s*0;/s);
  expect(css).toMatch(/\.capture-style-item__description\s*\{[^}]*overflow-wrap:\s*anywhere;/s);
});

test("defines shared UI tokens and layout utilities for the visual system", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/:root\s*\{[^}]*--color-surface:\s*rgba\(9,\s*18,\s*35,\s*0\.9\);/s);
  expect(css).toMatch(/:root\s*\{[^}]*--shadow-panel:/s);
  expect(css).toMatch(/h2,\s*h3\s*\{/s);
  expect(css).toMatch(/h2,\s*h3\s*\{[^}]*line-height:\s*1\.15;/s);
  expect(css).toMatch(/\.layout-split\s*\{/s);
  expect(css).toMatch(/\.sticky-actions\s*\{/s);
  expect(css).toMatch(/\.empty-state\s*\{/s);
});
