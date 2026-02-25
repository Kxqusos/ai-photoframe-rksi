import type {
  GalleryImage,
  JobCreated,
  JobStatus,
  MediaUploadResponse,
  ModelSetting,
  PromptCreate,
  StylePrompt
} from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const FALLBACK_STYLES: StylePrompt[] = [
  {
    id: 1,
    name: "Аниме",
    description: "Мягкая стилизация в аниме",
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

export async function listPrompts(): Promise<StylePrompt[]> {
  try {
    const response = await fetch(`${API_BASE}/api/prompts`);
    if (!response.ok) {
      return FALLBACK_STYLES;
    }
    return (await response.json()) as StylePrompt[];
  } catch {
    return FALLBACK_STYLES;
  }
}

export async function createJob(photo: File, promptId: number): Promise<JobCreated> {
  const formData = new FormData();
  formData.append("photo", photo);
  formData.append("prompt_id", String(promptId));

  const response = await fetch(`${API_BASE}/api/jobs`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error("Не удалось создать задачу генерации");
  }

  return (await response.json()) as JobCreated;
}

export async function getJobStatus(jpgHash: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE}/api/jobs/hash/${encodeURIComponent(jpgHash)}`);
  if (!response.ok) {
    throw new Error("Не удалось получить статус генерации");
  }
  return (await response.json()) as JobStatus;
}

export async function listGalleryResults(): Promise<GalleryImage[]> {
  const response = await fetch(`${API_BASE}/api/jobs/gallery`);
  if (!response.ok) {
    throw new Error("Не удалось получить изображения галереи");
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
    throw new Error("Не удалось обновить модель");
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
    throw new Error("Не удалось загрузить превью");
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
    throw new Error("Не удалось загрузить иконку");
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
    throw new Error("Не удалось создать стиль");
  }
  return (await response.json()) as StylePrompt;
}

export async function deletePrompt(promptId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/prompts/${promptId}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new Error("Не удалось удалить стиль");
  }
}
