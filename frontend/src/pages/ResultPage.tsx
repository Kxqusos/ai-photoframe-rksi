import React, { useEffect, useMemo, useState } from "react";

import { getRoomJobStatus } from "../lib/api";
import { buildPublicRoomPath, normalizeResultHash, normalizeRoomSlug } from "../lib/roomRouting";
import type { JobStatus } from "../types";

type Props = {
  roomSlug: string;
  jpgHash?: string;
};

function resolveJpgHash(provided?: string): string | null {
  if (typeof provided === "string" && provided.trim()) {
    return normalizeResultHash(provided);
  }

  const fromPath = window.location.pathname.match(/\/result\/([^/]+)\/?$/i)?.[1];
  if (!fromPath) {
    return null;
  }
  return normalizeResultHash(fromPath);
}

function isTerminalJobStatus(status: JobStatus | null): boolean {
  return status?.status === "completed" || status?.status === "error";
}

export function ResultPage({ roomSlug, jpgHash: providedJpgHash }: Props) {
  const resolvedRoomSlug = useMemo(() => normalizeRoomSlug(roomSlug), [roomSlug]);
  const jpgHash = useMemo(() => resolveJpgHash(providedJpgHash), [providedJpgHash]);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string>("");
  const [mediaFailed, setMediaFailed] = useState(false);

  function onBack() {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    window.location.assign(buildPublicRoomPath(resolvedRoomSlug));
  }

  useEffect(() => {
    setMediaFailed(false);
  }, [jpgHash, job?.result_url, job?.status]);

  useEffect(() => {
    if (jpgHash === null) {
      setError("Не указан идентификатор результата");
      return;
    }

    let cancelled = false;
    let settled = false;
    let timer = 0;

    async function poll() {
      try {
        const status = await getRoomJobStatus(resolvedRoomSlug, jpgHash);
        if (cancelled || settled) {
          return;
        }
        setError("");
        setJob(status);
        if (isTerminalJobStatus(status)) {
          settled = true;
          window.clearInterval(timer);
        }
      } catch (cause) {
        if (cancelled || settled) {
          return;
        }
        setError(cause instanceof Error ? cause.message : "Не удалось получить статус генерации");
      }
    }

    poll();
    timer = window.setInterval(poll, 1500);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [jpgHash, resolvedRoomSlug]);

  if (mediaFailed) {
    return (
      <main className="page result-page result-page--error">
        <section className="panel result-error-card">
          <p className="result-eyebrow">ИИ Фоторамка</p>
          <h1>Не получилось показать готовый кадр</h1>
          <p className="result-error-text" role="alert">
            Не удалось загрузить готовое фото
          </p>
          <p className="result-error-help">Откройте результат заново или вернитесь к съемке и создайте новый кадр.</p>
          <button type="button" onClick={onBack}>
            Вернуться и снять заново
          </button>
        </section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page result-page result-page--error">
        <section className="panel result-error-card">
          <p className="result-eyebrow">ИИ Фоторамка</p>
          <h1>Не получилось завершить обработку</h1>
          <p className="result-error-text" role="alert">
            {error}
          </p>
          <p className="result-error-help">Вернитесь к съемке и попробуйте снова. Мы сохраним привычный маршрут назад.</p>
          <button type="button" onClick={onBack}>
            Вернуться и снять заново
          </button>
        </section>
      </main>
    );
  }

  if (job?.status === "completed" && job.result_url && job.qr_url && job.download_url) {
    return (
      <main className="page result-page result-page--completed">
        <div className="result-shell">
          <section className="panel result-hero">
            <div className="result-media">
              <img className="result-photo" src={job.result_url} alt="generated photo" onError={() => setMediaFailed(true)} />
            </div>
          </section>

          <section className="panel result-download-panel">
            <p className="result-download-eyebrow">Готово к скачиванию</p>
            <h2>Заберите фото на телефон</h2>
            <p className="result-download-hint">Отсканируйте QR-код камерой телефона.</p>
            <p className="result-download-hint">После сканирования откроется страница с готовым кадром для сохранения.</p>
            <div className="result-download-qr-slot">
              <a href={job.download_url} className="result-qr-link" aria-label="Скачать фото через QR-код">
                <img className="result-qr" src={job.qr_url} alt="download qr" width={220} />
              </a>
            </div>
            <button type="button" className="button-secondary result-back-button" onClick={onBack}>
              Назад
            </button>
          </section>
        </div>
      </main>
    );
  }

  if (job?.status === "error") {
    return (
      <main className="page result-page result-page--error">
        <section className="panel result-error-card">
          <p className="result-eyebrow">ИИ Фоторамка</p>
          <h1>Не получилось завершить обработку</h1>
          <p className="result-error-text" role="alert">
            {job.error_message || "Ошибка генерации"}
          </p>
          <p className="result-error-help">Вернитесь к съемке и попробуйте снова. Мы сохраним привычный маршрут назад.</p>
          <button type="button" onClick={onBack}>
            Вернуться и снять заново
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="page result-page result-page--loading">
      <section className="panel result-loading-card">
        <div className="result-loading-header">
          <p className="result-eyebrow">ИИ Фоторамка</p>
          <h1 className="result-loading-title">Собираем ваш финальный кадр</h1>
        </div>
        <div className="result-loading-copy">
          <p className="result-loading-text">Обычно это занимает меньше минуты.</p>
        </div>
        <div className="result-loading-bar" aria-hidden="true">
          <span className="result-loading-bar__progress result-loading-bar__progress--indeterminate" />
        </div>
      </section>
    </main>
  );
}
