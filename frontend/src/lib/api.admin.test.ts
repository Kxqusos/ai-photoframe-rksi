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
  test("builds room-scoped URLs for prompts/jobs/status-by-id/gallery", async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 1, status: "processing" }), { status: 202 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 1, status: "processing" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    await listRoomPrompts("room-a");
    await createRoomJob("room-a", new File([new Uint8Array([1, 2])], "photo.jpg", { type: "image/jpeg" }), 10);
    await getRoomJobStatus("room-a", "1");
    await listRoomGalleryResults("room-a");

    expect(fetchMock).toHaveBeenNthCalledWith(1, expect.stringContaining("/api/rooms/room-a/prompts"));
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining("/api/rooms/room-a/jobs"),
      expect.objectContaining({ method: "POST" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(3, expect.stringContaining("/api/rooms/room-a/jobs/1"));
    expect(fetchMock).toHaveBeenNthCalledWith(4, expect.stringContaining("/api/rooms/room-a/jobs/gallery"));
  });

  test("falls back to hash endpoint when status-by-id lookup is not found", async () => {
    fetchMock
      .mockResolvedValueOnce(new Response("{}", { status: 404 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 7, status: "completed" }), { status: 200 }));

    const status = await getRoomJobStatus("room-a", "abc123hash");
    expect(status.status).toBe("completed");

    expect(fetchMock).toHaveBeenNthCalledWith(1, expect.stringContaining("/api/rooms/room-a/jobs/abc123hash"));
    expect(fetchMock).toHaveBeenNthCalledWith(2, expect.stringContaining("/api/rooms/room-a/jobs/hash/abc123hash"));
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
