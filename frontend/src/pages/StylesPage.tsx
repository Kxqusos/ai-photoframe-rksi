import React, { useEffect, useMemo, useState } from "react";

import { StyleCard } from "../components/StyleCard";
import { listPrompts } from "../lib/api";
import { readStoredStyleId, readStyleIdFromQuery, writeStoredStyleId } from "../lib/styleSelection";
import type { StylePrompt } from "../types";

export function StylesPage() {
  const [styles, setStyles] = useState<StylePrompt[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

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
          setIsLoading(false);
          return;
        }

        const querySelected = readStyleIdFromQuery(window.location.search);
        const storedSelected = readStoredStyleId();
        const preferred =
          (querySelected !== null && items.some((item) => item.id === querySelected) ? querySelected : null) ??
          (storedSelected !== null && items.some((item) => item.id === storedSelected) ? storedSelected : null) ??
          items[0].id;
        setSelectedId(preferred);
        setIsLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setError("Не удалось загрузить стили");
        setIsLoading(false);
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

      {isLoading ? <section className="status-inline">Загружаем стили</section> : null}

      {!isLoading && styles.length === 0 && !error ? <section className="empty-state">Пока нет стилей для выбора</section> : null}

      {styles.length > 0 ? (
        <section className="style-grid style-grid--catalog">
          {styles.map((item) => (
            <StyleCard key={item.id} style={item} selected={item.id === selectedId} onSelect={setSelectedId} />
          ))}
        </section>
      ) : null}

      <section className="styles-footer panel layout-split">
        <div className="styles-footer__summary">
          <p className="styles-footer__eyebrow">Готово к съемке</p>
          <h2>{selectedStyle ? selectedStyle.name : "Стиль пока не выбран"}</h2>
          <p className="styles-footer__selected">
            {selectedStyle
              ? selectedStyle.description
              : "Когда стили появятся, вы сможете выбрать визуальный стиль и вернуться на экран камеры."}
          </p>
        </div>
        <div className="sticky-actions styles-footer__actions">
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
