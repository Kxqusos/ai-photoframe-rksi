import React, { useEffect, useMemo, useState } from "react";

import { listPublicRooms } from "../lib/api";
import { navigateTo } from "../lib/navigation";
import { normalizeRoomSlug } from "../lib/roomRouting";
import type { PublicRoom } from "../types";

type Props = {
  currentRoomSlug: string;
};

function toDisplayRoomName(room: PublicRoom): string {
  if (room.slug === "main" && room.name.trim().toLowerCase() === "main") {
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

export function PublicRoomMenu({ currentRoomSlug }: Props) {
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

  const options = useMemo(() => {
    const fallback = { id: 0, slug: normalizedCurrent, name: normalizedCurrent === "main" ? "Главная" : normalizedCurrent };
    return uniqueBySlug([fallback, ...rooms]);
  }, [normalizedCurrent, rooms]);

  return (
    <header className="public-room-menu" aria-label="навигация по комнатам">
      <button
        type="button"
        className="public-room-menu__toggle"
        aria-label="Меню"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((value) => !value)}
      >
        <span />
        <span />
        <span />
      </button>

      {isOpen ? (
        <div className="public-room-menu__dropdown" role="menu">
          <label htmlFor="public-room-select">Комната</label>
          <select
            id="public-room-select"
            value={normalizedCurrent}
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

          <nav className="public-room-menu__links" aria-label="разделы комнаты">
            <a href={`/${normalizedCurrent}`} onClick={() => setIsOpen(false)}>
              Съемка
            </a>
            <a href={`/${normalizedCurrent}/gallery`} onClick={() => setIsOpen(false)}>
              Галерея
            </a>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
