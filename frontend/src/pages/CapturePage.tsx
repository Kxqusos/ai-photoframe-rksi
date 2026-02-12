import React from "react";
import { useEffect, useRef, useState } from "react";

import { createJob, listPrompts } from "../lib/api";
import { readStoredStyleId, writeStoredStyleId } from "../lib/styleSelection";
import type { StylePrompt } from "../types";

export function CapturePage() {
  const [styles, setStyles] = useState<StylePrompt[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const countdownTimerRef = useRef<number | null>(null);

  useEffect(() => {
    let active = true;

    listPrompts().then((items) => {
      if (active) {
        setStyles(items);
        if (items.length > 0) {
          const stored = readStoredStyleId();
          const initial =
            (stored !== null && items.some((item) => item.id === stored) ? stored : null) ?? items[0].id;
          setSelectedId(initial);
        }
      }
    });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function setupCamera() {
      if (!navigator.mediaDevices?.getUserMedia) {
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
        setCameraReady(true);
      } catch {}
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
    try {
      const job = await createJob(capturedPhoto, selectedId);
      window.location.assign(`/result?jobId=${job.id}`);
    } catch {
      setIsGenerating(false);
    }
  }

  function onStyleSelect(styleId: number) {
    setSelectedId(styleId);
    writeStoredStyleId(styleId);
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
    if (!cameraReady || countdown !== null || isGenerating || selectedId === null) {
      return;
    }
    let value = 3;
    setCountdown(value);

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

  return (
    <main className="capture-screen" aria-label="camera preview">
      <section className="capture-screen__preview" data-testid="camera-preview">
        <video ref={videoRef} className="capture-screen__video" autoPlay playsInline muted />
        {countdown !== null ? (
          <div className="camera-overlay" aria-live="assertive">
            <span className="camera-countdown">{countdown}</span>
          </div>
        ) : null}
        <div className="capture-screen__controls">
          <button
            type="button"
            className="capture-screen__button"
            onClick={startCountdown}
            disabled={!cameraReady || countdown !== null || isGenerating || selectedId === null}
          >
            {isGenerating ? "Генерация..." : "Сделать фото"}
          </button>
        </div>
      </section>
      <section className="capture-screen__styles-zone">
        <aside className="capture-screen__styles-panel" aria-label="style selection">
          <p className="capture-screen__styles-title">Стили</p>
          {styles.length === 0 ? <p className="capture-screen__styles-empty">Стили загружаются...</p> : null}
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
