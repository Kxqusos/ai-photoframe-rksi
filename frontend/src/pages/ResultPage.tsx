import React, { useEffect, useMemo, useState } from "react";

import { getJobStatus } from "../lib/api";
import type { JobStatus } from "../types";

type Props = {
  jpgHash?: string;
};

function resolveJpgHash(provided?: string): string | null {
  const pattern = /^[0-9a-f]{16}$/;

  if (typeof provided === "string" && pattern.test(provided)) {
    return provided;
  }

  if (typeof window === "undefined") {
    return null;
  }

  const match = window.location.pathname.match(/^\/result\/([0-9a-f]{16})$/i);
  if (!match) {
    return null;
  }

  return match[1].toLowerCase();
}

export function ResultPage({ jpgHash: providedJpgHash }: Props) {
  const jpgHash = useMemo(() => resolveJpgHash(providedJpgHash), [providedJpgHash]);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (jpgHash === null) {
      setError("Требуется параметр jpg_hash");
      return;
    }

    let cancelled = false;

    async function poll() {
      try {
        const status = await getJobStatus(jpgHash);
        if (cancelled) {
          return;
        }
        setJob(status);
      } catch (cause) {
        if (cancelled) {
          return;
        }
        setError(cause instanceof Error ? cause.message : "Не удалось получить статус генерации");
      }
    }

    poll();
    const timer = window.setInterval(poll, 1500);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [jpgHash]);

  if (error) {
    return <p role="alert">{error}</p>;
  }

  function onBack() {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    window.location.assign("/");
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
              <img className="result-photo" src={job.result_url} alt="сгенерированное фото" />
            </div>
          </section>

          <section className="panel result-download-panel">
            <button type="button" className="button-secondary result-back-button" onClick={onBack}>
              Назад
            </button>
            <h2>Сканируйте QR-код</h2>
            <p className="result-download-hint">Откройте ссылку с телефона, чтобы скачать фото в полном размере.</p>
            <a href={job.download_url} className="result-qr-link" aria-label="Скачать фото">
              <img className="result-qr" src={job.qr_url} alt="qr-код для скачивания" width={220} />
            </a>
          </section>
        </div>
      </main>
    );
  }

  if (job?.status === "error") {
    return <p role="alert">{job.error_message || "Генерация завершилась с ошибкой"}</p>;
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
