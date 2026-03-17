import type {
  AdminToken,
  GalleryImage,
  JobCreated,
  JobStatus,
  MediaUploadResponse,
  PublicRoom,
  PromptCreate,
  RoomAccessToken,
  RoomCreatePayload,
  RoomPatchPayload,
  Room,
  LlmRoutingSettings,
  StylePrompt
} from "../types";
import { loadAdminToken } from "./auth";
import { getRoomAccessToken } from "./roomAccess";
import { DEFAULT_ROOM_SLUG, buildRoomApiPath, normalizeResultHash, normalizeRoomSlug } from "./roomRouting";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const FALLBACK_STYLES: StylePrompt[] = [
  {
    id: 1,
    name: "Anime",
    description: "Soft anime shading",
    prompt: "Turn input photo into anime portrait",
    preview_image_url: "/media/previews/anime.jpg",
    icon_image_url: "/media/icons/anime.png"
  }
];
const AVAILABLE_MODELS = [
  "openai/gpt-5-image",
  "google/gemini-2.5-flash-image",
  "sourceful/riverflow-v2-fast-preview"
];

type RequestHeaders = Record<string, string>;

function requireAdminHeaders(extraHeaders?: RequestHeaders): RequestHeaders {
  const token = loadAdminToken();
  if (!token) {
    throw new Error("Admin token is missing");
  }
  return {
    ...(extraHeaders || {}),
    Authorization: `Bearer ${token}`
  };
}

function roomSlugOrDefault(roomSlug: string): string {
  return normalizeRoomSlug(roomSlug || DEFAULT_ROOM_SLUG);
}

function requireRoomHeaders(roomSlug: string, extraHeaders?: RequestHeaders): RequestHeaders {
  const token = getRoomAccessToken(roomSlug);
  if (!token) {
    throw new Error("Room access token is missing");
  }
  return {
    ...(extraHeaders || {}),
    "X-Room-Access-Token": token
  };
}

export async function listRoomPrompts(roomSlug: string): Promise<StylePrompt[]> {
  const response = await fetch(`${API_BASE}${buildRoomApiPath(roomSlugOrDefault(roomSlug), "/prompts")}`, {
    headers: requireRoomHeaders(roomSlug)
  });
  if (!response.ok) {
    throw new Error("Failed to fetch room prompts");
  }
  return (await response.json()) as StylePrompt[];
}

export async function listPublicRooms(): Promise<PublicRoom[]> {
  const response = await fetch(`${API_BASE}/api/rooms`);
  if (!response.ok) {
    throw new Error("Failed to fetch rooms");
  }
  return (await response.json()) as PublicRoom[];
}

export async function accessRoom(roomSlug: string, password: string): Promise<RoomAccessToken> {
  const response = await fetch(`${API_BASE}/api/rooms/${encodeURIComponent(roomSlugOrDefault(roomSlug))}/access`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ password })
  });
  if (!response.ok) {
    throw new Error("Неверный пароль комнаты");
  }
  return (await response.json()) as RoomAccessToken;
}

export async function createRoomJob(roomSlug: string, photo: File, promptId: number): Promise<JobCreated> {
  const formData = new FormData();
  formData.append("photo", photo);
  formData.append("prompt_id", String(promptId));

  const response = await fetch(`${API_BASE}${buildRoomApiPath(roomSlugOrDefault(roomSlug), "/jobs")}`, {
    method: "POST",
    headers: requireRoomHeaders(roomSlug),
    body: formData
  });

  if (!response.ok) {
    throw new Error("Failed to create generation job");
  }

  return (await response.json()) as JobCreated;
}

export async function getJobStatus(jobId: number): Promise<JobStatus> {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch generation status");
  }
  return (await response.json()) as JobStatus;
}

export async function getRoomJobStatus(roomSlug: string, jobRef: string): Promise<JobStatus> {
  const normalizedRef = normalizeResultHash(jobRef);
  if (!normalizedRef) {
    throw new Error("Invalid job reference");
  }
  const encoded = encodeURIComponent(normalizedRef);
  const byHashResponse = await fetch(
    `${API_BASE}${buildRoomApiPath(roomSlugOrDefault(roomSlug), `/jobs/hash/${encoded}`)}`,
    {
      headers: requireRoomHeaders(roomSlug)
    }
  );
  if (!byHashResponse.ok) {
    throw new Error("Failed to fetch generation status");
  }
  return (await byHashResponse.json()) as JobStatus;
}

export async function listRoomGalleryResults(roomSlug: string): Promise<GalleryImage[]> {
  const response = await fetch(`${API_BASE}${buildRoomApiPath(roomSlugOrDefault(roomSlug), "/jobs/gallery")}`, {
    headers: requireRoomHeaders(roomSlug)
  });
  if (!response.ok) {
    throw new Error("Failed to fetch gallery images");
  }
  return (await response.json()) as GalleryImage[];
}

export async function listModels(): Promise<string[]> {
  return AVAILABLE_MODELS;
}

export async function adminLogin(username: string, password: string): Promise<AdminToken> {
  const response = await fetch(`${API_BASE}/api/admin/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username, password })
  });
  if (!response.ok) {
    throw new Error("Failed to sign in");
  }
  return (await response.json()) as AdminToken;
}

export async function listRooms(): Promise<Room[]> {
  const response = await fetch(`${API_BASE}/api/admin/rooms`, {
    headers: requireAdminHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to fetch rooms");
  }
  return (await response.json()) as Room[];
}

export async function createRoom(payload: RoomCreatePayload): Promise<Room> {
  const response = await fetch(`${API_BASE}/api/admin/rooms`, {
    method: "POST",
    headers: requireAdminHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Failed to create room");
  }
  return (await response.json()) as Room;
}

export async function updateRoom(roomId: number, payload: Omit<Room, "id">): Promise<Room> {
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}`, {
    method: "PUT",
    headers: requireAdminHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Failed to update room");
  }
  return (await response.json()) as Room;
}

export async function patchRoom(roomId: number, payload: RoomPatchPayload): Promise<Room> {
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}`, {
    method: "PATCH",
    headers: requireAdminHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Failed to update room");
  }
  return (await response.json()) as Room;
}

export async function deleteRoom(roomId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}`, {
    method: "DELETE",
    headers: requireAdminHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to delete room");
  }
}

export async function getLlmRouting(): Promise<LlmRoutingSettings> {
  const response = await fetch(`${API_BASE}/api/admin/llm-routing`, {
    headers: requireAdminHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to fetch llm routing settings");
  }
  return (await response.json()) as LlmRoutingSettings;
}

export async function updateLlmRoutingConfig(vlessUri: string): Promise<LlmRoutingSettings> {
  const response = await fetch(`${API_BASE}/api/admin/llm-routing/config`, {
    method: "PUT",
    headers: requireAdminHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ vless_uri: vlessUri })
  });
  if (!response.ok) {
    throw new Error("Failed to update llm routing settings");
  }
  return (await response.json()) as LlmRoutingSettings;
}

export async function testLlmRouting(): Promise<LlmRoutingSettings> {
  const response = await fetch(`${API_BASE}/api/admin/llm-routing/test`, {
    method: "POST",
    headers: requireAdminHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to test llm routing");
  }
  return (await response.json()) as LlmRoutingSettings;
}

export async function toggleLlmRouting(enabled: boolean): Promise<LlmRoutingSettings> {
  const response = await fetch(`${API_BASE}/api/admin/llm-routing/toggle`, {
    method: "POST",
    headers: requireAdminHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ enabled })
  });
  if (!response.ok) {
    throw new Error("Failed to toggle llm routing");
  }
  return (await response.json()) as LlmRoutingSettings;
}

export async function updateRoomModel(roomId: number, modelName: string): Promise<Room> {
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}/model`, {
    method: "PUT",
    headers: requireAdminHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ model_name: modelName })
  });
  if (!response.ok) {
    throw new Error("Failed to update room model");
  }
  return (await response.json()) as Room;
}

export async function listRoomAdminPrompts(roomId: number): Promise<StylePrompt[]> {
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}/prompts`, {
    headers: requireAdminHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to fetch room prompts");
  }
  return (await response.json()) as StylePrompt[];
}

export async function createRoomAdminPrompt(roomId: number, payload: PromptCreate): Promise<StylePrompt> {
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}/prompts`, {
    method: "POST",
    headers: requireAdminHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Failed to create room prompt");
  }
  return (await response.json()) as StylePrompt;
}

export async function updateRoomAdminPrompt(roomId: number, promptId: number, payload: PromptCreate): Promise<StylePrompt> {
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}/prompts/${promptId}`, {
    method: "PUT",
    headers: requireAdminHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Failed to update room prompt");
  }
  return (await response.json()) as StylePrompt;
}

export async function deleteRoomAdminPrompt(roomId: number, promptId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}/prompts/${promptId}`, {
    method: "DELETE",
    headers: requireAdminHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to delete room prompt");
  }
}

export async function uploadRoomPromptPreview(roomId: number, file: File): Promise<MediaUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}/media/prompt-preview`, {
    method: "POST",
    headers: requireAdminHeaders(),
    body: formData
  });
  if (!response.ok) {
    throw new Error("Failed to upload room preview image");
  }
  return (await response.json()) as MediaUploadResponse;
}

export async function uploadRoomPromptIcon(roomId: number, file: File): Promise<MediaUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/api/admin/rooms/${roomId}/media/prompt-icon`, {
    method: "POST",
    headers: requireAdminHeaders(),
    body: formData
  });
  if (!response.ok) {
    throw new Error("Failed to upload room icon image");
  }
  return (await response.json()) as MediaUploadResponse;
}
