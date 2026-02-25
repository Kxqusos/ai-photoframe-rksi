import React, { useEffect, useState } from "react";

import { PromptForm, type PromptFormValues } from "../components/PromptForm";
import {
  createPrompt,
  deletePrompt,
  getModel,
  listModels,
  listPrompts,
  setModel,
  uploadPromptIcon,
  uploadPromptPreview
} from "../lib/api";
import type { PromptCreate, StylePrompt } from "../types";

const EMPTY_FORM: PromptFormValues = {
  name: "",
  description: "",
  prompt: "",
  previewFile: null,
  iconFile: null
};

export function SettingsPage() {
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [prompts, setPrompts] = useState<StylePrompt[]>([]);
  const [formValues, setFormValues] = useState<PromptFormValues>(EMPTY_FORM);
  const [savingPrompt, setSavingPrompt] = useState(false);
  const [savingModel, setSavingModel] = useState(false);
  const [deletingPromptIds, setDeletingPromptIds] = useState<number[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    async function load() {
      const [modelNames, modelSetting, promptItems] = await Promise.all([
        listModels(),
        getModel(),
        listPrompts()
      ]);

      setModels(modelNames);
      setSelectedModel(modelSetting.model_name);
      setPrompts(promptItems);
    }

    load().catch((cause) => {
      setError(cause instanceof Error ? cause.message : "Не удалось загрузить настройки");
    });
  }, []);

  async function onSaveModel() {
    if (!selectedModel) {
      return;
    }

    setSavingModel(true);
    setError("");
    try {
      await setModel(selectedModel);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось сохранить модель");
    } finally {
      setSavingModel(false);
    }
  }

  async function onSavePrompt() {
    if (
      !formValues.name.trim() ||
      !formValues.description.trim() ||
      !formValues.prompt.trim() ||
      !formValues.previewFile ||
      !formValues.iconFile
    ) {
      setError("Заполните все поля и загрузите обе картинки");
      return;
    }

    setSavingPrompt(true);
    setError("");

    try {
      const [preview, icon] = await Promise.all([
        uploadPromptPreview(formValues.previewFile),
        uploadPromptIcon(formValues.iconFile)
      ]);

      const payload: PromptCreate = {
        name: formValues.name.trim(),
        description: formValues.description.trim(),
        prompt: formValues.prompt.trim(),
        preview_image_url: preview.url,
        icon_image_url: icon.url
      };

      const created = await createPrompt(payload);
      setPrompts((current) => [...current, created]);
      setFormValues(EMPTY_FORM);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось сохранить стиль");
    } finally {
      setSavingPrompt(false);
    }
  }

  async function onDeletePrompt(promptId: number) {
    setError("");
    setDeletingPromptIds((current) => [...current, promptId]);
    try {
      await deletePrompt(promptId);
      setPrompts((current) => current.filter((item) => item.id !== promptId));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось удалить стиль");
    } finally {
      setDeletingPromptIds((current) => current.filter((id) => id !== promptId));
    }
  }

  return (
    <main className="page">
      <h1>Настройки</h1>

      <section className="panel form-grid">
        <h2>Модель OpenRouter</h2>
        <select value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)}>
          {models.map((modelName) => (
            <option key={modelName} value={modelName}>
              {modelName}
            </option>
          ))}
        </select>
        <div className="action-row">
          <button type="button" onClick={onSaveModel} disabled={savingModel || !selectedModel}>
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
            <img src={item.preview_image_url} alt={`${item.name} превью`} width={120} height={80} />
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
