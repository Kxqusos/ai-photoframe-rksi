import React, { useState } from "react";

import type { RoomCreatePayload } from "../types";

type Props = {
  onCreate: (payload: RoomCreatePayload) => Promise<void>;
};

export function AdminRoomForm({ onCreate }: Props) {
  const [name, setName] = useState("");
  const [modelName, setModelName] = useState("openai/gpt-5-image");

  async function submit() {
    if (!name.trim()) {
      return;
    }
    await onCreate({
      name: name.trim(),
      model_name: modelName.trim() || "openai/gpt-5-image",
      is_active: true
    });
    setName("");
  }

  return (
    <section className="panel form-grid" aria-label="форма комнаты">
      <label htmlFor="admin-room-name">Название</label>
      <input id="admin-room-name" value={name} onChange={(event) => setName(event.target.value)} />

      <label htmlFor="admin-room-model">Модель</label>
      <input id="admin-room-model" value={modelName} onChange={(event) => setModelName(event.target.value)} />

      <button type="button" onClick={() => void submit()}>
        Создать комнату
      </button>
    </section>
  );
}
