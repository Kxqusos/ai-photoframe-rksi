export type StylePrompt = {
  id: number;
  name: string;
  description: string;
  preview_image_url: string;
  icon_image_url: string;
  prompt: string;
};

export type JobCreated = {
  id: number;
  status: string;
};

export type JobStatus = {
  id: number;
  status: "processing" | "completed" | "error" | string;
  result_url?: string | null;
  download_url?: string | null;
  qr_url?: string | null;
  error_message?: string | null;
};

export type PromptCreate = {
  name: string;
  description: string;
  prompt: string;
  preview_image_url: string;
  icon_image_url: string;
};

export type ModelSetting = {
  id: number;
  model_name: string;
};

export type MediaUploadResponse = {
  url: string;
};
