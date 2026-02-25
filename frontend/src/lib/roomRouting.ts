export const DEFAULT_ROOM_SLUG = "main";

export function normalizeRoomSlug(raw: string | null | undefined): string {
  const value = (raw || "").trim().toLowerCase();
  if (!value) {
    return DEFAULT_ROOM_SLUG;
  }
  return value.replace(/[^a-z0-9-]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "") || DEFAULT_ROOM_SLUG;
}

export function buildRoomApiPath(roomSlug: string, suffix: string): string {
  const slug = normalizeRoomSlug(roomSlug);
  const normalizedSuffix = suffix.startsWith("/") ? suffix : `/${suffix}`;
  return `/api/rooms/${encodeURIComponent(slug)}${normalizedSuffix}`;
}
