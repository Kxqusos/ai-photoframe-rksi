import { useEffect, useMemo, useState } from "react";

import { AdminPromptManager } from "../components/AdminPromptManager";
import {
  createRoomAdminPrompt,
  deleteRoomAdminPrompt,
  listRoomAdminPrompts,
  listRooms,
  updateRoomAdminPrompt,
  updateRoomModel,
  uploadRoomPromptPreview
} from "../lib/api";
import { loadAdminToken } from "../lib/auth";
import { navigateTo } from "../lib/navigation";
import type { Room, StylePrompt } from "../types";

type Props = {
  roomSlug: string;
};

export function AdminRoomEditorPage({ roomSlug }: Props) {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [prompts, setPrompts] = useState<StylePrompt[]>([]);
  const [modelName, setModelName] = useState("");
  const [savingModel, setSavingModel] = useState(false);
  const [error, setError] = useState("");

  const room = useMemo(() => rooms.find((item) => item.slug === roomSlug) || null, [roomSlug, rooms]);

  async function loadAll(): Promise<boolean> {
    try {
      const nextRooms = await listRooms();
      setRooms(nextRooms);
      const current = nextRooms.find((item) => item.slug === roomSlug);
      if (current) {
        setModelName(current.model_name);
        const nextPrompts = await listRoomAdminPrompts(current.id);
        setPrompts(nextPrompts);
        setError("");
        return true;
      }
      setPrompts([]);
      setModelName("");
      setError("");
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось загрузить комнату");
      return false;
    }
  }

  useEffect(() => {
    if (!loadAdminToken()) {
      navigateTo("/admin/login");
      return;
    }
    void loadAll();
  }, [roomSlug]);

  async function saveModel() {
    if (!room) {
      return;
    }

    setSavingModel(true);
    setError("");
    try {
      await updateRoomModel(room.id, modelName);
      await loadAll();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось сохранить модель");
    } finally {
      setSavingModel(false);
    }
  }

  async function createPrompt(payload: {
    name: string;
    description: string;
    prompt: string;
    previewFile: File;
  }): Promise<boolean> {
    if (!room) {
      return false;
    }

    setError("");
    try {
      const preview = await uploadRoomPromptPreview(room.id, payload.previewFile);
      await createRoomAdminPrompt(room.id, {
        name: payload.name,
        description: payload.description,
        prompt: payload.prompt,
        preview_image_url: preview.url,
        icon_image_url: preview.url
      });
      return await loadAll();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось создать промпт");
      return false;
    }
  }

  async function deletePrompt(promptId: number): Promise<boolean> {
    if (!room) {
      return false;
    }

    setError("");
    try {
      await deleteRoomAdminPrompt(room.id, promptId);
      return await loadAll();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось удалить промпт");
      return false;
    }
  }

  async function updatePrompt(payload: {
    id: number;
    name: string;
    description: string;
    prompt: string;
    previewFile: File | null;
    previewImageUrl: string;
    iconImageUrl: string;
  }): Promise<boolean> {
    if (!room) {
      return false;
    }

    setError("");

    try {
      let previewImageUrl = payload.previewImageUrl;
      let iconImageUrl = payload.iconImageUrl;

      if (payload.previewFile) {
        const preview = await uploadRoomPromptPreview(room.id, payload.previewFile);
        previewImageUrl = preview.url;
      }

      const updated = await updateRoomAdminPrompt(room.id, payload.id, {
        name: payload.name,
        description: payload.description,
        prompt: payload.prompt,
        preview_image_url: previewImageUrl,
        icon_image_url: iconImageUrl
      });
      setPrompts((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось обновить промпт");
      return false;
    }
  }

  return (
    <main className="page">
      <h1>{room?.name || "Редактор комнаты"}</h1>
      {error ? <p role="alert">{error}</p> : null}

      <section className="page-section panel">
        <div className="section-header">
          <div>
            <h2>Сводка комнаты</h2>
            <p className="section-support">Ключевые параметры комнаты собраны в одном месте перед изменениями.</p>
          </div>
        </div>
        <div className="summary-grid">
          <article className="summary-card">
            <span className="summary-card__label">Статус</span>
            <strong className="summary-card__value">{room?.is_active ? "Активна" : "Выключена"}</strong>
          </article>
          <article className="summary-card">
            <span className="summary-card__label">Текущая модель</span>
            <strong className="summary-card__value">{room?.model_name || "Не выбрана"}</strong>
          </article>
          <article className="summary-card">
            <span className="summary-card__label">Промптов</span>
            <strong className="summary-card__value">{prompts.length}</strong>
          </article>
        </div>
      </section>

      <section className="page-section panel">
        <div className="section-header">
          <div>
            <h2>Управление моделью</h2>
            <p className="section-support">Обновляйте модель отдельно от промптов, чтобы изменения были прозрачными.</p>
          </div>
          {savingModel ? <span className="status-inline">Сохраняем параметры комнаты...</span> : null}
        </div>
        <div className="form-grid">
          <label htmlFor="admin-room-model-editor">Модель</label>
          <input id="admin-room-model-editor" value={modelName} onChange={(event) => setModelName(event.target.value)} />
        </div>
        <div className="action-row">
          <button type="button" onClick={() => void saveModel()} disabled={savingModel || !room}>
            {savingModel ? "Сохраняем модель..." : "Сохранить модель"}
          </button>
        </div>
      </section>

      <section className="page-section">
        <div className="section-header">
          <div>
            <h2>Промпты комнаты</h2>
          </div>
        </div>

        <AdminPromptManager prompts={prompts} onCreate={createPrompt} onUpdate={updatePrompt} onDelete={deletePrompt} />
      </section>
    </main>
  );
}
