import React, { useEffect, useMemo, useState } from "react";

import { getJobStatus } from "../lib/api";
import type { JobStatus } from "../types";

type Props = {
  jobId?: number;
};

function resolveJobId(provided?: number): number | null {
  if (typeof provided === "number" && Number.isFinite(provided)) {
    return provided;
  }

  const fromQuery = new URLSearchParams(window.location.search).get("jobId");
  if (!fromQuery) {
    return null;
  }

  const value = Number(fromQuery);
  return Number.isFinite(value) ? value : null;
}

export function ResultPage({ jobId: providedJobId }: Props) {
  const jobId = useMemo(() => resolveJobId(providedJobId), [providedJobId]);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (jobId === null) {
      setError("jobId is required");
      return;
    }

    let cancelled = false;

    async function poll() {
      try {
        const status = await getJobStatus(jobId);
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
  }, [jobId]);

  if (error) {
    return <p role="alert">{error}</p>;
  }

  if (job?.status === "completed" && job.result_url && job.qr_url && job.download_url) {
    return (
      <main className="page result-page result-page--completed">
        <div className="result-shell">
          <section className="panel result-hero">
            <p className="result-eyebrow">AI Photoframe</p>
            <h1>Результат</h1>
            <p className="result-subtitle">Ваше изображение готово. Сохраните его на телефон через QR-код.</p>
            <div className="result-media">
              <img className="result-photo" src={job.result_url} alt="generated photo" />
            </div>
          </section>

          <section className="panel result-download-panel">
            <h2>Сканируйте QR-код</h2>
            <p className="result-download-hint">Откройте ссылку с телефона, чтобы скачать фото в полном размере.</p>
            <a href={job.download_url} className="result-qr-link" aria-label="Скачать фото">
              <img className="result-qr" src={job.qr_url} alt="download qr" width={220} />
            </a>
            <a href={job.download_url} className="result-download-link">
              Скачать фото
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
        <p className="result-eyebrow">AI Photoframe</p>
        <h1>Результат</h1>
        <p className="result-loading-text">Обработка изображения...</p>
        <div className="result-loading-bar" aria-hidden="true">
          <span className="result-loading-bar__progress" />
        </div>
      </section>
    </main>
  );
}
