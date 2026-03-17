import { describe, expect, test } from "vitest";

import { buildPublicRoomPath, buildRoomApiPath, normalizeRoomSlug, resolvePublicRoute } from "./roomRouting";

describe("roomRouting", () => {
  test("normalizes room slug", () => {
    expect(normalizeRoomSlug("aaaaaaaa")).toBe("aaaaaaaa");
    expect(normalizeRoomSlug(" Room A ")).toBe("ph000000");
    expect(normalizeRoomSlug("")).toBe("ph000000");
  });

  test("builds room api path", () => {
    expect(buildRoomApiPath("Room A", "/jobs")).toBe("/api/rooms/ph000000/jobs");
  });

  test("builds public room path and keeps default room on root", () => {
    expect(buildPublicRoomPath("ph000000")).toBe("/");
    expect(buildPublicRoomPath("ph000000", "/gallery")).toBe("/gallery");
    expect(buildPublicRoomPath("ph000000", "/result/dddddddd")).toBe("/result/dddddddd");
    expect(buildPublicRoomPath("aaaaaaaa")).toBe("/aaaaaaaa");
    expect(buildPublicRoomPath("aaaaaaaa", "/gallery")).toBe("/aaaaaaaa/gallery");
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
