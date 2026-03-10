import React, { useEffect, useState } from "react";

import { PromptForm, type PromptFormValues } from "../components/PromptForm";
import {
  createRoomAdminPrompt,
  deleteRoomAdminPrompt,
  listModels,
  listRoomAdminPrompts,
  listRooms,
  updateRoomModel,
  uploadRoomPromptPreview
} from "../lib/api";
import { loadAdminToken } from "../lib/auth";
import { navigateTo } from "../lib/navigation";
import type { PromptCreate, Room, StylePrompt } from "../types";

const EMPTY_FORM: PromptFormValues = {
  name: "",
  description: "",
  prompt: "",
  previewFile: null
};

export function SettingsPage() {
  const [models, setModels] = useState<string[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [prompts, setPrompts] = useState<StylePrompt[]>([]);
  const [formValues, setFormValues] = useState<PromptFormValues>(EMPTY_FORM);
  const [savingPrompt, setSavingPrompt] = useState(false);
  const [savingModel, setSavingModel] = useState(false);
  const [deletingPromptIds, setDeletingPromptIds] = useState<number[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (!loadAdminToken()) {
      navigateTo("/admin/login");
      return;
    }

    async function load() {
      const [modelNames, roomItems] = await Promise.all([listModels(), listRooms()]);

      setModels(modelNames);
      setRooms(roomItems);

      if (roomItems.length === 0) {
        setSelectedRoomId(null);
        setSelectedModel("");
        setPrompts([]);
        return;
      }

      const firstRoom = roomItems[0];
      setSelectedRoomId(firstRoom.id);
      setSelectedModel(firstRoom.model_name);
      const promptItems = await listRoomAdminPrompts(firstRoom.id);
      setPrompts(promptItems);
    }

    load().catch((cause) => {
      setError(cause instanceof Error ? cause.message : "Failed to load settings");
    });
  }, []);

  async function onSelectRoom(roomId: number) {
    const room = rooms.find((item) => item.id === roomId);
    setSelectedRoomId(roomId);
    setSelectedModel(room?.model_name || "");
    setPrompts(await listRoomAdminPrompts(roomId));
  }

  async function onSaveModel() {
    if (!selectedModel || selectedRoomId === null) {
      return;
    }

    setSavingModel(true);
    setError("");
    try {
      const updatedRoom = await updateRoomModel(selectedRoomId, selectedModel);
      setRooms((current) => current.map((item) => (item.id === updatedRoom.id ? updatedRoom : item)));
      setSelectedModel(updatedRoom.model_name);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to save model");
    } finally {
      setSavingModel(false);
    }
  }

  async function onSavePrompt() {
    if (selectedRoomId === null) {
      return;
    }

    if (
      !formValues.name.trim() ||
      !formValues.description.trim() ||
      !formValues.prompt.trim() ||
      !formValues.previewFile
    ) {
      setError("Заполните все поля и загрузите изображение");
      return;
    }

    setSavingPrompt(true);
    setError("");

    try {
      const preview = await uploadRoomPromptPreview(selectedRoomId, formValues.previewFile);

      const payload: PromptCreate = {
        name: formValues.name.trim(),
        description: formValues.description.trim(),
        prompt: formValues.prompt.trim(),
        preview_image_url: preview.url,
        icon_image_url: preview.url
      };

      const created = await createRoomAdminPrompt(selectedRoomId, payload);
      setPrompts((current) => [...current, created]);
      setFormValues(EMPTY_FORM);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to save prompt");
    } finally {
      setSavingPrompt(false);
    }
  }

  async function onDeletePrompt(promptId: number) {
    if (selectedRoomId === null) {
      return;
    }

    setError("");
    setDeletingPromptIds((current) => [...current, promptId]);
    try {
      await deleteRoomAdminPrompt(selectedRoomId, promptId);
      setPrompts((current) => current.filter((item) => item.id !== promptId));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to delete prompt");
    } finally {
      setDeletingPromptIds((current) => current.filter((id) => id !== promptId));
    }
  }

  return (
    <main className="page">
      <h1>Настройки комнаты</h1>

      <section className="panel form-grid">
        <h2>Комната</h2>
        <label htmlFor="settings-room">Комната</label>
        <select
          id="settings-room"
          value={selectedRoomId ?? ""}
          onChange={(event) => void onSelectRoom(Number(event.target.value))}
          disabled={rooms.length === 0}
        >
          {rooms.length === 0 ? <option value="">Нет доступных комнат</option> : null}
          {rooms.map((room) => (
            <option key={room.id} value={room.id}>
              {room.name} ({room.slug})
            </option>
          ))}
        </select>
      </section>

      <section className="panel form-grid">
        <h2>Модель комнаты</h2>
        <label htmlFor="settings-room-model">Модель комнаты</label>
        <select id="settings-room-model" value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)}>
          {models.map((modelName) => (
            <option key={modelName} value={modelName}>
              {modelName}
            </option>
          ))}
        </select>
        <div className="action-row">
          <button type="button" onClick={onSaveModel} disabled={savingModel || !selectedModel || selectedRoomId === null}>
            Применить модель
          </button>
        </div>
      </section>

      <PromptForm values={formValues} onChange={setFormValues} onSubmit={onSavePrompt} isSubmitting={savingPrompt} />

      {error ? <p role="alert">{error}</p> : null}

      <section className="prompt-list">
        <h2>Стили</h2>
        {prompts.length === 0 ? <p>Пока нет стилей</p> : null}
        {prompts.map((item) => (
          <article key={item.id} className="prompt-item">
            <h3>{item.name}</h3>
            <p>{item.description}</p>
            <img src={item.preview_image_url} alt={`${item.name} preview`} width={120} height={80} />
            <div className="prompt-item__actions">
              <button
                type="button"
                className="button-secondary"
                aria-label={`Удалить стиль ${item.name}`}
                onClick={() => void onDeletePrompt(item.id)}
                disabled={deletingPromptIds.includes(item.id)}
              >
                Удалить
              </button>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
