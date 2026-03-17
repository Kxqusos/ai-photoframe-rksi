import { normalizeRoomSlug } from "./roomRouting";

const ROOM_ACCESS_PREFIX = "ai_photoframe.room_access.";

function roomAccessKey(roomSlug: string): string {
  return `${ROOM_ACCESS_PREFIX}${normalizeRoomSlug(roomSlug)}`;
}

export function getRoomAccessToken(roomSlug: string): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.sessionStorage.getItem(roomAccessKey(roomSlug));
}

export function hasRoomAccessToken(roomSlug: string): boolean {
  return Boolean(getRoomAccessToken(roomSlug));
}

export function saveRoomAccessToken(roomSlug: string, token: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.setItem(roomAccessKey(roomSlug), token);
}

export function clearRoomAccessToken(roomSlug: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.removeItem(roomAccessKey(roomSlug));
}
