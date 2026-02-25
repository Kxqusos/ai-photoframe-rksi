import { describe, expect, test } from "vitest";

import { buildRoomApiPath, normalizeRoomSlug, resolvePublicRoute } from "./roomRouting";

describe("roomRouting", () => {
  test("normalizes room slug", () => {
    expect(normalizeRoomSlug(" Room A ")).toBe("room-a");
    expect(normalizeRoomSlug("")).toBe("main");
  });

  test("builds room api path", () => {
    expect(buildRoomApiPath("Room A", "/jobs")).toBe("/api/rooms/room-a/jobs");
  });

  test("resolves room public routes", () => {
    expect(resolvePublicRoute("/room-a")).toEqual({ page: "capture", roomSlug: "room-a" });
    expect(resolvePublicRoute("/room-a/gallery")).toEqual({ page: "gallery", roomSlug: "room-a" });
    expect(resolvePublicRoute("/room-a/result/abc123")).toEqual({
      page: "result",
      roomSlug: "room-a",
      jpgHash: "abc123"
    });
  });
});
