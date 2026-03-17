import React, { useEffect, useState } from "react";

import { AdminRoomForm } from "../components/AdminRoomForm";
import { createRoom, deleteRoom, getLlmRouting, listRooms, patchRoom, testLlmRouting, toggleLlmRouting, updateLlmRoutingConfig } from "../lib/api";
import { loadAdminToken } from "../lib/auth";
import { navigateTo } from "../lib/navigation";
import type { LlmRoutingSettings, Room, RoomCreatePayload, RoomPatchPayload } from "../types";

export function AdminDashboardPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [routing, setRouting] = useState<LlmRoutingSettings | null>(null);
  const [routingDraft, setRoutingDraft] = useState("");
  const [editingRoom, setEditingRoom] = useState<Room | null>(null);
  const [deletingRoomId, setDeletingRoomId] = useState<number | null>(null);
  const [routingPending, setRoutingPending] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    try {
      const [nextRooms, nextRouting] = await Promise.all([listRooms(), getLlmRouting()]);
      setRooms(nextRooms);
      setRouting(nextRouting);
      setRoutingDraft(nextRouting.vless_uri);
      setError("");
    } catch {
      setError("Не удалось загрузить данные админки");
    }
  }

  useEffect(() => {
    if (!loadAdminToken()) {
      navigateTo("/admin/login");
      return;
    }
    void load();
  }, []);

  async function onCreate(payload: RoomCreatePayload): Promise<boolean> {
    setError("");
    try {
      await createRoom(payload);
      await load();
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось создать комнату");
      return false;
    }
  }

  async function onUpdate(roomId: number, payload: RoomPatchPayload): Promise<boolean> {
    setError("");
    try {
      await patchRoom(roomId, payload);
      await load();
      setEditingRoom(null);
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось обновить комнату");
      return false;
    }
  }

  async function onDelete(roomId: number): Promise<void> {
    setDeletingRoomId(roomId);
    setError("");
    try {
      await deleteRoom(roomId);
      await load();
      if (editingRoom?.id === roomId) {
        setEditingRoom(null);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось удалить комнату");
    } finally {
      setDeletingRoomId(null);
    }
  }

  function onCancelEdit() {
    setEditingRoom(null);
    setError("");
  }

  async function onSaveRouting(): Promise<void> {
    setRoutingPending(true);
    setError("");
    try {
      const next = await updateLlmRoutingConfig(routingDraft);
      setRouting(next);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось сохранить llm routing");
    } finally {
      setRoutingPending(false);
    }
  }

  async function onTestRouting(): Promise<void> {
    setRoutingPending(true);
    setError("");
    try {
      const next = await testLlmRouting();
      setRouting(next);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось проверить llm routing");
    } finally {
      setRoutingPending(false);
    }
  }

  async function onToggleRouting(enabled: boolean): Promise<void> {
    setRoutingPending(true);
    setError("");
    try {
      const next = await toggleLlmRouting(enabled);
      setRouting(next);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось переключить llm routing");
    } finally {
      setRoutingPending(false);
    }
  }

  return (
    <main className="page">
      <h1>Панель администратора</h1>
      {error ? <p role="alert">{error}</p> : null}

      <AdminRoomForm editingRoom={editingRoom} onCreate={onCreate} onUpdate={onUpdate} onCancelEdit={onCancelEdit} />

      <section className="page-section panel" aria-label="llm routing">
        <div className="section-header">
          <div>
            <h2>LLM Routing</h2>
            <p className="section-support">Глобальная маршрутизация LLM-запросов через VLESS+Reality для всех комнат.</p>
          </div>
        </div>

        <label htmlFor="admin-llm-routing-vless">VLESS URI</label>
        <textarea
          id="admin-llm-routing-vless"
          value={routingDraft}
          onChange={(event) => setRoutingDraft(event.target.value)}
          rows={4}
          placeholder="vless://..."
        />
        <div className="detail-pills">
          <span className="detail-pill">Статус: {routing?.status || "disabled"}</span>
          <span className="detail-pill">Маршрутизация: {routing?.enabled ? "Включена" : "Выключена"}</span>
        </div>
        {routing?.last_error ? <p role="status">{routing.last_error}</p> : null}
        <div className="action-row">
          <button type="button" onClick={() => void onSaveRouting()} disabled={routingPending}>
            Сохранить и применить
          </button>
          <button type="button" className="button-secondary" onClick={() => void onTestRouting()} disabled={routingPending}>
            Проверить подключение
          </button>
          <button
            type="button"
            className="button-secondary"
            onClick={() => void onToggleRouting(!(routing?.enabled ?? false))}
            disabled={routingPending}
          >
            {routing?.enabled ? "Отключить маршрутизацию" : "Включить маршрутизацию"}
          </button>
        </div>
      </section>

      <section className="page-section panel" aria-label="список комнат">
        <div className="section-header">
          <div>
            <h2>Комнаты</h2>
            <p className="section-support">Здесь собраны все комнаты с краткой сводкой и быстрым переходом в редактор.</p>
          </div>
        </div>

        <div className="prompt-list">
          {rooms.length === 0 ? (
            <div className="empty-state">
              <p>Сначала создайте первую комнату.</p>
              <p>После создания здесь появятся карточки с быстрыми действиями.</p>
            </div>
          ) : null}
          {rooms.map((room) => (
            <article key={room.id} className="prompt-item room-card">
              <div className="prompt-card__content">
                <h3>{room.name}</h3>
                <p>{room.slug}</p>
                <div className="detail-pills">
                  <span className="detail-pill">{room.is_active ? "Активна" : "Выключена"}</span>
                  <span className="detail-pill">{room.model_name}</span>
                </div>
              </div>
              <div className="prompt-item__actions">
                <button type="button" className="button-secondary" onClick={() => setEditingRoom(room)}>
                  Редактировать {room.name}
                </button>
                <button
                  type="button"
                  className="button-danger"
                  aria-label={`Удалить ${room.name}`}
                  onClick={() => void onDelete(room.id)}
                  disabled={deletingRoomId === room.id}
                >
                  {deletingRoomId === room.id ? "Удаляем..." : "Удалить"}
                </button>
                <a
                  href={`/admin/rooms/${room.slug}`}
                  aria-label={`Открыть ${room.name}`}
                  className="button-secondary room-card__link"
                >
                  Открыть
                </a>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
