import { useEffect, useState } from "react";

import { AdminRoomForm } from "../components/AdminRoomForm";
import { createRoom, deleteRoom, getLlmRouting, listRooms, patchRoom, testLlmRouting, toggleLlmRouting, updateLlmRoutingConfig } from "../lib/api";
import { loadAdminToken } from "../lib/auth";
import { navigateTo } from "../lib/navigation";
import type { LlmRoutingSettings, Room, RoomCreatePayload, RoomPatchPayload } from "../types";

function hasSuccessfulRoutingCheck(routing: LlmRoutingSettings | null): boolean {
  return Boolean(routing?.last_checked_at && !routing?.last_error);
}

export function AdminDashboardPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [routing, setRouting] = useState<LlmRoutingSettings | null>(null);
  const [routingDraft, setRoutingDraft] = useState("");
  const [editingRoom, setEditingRoom] = useState<Room | null>(null);
  const [roomPendingDelete, setRoomPendingDelete] = useState<Room | null>(null);
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

  async function confirmDeleteRoom(): Promise<void> {
    if (!roomPendingDelete) {
      return;
    }

    const roomId = roomPendingDelete.id;
    await onDelete(roomId);
    setRoomPendingDelete(null);
  }

  async function persistRoutingDraftIfNeeded(): Promise<LlmRoutingSettings | null> {
    const draft = routingDraft.trim();
    const current = routing?.vless_uri.trim() || "";
    if (!draft || draft === current) {
      return null;
    }

    const next = await updateLlmRoutingConfig(draft);
    setRouting(next);
    setRoutingDraft(next.vless_uri);
    return next;
  }

  async function onTestRouting(): Promise<void> {
    setRoutingPending(true);
    setError("");
    try {
      await persistRoutingDraftIfNeeded();
      const next = await testLlmRouting();
      setRouting(next);
      setRoutingDraft(next.vless_uri);
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
      await persistRoutingDraftIfNeeded();
      const next = await toggleLlmRouting(enabled);
      setRouting(next);
      setRoutingDraft(next.vless_uri);
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
          </div>
        </div>

        <div className="routing-stack">
          <label htmlFor="admin-llm-routing-vless">VLESS URL</label>
          <textarea
            id="admin-llm-routing-vless"
            value={routingDraft}
            onChange={(event) => setRoutingDraft(event.target.value)}
            rows={4}
            placeholder="vless://..."
          />
          <div className="detail-pills">
            <span className={`routing-status-chip${routing?.enabled ? " routing-status-chip--enabled" : " routing-status-chip--disabled"}`}>
              <span className="routing-status-chip__dot" aria-hidden="true" />
              <span className="routing-status-chip__label">Маршрутизация</span>
              <span className="routing-status-chip__value">{routing?.enabled ? "Включена" : "Выключена"}</span>
            </span>
          </div>
          {hasSuccessfulRoutingCheck(routing) ? (
            <p role="status" aria-label="Подключение успешно проверено" className="routing-feedback routing-feedback--success">
              <span className="routing-feedback__body">
                <strong className="routing-feedback__title">Ключ VLESS проверен</strong>
              </span>
            </p>
          ) : null}
          {routing?.last_error ? (
            <p role="status" className="routing-feedback routing-feedback--error">
              <span className="routing-feedback__body">
                <strong className="routing-feedback__title">Ошибка проверки</strong>
                <span className="routing-feedback__message">Последняя ошибка: {routing.last_error}</span>
              </span>
            </p>
          ) : null}
          <div className="action-row">
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
        </div>
      </section>

      <section className="page-section panel" aria-label="список комнат">
        <div className="section-header">
          <div>
            <h2>Комнаты</h2>
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
                <div className="detail-pills">
                  <span className="detail-pill">{room.is_active ? "Активна" : "Выключена"}</span>
                  <span className="detail-pill">{room.model_name}</span>
                </div>
              </div>
              <div className="prompt-item__actions">
                <button type="button" className="button-secondary" onClick={() => setEditingRoom(room)}>
                  Редактировать
                </button>
                <button
                  type="button"
                  className="button-danger"
                  aria-label="Удалить"
                  onClick={() => setRoomPendingDelete(room)}
                  disabled={deletingRoomId === room.id}
                >
                  {deletingRoomId === room.id ? "Удаляем..." : "Удалить"}
                </button>
                <a href={`/admin/rooms/${room.slug}`} aria-label="Открыть" className="button-secondary room-card__link">
                  Открыть
                </a>
              </div>
            </article>
          ))}
        </div>
      </section>

      {roomPendingDelete ? (
        <div className="modal-backdrop">
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="confirm-room-delete-title">
            <p className="modal-eyebrow">Подтверждение</p>
            <h2 id="confirm-room-delete-title" className="modal-title">
              Подтвердить удаление комнаты
            </h2>
            <p className="modal-text">
              Комната <strong>{roomPendingDelete.name}</strong> будет удалена вместе со связанными данными.
            </p>
            <div className="modal-actions">
              <button type="button" className="button-secondary" onClick={() => setRoomPendingDelete(null)} disabled={deletingRoomId !== null}>
                Отменить
              </button>
              <button type="button" className="button-danger" onClick={() => void confirmDeleteRoom()} disabled={deletingRoomId !== null}>
                {deletingRoomId === roomPendingDelete.id ? "Удаляем..." : "Удалить комнату"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
