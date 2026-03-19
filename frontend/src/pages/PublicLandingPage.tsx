import { useEffect, useMemo, useState } from "react";

import { accessRoom, listPublicRooms } from "../lib/api";
import { navigateTo } from "../lib/navigation";
import { saveRoomAccessToken } from "../lib/roomAccess";
import { buildPublicRoomPath, DEFAULT_ROOM_SLUG, normalizeRoomSlug } from "../lib/roomRouting";
import type { PublicRoom } from "../types";

type Props = {
  initialRoomSlug?: string | null;
  redirectPath?: string;
};

function toDisplayRoomName(room: PublicRoom): string {
  if (room.slug === DEFAULT_ROOM_SLUG && room.name.trim().toLowerCase() === "main") {
    return "Главная";
  }
  return room.name;
}

export function PublicLandingPage({ initialRoomSlug = null, redirectPath }: Props) {
  const normalizedInitial = normalizeRoomSlug(initialRoomSlug || DEFAULT_ROOM_SLUG);
  const [selectedDestination, setSelectedDestination] = useState<"capture" | "gallery">(() =>
    redirectPath && /\/gallery\/?$/i.test(redirectPath) ? "gallery" : "capture"
  );
  const [rooms, setRooms] = useState<PublicRoom[]>([]);
  const [selectedRoomSlug, setSelectedRoomSlug] = useState(normalizedInitial);
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const roomList = await listPublicRooms();
        if (!active) {
          return;
        }
        setRooms(roomList);
        if (roomList.length > 0 && !roomList.some((room) => room.slug === normalizedInitial)) {
          setSelectedRoomSlug(roomList[0].slug);
        }
      } catch (cause) {
        if (!active) {
          return;
        }
        setError(cause instanceof Error ? cause.message : "Не удалось загрузить комнаты");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [normalizedInitial]);

  const selectedRoomName = useMemo(() => {
    const selected = rooms.find((room) => room.slug === selectedRoomSlug);
    return selected ? toDisplayRoomName(selected) : "Комната";
  }, [rooms, selectedRoomSlug]);

  async function onSubmit() {
    if (!selectedRoomSlug || !password.trim()) {
      setError("Введите пароль комнаты");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const token = await accessRoom(selectedRoomSlug, password.trim());
      saveRoomAccessToken(selectedRoomSlug, token.access_token);
      const targetPath =
        redirectPath ||
        (selectedDestination === "gallery"
          ? buildPublicRoomPath(selectedRoomSlug, "/gallery")
          : buildPublicRoomPath(selectedRoomSlug));
      navigateTo(targetPath);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось открыть комнату");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page public-landing-page">
      <section className="public-landing-page__panel">
        <div className="public-landing-page__panel-head">
          <div className="public-landing-page__intro">
            <p className="public-landing-page__eyebrow">Выбор комнаты</p>
            <h1>{selectedRoomName}</h1>
            <p>Выберите комнату и введите пароль, чтобы открыть съемку, галерею и результаты.</p>
          </div>
          <a className="public-landing-page__admin-link" href="/admin/login">
            Вход
          </a>
        </div>

        {loading ? <p className="public-landing-page__status">Загружаем комнаты...</p> : null}
        {error ? <p className="public-landing-page__status public-landing-page__status--error">{error}</p> : null}

        <div className="public-landing-page__content">
          <section className="public-landing-page__rooms-panel">
            <div className="public-landing-page__rooms-header">
              <p className="public-landing-page__rooms-label">Комнаты</p>
              <p className="public-landing-page__rooms-support">Выберите нужную сцену перед входом.</p>
            </div>

            <div className="public-landing-page__rooms" aria-label="список комнат">
              {rooms.map((room) => (
                <button
                  key={room.slug}
                  type="button"
                  className={`public-landing-page__room${room.slug === selectedRoomSlug ? " is-selected" : ""}`}
                  onClick={() => {
                    setSelectedRoomSlug(room.slug);
                    setError("");
                  }}
                >
                  <span className="public-landing-page__room-name">{toDisplayRoomName(room)}</span>
                </button>
              ))}
            </div>
          </section>

          <section className="public-landing-page__form" aria-label="настройки входа">
            <div className="public-landing-page__form-header">
              <p className="public-landing-page__form-eyebrow">Вход в комнату</p>
              <p className="public-landing-page__form-room">Выбрано: {selectedRoomName}</p>
            </div>

            {redirectPath ? null : (
              <div className="public-landing-page__targets" aria-label="раздел комнаты">
                <button
                  type="button"
                  className={`public-landing-page__target${selectedDestination === "capture" ? " is-selected" : ""}`}
                  onClick={() => setSelectedDestination("capture")}
                >
                  Съемка
                </button>
                <button
                  type="button"
                  className={`public-landing-page__target${selectedDestination === "gallery" ? " is-selected" : ""}`}
                  onClick={() => setSelectedDestination("gallery")}
                >
                  Галерея
                </button>
              </div>
            )}
            <label htmlFor="public-room-password">Пароль комнаты</label>
            <input
              id="public-room-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void onSubmit();
                }
              }}
              placeholder="Введите пароль"
            />
            <button type="button" onClick={() => void onSubmit()} disabled={submitting || loading || rooms.length === 0}>
              {submitting ? "Проверяем..." : "Открыть комнату"}
            </button>
          </section>
        </div>
      </section>
    </main>
  );
}
