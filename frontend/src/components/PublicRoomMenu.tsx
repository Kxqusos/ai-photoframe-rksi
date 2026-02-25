import React, { useEffect, useMemo, useState } from "react";

import { listPublicRooms } from "../lib/api";
import { navigateTo } from "../lib/navigation";
import { normalizeRoomSlug } from "../lib/roomRouting";
import type { PublicRoom } from "../types";

type Props = {
  currentRoomSlug: string;
};

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
    const fallback = { id: 0, slug: normalizedCurrent, name: normalizedCurrent };
    return uniqueBySlug([fallback, ...rooms]);
  }, [normalizedCurrent, rooms]);

  return (
    <header className="public-room-menu" aria-label="room navigation">
      <div className="public-room-menu__inner">
        <label htmlFor="public-room-select">Комната</label>
        <select
          id="public-room-select"
          value={normalizedCurrent}
          onChange={(event) => navigateTo(`/${normalizeRoomSlug(event.target.value)}`)}
        >
          {options.map((room) => (
            <option key={room.slug} value={room.slug}>
              {room.name}
            </option>
          ))}
        </select>

        <nav className="public-room-menu__links" aria-label="room links">
          <a href={`/${normalizedCurrent}`}>Съемка</a>
          <a href={`/${normalizedCurrent}/gallery`}>Галерея</a>
        </nav>
      </div>
    </header>
  );
}
