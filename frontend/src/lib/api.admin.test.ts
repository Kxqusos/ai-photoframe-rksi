import { beforeEach, describe, expect, test, vi } from "vitest";

import {
  adminLogin,
  createRoomJob,
  getRoomJobStatus,
  listRoomGalleryResults,
  listRoomPrompts,
  listRooms
} from "./api";
import { clearAdminToken, loadAdminToken, saveAdminToken } from "./auth";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  window.localStorage.clear();
});

describe("room-scoped public API client", () => {
  test("builds room-scoped URLs for prompts/jobs/status-by-hash/gallery", async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "dddddddd", status: "processing" }), { status: 202 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "dddddddd", status: "processing" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    await listRoomPrompts("aaaaaaaa");
    await createRoomJob("aaaaaaaa", new File([new Uint8Array([1, 2])], "photo.jpg", { type: "image/jpeg" }), 10);
    await getRoomJobStatus("aaaaaaaa", "dddddddd");
    await listRoomGalleryResults("aaaaaaaa");

    expect(fetchMock).toHaveBeenNthCalledWith(1, expect.stringContaining("/api/rooms/aaaaaaaa/prompts"));
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining("/api/rooms/aaaaaaaa/jobs"),
      expect.objectContaining({ method: "POST" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      expect.stringContaining("/api/rooms/aaaaaaaa/jobs/hash/dddddddd")
    );
    expect(fetchMock).toHaveBeenNthCalledWith(4, expect.stringContaining("/api/rooms/aaaaaaaa/jobs/gallery"));
  });

  test("requests status directly from hash endpoint", async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ id: "abcd1234", status: "completed" }), { status: 200 }));

    const status = await getRoomJobStatus("aaaaaaaa", "abcd1234");
    expect(status.status).toBe("completed");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining("/api/rooms/aaaaaaaa/jobs/hash/abcd1234")
    );
  });
});

describe("admin auth token helpers", () => {
  test("save/load/clear token in localStorage", () => {
    expect(loadAdminToken()).toBeNull();
    saveAdminToken("jwt-token");
    expect(loadAdminToken()).toBe("jwt-token");
    clearAdminToken();
    expect(loadAdminToken()).toBeNull();
  });
});

describe("admin API client", () => {
  test("sends Bearer token for protected admin endpoints", async () => {
    saveAdminToken("jwt-token");
    fetchMock.mockResolvedValue(new Response(JSON.stringify([]), { status: 200 }));

    await listRooms();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/admin/rooms"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer jwt-token"
        })
      })
    );
  });

  test("posts credentials to admin login endpoint", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ access_token: "jwt-token", token_type: "bearer" }), { status: 200 })
    );

    const response = await adminLogin("admin", "password");

    expect(response.access_token).toBe("jwt-token");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/admin/auth/login"),
      expect.objectContaining({
        method: "POST"
      })
    );
  });
});
