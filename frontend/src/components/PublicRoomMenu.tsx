import React, { useEffect, useMemo, useState } from "react";

import { listPublicRooms } from "../lib/api";
import { navigateTo } from "../lib/navigation";
import { DEFAULT_ROOM_SLUG, normalizeRoomSlug } from "../lib/roomRouting";
import type { PublicRoom } from "../types";

type Props = {
  currentRoomSlug: string;
  variant?: "default" | "embedded";
  isLocked?: boolean;
};

function toDisplayRoomName(room: PublicRoom): string {
  if (room.slug === DEFAULT_ROOM_SLUG && room.name.trim().toLowerCase() === "main") {
    return "Главная";
  }
  return room.name;
}

function uniqueBySlug(items: PublicRoom[]): PublicRoom[] {
  const seen = new Set<string>();
  const result: PublicRoom[] = [];

  for (const item of items) {
    if (seen.has(item.slug)) {
      continue;
    }
    seen.add(item.slug);
    result.push(item);
  }
  return result;
}

export function PublicRoomMenu({ currentRoomSlug, variant = "default", isLocked = false }: Props) {
  const normalizedCurrent = normalizeRoomSlug(currentRoomSlug);
  const [rooms, setRooms] = useState<PublicRoom[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const rows = await listPublicRooms();
        if (!active) {
          return;
        }
        setRooms(rows);
      } catch {
        if (!active) {
          return;
        }
        setRooms([]);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (isLocked) {
      setIsOpen(false);
    }
  }, [isLocked]);

  const options = useMemo(() => {
    const fallback = {
      id: 0,
      slug: normalizedCurrent,
      name: normalizedCurrent === DEFAULT_ROOM_SLUG ? "Главная" : normalizedCurrent
    };
    return uniqueBySlug([...rooms, fallback]);
  }, [normalizedCurrent, rooms]);

  const currentRoomName = useMemo(() => {
    const current = options.find((room) => room.slug === normalizedCurrent);
    return toDisplayRoomName(current ?? options[0]);
  }, [normalizedCurrent, options]);

  const currentSection = (() => {
    if (typeof window === "undefined") {
      return "capture";
    }

    const pathname = window.location.pathname;
    if (/\/gallery\/?$/i.test(pathname)) {
      return "gallery";
    }
    if (/\/result\/[^/]+\/?$/i.test(pathname)) {
      return null;
    }
    return "capture";
  })();

  return (
    <header
      className={`public-room-menu${variant === "embedded" ? " public-room-menu--embedded" : ""}`}
      aria-label="навигация по комнатам"
    >
      <button
        type="button"
        className="public-room-menu__toggle"
        aria-label="Меню"
        aria-expanded={isOpen}
        disabled={isLocked}
        onClick={() => setIsOpen((value) => !value)}
      >
        <span className="public-room-menu__toggle-icon" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span className="public-room-menu__toggle-copy">
          <span className="public-room-menu__toggle-label">Комната</span>
          <span className="public-room-menu__toggle-room">{currentRoomName}</span>
        </span>
      </button>

      {isOpen ? (
        <div className="public-room-menu__dropdown" role="menu">
          <div className="public-room-menu__room-panel">
            <div className="public-room-menu__current">
              <p className="public-room-menu__eyebrow">Текущая комната</p>
              <p className="public-room-menu__room-name">{currentRoomName}</p>
            </div>

            <div className="public-room-menu__field">
              <label htmlFor="public-room-select">Комната</label>
              <select
                id="public-room-select"
                value={normalizedCurrent}
                disabled={isLocked}
                onChange={(event) => {
                  setIsOpen(false);
                  navigateTo(`/${normalizeRoomSlug(event.target.value)}`);
                }}
              >
                {options.map((room) => (
                  <option key={room.slug} value={room.slug}>
                    {toDisplayRoomName(room)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <nav className="public-room-menu__links" aria-label="разделы комнаты">
            <a
              href={`/${normalizedCurrent}`}
              className={`public-room-menu__link${currentSection === "capture" ? " is-active" : ""}`}
              aria-current={currentSection === "capture" ? "page" : undefined}
              aria-disabled={isLocked ? "true" : undefined}
              onClick={(event) => {
                if (isLocked) {
                  event.preventDefault();
                  return;
                }
                setIsOpen(false);
              }}
            >
              Съемка
            </a>
            <a
              href={`/${normalizedCurrent}/gallery`}
              className={`public-room-menu__link${currentSection === "gallery" ? " is-active" : ""}`}
              aria-current={currentSection === "gallery" ? "page" : undefined}
              aria-disabled={isLocked ? "true" : undefined}
              onClick={(event) => {
                if (isLocked) {
                  event.preventDefault();
                  return;
                }
                setIsOpen(false);
              }}
            >
              Галерея
            </a>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
