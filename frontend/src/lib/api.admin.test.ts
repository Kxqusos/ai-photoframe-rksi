import { beforeEach, describe, expect, test, vi } from "vitest";

import {
  adminLogin,
  getLlmRouting,
  testLlmRouting,
  toggleLlmRouting,
  updateLlmRoutingConfig,
  deleteRoom,
  createRoomJob,
  getRoomJobStatus,
  listRoomGalleryResults,
  listRoomPrompts,
  listRooms,
  patchRoom,
  updateRoomAdminPrompt
} from "./api";
import { clearAdminToken, loadAdminToken, saveAdminToken } from "./auth";
import { saveRoomAccessToken } from "./roomAccess";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  window.localStorage.clear();
  window.sessionStorage.clear();
  saveRoomAccessToken("aaaaaaaa", "room-token");
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

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining("/api/rooms/aaaaaaaa/prompts"),
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Room-Access-Token": "room-token" })
      })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining("/api/rooms/aaaaaaaa/jobs"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "X-Room-Access-Token": "room-token" })
      })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      expect.stringContaining("/api/rooms/aaaaaaaa/jobs/hash/dddddddd"),
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Room-Access-Token": "room-token" })
      })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      expect.stringContaining("/api/rooms/aaaaaaaa/jobs/gallery"),
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Room-Access-Token": "room-token" })
      })
    );
  });

  test("requests status directly from hash endpoint", async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ id: "abcd1234", status: "completed" }), { status: 200 }));

    const status = await getRoomJobStatus("aaaaaaaa", "abcd1234");
    expect(status.status).toBe("completed");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining("/api/rooms/aaaaaaaa/jobs/hash/abcd1234"),
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Room-Access-Token": "room-token" })
      })
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

  test("updates room prompt via protected admin endpoint", async () => {
    saveAdminToken("jwt-token");
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 12,
          name: "Edited",
          description: "Updated description",
          prompt: "Updated prompt",
          preview_image_url: "/media/previews/edited.jpg",
          icon_image_url: "/media/previews/edited.jpg"
        }),
        { status: 200 }
      )
    );

    await updateRoomAdminPrompt(7, 12, {
      name: "Edited",
      description: "Updated description",
      prompt: "Updated prompt",
      preview_image_url: "/media/previews/edited.jpg",
      icon_image_url: "/media/previews/edited.jpg"
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/admin/rooms/7/prompts/12"),
      expect.objectContaining({
        method: "PUT",
        headers: expect.objectContaining({
          Authorization: "Bearer jwt-token",
          "Content-Type": "application/json"
        })
      })
    );
  });

  test("patches room via protected admin endpoint", async () => {
    saveAdminToken("jwt-token");
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 7,
          slug: "aaaaaaaa",
          name: "Room A Updated",
          model_name: "openai/gpt-5-image",
          is_active: false
        }),
        { status: 200 }
      )
    );

    await patchRoom(7, { name: "Room A Updated", is_active: false });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/admin/rooms/7"),
      expect.objectContaining({
        method: "PATCH",
        headers: expect.objectContaining({
          Authorization: "Bearer jwt-token",
          "Content-Type": "application/json"
        }),
        body: JSON.stringify({ name: "Room A Updated", is_active: false })
      })
    );
  });

  test("deletes room via protected admin endpoint", async () => {
    saveAdminToken("jwt-token");
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await deleteRoom(7);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/admin/rooms/7"),
      expect.objectContaining({
        method: "DELETE",
        headers: expect.objectContaining({
          Authorization: "Bearer jwt-token"
        })
      })
    );
  });

  test("reads llm routing settings via protected admin endpoint", async () => {
    saveAdminToken("jwt-token");
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          enabled: false,
          status: "disabled",
          vless_uri: "",
          last_error: null,
          last_checked_at: null,
          last_applied_at: null
        }),
        { status: 200 }
      )
    );

    await getLlmRouting();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/admin/llm-routing"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer jwt-token"
        })
      })
    );
  });

  test("updates llm routing config via protected admin endpoint", async () => {
    saveAdminToken("jwt-token");
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          enabled: false,
          status: "error",
          vless_uri: "vless://uuid@example.com:443",
          last_error: "probe timeout",
          last_checked_at: "2026-03-17T12:00:00",
          last_applied_at: "2026-03-17T12:00:00"
        }),
        { status: 200 }
      )
    );

    await updateLlmRoutingConfig("vless://uuid@example.com:443");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/admin/llm-routing/config"),
      expect.objectContaining({
        method: "PUT",
        headers: expect.objectContaining({
          Authorization: "Bearer jwt-token",
          "Content-Type": "application/json"
        }),
        body: JSON.stringify({ vless_uri: "vless://uuid@example.com:443" })
      })
    );
  });

  test("tests and toggles llm routing via protected admin endpoints", async () => {
    saveAdminToken("jwt-token");
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            enabled: false,
            status: "disabled",
            vless_uri: "vless://uuid@example.com:443",
            last_error: null,
            last_checked_at: "2026-03-17T12:00:00",
            last_applied_at: "2026-03-17T12:00:00"
          }),
          { status: 200 }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            enabled: true,
            status: "active",
            vless_uri: "vless://uuid@example.com:443",
            last_error: null,
            last_checked_at: "2026-03-17T12:01:00",
            last_applied_at: "2026-03-17T12:01:00"
          }),
          { status: 200 }
        )
      );

    await testLlmRouting();
    await toggleLlmRouting(true);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining("/api/admin/llm-routing/test"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer jwt-token"
        })
      })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining("/api/admin/llm-routing/toggle"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer jwt-token",
          "Content-Type": "application/json"
        }),
        body: JSON.stringify({ enabled: true })
      })
    );
  });
});
