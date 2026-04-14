export type StylePrompt = {
  id: number;
  name: string;
  description: string;
  preview_image_url: string;
  icon_image_url: string;
  prompt: string;
};

export type JobCreated = {
  id: string;
  status: string;
};

export type Room = {
  id: number;
  slug: string;
  name: string;
  model_name: string;
  is_active: boolean;
};

export type RoomCreatePayload = {
  name: string;
  model_name: string;
  is_active: boolean;
  password: string;
};

export type RoomPatchPayload = {
  slug?: string;
  name?: string;
  model_name?: string;
  is_active?: boolean;
  password?: string;
};

export type PublicRoom = {
  id: number;
  slug: string;
  name: string;
};

export type AdminToken = {
  access_token: string;
  token_type: string;
};

export type RoomAccessToken = {
  access_token: string;
  token_type: string;
};

export type JobStatus = {
  id: string;
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

export type GalleryImage = {
  name: string;
  url: string;
  modified_at: number;
};

export type LlmRoutingSettings = {
  enabled: boolean;
  status: string;
  vless_uri: string;
  provider_base_url: string;
  provider_api_key: string;
  custom_providers: Array<{
    base_url: string;
    api_key: string;
  }>;
  last_error: string | null;
  last_checked_at: string | null;
  last_applied_at: string | null;
};

export type LlmRoutingConfigPayload = {
  vlessUri: string;
  providerBaseUrl: string;
  providerApiKey: string;
  customProviders: Array<{
    baseUrl: string;
    apiKey: string;
  }>;
};
