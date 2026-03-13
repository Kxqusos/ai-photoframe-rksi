import React, { useEffect, useRef, useState } from "react";

import { PromptForm, type PromptFormValues } from "../components/PromptForm";
import {
  createRoomAdminPrompt,
  deleteRoomAdminPrompt,
  listModels,
  listRoomAdminPrompts,
  listRooms,
  updateRoomAdminPrompt,
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
  const [editingPrompt, setEditingPrompt] = useState<StylePrompt | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [savingPrompt, setSavingPrompt] = useState(false);
  const [savingModel, setSavingModel] = useState(false);
  const [deletingPromptIds, setDeletingPromptIds] = useState<number[]>([]);
  const [error, setError] = useState<string>("");
  const promptRequestIdRef = useRef(0);

  async function loadPromptsForRoom(roomId: number) {
    const requestId = ++promptRequestIdRef.current;
    const promptItems = await listRoomAdminPrompts(roomId);

    if (promptRequestIdRef.current !== requestId) {
      return false;
    }

    setPrompts(promptItems);
    return true;
  }

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
        promptRequestIdRef.current += 1;
        setSelectedRoomId(null);
        setSelectedModel("");
        setPrompts([]);
        return;
      }

      const firstRoom = roomItems[0];
      setSelectedRoomId(firstRoom.id);
      setSelectedModel(firstRoom.model_name);
      await loadPromptsForRoom(firstRoom.id);
    }

    load().catch((cause) => {
      setError(cause instanceof Error ? cause.message : "Failed to load settings");
    });
  }, []);

  async function onSelectRoom(roomId: number) {
    const room = rooms.find((item) => item.id === roomId);
    setSelectedRoomId(roomId);
    setSelectedModel(room?.model_name || "");
    setEditingPrompt(null);
    setFormValues(EMPTY_FORM);
    setFileInputKey((current) => current + 1);
    setError("");

    try {
      const applied = await loadPromptsForRoom(roomId);
      if (!applied && promptRequestIdRef.current > 0) {
        return;
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to load prompts");
    }
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

  function resetPromptForm() {
    setEditingPrompt(null);
    setFormValues(EMPTY_FORM);
    setFileInputKey((current) => current + 1);
  }

  function onEditPrompt(prompt: StylePrompt) {
    setEditingPrompt(prompt);
    setFormValues({
      name: prompt.name,
      description: prompt.description,
      prompt: prompt.prompt,
      previewFile: null
    });
    setFileInputKey((current) => current + 1);
  }

  async function onSavePrompt() {
    if (selectedRoomId === null) {
      return;
    }

    if (!formValues.name.trim() || !formValues.description.trim() || !formValues.prompt.trim()) {
      setError("Заполните все поля и загрузите изображение");
      return;
    }

    if (!editingPrompt && !formValues.previewFile) {
      setError("Заполните все поля и загрузите изображение");
      return;
    }

    setSavingPrompt(true);
    setError("");

    try {
      if (editingPrompt) {
        let previewImageUrl = editingPrompt.preview_image_url;
        if (formValues.previewFile) {
          const preview = await uploadRoomPromptPreview(selectedRoomId, formValues.previewFile);
          previewImageUrl = preview.url;
        }

        const updated = await updateRoomAdminPrompt(selectedRoomId, editingPrompt.id, {
          name: formValues.name.trim(),
          description: formValues.description.trim(),
          prompt: formValues.prompt.trim(),
          preview_image_url: previewImageUrl,
          icon_image_url: editingPrompt.icon_image_url
        });

        setPrompts((current) => current.map((item) => (item.id === updated.id ? updated : item)));
        resetPromptForm();
        return;
      }

      const preview = await uploadRoomPromptPreview(selectedRoomId, formValues.previewFile as File);

      const payload: PromptCreate = {
        name: formValues.name.trim(),
        description: formValues.description.trim(),
        prompt: formValues.prompt.trim(),
        preview_image_url: preview.url,
        icon_image_url: preview.url
      };

      const created = await createRoomAdminPrompt(selectedRoomId, payload);
      setPrompts((current) => [...current, created]);
      resetPromptForm();
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
      if (editingPrompt?.id === promptId) {
        resetPromptForm();
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to delete prompt");
    } finally {
      setDeletingPromptIds((current) => current.filter((id) => id !== promptId));
    }
  }

  return (
    <main className="page">
      <h1>Настройки комнаты</h1>

      <section className="page-section panel">
        <div className="section-header">
          <div>
            <h2>Параметры комнаты</h2>
            <p className="section-support">Выберите комнату и модель, чтобы быстро обновить рабочую конфигурацию.</p>
          </div>
          {savingModel ? <span className="status-inline">Сохраняем модель...</span> : null}
        </div>

        <div className="form-grid">
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

          <label htmlFor="settings-room-model">Модель комнаты</label>
          <select id="settings-room-model" value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)}>
            {models.map((modelName) => (
              <option key={modelName} value={modelName}>
                {modelName}
              </option>
            ))}
          </select>
        </div>

        <div className="action-row">
          <button type="button" onClick={onSaveModel} disabled={savingModel || !selectedModel || selectedRoomId === null}>
            {savingModel ? "Сохраняем модель..." : "Применить модель"}
          </button>
        </div>
      </section>

      <section className="page-section">
        <div className="section-header">
          <div>
            <h2>Промпты комнаты</h2>
            <p className="section-support">Создавайте, обновляйте и удаляйте стили в одном и том же рабочем потоке.</p>
          </div>
        </div>

        <PromptForm
          values={formValues}
          onChange={setFormValues}
          onSubmit={onSavePrompt}
          onCancel={resetPromptForm}
          isSubmitting={savingPrompt}
          mode={editingPrompt ? "edit" : "create"}
          fileInputKey={fileInputKey}
          previewHint={editingPrompt ? "Оставьте поле пустым, чтобы сохранить текущее превью." : undefined}
        />
      </section>

      {error ? <p role="alert">{error}</p> : null}

      <section className="prompt-list">
        {prompts.length === 0 ? (
          <div className="empty-state">
            <p>В этой комнате пока нет промптов.</p>
            <p>Добавьте первый стиль, чтобы команда сразу видела превью и описание.</p>
          </div>
        ) : null}
        {prompts.map((item) => (
          <article key={item.id} className="prompt-item prompt-card">
            <div className="prompt-card__media">
              <img src={item.preview_image_url} alt={`${item.name} preview`} width={120} height={80} />
            </div>
            <div className="prompt-card__content">
              <h3>{item.name}</h3>
              <p>{item.description}</p>
              <p className="prompt-card__meta">Превью: {item.preview_image_url}</p>
            </div>
            <div className="prompt-item__actions">
              <button type="button" className="button-secondary" onClick={() => onEditPrompt(item)}>
                Редактировать {item.name}
              </button>
              <button
                type="button"
                className="button-danger"
                aria-label={deletingPromptIds.includes(item.id) ? `Удаляем ${item.name}` : `Удалить ${item.name} навсегда`}
                onClick={() => void onDeletePrompt(item.id)}
                disabled={deletingPromptIds.includes(item.id)}
              >
                {deletingPromptIds.includes(item.id) ? "Удаляем..." : "Удалить навсегда"}
              </button>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
