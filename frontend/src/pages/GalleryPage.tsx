import React, { useEffect, useRef, useState } from "react";

import { listGalleryResults } from "../lib/api";
import type { GalleryImage } from "../types";

const POLL_INTERVAL_MS = 5000;
const AUTO_SCROLL_PIXELS_PER_SECOND = 24;

export function GalleryPage() {
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [error, setError] = useState<string>("");
  const scrollRef = useRef<HTMLElement | null>(null);
  const loopImages = images.length > 0 ? [...images, ...images] : images;

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const rows = await listGalleryResults();
        if (!active) {
          return;
        }
        setImages(rows);
        setError("");
      } catch (cause) {
        if (!active) {
          return;
        }
        setError(cause instanceof Error ? cause.message : "Failed to load gallery");
      }
    }

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, POLL_INTERVAL_MS);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) {
      return;
    }
    if (images.length === 0) {
      return;
    }

    let frameId = 0;
    let lastTick = 0;

    const step = (timestamp: number) => {
      if (lastTick === 0) {
        lastTick = timestamp;
      }

      const elapsed = timestamp - lastTick;
      lastTick = timestamp;

      const cycleHeight = container.scrollHeight / 2;
      if (cycleHeight > 0 && container.scrollHeight > container.clientHeight) {
        const next = container.scrollTop + (elapsed / 1000) * AUTO_SCROLL_PIXELS_PER_SECOND;
        container.scrollTop = next >= cycleHeight ? next - cycleHeight : next;
      }

      frameId = window.requestAnimationFrame(step);
    };

    frameId = window.requestAnimationFrame(step);

    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [images.length]);

  return (
    <main className="page gallery-page">
      <header className="gallery-header panel">
        <p className="gallery-header__eyebrow">ИИ Фоторамка</p>
        <h1>Галерея</h1>
      </header>

      <section className="gallery-scroll" ref={scrollRef} aria-label="gallery auto scroll">
        {error ? <p role="alert">{error}</p> : null}
        {images.length === 0 && !error ? <p className="gallery-empty">Пока нет изображений.</p> : null}
        <div className="gallery-masonry">
          {loopImages.map((image, index) => (
            <figure key={`${image.url}-${index}`} className="gallery-card">
              <img src={image.url} alt={image.name} loading="lazy" />
            </figure>
          ))}
        </div>
      </section>
    </main>
  );
}
