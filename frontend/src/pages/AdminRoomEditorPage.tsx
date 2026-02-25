import React, { useEffect, useMemo, useState } from "react";

import { AdminPromptManager } from "../components/AdminPromptManager";
import { createRoomAdminPrompt, deleteRoomAdminPrompt, listRoomAdminPrompts, listRooms, updateRoomModel } from "../lib/api";
import { loadAdminToken } from "../lib/auth";
import { navigateTo } from "../lib/navigation";
import type { Room, StylePrompt } from "../types";

type Props = {
  roomId: number;
};

export function AdminRoomEditorPage({ roomId }: Props) {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [prompts, setPrompts] = useState<StylePrompt[]>([]);
  const [modelName, setModelName] = useState("");

  const room = useMemo(() => rooms.find((item) => item.id === roomId) || null, [roomId, rooms]);

  async function loadAll() {
    const [nextRooms, nextPrompts] = await Promise.all([listRooms(), listRoomAdminPrompts(roomId)]);
    setRooms(nextRooms);
    setPrompts(nextPrompts);
    const current = nextRooms.find((item) => item.id === roomId);
    if (current) {
      setModelName(current.model_name);
    }
  }

  useEffect(() => {
    if (!loadAdminToken()) {
      navigateTo("/admin/login");
      return;
    }
    void loadAll();
  }, [roomId]);

  async function saveModel() {
    await updateRoomModel(roomId, modelName);
    await loadAll();
  }

  async function createPrompt(payload: {
    name: string;
    description: string;
    prompt: string;
    preview_image_url: string;
    icon_image_url: string;
  }) {
    await createRoomAdminPrompt(roomId, payload);
    await loadAll();
  }

  async function deletePrompt(promptId: number) {
    await deleteRoomAdminPrompt(roomId, promptId);
    await loadAll();
  }

  return (
    <main className="page">
      <h1>{room?.name || "Room editor"}</h1>

      <section className="panel form-grid">
        <label htmlFor="admin-room-model-editor">Model</label>
        <input id="admin-room-model-editor" value={modelName} onChange={(event) => setModelName(event.target.value)} />
        <button type="button" onClick={() => void saveModel()}>
          Save model
        </button>
      </section>

      <AdminPromptManager prompts={prompts} onCreate={createPrompt} onDelete={deletePrompt} />
    </main>
  );
}
