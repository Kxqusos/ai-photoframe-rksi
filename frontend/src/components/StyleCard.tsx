import React from "react";
import type { StylePrompt } from "../types";

type Props = {
  style: StylePrompt;
  selected: boolean;
  onSelect: (styleId: number) => void;
};

export function StyleCard({ style, selected, onSelect }: Props) {
  return (
    <button
      type="button"
      onClick={() => onSelect(style.id)}
      aria-pressed={selected}
      className={`style-card${selected ? " is-selected" : ""}`}
    >
      <img
        src={style.preview_image_url}
        alt={`${style.name} preview`}
        width={140}
        height={90}
        className="style-card__preview"
      />
      <h3 className="style-card__title">{style.name}</h3>
      <p className="style-card__description">{style.description}</p>
    </button>
  );
}
