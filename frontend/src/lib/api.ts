import type {
  AdminToken,
  GalleryImage,
  JobCreated,
  JobStatus,
  MediaUploadResponse,
  ModelSetting,
  PromptCreate,
  Room,
  StylePrompt
} from "../types";
import { loadAdminToken } from "./auth";
import { DEFAULT_ROOM_SLUG, buildRoomApiPath, normalizeRoomSlug } from "./roomRouting";

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
const DEFAULT_MODEL = "openai/gpt-5-image";
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

export async function listPrompts(): Promise<StylePrompt[]> {
  return listRoomPrompts(DEFAULT_ROOM_SLUG);
}

export async function listRoomPrompts(roomSlug: string): Promise<StylePrompt[]> {
  try {
    const response = await fetch(`${API_BASE}${buildRoomApiPath(roomSlugOrDefault(roomSlug), "/prompts")}`);
    if (!response.ok) {
      return FALLBACK_STYLES;
    }
    return (await response.json()) as StylePrompt[];
  } catch {
    return FALLBACK_STYLES;
  }
}

export async function createJob(photo: File, promptId: number): Promise<JobCreated> {
  return createRoomJob(DEFAULT_ROOM_SLUG, photo, promptId);
}

export async function createRoomJob(roomSlug: string, photo: File, promptId: number): Promise<JobCreated> {
  const formData = new FormData();
  formData.append("photo", photo);
  formData.append("prompt_id", String(promptId));

  const response = await fetch(`${API_BASE}${buildRoomApiPath(roomSlugOrDefault(roomSlug), "/jobs")}`, {
    method: "POST",
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
  const encoded = encodeURIComponent(jobRef);
  const byIdResponse = await fetch(`${API_BASE}${buildRoomApiPath(roomSlugOrDefault(roomSlug), `/jobs/${encoded}`)}`);
  if (byIdResponse.ok) {
    return (await byIdResponse.json()) as JobStatus;
  }

  // Backward compatibility: support result URLs that still pass qr-hash in pathname.
  if (byIdResponse.status !== 404 && byIdResponse.status !== 422) {
    throw new Error("Failed to fetch generation status");
  }

  const byHashResponse = await fetch(
    `${API_BASE}${buildRoomApiPath(roomSlugOrDefault(roomSlug), `/jobs/hash/${encoded}`)}`
  );
  if (!byHashResponse.ok) {
    throw new Error("Failed to fetch generation status");
  }
  return (await byHashResponse.json()) as JobStatus;
}

export async function listGalleryResults(): Promise<GalleryImage[]> {
  return listRoomGalleryResults(DEFAULT_ROOM_SLUG);
}

export async function listRoomGalleryResults(roomSlug: string): Promise<GalleryImage[]> {
  const response = await fetch(`${API_BASE}${buildRoomApiPath(roomSlugOrDefault(roomSlug), "/jobs/gallery")}`);
  if (!response.ok) {
    throw new Error("Failed to fetch gallery images");
  }
  return (await response.json()) as GalleryImage[];
}

export async function listModels(): Promise<string[]> {
  return AVAILABLE_MODELS;
}

export async function getModel(): Promise<ModelSetting> {
  try {
    const response = await fetch(`${API_BASE}/api/settings/model`);
    if (!response.ok) {
      return { id: 1, model_name: DEFAULT_MODEL };
    }
    return (await response.json()) as ModelSetting;
  } catch {
    return { id: 1, model_name: DEFAULT_MODEL };
  }
}

export async function setModel(model: string): Promise<ModelSetting> {
  const response = await fetch(`${API_BASE}/api/settings/model`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ model_name: model })
  });
  if (!response.ok) {
    throw new Error("Failed to update model");
  }
  return (await response.json()) as ModelSetting;
}

export async function uploadPromptPreview(file: File): Promise<MediaUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/media/prompt-preview`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    throw new Error("Failed to upload preview image");
  }
  return (await response.json()) as MediaUploadResponse;
}

export async function uploadPromptIcon(file: File): Promise<MediaUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/media/prompt-icon`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    throw new Error("Failed to upload icon image");
  }
  return (await response.json()) as MediaUploadResponse;
}

export async function createPrompt(payload: PromptCreate): Promise<StylePrompt> {
  const response = await fetch(`${API_BASE}/api/prompts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Failed to create style prompt");
  }
  return (await response.json()) as StylePrompt;
}

export async function deletePrompt(promptId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/prompts/${promptId}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new Error("Failed to delete style prompt");
  }
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

export async function createRoom(payload: Omit<Room, "id">): Promise<Room> {
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
