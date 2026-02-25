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

export type PublicRoute =
  | { page: "capture"; roomSlug: string }
  | { page: "gallery"; roomSlug: string }
  | { page: "result"; roomSlug: string; jpgHash: string };

export function resolvePublicRoute(pathname: string): PublicRoute | null {
  const clean = pathname || "/";
  if (clean === "/") {
    return { page: "capture", roomSlug: DEFAULT_ROOM_SLUG };
  }

  const roomGallery = clean.match(/^\/([^/]+)\/gallery\/?$/i);
  if (roomGallery) {
    return { page: "gallery", roomSlug: normalizeRoomSlug(roomGallery[1]) };
  }

  const roomResult = clean.match(/^\/([^/]+)\/result\/([^/]+)\/?$/i);
  if (roomResult) {
    return { page: "result", roomSlug: normalizeRoomSlug(roomResult[1]), jpgHash: roomResult[2] };
  }

  const roomCapture = clean.match(/^\/([^/]+)\/?$/i);
  if (roomCapture) {
    return { page: "capture", roomSlug: normalizeRoomSlug(roomCapture[1]) };
  }

  if (clean === "/gallery") {
    return { page: "gallery", roomSlug: DEFAULT_ROOM_SLUG };
  }

  const legacyResult = clean.match(/^\/result\/([^/]+)\/?$/i);
  if (legacyResult) {
    return { page: "result", roomSlug: DEFAULT_ROOM_SLUG, jpgHash: legacyResult[1] };
  }

  return null;
}
