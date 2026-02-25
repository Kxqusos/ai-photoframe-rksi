import { DEFAULT_ROOM_SLUG, normalizeRoomSlug } from "./roomRouting";

function styleStorageKey(roomSlug: string): string {
  return `ai_photoframe.selected_style_id.${normalizeRoomSlug(roomSlug)}`;
}

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

export function readStoredStyleId(roomSlug: string = DEFAULT_ROOM_SLUG): number | null {
  if (typeof window === "undefined") {
    return null;
  }
  return parseStyleId(window.localStorage.getItem(styleStorageKey(roomSlug)));
}

export function writeStoredStyleId(styleId: number, roomSlug: string = DEFAULT_ROOM_SLUG): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(styleStorageKey(roomSlug), String(styleId));
}

export function readStyleIdFromQuery(search: string): number | null {
  return parseStyleId(new URLSearchParams(search).get("selectedId"));
}
