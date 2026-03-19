import { useEffect, useState } from "react";

import { PromptForm, type PromptFormValues } from "./PromptForm";
import type { StylePrompt } from "../types";

type PromptCreateInput = {
  name: string;
  description: string;
  prompt: string;
  previewFile: File;
};

type PromptUpdateInput = {
  id: number;
  name: string;
  description: string;
  prompt: string;
  previewFile: File | null;
  previewImageUrl: string;
  iconImageUrl: string;
};

type Props = {
  prompts: StylePrompt[];
  onCreate: (payload: PromptCreateInput) => Promise<boolean>;
  onUpdate: (payload: PromptUpdateInput) => Promise<boolean>;
  onDelete: (promptId: number) => Promise<boolean>;
};

export function AdminPromptManager({ prompts, onCreate, onUpdate, onDelete }: Props) {
  const [formValues, setFormValues] = useState<PromptFormValues>({
    name: "",
    description: "",
    prompt: "",
    previewFile: null
  });
  const [editingPrompt, setEditingPrompt] = useState<StylePrompt | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingPromptId, setDeletingPromptId] = useState<number | null>(null);

  useEffect(() => {
    if (!editingPrompt) {
      return;
    }

    if (prompts.some((item) => item.id === editingPrompt.id)) {
      return;
    }

    resetForm();
  }, [editingPrompt, prompts]);

  function resetForm() {
    setFormValues({
      name: "",
      description: "",
      prompt: "",
      previewFile: null
    });
    setEditingPrompt(null);
    setFileInputKey((current) => current + 1);
  }

  function startEditing(item: StylePrompt) {
    setEditingPrompt(item);
    setFormValues({
      name: item.name,
      description: item.description,
      prompt: item.prompt,
      previewFile: null
    });
    setFileInputKey((current) => current + 1);
  }

  async function submit() {
    if (!formValues.name.trim() || !formValues.description.trim() || !formValues.prompt.trim()) {
      return;
    }

    if (!editingPrompt && !formValues.previewFile) {
      return;
    }

    setIsSaving(true);
    try {
      if (editingPrompt) {
        const updated = await onUpdate({
          id: editingPrompt.id,
          name: formValues.name.trim(),
          description: formValues.description.trim(),
          prompt: formValues.prompt.trim(),
          previewFile: formValues.previewFile,
          previewImageUrl: editingPrompt.preview_image_url,
          iconImageUrl: editingPrompt.icon_image_url
        });
        if (!updated) {
          return;
        }
        resetForm();
        return;
      }

      const created = await onCreate({
        name: formValues.name.trim(),
        description: formValues.description.trim(),
        prompt: formValues.prompt.trim(),
        previewFile: formValues.previewFile as File
      });
      if (!created) {
        return;
      }
      resetForm();
    } catch {
      return;
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(promptId: number) {
    setDeletingPromptId(promptId);
    try {
      const deleted = await onDelete(promptId);
      if (deleted && editingPrompt?.id === promptId) {
        resetForm();
      }
    } catch {
      return;
    } finally {
      setDeletingPromptId(null);
    }
  }

  return (
    <section aria-label="управление промптами">
      <PromptForm
        values={formValues}
        onChange={setFormValues}
        onSubmit={() => void submit()}
        onCancel={resetForm}
        isSubmitting={isSaving}
        mode={editingPrompt ? "edit" : "create"}
        fileInputKey={fileInputKey}
        submitLabel={editingPrompt ? "Сохранить изменения" : "Добавить промпт"}
        submittingLabel={editingPrompt ? "Сохраняем изменения..." : "Добавляем промпт..."}
        nameLabel="Название промпта"
        descriptionLabel="Описание промпта"
        promptLabel="Текст промпта"
        previewLabel="Превью (PNG/JPG/JPEG)"
        previewHint={editingPrompt ? "Оставьте поле пустым, чтобы сохранить текущее превью." : undefined}
      />

      <div className="prompt-list">
        {prompts.length === 0 ? (
          <div className="empty-state">
            <p>Промптов пока нет.</p>
            <p>Добавьте первый промпт, чтобы у комнаты появился наглядный набор стилей.</p>
          </div>
        ) : null}
        {prompts.map((item) => {
          const isDeleting = deletingPromptId === item.id;
          return (
            <article key={item.id} className="prompt-item prompt-card">
              <div className="prompt-card__media">
                <img src={item.preview_image_url} alt={`${item.name} preview`} width={148} height={112} />
              </div>
              <div className="prompt-card__content">
                <h3>{item.name}</h3>
                <p>{item.description}</p>
              </div>
              <div className="prompt-item__actions">
                <button type="button" className="button-secondary" onClick={() => startEditing(item)}>
                  Редактировать
                </button>
                <button
                  type="button"
                  className="button-danger"
                  aria-label={isDeleting ? "Удаляем..." : "Удалить"}
                  onClick={() => void handleDelete(item.id)}
                  disabled={isDeleting}
                >
                  {isDeleting ? "Удаляем..." : "Удалить"}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
