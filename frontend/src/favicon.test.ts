import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

test("frontend entrypoint declares a favicon asset for the page", () => {
  const indexPath = resolve(__dirname, "..", "index.html");
  const html = readFileSync(indexPath, "utf8");

  expect(html).toMatch(/<link\s+rel="icon"\s+type="image\/svg\+xml"\s+href="\/favicon\.svg"\s*\/?>/i);
  expect(existsSync(resolve(__dirname, "..", "public", "favicon.svg"))).toBe(true);
});
