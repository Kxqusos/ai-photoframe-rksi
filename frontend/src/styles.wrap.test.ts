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

test("does not keep legacy public room menu or stale capture cta meta styles", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).not.toMatch(/\.public-room-menu__/);
  expect(css).not.toMatch(/\.capture-screen__cta-meta/);
});

test("keeps mobile public screens free from legacy room-menu safe-gutter hacks", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).not.toMatch(/padding-right:\s*calc\(3\.25rem\s*\+\s*env\(safe-area-inset-right,\s*0px\)\)/);
});

test("keeps result back button pinned to the bottom of the qr panel", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.result-download-panel\s*\{[^}]*display:\s*flex;[^}]*flex-direction:\s*column;[^}]*min-height:\s*100%;/s);
  expect(css).toMatch(/\.result-download-qr-slot\s*\{[^}]*flex:\s*1;[^}]*display:\s*flex;[^}]*align-items:\s*center;[^}]*justify-content:\s*center;/s);
  expect(css).toMatch(/\.result-back-button\s*\{[^}]*margin-top:\s*auto;/s);
  expect(css).toMatch(/\.result-qr-link\s*\{[^}]*display:\s*inline-flex;[^}]*justify-content:\s*center;/s);
});

test("keeps result loading title readable instead of breaking every word", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.result-loading-title\s*\{[^}]*max-width:\s*18ch;/s);
  expect(css).toMatch(/\.result-loading-title\s*\{[^}]*line-height:\s*0\.98;/s);
});

test("lets the generated result image fill the full result hero panel", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.result-hero\s*\{[^}]*padding:\s*0;/s);
  expect(css).toMatch(/\.result-hero\s*\{[^}]*overflow:\s*hidden;/s);
  expect(css).toMatch(/\.result-media\s*\{[^}]*height:\s*100%;/s);
  expect(css).toMatch(/\.result-photo\s*\{[^}]*height:\s*100%;/s);
  expect(css).toMatch(/\.result-photo\s*\{[^}]*max-height:\s*none;/s);
  expect(css).toMatch(/\.result-photo\s*\{[^}]*border:\s*0;/s);
});

test("keeps gallery scrollbar clipped inside the rounded viewport", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.gallery-scroll\s*\{[^}]*overflow:\s*hidden;/s);
  expect(css).toMatch(/\.gallery-scroll__viewport\s*\{[^}]*overflow-y:\s*auto;/s);
  expect(css).toMatch(/\.gallery-scroll__viewport\s*\{[^}]*border-radius:\s*inherit;/s);
});
