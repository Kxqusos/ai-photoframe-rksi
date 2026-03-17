import React, { useEffect, useState } from "react";

import type { Room, RoomCreatePayload, RoomPatchPayload } from "../types";

type Props = {
  editingRoom: Room | null;
  onCreate: (payload: RoomCreatePayload) => Promise<boolean>;
  onUpdate: (roomId: number, payload: RoomPatchPayload) => Promise<boolean>;
  onCancelEdit: () => void;
};

const DEFAULT_MODEL = "openai/gpt-5-image";

export function AdminRoomForm({ editingRoom, onCreate, onUpdate, onCancelEdit }: Props) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [modelName, setModelName] = useState(DEFAULT_MODEL);
  const [isActive, setIsActive] = useState(true);
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (!editingRoom) {
      setName("");
      setSlug("");
      setModelName(DEFAULT_MODEL);
      setIsActive(true);
      setPassword("");
      return;
    }

    setName(editingRoom.name);
    setSlug(editingRoom.slug);
    setModelName(editingRoom.model_name);
    setIsActive(editingRoom.is_active);
    setPassword("");
  }, [editingRoom]);

  async function submit() {
    if (!name.trim() || (!editingRoom && !password.trim())) {
      return;
    }

    if (editingRoom) {
      if (!slug.trim()) {
        return;
      }

      const updated = await onUpdate(editingRoom.id, {
        slug: slug.trim(),
        name: name.trim(),
        model_name: modelName.trim() || DEFAULT_MODEL,
        is_active: isActive,
        password: password.trim() || undefined
      });
      if (!updated) {
        return;
      }
      return;
    }

    const created = await onCreate({
      name: name.trim(),
      model_name: modelName.trim() || DEFAULT_MODEL,
      is_active: true,
      password: password.trim()
    });
    if (!created) {
      return;
    }
    setName("");
    setModelName(DEFAULT_MODEL);
    setPassword("");
  }

  function cancelEdit() {
    onCancelEdit();
  }

  return (
    <section className="panel form-grid" aria-label="форма комнаты">
      <div className="section-header">
        <div>
          <h2>{editingRoom ? "Редактирование комнаты" : "Новая комната"}</h2>
          <p className="section-support">
            {editingRoom
              ? "Обновите параметры комнаты и сохраните изменения без перехода в отдельный экран."
              : "Задайте название и модель, чтобы сразу подготовить комнату к работе."}
          </p>
        </div>
      </div>

      <label htmlFor="admin-room-name">Название</label>
      <input id="admin-room-name" value={name} onChange={(event) => setName(event.target.value)} />

      {editingRoom ? (
        <>
          <label htmlFor="admin-room-slug">Slug</label>
          <input id="admin-room-slug" value={slug} onChange={(event) => setSlug(event.target.value)} />
        </>
      ) : null}

      <label htmlFor="admin-room-model">Модель</label>
      <input id="admin-room-model" value={modelName} onChange={(event) => setModelName(event.target.value)} />

      <label htmlFor="admin-room-password">Пароль комнаты</label>
      <input
        id="admin-room-password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        placeholder={editingRoom ? "Оставьте пустым, чтобы не менять" : "Введите пароль комнаты"}
      />

      {editingRoom ? (
        <>
          <label htmlFor="admin-room-active">
            <input
              id="admin-room-active"
              type="checkbox"
              checked={isActive}
              onChange={(event) => setIsActive(event.target.checked)}
            />
            Комната активна
          </label>
        </>
      ) : null}

      <div className="action-row">
        <button type="button" onClick={() => void submit()}>
          {editingRoom ? "Сохранить изменения" : "Создать комнату"}
        </button>
        {editingRoom ? (
          <button type="button" className="button-secondary" onClick={cancelEdit}>
            Отменить редактирование
          </button>
        ) : null}
      </div>
    </section>
  );
}
