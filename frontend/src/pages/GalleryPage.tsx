import React, { useEffect, useRef, useState } from "react";

import { listGalleryResults } from "../lib/api";
import type { GalleryImage } from "../types";

const POLL_INTERVAL_MS = 5000;
const AUTO_SCROLL_PIXELS_PER_SECOND = 24;
const CARD_SIZE_VARIANTS = ["square", "portrait", "landscape", "tall", "wide"] as const;

function getCardSizeVariant(index: number): (typeof CARD_SIZE_VARIANTS)[number] {
  return CARD_SIZE_VARIANTS[index % CARD_SIZE_VARIANTS.length];
}

function buildLoopImages(images: GalleryImage[]): GalleryImage[] {
  if (images.length === 0) {
    return images;
  }

  if (images.length === 1) {
    return [...images, ...images];
  }

  if (images.length === 2) {
    return [...images, ...images];
  }

  const offset = 1;
  const shifted = images.map((_, index) => images[(index + offset) % images.length]);
  return [...images, ...shifted];
}

export function GalleryPage() {
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [error, setError] = useState<string>("");
  const scrollRef = useRef<HTMLElement | null>(null);
  const trackRef = useRef<HTMLDivElement | null>(null);
  const loopImages = buildLoopImages(images);

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
    const track = trackRef.current;
    if (!container) {
      return;
    }
    if (!track) {
      return;
    }
    if (images.length === 0) {
      return;
    }

    let frameId = 0;
    let lastTick = 0;
    let virtualScrollTop = container.scrollTop;

    const step = (timestamp: number) => {
      if (lastTick === 0) {
        lastTick = timestamp;
      }

      const elapsed = timestamp - lastTick;
      lastTick = timestamp;

      const cycleHeight = track.scrollHeight / 2;
      if (cycleHeight > 0 && track.scrollHeight > container.clientHeight) {
        const next = virtualScrollTop + (elapsed / 1000) * AUTO_SCROLL_PIXELS_PER_SECOND;
        virtualScrollTop = next >= cycleHeight ? next - cycleHeight : next;
        container.scrollTop = virtualScrollTop;
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
      <section className="gallery-scroll" ref={scrollRef} aria-label="gallery auto scroll">
        {error ? <p role="alert">{error}</p> : null}
        {images.length === 0 && !error ? <p className="gallery-empty">Пока нет изображений.</p> : null}
        {images.length > 0 ? (
          <div className="gallery-track" ref={trackRef}>
            <div className="gallery-masonry" data-testid="gallery-masonry-group">
              {loopImages.map((image, index) => {
                return (
                  <figure
                    key={`loop-${image.url}-${index}`}
                    className={`gallery-card gallery-card--${getCardSizeVariant(index)}`}
                  >
                    <img src={image.url} alt={image.name} loading="lazy" />
                  </figure>
                );
              })}
            </div>
          </div>
        ) : null}
      </section>
    </main>
  );
}
