const STYLE_STORAGE_KEY = "ai_photoframe.selected_style_id";

function parseStyleId(raw: string | null): number | null {
  if (!raw) {
    return null;
  }
  const value = Number(raw);
  if (!Number.isFinite(value) || value <= 0) {
    return null;
  }
  return value;
}

export function readStoredStyleId(): number | null {
  if (typeof window === "undefined") {
    return null;
  }
  return parseStyleId(window.localStorage.getItem(STYLE_STORAGE_KEY));
}

export function writeStoredStyleId(styleId: number): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STYLE_STORAGE_KEY, String(styleId));
}

export function readStyleIdFromQuery(search: string): number | null {
  return parseStyleId(new URLSearchParams(search).get("selectedId"));
}
