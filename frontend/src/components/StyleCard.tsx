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
      style={{
        border: selected ? "2px solid #0f766e" : "1px solid #d4d4d8",
        borderRadius: 12,
        padding: 12,
        textAlign: "left",
        background: "#ffffff"
      }}
    >
      <img src={style.preview_image_url} alt={`${style.name} preview`} width={140} height={90} />
      <h3>{style.name}</h3>
      <p>{style.description}</p>
    </button>
  );
}
