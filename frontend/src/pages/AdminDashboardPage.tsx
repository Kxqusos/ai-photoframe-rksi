import React, { useEffect, useState } from "react";

import { AdminRoomForm } from "../components/AdminRoomForm";
import { createRoom, listRooms } from "../lib/api";
import { loadAdminToken } from "../lib/auth";
import { navigateTo } from "../lib/navigation";
import type { Room } from "../types";

export function AdminDashboardPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const next = await listRooms();
      setRooms(next);
      setError("");
    } catch {
      setError("Не удалось загрузить комнаты");
    }
  }

  useEffect(() => {
    if (!loadAdminToken()) {
      navigateTo("/admin/login");
      return;
    }
    void load();
  }, []);

  async function onCreate(payload: Omit<Room, "id">) {
    await createRoom(payload);
    await load();
  }

  return (
    <main className="page">
      <h1>Панель администратора</h1>
      {error ? <p role="alert">{error}</p> : null}

      <AdminRoomForm onCreate={onCreate} />

      <section className="panel prompt-list" aria-label="список комнат">
        {rooms.map((room) => (
          <div key={room.id} className="prompt-item">
            <h3>{room.name}</h3>
            <p>{room.slug}</p>
            <a href={`/admin/rooms/${room.id}`}>Открыть</a>
          </div>
        ))}
      </section>
    </main>
  );
}
