import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { PromptForm } from "./PromptForm";

test("renders prompt preview as a dedicated upload surface and reflects the selected file", () => {
  const onChange = vi.fn();
  const onSubmit = vi.fn();
  const baseValues = {
    name: "Anime",
    description: "Bright studio portrait",
    prompt: "Turn input photo into anime portrait",
    previewFile: null
  };

  const { container, rerender } = render(<PromptForm values={baseValues} onChange={onChange} onSubmit={onSubmit} />);

  const uploadField = container.querySelector(".file-upload-field");
  expect(uploadField).not.toBeNull();
  expect(uploadField?.querySelector(".file-upload-field__surface")).not.toBeNull();
  expect(screen.queryByText(/превью стиля/i)).not.toBeInTheDocument();
  expect(screen.getByText(/выберите изображение для карточки стиля/i)).toBeInTheDocument();
  expect(screen.getByText(/png, jpg или jpeg\. нажмите, чтобы выбрать файл/i)).toBeInTheDocument();

  const previewFile = new File(["x"], "preview.png", { type: "image/png" });
  fireEvent.change(screen.getByLabelText(/пример результата/i), { target: { files: [previewFile] } });

  expect(onChange).toHaveBeenCalledWith({ ...baseValues, previewFile });

  rerender(<PromptForm values={{ ...baseValues, previewFile }} onChange={onChange} onSubmit={onSubmit} />);

  expect(screen.getByText("preview.png")).toBeInTheDocument();
  expect(screen.getByText(/новый файл готов к загрузке/i)).toBeInTheDocument();
  expect(container.querySelector(".file-upload-field--has-file")).not.toBeNull();
});
