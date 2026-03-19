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

  expect(css).toMatch(/:root\s*\{[^}]*color-scheme:\s*light;/s);
  expect(css).toMatch(/:root\s*\{[^}]*--color-page-bg:\s*#f3f6fb;/s);
  expect(css).toMatch(/:root\s*\{[^}]*--color-accent:\s*#2f6b9a;/s);
  expect(css).toMatch(/:root\s*\{[^}]*--color-surface:\s*rgba\(255,\s*255,\s*255,\s*0\.94\);/s);
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

test("gives shared buttons a stronger visual weight and more deliberate proportions", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/button\s*\{[^}]*min-height:\s*48px;/s);
  expect(css).toMatch(/button\s*\{[^}]*padding:\s*0\.7rem\s+1\.15rem;/s);
  expect(css).toMatch(/button\s*\{[^}]*border-radius:\s*14px;/s);
  expect(css).toMatch(/button\s*\{[^}]*letter-spacing:\s*0\.01em;/s);
});

test("uses roomier action spacing around grouped controls and card actions", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.action-row\s*\{[^}]*gap:\s*0\.75rem;/s);
  expect(css).toMatch(/\.action-row\s*\{[^}]*margin-top:\s*1rem;/s);
  expect(css).toMatch(/\.prompt-item__actions\s*\{[^}]*gap:\s*0\.65rem;/s);
  expect(css).toMatch(/\.prompt-item__actions\s*\{[^}]*margin-top:\s*0\.75rem;/s);
  expect(css).toMatch(/\.prompt-item__actions\s*>\s*button,\s*\.prompt-item__actions\s*>\s*a\s*\{[^}]*min-height:\s*46px;/s);
  expect(css).toMatch(/\.button-secondary:hover:not\(:disabled\)\s*\{[^}]*transform:\s*translateY\(-1px\);/s);
  expect(css).toMatch(/\.button-danger:hover:not\(:disabled\)\s*\{[^}]*transform:\s*translateY\(-1px\);/s);
  expect(css).toMatch(/\.room-card__link:hover\s*\{[^}]*transform:\s*translateY\(-1px\);/s);
  expect(css).toMatch(/\.room-card\s+\.prompt-item__actions\s*\{[^}]*justify-content:\s*flex-end;/s);
  expect(css).toMatch(/\.room-card\s+\.prompt-item__actions\s*\{[^}]*align-self:\s*center;/s);
});

test("uses a larger and taller prompt preview frame so style thumbnails are less aggressively cropped", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.prompt-card__media\s*\{[^}]*width:\s*148px;/s);
  expect(css).toMatch(/\.prompt-card__media\s*\{[^}]*height:\s*112px;/s);
  expect(css).toMatch(/\.prompt-card__media\s*\{[^}]*overflow:\s*hidden;/s);
  expect(css).toMatch(/\.prompt-card__media img\s*\{[^}]*width:\s*100%;/s);
  expect(css).toMatch(/\.prompt-card__media img\s*\{[^}]*height:\s*100%;/s);
});

test("keeps the public landing chooser free from nested box-in-box framing", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.public-landing-page__content\s*\{[^}]*display:\s*grid;/s);
  expect(css).toMatch(/\.public-landing-page__rooms\s*\{[^}]*padding:\s*0;/s);
  expect(css).toMatch(/\.public-landing-page__rooms\s*\{[^}]*border:\s*0;/s);
  expect(css).toMatch(/\.public-landing-page__rooms\s*\{[^}]*background:\s*transparent;/s);
  expect(css).toMatch(/\.public-landing-page__form\s*\{[^}]*padding:\s*1rem;/s);
  expect(css).toMatch(/\.public-landing-page__form\s*\{[^}]*border:\s*1px solid rgba\(103,\s*124,\s*145,\s*0\.18\);/s);
  expect(css).toMatch(/\.public-landing-page__room\s*\{[^}]*min-height:\s*180px;/s);
});

test("uses calmer public landing gradients instead of strong icy radial highlights", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.public-landing-page__panel\s*\{[^}]*background:\s*linear-gradient\(180deg,\s*rgba\(255,\s*255,\s*255,\s*0\.92\),\s*rgba\(246,\s*249,\s*252,\s*0\.94\)\);/s);
  expect(css).toMatch(/\.public-landing-page__room\s*\{[^}]*background:\s*linear-gradient\(180deg,\s*rgba\(255,\s*255,\s*255,\s*0\.96\),\s*rgba\(246,\s*249,\s*252,\s*0\.98\)\);/s);
  expect(css).toMatch(/\.public-landing-page__room\.is-selected\s*\{[^}]*background:\s*linear-gradient\(180deg,\s*rgba\(235,\s*242,\s*248,\s*0\.98\),\s*rgba\(245,\s*249,\s*252,\s*0\.99\)\);/s);
  expect(css).toMatch(/\.public-landing-page__form\s*\{[^}]*background:\s*linear-gradient\(180deg,\s*rgba\(250,\s*252,\s*254,\s*0\.98\),\s*rgba\(244,\s*248,\s*251,\s*0\.98\)\);/s);
});

test("keeps the public landing panel content-sized instead of forcing a tall empty shell", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.public-landing-page__panel\s*\{[^}]*gap:\s*1rem;/s);
  expect(css).toMatch(/\.public-landing-page__panel\s*\{[^}]*min-height:\s*0;/s);
  expect(css).toMatch(/\.public-landing-page__content\s*\{[^}]*gap:\s*0\.85rem;/s);
  expect(css).toMatch(/\.public-landing-page__rooms-panel\s*\{[^}]*gap:\s*0\.65rem;/s);
});

test("anchors the public landing login action inside the panel header instead of a detached top bar", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.public-landing-page__panel-head\s*\{[^}]*display:\s*grid;/s);
  expect(css).toMatch(/\.public-landing-page__panel-head\s*\{[^}]*gap:\s*0\.85rem;/s);
  expect(css).toMatch(/\.public-landing-page__admin-link\s*\{[^}]*justify-self:\s*start;/s);
  expect(css).toMatch(/\.public-landing-page__admin-link:hover\s*\{[^}]*border-color:\s*rgba\(47,\s*107,\s*154,\s*0\.32\);/s);
  expect(css).toMatch(/\.public-landing-page__admin-link:hover\s*\{[^}]*background:\s*rgba\(245,\s*249,\s*253,\s*0\.98\);/s);
  expect(css).toMatch(/\.public-landing-page__admin-link:focus-visible\s*\{[^}]*box-shadow:\s*0 0 0 4px rgba\(47,\s*107,\s*154,\s*0\.12\)/s);
  expect(css).not.toMatch(/\.public-landing-page__header\s*\{/s);
});

test("uses one light-surface hover and focus language instead of sending public cards through the dark primary button hover", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(
    /button:hover:not\(:disabled\):not\(\.style-card\):not\(\.button-secondary\):not\(\.button-danger\):not\(\.capture-style-item\):not\(\.capture-screen__button\):not\(\.public-landing-page__room\):not\(\.public-landing-page__target\)/s
  );
  expect(css).toMatch(/\.public-landing-page__room:hover\s*\{[^}]*color:\s*var\(--color-text\);/s);
  expect(css).toMatch(/\.public-landing-page__room:hover\s*\{[^}]*box-shadow:\s*0 10px 24px rgba\(64,\s*87,\s*109,\s*0\.12\);/s);
  expect(css).toMatch(/\.public-landing-page__target:hover\s*\{[^}]*background:\s*rgba\(245,\s*249,\s*253,\s*0\.98\);/s);
  expect(css).toMatch(
    /\.public-landing-page__admin-link:focus-visible,\s*\.public-landing-page__room:focus-visible,\s*\.public-landing-page__target:focus-visible,\s*\.room-card__link:focus-visible,\s*\.button-secondary:focus-visible\s*\{[^}]*box-shadow:\s*0 0 0 4px rgba\(47,\s*107,\s*154,\s*0\.12\)/s
  );
});

test("keeps danger buttons on their danger hover instead of falling back to the generic blue button hover", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(
    /button:hover:not\(:disabled\):not\(\.style-card\):not\(\.button-secondary\):not\(\.button-danger\):not\(\.capture-style-item\):not\(\.capture-screen__button\):not\(\.public-landing-page__room\):not\(\.public-landing-page__target\)/s
  );
  expect(css).toMatch(/\.button-danger:hover:not\(:disabled\)\s*\{[^}]*background:\s*#a94d4a;/s);
  expect(css).toMatch(/\.button-danger:hover:not\(:disabled\)\s*\{[^}]*border-color:\s*#a94d4a;/s);
});

test("keeps llm routing controls on a dedicated stack instead of mixing manual margins", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.routing-stack\s*\{[^}]*display:\s*grid;/s);
  expect(css).toMatch(/\.routing-stack\s*\{[^}]*gap:\s*0\.9rem;/s);
  expect(css).toMatch(/\.routing-stack\s*>\s*\.action-row\s*\{[^}]*margin-top:\s*0;/s);
});

test("keeps routing feedback centered and compact after reducing the success copy to one line", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.routing-feedback\s*\{[^}]*align-items:\s*center;/s);
  expect(css).toMatch(/\.routing-feedback\s*\{[^}]*padding:\s*0\.75rem\s+0\.9rem;/s);
  expect(css).toMatch(/\.routing-feedback::before\s*\{[^}]*width:\s*1\.4rem;/s);
  expect(css).toMatch(/\.routing-feedback::before\s*\{[^}]*height:\s*1\.4rem;/s);
  expect(css).toMatch(/\.routing-feedback::before\s*\{[^}]*margin-top:\s*0;/s);
});

test("uses a dedicated routing status chip instead of the generic detail pill styling", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.routing-status-chip\s*\{[^}]*display:\s*inline-flex;/s);
  expect(css).toMatch(/\.routing-status-chip\s*\{[^}]*gap:\s*0\.45rem;/s);
  expect(css).toMatch(/\.routing-status-chip\s*\{[^}]*width:\s*fit-content;/s);
  expect(css).toMatch(/\.routing-status-chip\s*\{[^}]*border-radius:\s*999px;/s);
  expect(css).toMatch(/\.routing-status-chip__dot\s*\{[^}]*width:\s*0\.6rem;/s);
  expect(css).toMatch(/\.routing-status-chip__label\s*\{/s);
  expect(css).toMatch(/\.routing-status-chip__value\s*\{/s);
  expect(css).toMatch(/\.routing-status-chip--disabled\s*\{/s);
  expect(css).toMatch(/\.routing-status-chip--enabled\s*\{/s);
});

test("renders the active-room checkbox with a dedicated custom control instead of the browser default", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.checkbox-field\s*\{/s);
  expect(css).toMatch(/\.checkbox-field\s*\{[^}]*align-items:\s*flex-start;/s);
  expect(css).toMatch(/\.checkbox-field\s*\{[^}]*padding-top:\s*0\.2rem;/s);
  expect(css).toMatch(/\.checkbox-input\s*\{[^}]*appearance:\s*none;/s);
  expect(css).toMatch(/\.checkbox-input\s*\{[^}]*border-radius:\s*8px;/s);
  expect(css).toMatch(/\.checkbox-input::after\s*\{[^}]*width:\s*5px;/s);
  expect(css).toMatch(/\.checkbox-input::after\s*\{[^}]*height:\s*9px;/s);
  expect(css).toMatch(/\.checkbox-input::after\s*\{[^}]*border-right:\s*2px solid transparent;/s);
  expect(css).toMatch(/\.checkbox-input:checked::after\s*\{/s);
});

test("uses explicit field stacks so admin room form keeps equal spacing between fields", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.field-stack\s*\{[^}]*display:\s*grid;/s);
  expect(css).toMatch(/\.field-stack\s*\{[^}]*gap:\s*0\.4rem;/s);
  expect(css).toMatch(/\.form-grid\s*\{[^}]*gap:\s*0\.9rem;/s);
});

test("renders prompt preview uploads with the same surface language as the other form fields", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/\.file-upload-field\s*\{[^}]*position:\s*relative;/s);
  expect(css).toMatch(/\.file-upload-field__surface\s*\{[^}]*display:\s*grid;/s);
  expect(css).toMatch(/\.file-upload-field__surface\s*\{[^}]*min-height:\s*104px;/s);
  expect(css).toMatch(/\.file-upload-field__surface\s*\{[^}]*border:\s*1px solid var\(--color-border\);/s);
  expect(css).toMatch(/\.file-upload-field__surface\s*\{[^}]*border-radius:\s*var\(--radius-control\);/s);
  expect(css).toMatch(/\.file-upload-field__surface\s*\{[^}]*background:\s*var\(--color-surface-raised\);/s);
  expect(css).toMatch(/\.file-upload-field__input\s*\{[^}]*opacity:\s*0;/s);
  expect(css).toMatch(/\.file-upload-field--has-file\s+\.file-upload-field__surface\s*\{[^}]*border-color:\s*rgba\(47,\s*107,\s*154,\s*0\.36\);/s);
  expect(css).not.toMatch(/\.file-upload-field__eyebrow\s*\{/s);
});

test("does not apply generic text-input sizing styles to the custom checkbox and prompt upload controls", () => {
  const stylesPath = resolve(__dirname, "styles.css");
  const css = readFileSync(stylesPath, "utf8");

  expect(css).toMatch(/input:not\(\.checkbox-input\):not\(\.file-upload-field__input\),\s*select,\s*textarea\s*\{/s);
  expect(css).toMatch(/input:not\(\.checkbox-input\):not\(\.file-upload-field__input\):focus,\s*select:focus,\s*textarea:focus\s*\{/s);
});
