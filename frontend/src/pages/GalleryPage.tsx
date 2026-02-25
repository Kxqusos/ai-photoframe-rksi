import React, { useEffect, useRef, useState } from "react";

import { listRoomGalleryResults } from "../lib/api";
import { normalizeRoomSlug } from "../lib/roomRouting";
import type { GalleryImage } from "../types";

const POLL_INTERVAL_MS = 5000;
const AUTO_SCROLL_PIXELS_PER_SECOND = 24;
const CARD_SIZE_VARIANTS = ["square", "portrait", "landscape", "tall", "wide"] as const;

function getCardSizeVariant(index: number): (typeof CARD_SIZE_VARIANTS)[number] {
  return CARD_SIZE_VARIANTS[index % CARD_SIZE_VARIANTS.length];
}

function getImageKey(image: GalleryImage): string {
  return image.url;
}

function hasSameImageSet(current: GalleryImage[], incoming: GalleryImage[]): boolean {
  if (current.length !== incoming.length) {
    return false;
  }

  const counts = new Map<string, number>();
  for (const image of current) {
    const key = getImageKey(image);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  for (const image of incoming) {
    const key = getImageKey(image);
    const count = counts.get(key);
    if (!count) {
      return false;
    }
    if (count === 1) {
      counts.delete(key);
    } else {
      counts.set(key, count - 1);
    }
  }

  return counts.size === 0;
}

function shuffleImages(images: GalleryImage[]): GalleryImage[] {
  if (images.length < 2) {
    return images;
  }

  const next = [...images];
  for (let index = next.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [next[index], next[swapIndex]] = [next[swapIndex], next[index]];
  }

  const sameOrder = next.every((image, index) => getImageKey(image) === getImageKey(images[index]));
  if (sameOrder) {
    const [first] = next;
    next.splice(0, 1);
    next.push(first);
  }

  return next;
}

function syncDisplayImages(current: GalleryImage[], incoming: GalleryImage[]): GalleryImage[] {
  if (!hasSameImageSet(current, incoming)) {
    return incoming;
  }
  return current;
}

type Props = {
  roomSlug: string;
};

export function GalleryPage({ roomSlug }: Props) {
  const resolvedRoomSlug = normalizeRoomSlug(roomSlug);
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [displayImages, setDisplayImages] = useState<GalleryImage[]>([]);
  const [error, setError] = useState<string>("");
  const scrollRef = useRef<HTMLElement | null>(null);
  const trackRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const rows = await listRoomGalleryResults(resolvedRoomSlug);
        if (!active) {
          return;
        }
        setImages(rows);
        setDisplayImages((current) => syncDisplayImages(current, rows));
        setError("");
      } catch (cause) {
        if (!active) {
          return;
        }
        setError(cause instanceof Error ? cause.message : "Не удалось загрузить галерею");
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
  }, [resolvedRoomSlug]);

  useEffect(() => {
    const container = scrollRef.current;
    const track = trackRef.current;
    if (!container) {
      return;
    }
    if (!track) {
      return;
    }
    if (displayImages.length === 0) {
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

      const maxScrollTop = track.scrollHeight - container.clientHeight;
      if (maxScrollTop > 0) {
        const next = virtualScrollTop + (elapsed / 1000) * AUTO_SCROLL_PIXELS_PER_SECOND;
        if (next >= maxScrollTop) {
          virtualScrollTop = 0;
          if (displayImages.length > 1) {
            setDisplayImages((current) => shuffleImages(current));
          }
        } else {
          virtualScrollTop = next;
        }
        container.scrollTop = virtualScrollTop;
      }

      frameId = window.requestAnimationFrame(step);
    };

    frameId = window.requestAnimationFrame(step);

    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [displayImages.length]);

  return (
    <main className="page gallery-page">
      <section className="gallery-scroll" ref={scrollRef} aria-label="gallery auto scroll">
        {error ? <p role="alert">{error}</p> : null}
        {images.length === 0 && !error ? <p className="gallery-empty">Пока нет изображений.</p> : null}
        {displayImages.length > 0 ? (
          <div className="gallery-track" ref={trackRef}>
            <div className="gallery-masonry" data-testid="gallery-masonry-group">
              {displayImages.map((image, index) => {
                return (
                  <figure
                    key={`${image.url}-${index}`}
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
