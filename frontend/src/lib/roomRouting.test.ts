import { describe, expect, test } from "vitest";

import { buildRoomApiPath, normalizeRoomSlug, resolvePublicRoute } from "./roomRouting";

describe("roomRouting", () => {
  test("normalizes room slug", () => {
    expect(normalizeRoomSlug("aaaaaaaa")).toBe("aaaaaaaa");
    expect(normalizeRoomSlug(" Room A ")).toBe("ph000000");
    expect(normalizeRoomSlug("")).toBe("ph000000");
  });

  test("builds room api path", () => {
    expect(buildRoomApiPath("Room A", "/jobs")).toBe("/api/rooms/ph000000/jobs");
  });

  test("resolves room public routes", () => {
    expect(resolvePublicRoute("/aaaaaaaa")).toEqual({ page: "capture", roomSlug: "aaaaaaaa" });
    expect(resolvePublicRoute("/aaaaaaaa/gallery")).toEqual({ page: "gallery", roomSlug: "aaaaaaaa" });
    expect(resolvePublicRoute("/aaaaaaaa/result/dddddddd")).toEqual({
      page: "result",
      roomSlug: "aaaaaaaa",
      jpgHash: "dddddddd"
    });
    expect(resolvePublicRoute("/aaaaaaaa/result/abc123")).toBeNull();
  });
});
