import React, { useEffect, useMemo, useState } from "react";

import { AdminPromptManager } from "../components/AdminPromptManager";
import {
  createRoomAdminPrompt,
  deleteRoomAdminPrompt,
  listRoomAdminPrompts,
  listRooms,
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

  const room = useMemo(() => rooms.find((item) => item.slug === roomSlug) || null, [roomSlug, rooms]);

  async function loadAll() {
    const nextRooms = await listRooms();
    setRooms(nextRooms);
    const current = nextRooms.find((item) => item.slug === roomSlug);
    if (current) {
      setModelName(current.model_name);
      const nextPrompts = await listRoomAdminPrompts(current.id);
      setPrompts(nextPrompts);
      return;
    }
    setPrompts([]);
    setModelName("");
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
    await updateRoomModel(room.id, modelName);
    await loadAll();
  }

  async function createPrompt(payload: {
    name: string;
    description: string;
    prompt: string;
    previewFile: File;
  }) {
    if (!room) {
      return;
    }
    const preview = await uploadRoomPromptPreview(room.id, payload.previewFile);
    await createRoomAdminPrompt(room.id, {
      name: payload.name,
      description: payload.description,
      prompt: payload.prompt,
      preview_image_url: preview.url,
      icon_image_url: preview.url
    });
    await loadAll();
  }

  async function deletePrompt(promptId: number) {
    if (!room) {
      return;
    }
    await deleteRoomAdminPrompt(room.id, promptId);
    await loadAll();
  }

  return (
    <main className="page">
      <h1>{room?.name || "Редактор комнаты"}</h1>

      <section className="panel form-grid">
        <label htmlFor="admin-room-model-editor">Модель</label>
        <input id="admin-room-model-editor" value={modelName} onChange={(event) => setModelName(event.target.value)} />
        <button type="button" onClick={() => void saveModel()}>
          Сохранить модель
        </button>
      </section>

      <AdminPromptManager prompts={prompts} onCreate={createPrompt} onDelete={deletePrompt} />
    </main>
  );
}
