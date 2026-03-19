import { useEffect, useRef, useState } from "react";

import { listRoomGalleryResults } from "../lib/api";
import { normalizeRoomSlug } from "../lib/roomRouting";
import type { GalleryImage } from "../types";

const POLL_INTERVAL_MS = 5000;
const AUTO_SCROLL_PIXELS_PER_SECOND = 24;
const AUTO_SCROLL_RESUME_DELAY_MS = 3000;
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
  const pendingProgrammaticScrollEventsRef = useRef(0);
  const resumeAutoScrollAtRef = useRef(0);

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
    let lastTick: number | null = null;
    let virtualScrollTop = container.scrollTop;

    const step = (timestamp: number) => {
      if (lastTick === null) {
        lastTick = timestamp;
        frameId = window.requestAnimationFrame(step);
        return;
      }

      const elapsed = timestamp - lastTick;
      lastTick = timestamp;

      if (Date.now() < resumeAutoScrollAtRef.current) {
        frameId = window.requestAnimationFrame(step);
        return;
      }

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
        if (virtualScrollTop !== container.scrollTop) {
          pendingProgrammaticScrollEventsRef.current += 1;
          container.scrollTop = virtualScrollTop;
        }
      }

      frameId = window.requestAnimationFrame(step);
    };

    frameId = window.requestAnimationFrame(step);

    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [displayImages.length]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) {
      return;
    }

    const pauseAutoScroll = () => {
      resumeAutoScrollAtRef.current = Date.now() + AUTO_SCROLL_RESUME_DELAY_MS;
    };

    const handleScroll = () => {
      if (pendingProgrammaticScrollEventsRef.current > 0) {
        pendingProgrammaticScrollEventsRef.current -= 1;
        return;
      }
      pauseAutoScroll();
    };

    container.addEventListener("wheel", pauseAutoScroll, { passive: true });
    container.addEventListener("touchstart", pauseAutoScroll, { passive: true });
    container.addEventListener("pointerdown", pauseAutoScroll, { passive: true });
    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      container.removeEventListener("wheel", pauseAutoScroll);
      container.removeEventListener("touchstart", pauseAutoScroll);
      container.removeEventListener("pointerdown", pauseAutoScroll);
      container.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <main className="page gallery-page">
      <header className="panel gallery-header">
        <p className="gallery-eyebrow">Подборка комнаты</p>
        <h1>Лента лучших кадров</h1>
      </header>

      <section className="gallery-scroll">
        <div className="gallery-scroll__viewport" ref={scrollRef} aria-label="gallery auto scroll">
          {error ? (
            <div className="gallery-state gallery-state--error">
              <h2>Не удалось обновить подборку</h2>
              <p role="alert">{error}</p>
              <p>Попробуйте открыть галерею чуть позже. Как только сервис вернется, новые кадры снова появятся автоматически.</p>
            </div>
          ) : null}
          {images.length === 0 && !error ? (
            <div className="gallery-state gallery-empty">
              <h2>Пока в подборке нет готовых кадров</h2>
              <p>Первые фотографии появятся здесь автоматически, как только кто-то завершит съемку.</p>
            </div>
          ) : null}
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
        </div>
      </section>
    </main>
  );
}
