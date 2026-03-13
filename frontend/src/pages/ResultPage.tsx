import React, { useEffect, useMemo, useState } from "react";

import { getRoomJobStatus } from "../lib/api";
import { normalizeResultHash, normalizeRoomSlug } from "../lib/roomRouting";
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

  function onBack() {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    window.location.assign(`/${resolvedRoomSlug}`);
  }

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
            <p className="result-eyebrow">ИИ Фоторамка</p>
            <h1>Результат готов</h1>
            <p className="result-subtitle">Ваш кадр готов. Следующий шаг: откройте ссылку для скачивания или заберите фото через QR-код.</p>
            <div className="result-media">
              <img className="result-photo" src={job.result_url} alt="generated photo" />
            </div>
          </section>

          <section className="panel result-download-panel">
            <button type="button" className="button-secondary result-back-button" onClick={onBack}>
              Назад
            </button>
            <p className="result-download-eyebrow">Следующий шаг</p>
            <h2>Скачайте фото</h2>
            <a href={job.download_url} className="result-download-link">
              Открыть ссылку для скачивания
            </a>
            <p className="result-download-hint">Или отсканируйте QR-код камерой телефона.</p>
            <a href={job.download_url} className="result-qr-link" aria-label="Скачать фото через QR-код">
              <img className="result-qr" src={job.qr_url} alt="download qr" width={220} />
            </a>
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
        <p className="result-eyebrow">ИИ Фоторамка</p>
        <h1>Собираем ваш финальный кадр</h1>
        <p className="result-loading-text">Обычно это занимает меньше минуты.</p>
        <p className="result-loading-support">Не закрывайте страницу: как только изображение будет готово, здесь появится результат и ссылка для скачивания.</p>
        <div className="result-loading-preview" data-testid="result-loading-preview" aria-hidden="true" />
        <div className="result-loading-bar" aria-hidden="true">
          <span className="result-loading-bar__progress result-loading-bar__progress--indeterminate" />
        </div>
      </section>
    </main>
  );
}
