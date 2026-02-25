import React, { useEffect, useMemo, useState } from "react";

import { getRoomJobStatus } from "../lib/api";
import { normalizeRoomSlug } from "../lib/roomRouting";
import type { JobStatus } from "../types";

type Props = {
  roomSlug: string;
  jpgHash?: string;
};

function resolveJpgHash(provided?: string): string | null {
  if (typeof provided === "string" && provided.trim()) {
    return provided;
  }

  const fromPath = window.location.pathname.match(/\/result\/([^/]+)\/?$/i)?.[1];
  if (!fromPath) {
    return null;
  }
  return fromPath;
}

export function ResultPage({ roomSlug, jpgHash: providedJpgHash }: Props) {
  const resolvedRoomSlug = useMemo(() => normalizeRoomSlug(roomSlug), [roomSlug]);
  const jpgHash = useMemo(() => resolveJpgHash(providedJpgHash), [providedJpgHash]);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (jpgHash === null) {
      setError("jpgHash is required");
      return;
    }

    let cancelled = false;

    async function poll() {
      try {
        const status = await getRoomJobStatus(resolvedRoomSlug, jpgHash);
        if (cancelled) {
          return;
        }
        setJob(status);
      } catch (cause) {
        if (cancelled) {
          return;
        }
        setError(cause instanceof Error ? cause.message : "Failed to get job status");
      }
    }

    poll();
    const timer = window.setInterval(poll, 1500);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [jpgHash, resolvedRoomSlug]);

  if (error) {
    return <p role="alert">{error}</p>;
  }

  function onBack() {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    window.location.assign(`/${resolvedRoomSlug}`);
  }

  if (job?.status === "completed" && job.result_url && job.qr_url && job.download_url) {
    return (
      <main className="page result-page result-page--completed">
        <div className="result-shell">
          <section className="panel result-hero">
            <p className="result-eyebrow">ИИ Фоторамка</p>
            <h1>Результат</h1>
            <p className="result-subtitle">Ваше изображение готово. Сохраните его на телефон через QR-код.</p>
            <div className="result-media">
              <img className="result-photo" src={job.result_url} alt="generated photo" />
            </div>
          </section>

          <section className="panel result-download-panel">
            <button type="button" className="button-secondary result-back-button" onClick={onBack}>
              Назад
            </button>
            <h2>Сканируйте QR-код</h2>
            <p className="result-download-hint">Откройте ссылку с телефона, чтобы скачать фото в полном размере.</p>
            <a href={job.download_url} className="result-qr-link" aria-label="Скачать фото">
              <img className="result-qr" src={job.qr_url} alt="download qr" width={220} />
            </a>
          </section>
        </div>
      </main>
    );
  }

  if (job?.status === "error") {
    return <p role="alert">{job.error_message || "Generation failed"}</p>;
  }

  return (
    <main className="page result-page result-page--loading">
      <section className="panel result-loading-card">
        <p className="result-eyebrow">ИИ Фоторамка</p>
        <h1>Результат</h1>
        <p className="result-loading-text">Обработка изображения...</p>
        <div className="result-loading-bar" aria-hidden="true">
          <span className="result-loading-bar__progress result-loading-bar__progress--indeterminate" />
        </div>
      </section>
    </main>
  );
}
