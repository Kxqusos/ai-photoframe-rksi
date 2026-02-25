import React, { useState } from "react";

import type { PromptCreate, StylePrompt } from "../types";

type Props = {
  prompts: StylePrompt[];
  onCreate: (payload: PromptCreate) => Promise<void>;
  onDelete: (promptId: number) => Promise<void>;
};

export function AdminPromptManager({ prompts, onCreate, onDelete }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [prompt, setPrompt] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [iconUrl, setIconUrl] = useState("");

  async function submit() {
    if (!name.trim() || !description.trim() || !prompt.trim()) {
      return;
    }
    await onCreate({
      name: name.trim(),
      description: description.trim(),
      prompt: prompt.trim(),
      preview_image_url: previewUrl.trim() || "/media/previews/default.jpg",
      icon_image_url: iconUrl.trim() || "/media/icons/default.png"
    });
    setName("");
    setDescription("");
    setPrompt("");
    setPreviewUrl("");
    setIconUrl("");
  }

  return (
    <section className="panel form-grid" aria-label="admin prompt manager">
      <label htmlFor="admin-prompt-name">Prompt name</label>
      <input id="admin-prompt-name" value={name} onChange={(event) => setName(event.target.value)} />

      <label htmlFor="admin-prompt-description">Prompt description</label>
      <input id="admin-prompt-description" value={description} onChange={(event) => setDescription(event.target.value)} />

      <label htmlFor="admin-prompt-text">Prompt text</label>
      <textarea id="admin-prompt-text" value={prompt} onChange={(event) => setPrompt(event.target.value)} />

      <label htmlFor="admin-prompt-preview-url">Preview URL</label>
      <input id="admin-prompt-preview-url" value={previewUrl} onChange={(event) => setPreviewUrl(event.target.value)} />

      <label htmlFor="admin-prompt-icon-url">Icon URL</label>
      <input id="admin-prompt-icon-url" value={iconUrl} onChange={(event) => setIconUrl(event.target.value)} />

      <button type="button" onClick={() => void submit()}>
        Add prompt
      </button>

      <div className="prompt-list">
        {prompts.map((item) => (
          <div key={item.id} className="prompt-item">
            <h3>{item.name}</h3>
            <button type="button" onClick={() => void onDelete(item.id)}>
              Delete {item.name}
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
