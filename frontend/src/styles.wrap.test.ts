import { readFileSync } from "node:fs";
import { resolve } from "node:path";

test("capture style description allows breaking long tokens without overflowing card width", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.capture-style-item__description\s*\{[^}]*min-width:\s*0;/s);
  expect(css).toMatch(/\.capture-style-item__description\s*\{[^}]*overflow-wrap:\s*anywhere;/s);
});
