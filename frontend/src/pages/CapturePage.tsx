import React from "react";
import { useEffect, useRef, useState } from "react";

import { PublicRoomMenu } from "../components/PublicRoomMenu";
import { createRoomJob, listRoomPrompts } from "../lib/api";
import { normalizeRoomSlug } from "../lib/roomRouting";
import { readStoredStyleId, writeStoredStyleId } from "../lib/styleSelection";
import type { StylePrompt } from "../types";

type Props = {
  roomSlug: string;
};

export function CapturePage({ roomSlug }: Props) {
  const resolvedRoomSlug = normalizeRoomSlug(roomSlug);
  const [styles, setStyles] = useState<StylePrompt[]>([]);
  const [stylesRoomSlug, setStylesRoomSlug] = useState<string | null>(null);
  const [stylesLoading, setStylesLoading] = useState(true);
  const [stylesError, setStylesError] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [countdown, setCountdown] = useState<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState("");
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const countdownTimerRef = useRef<number | null>(null);

  useEffect(() => {
    let active = true;

    if (countdownTimerRef.current !== null) {
      window.clearInterval(countdownTimerRef.current);
      countdownTimerRef.current = null;
    }

    setCountdown(null);
    setStyles([]);
    setStylesRoomSlug(null);
    setSelectedId(null);
    setStylesLoading(true);
    setStylesError("");
    setGenerationError("");

    listRoomPrompts(resolvedRoomSlug)
      .then((items) => {
        if (active) {
          setStyles(items);
          setStylesRoomSlug(resolvedRoomSlug);
          if (items.length > 0) {
            const stored = readStoredStyleId(resolvedRoomSlug);
            const initial =
              (stored !== null && items.some((item) => item.id === stored) ? stored : null) ?? items[0].id;
            setSelectedId(initial);
            return;
          }
          setSelectedId(null);
        }
      })
      .catch(() => {
        if (active) {
          setStyles([]);
          setStylesRoomSlug(resolvedRoomSlug);
          setSelectedId(null);
          setStylesError("Не удалось загрузить стили. Обновите экран и попробуйте ещё раз.");
        }
      })
      .finally(() => {
        if (active) {
          setStylesLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [resolvedRoomSlug]);

  useEffect(() => {
    let active = true;

    async function setupCamera() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError("Камера недоступна. Проверьте разрешения браузера или устройство.");
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user" },
          audio: false
        });
        if (!active) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;
        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          await video.play().catch(() => undefined);
        }
        setCameraError("");
        setCameraReady(true);
      } catch {
        setCameraError("Не удалось открыть камеру. Разрешите доступ и попробуйте ещё раз.");
      }
    }

    setupCamera().catch(() => undefined);

    return () => {
      active = false;
      if (countdownTimerRef.current !== null) {
        window.clearInterval(countdownTimerRef.current);
        countdownTimerRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, []);

  async function startGeneration(capturedPhoto: File) {
    if (selectedId === null) {
      return;
    }

    setIsGenerating(true);
    setGenerationError("");
    try {
      const job = await createRoomJob(resolvedRoomSlug, capturedPhoto, selectedId);
      window.location.assign(`/${resolvedRoomSlug}/result/${job.id}`);
    } catch {
      setIsGenerating(false);
      setGenerationError("Не удалось отправить фото. Попробуйте ещё раз.");
    }
  }

  function onStyleSelect(styleId: number) {
    setSelectedId(styleId);
    setGenerationError("");
    writeStoredStyleId(styleId, resolvedRoomSlug);
  }

  function capturePhoto() {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || video.videoWidth === 0 || video.videoHeight === 0) {
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          return;
        }
        const capturedPhoto = new File([blob], `capture-${Date.now()}.jpg`, { type: "image/jpeg" });
        void startGeneration(capturedPhoto);
      },
      "image/jpeg",
      0.95
    );
  }

  function startCountdown() {
    if (!canStartCapture) {
      return;
    }
    let value = 3;
    setCountdown(value);
    setGenerationError("");

    countdownTimerRef.current = window.setInterval(() => {
      value -= 1;
      if (value <= 0) {
        if (countdownTimerRef.current !== null) {
          window.clearInterval(countdownTimerRef.current);
          countdownTimerRef.current = null;
        }
        setCountdown(null);
        capturePhoto();
        return;
      }
      setCountdown(value);
    }, 1000);
  }

  const stylesMatchCurrentRoom = stylesRoomSlug === resolvedRoomSlug;
  const selectedStyle = stylesMatchCurrentRoom ? styles.find((item) => item.id === selectedId) ?? null : null;
  const canStartCapture = cameraReady && countdown === null && !isGenerating && !stylesLoading && selectedStyle !== null;
  const isReadyToCapture = canStartCapture;
  const captureStatusLabel = stylesLoading
    ? "Загружаем стили"
    : isGenerating
      ? "Генерируем кадр"
      : countdown !== null
        ? "Таймер съёмки"
        : selectedStyle
          ? isReadyToCapture
            ? "Готово к съемке"
            : "Подготовка к съемке"
          : "Выберите стиль";
  const captureStatusDescription = stylesLoading
    ? "Подбираем стили для этой комнаты."
    : isGenerating
      ? "Отправляем фото в генерацию. Не закрывайте экран."
      : countdown !== null
        ? `Снимок будет сделан через ${countdown}.`
        : selectedStyle
          ? selectedStyle.description
          : stylesError || "Выберите визуальный стиль, чтобы активировать съёмку.";
  const stylesEmptyMessage =
    !stylesLoading && !stylesError && styles.length === 0
      ? "Для этой комнаты пока нет стилей. Добавьте их в админке."
      : null;
  const screenReaderStatusMessage = [
    captureStatusLabel,
    selectedStyle ? `${selectedStyle.name}. ${captureStatusDescription}` : captureStatusDescription,
    cameraError,
    stylesError,
    stylesEmptyMessage,
    generationError
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <main className="capture-screen" aria-label="camera preview">
      <section className="capture-screen__stage">
        <section className="capture-screen__preview" data-testid="camera-preview">
          <video ref={videoRef} className="capture-screen__video" autoPlay playsInline muted />
          {countdown !== null ? (
            <div className="camera-overlay" aria-live="assertive">
              <span className="camera-countdown">{countdown}</span>
            </div>
          ) : null}
        </section>

        <aside className="capture-screen__action-rail" aria-label="capture controls">
          <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
            {screenReaderStatusMessage}
          </div>
          <div className="capture-screen__room-menu-slot">
            <PublicRoomMenu currentRoomSlug={resolvedRoomSlug} variant="embedded" />
          </div>
          <p className="capture-screen__eyebrow">{captureStatusLabel}</p>
          <h2 className="capture-screen__selection-name">{selectedStyle?.name || "Стиль не выбран"}</h2>
          <p className="capture-screen__selection-description">{captureStatusDescription}</p>

          {cameraError ? <p className="capture-screen__state capture-screen__state--warning">{cameraError}</p> : null}
          {stylesEmptyMessage ? <p className="capture-screen__state">{stylesEmptyMessage}</p> : null}
          {generationError ? <p role="alert" className="capture-screen__state capture-screen__state--error">{generationError}</p> : null}

          <div className="capture-screen__controls">
            <div className="capture-screen__cta-meta">
              <span>{selectedStyle ? "Стиль выбран" : "Стиль не выбран"}</span>
            </div>
            <button
              type="button"
              className="capture-screen__button"
              onClick={startCountdown}
              disabled={!canStartCapture}
            >
              {isGenerating ? "Генерация..." : "Сделать фото"}
            </button>
          </div>
        </aside>
      </section>

      <section className="capture-screen__styles-zone">
        <aside className="capture-screen__styles-panel" aria-label="style selection">
          <div className="capture-screen__styles-header">
            <p className="capture-screen__styles-title">Стили</p>
            <p className="capture-screen__styles-subtitle">Выберите стиль перед съёмкой.</p>
          </div>
          {stylesLoading ? <p className="capture-screen__styles-empty">Загружаем стили</p> : null}
          {stylesError ? <p className="capture-screen__styles-empty">{stylesError}</p> : null}
          {stylesEmptyMessage ? <p className="capture-screen__styles-empty">{stylesEmptyMessage}</p> : null}
          <div className="capture-screen__styles-list">
            {styles.map((style) => (
              <button
                key={style.id}
                type="button"
                className={`capture-style-item${style.id === selectedId ? " is-selected" : ""}`}
                onClick={() => onStyleSelect(style.id)}
                aria-pressed={style.id === selectedId}
                disabled={isGenerating}
              >
                <img
                  src={style.preview_image_url}
                  alt={`${style.name} preview`}
                  width={92}
                  height={62}
                  className="capture-style-item__preview"
                />
                <span className="capture-style-item__meta">
                  <span className="capture-style-item__name">{style.name}</span>
                  <span className="capture-style-item__description">{style.description}</span>
                </span>
              </button>
            ))}
          </div>
        </aside>
      </section>
      <canvas ref={canvasRef} hidden />
    </main>
  );
}
