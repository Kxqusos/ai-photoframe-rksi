import React from "react";

type PromptFormValues = {
  name: string;
  description: string;
  prompt: string;
  previewFile: File | null;
};

type Props = {
  values: PromptFormValues;
  onChange: (next: PromptFormValues) => void;
  onSubmit: () => void;
  onCancel?: () => void;
  isSubmitting?: boolean;
  mode?: "create" | "edit";
  heading?: string;
  supportText?: string;
  submitLabel?: string;
  submittingLabel?: string;
  cancelLabel?: string;
  fileInputKey?: number;
  nameLabel?: string;
  descriptionLabel?: string;
  promptLabel?: string;
  previewLabel?: string;
  previewHint?: string;
};

export function PromptForm({
  values,
  onChange,
  onSubmit,
  onCancel,
  isSubmitting = false,
  mode = "create",
  heading,
  supportText,
  submitLabel,
  submittingLabel,
  cancelLabel = "Отменить редактирование",
  fileInputKey = 0,
  nameLabel = "Название",
  descriptionLabel = "Описание",
  promptLabel = "Промпт",
  previewLabel = "Пример результата",
  previewHint
}: Props) {
  const isEditing = mode === "edit";
  const resolvedHeading = heading || (isEditing ? "Редактирование промпта" : "Новый промпт");
  const resolvedSubmitLabel = submitLabel || (isEditing ? "Сохранить изменения" : "Создать промпт");
  const resolvedSubmittingLabel = submittingLabel || (isEditing ? "Сохраняем изменения..." : "Создаем промпт...");

  return (
    <section className="panel form-grid prompt-form">
      <div className="section-header">
        <div>
          <h2>{resolvedHeading}</h2>
          {supportText ? <p className="section-support">{supportText}</p> : null}
        </div>
      </div>

      <label htmlFor="prompt-name">{nameLabel}</label>
      <input
        id="prompt-name"
        value={values.name}
        onChange={(event) => onChange({ ...values, name: event.target.value })}
      />

      <label htmlFor="prompt-description">{descriptionLabel}</label>
      <input
        id="prompt-description"
        value={values.description}
        onChange={(event) => onChange({ ...values, description: event.target.value })}
      />

      <label htmlFor="prompt-text">{promptLabel}</label>
      <textarea
        id="prompt-text"
        value={values.prompt}
        onChange={(event) => onChange({ ...values, prompt: event.target.value })}
      />

      <label htmlFor="prompt-preview">{previewLabel}</label>
      <input
        key={fileInputKey}
        id="prompt-preview"
        type="file"
        accept="image/*"
        onChange={(event) => onChange({ ...values, previewFile: event.target.files?.[0] ?? null })}
      />
      {previewHint ? <p className="field-support">{previewHint}</p> : null}

      <div className="action-row">
        <button type="button" onClick={onSubmit} disabled={isSubmitting}>
          {isSubmitting ? resolvedSubmittingLabel : resolvedSubmitLabel}
        </button>
        {isEditing && onCancel ? (
          <button type="button" className="button-secondary" onClick={onCancel} disabled={isSubmitting}>
            {cancelLabel}
          </button>
        ) : null}
      </div>
    </section>
  );
}

export type { PromptFormValues };
