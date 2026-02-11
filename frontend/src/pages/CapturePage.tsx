import React from "react";
import { useEffect, useMemo, useState } from "react";

import { StyleCard } from "../components/StyleCard";
import { createJob, listPrompts } from "../lib/api";
import type { StylePrompt } from "../types";

export function CapturePage() {
  const [styles, setStyles] = useState<StylePrompt[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [photo, setPhoto] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    listPrompts().then((items) => {
      setStyles(items);
      if (items.length > 0) {
        setSelectedId(items[0].id);
      }
    });
  }, []);

  const canSubmit = useMemo(() => selectedId !== null && photo !== null, [selectedId, photo]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!canSubmit || selectedId === null || photo === null) {
      return;
    }

    const job = await createJob(photo, selectedId);
    setStatus(`Job ${job.id}: ${job.status}`);
    window.location.assign(`/result?jobId=${job.id}`);
  }

  return (
    <main>
      <h1>AI Photoframe</h1>
      <section aria-label="style selection">
        {styles.map((style) => (
          <StyleCard key={style.id} style={style} selected={style.id === selectedId} onSelect={setSelectedId} />
        ))}
      </section>

      <form onSubmit={onSubmit}>
        <label htmlFor="photo">Upload photo</label>
        <input
          id="photo"
          name="photo"
          type="file"
          accept="image/*"
          onChange={(event) => setPhoto(event.target.files?.[0] ?? null)}
        />
        <button type="submit" disabled={!canSubmit}>
          Generate
        </button>
      </form>

      {status ? <p>{status}</p> : null}
    </main>
  );
}
