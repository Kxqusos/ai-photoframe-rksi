import React, { useState } from "react";

import type { StylePrompt } from "../types";

type PromptCreateInput = {
  name: string;
  description: string;
  prompt: string;
  previewFile: File;
};

type Props = {
  prompts: StylePrompt[];
  onCreate: (payload: PromptCreateInput) => Promise<void>;
  onDelete: (promptId: number) => Promise<void>;
};

export function AdminPromptManager({ prompts, onCreate, onDelete }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [prompt, setPrompt] = useState("");
  const [previewFile, setPreviewFile] = useState<File | null>(null);

  async function submit() {
    if (!name.trim() || !description.trim() || !prompt.trim() || !previewFile) {
      return;
    }

    await onCreate({
      name: name.trim(),
      description: description.trim(),
      prompt: prompt.trim(),
      previewFile
    });
    setName("");
    setDescription("");
    setPrompt("");
    setPreviewFile(null);
  }

  return (
    <section className="panel form-grid" aria-label="управление промптами">
      <label htmlFor="admin-prompt-name">Название промпта</label>
      <input id="admin-prompt-name" value={name} onChange={(event) => setName(event.target.value)} />

      <label htmlFor="admin-prompt-description">Описание промпта</label>
      <input id="admin-prompt-description" value={description} onChange={(event) => setDescription(event.target.value)} />

      <label htmlFor="admin-prompt-text">Текст промпта</label>
      <textarea id="admin-prompt-text" value={prompt} onChange={(event) => setPrompt(event.target.value)} />

      <label htmlFor="admin-prompt-preview-file">Превью (PNG/JPG/JPEG)</label>
      <input
        id="admin-prompt-preview-file"
        type="file"
        accept="image/png,image/jpeg,image/jpg"
        onChange={(event) => setPreviewFile(event.target.files?.[0] ?? null)}
      />

      <button type="button" onClick={() => void submit()}>
        Добавить промпт
      </button>

      <div className="prompt-list">
        {prompts.map((item) => (
          <div key={item.id} className="prompt-item">
            <h3>{item.name}</h3>
            <button type="button" onClick={() => void onDelete(item.id)}>
              Удалить {item.name}
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
