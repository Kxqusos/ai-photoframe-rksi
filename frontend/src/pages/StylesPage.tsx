import React, { useEffect, useMemo, useState } from "react";

import { StyleCard } from "../components/StyleCard";
import { listPrompts } from "../lib/api";
import { readStoredStyleId, readStyleIdFromQuery, writeStoredStyleId } from "../lib/styleSelection";
import type { StylePrompt } from "../types";

export function StylesPage() {
  const [styles, setStyles] = useState<StylePrompt[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    listPrompts()
      .then((items) => {
        if (!active) {
          return;
        }
        setStyles(items);
        if (items.length === 0) {
          setSelectedId(null);
          return;
        }

        const querySelected = readStyleIdFromQuery(window.location.search);
        const storedSelected = readStoredStyleId();
        const preferred =
          (querySelected !== null && items.some((item) => item.id === querySelected) ? querySelected : null) ??
          (storedSelected !== null && items.some((item) => item.id === storedSelected) ? storedSelected : null) ??
          items[0].id;
        setSelectedId(preferred);
      })
      .catch((cause) => {
        if (!active) {
          return;
        }
        setError(cause instanceof Error ? cause.message : "Не удалось загрузить стили");
      });

    return () => {
      active = false;
    };
  }, []);

  const selectedStyle = useMemo(
    () => styles.find((item) => item.id === selectedId) ?? null,
    [styles, selectedId]
  );

  function onBack() {
    window.location.assign("/");
  }

  function onApply() {
    if (selectedId === null) {
      return;
    }
    writeStoredStyleId(selectedId);
    window.location.assign("/");
  }

  return (
    <main className="page styles-page">
      <section className="styles-hero">
        <p className="styles-hero__eyebrow">ИИ Фоторамка</p>
        <h1>Выберите стиль</h1>
        <p className="styles-hero__description">
          Подберите визуальный стиль перед съёмкой: просмотр, сравнение и быстрый возврат на экран камеры.
        </p>
      </section>

      {error ? <p role="alert">{error}</p> : null}

      <section className="style-grid style-grid--catalog">
        {styles.map((item) => (
          <StyleCard key={item.id} style={item} selected={item.id === selectedId} onSelect={setSelectedId} />
        ))}
      </section>

      <section className="styles-footer panel">
        <p className="styles-footer__selected">
          {selectedStyle ? `Выбран стиль: ${selectedStyle.name}` : "Стиль пока не выбран"}
        </p>
        <div className="action-row">
          <button type="button" className="button-secondary" onClick={onBack}>
            Назад
          </button>
          <button type="button" onClick={onApply} disabled={selectedId === null}>
            Выбрать стиль и вернуться
          </button>
        </div>
      </section>
    </main>
  );
}
