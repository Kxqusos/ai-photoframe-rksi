import React from "react";

type PromptFormValues = {
  name: string;
  description: string;
  prompt: string;
  previewFile: File | null;
  iconFile: File | null;
};

type Props = {
  values: PromptFormValues;
  onChange: (next: PromptFormValues) => void;
  onSubmit: () => void;
  isSubmitting?: boolean;
};

export function PromptForm({ values, onChange, onSubmit, isSubmitting = false }: Props) {
  return (
    <section>
      <h2>Новый стиль</h2>

      <label htmlFor="prompt-name">Название</label>
      <input
        id="prompt-name"
        value={values.name}
        onChange={(event) => onChange({ ...values, name: event.target.value })}
      />

      <label htmlFor="prompt-description">Описание</label>
      <input
        id="prompt-description"
        value={values.description}
        onChange={(event) => onChange({ ...values, description: event.target.value })}
      />

      <label htmlFor="prompt-text">Промпт</label>
      <textarea
        id="prompt-text"
        value={values.prompt}
        onChange={(event) => onChange({ ...values, prompt: event.target.value })}
      />

      <label htmlFor="prompt-preview">Пример результата</label>
      <input
        id="prompt-preview"
        type="file"
        accept="image/*"
        onChange={(event) => onChange({ ...values, previewFile: event.target.files?.[0] ?? null })}
      />

      <label htmlFor="prompt-icon">Иконка</label>
      <input
        id="prompt-icon"
        type="file"
        accept="image/*"
        onChange={(event) => onChange({ ...values, iconFile: event.target.files?.[0] ?? null })}
      />

      <button type="button" onClick={onSubmit} disabled={isSubmitting}>
        Сохранить
      </button>
    </section>
  );
}

export type { PromptFormValues };
