export const DEFAULT_ROOM_SLUG = "ph000000";
const PUBLIC_ID_PATTERN = /^[a-z0-9]{8}$/;

function normalizePublicId(raw: string | null | undefined): string | null {
  const value = (raw || "").trim().toLowerCase();
  if (!PUBLIC_ID_PATTERN.test(value)) {
    return null;
  }
  return value;
}

export function normalizeRoomSlug(raw: string | null | undefined): string {
  return normalizePublicId(raw) ?? DEFAULT_ROOM_SLUG;
}

export function normalizeResultHash(raw: string | null | undefined): string | null {
  return normalizePublicId(raw);
}

export function buildRoomApiPath(roomSlug: string, suffix: string): string {
  const slug = normalizeRoomSlug(roomSlug);
  const normalizedSuffix = suffix.startsWith("/") ? suffix : `/${suffix}`;
  return `/api/rooms/${encodeURIComponent(slug)}${normalizedSuffix}`;
}

export function buildPublicRoomPath(roomSlug: string, suffix = ""): string {
  const slug = normalizeRoomSlug(roomSlug);
  const normalizedSuffix = suffix ? (suffix.startsWith("/") ? suffix : `/${suffix}`) : "";
  return `/${slug}${normalizedSuffix}`;
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
    const jpgHash = normalizeResultHash(roomResult[2]);
    if (!jpgHash) {
      return null;
    }
    return { page: "result", roomSlug: normalizeRoomSlug(roomResult[1]), jpgHash };
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
    const jpgHash = normalizeResultHash(legacyResult[1]);
    if (!jpgHash) {
      return null;
    }
    return { page: "result", roomSlug: DEFAULT_ROOM_SLUG, jpgHash };
  }

  return null;
}
