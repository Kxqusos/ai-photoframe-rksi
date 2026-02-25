import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { SettingsPage } from "./SettingsPage";

const listPromptsMock = vi.fn();
const listModelsMock = vi.fn();
const getModelMock = vi.fn();
const setModelMock = vi.fn();
const uploadPromptPreviewMock = vi.fn();
const uploadPromptIconMock = vi.fn();
const createPromptMock = vi.fn();
const deletePromptMock = vi.fn();

vi.mock("../lib/api", () => ({
  listPrompts: () => listPromptsMock(),
  listModels: () => listModelsMock(),
  getModel: () => getModelMock(),
  setModel: (model: string) => setModelMock(model),
  uploadPromptPreview: (file: File) => uploadPromptPreviewMock(file),
  uploadPromptIcon: (file: File) => uploadPromptIconMock(file),
  createPrompt: (payload: unknown) => createPromptMock(payload),
  deletePrompt: (promptId: number) => deletePromptMock(promptId)
}));

test("creates prompt with name, description, prompt text, preview and icon", async () => {
  listModelsMock.mockResolvedValue(["openai/gpt-5-image"]);
  getModelMock.mockResolvedValue({ id: 1, model_name: "openai/gpt-5-image" });
  listPromptsMock.mockResolvedValue([]);

  uploadPromptPreviewMock.mockResolvedValue({ url: "/media/previews/preview.jpg" });
  uploadPromptIconMock.mockResolvedValue({ url: "/media/icons/icon.png" });
  createPromptMock.mockResolvedValue({
    id: 12,
    name: "Watercolor",
    description: "Painterly style",
    prompt: "watercolor painting",
    preview_image_url: "/media/previews/preview.jpg",
    icon_image_url: "/media/icons/icon.png"
  });

  render(<SettingsPage />);

  await screen.findByText("Settings");

  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Watercolor" } });
  fireEvent.change(screen.getByLabelText(/описание/i), { target: { value: "Painterly style" } });
  fireEvent.change(screen.getByLabelText(/^промпт$/i), { target: { value: "watercolor painting" } });

  const previewFile = new File(["x"], "preview.jpg", { type: "image/jpeg" });
  fireEvent.change(screen.getByLabelText(/пример результата/i), { target: { files: [previewFile] } });

  const iconFile = new File(["x"], "icon.png", { type: "image/png" });
  fireEvent.change(screen.getByLabelText(/иконка/i), { target: { files: [iconFile] } });

  fireEvent.click(screen.getByRole("button", { name: /сохранить/i }));

  await waitFor(() => {
    expect(uploadPromptPreviewMock).toHaveBeenCalled();
    expect(uploadPromptIconMock).toHaveBeenCalled();
    expect(createPromptMock).toHaveBeenCalled();
  });

  expect(await screen.findByText("Watercolor")).toBeInTheDocument();
});

test("deletes style from settings list", async () => {
  listModelsMock.mockResolvedValue(["openai/gpt-5-image"]);
  getModelMock.mockResolvedValue({ id: 1, model_name: "openai/gpt-5-image" });
  listPromptsMock.mockResolvedValue([
    {
      id: 1,
      name: "Anime",
      description: "Soft anime shading",
      prompt: "Turn input photo into anime portrait",
      preview_image_url: "/media/previews/anime.jpg",
      icon_image_url: "/media/icons/anime.png"
    }
  ]);
  deletePromptMock.mockResolvedValue(undefined);

  render(<SettingsPage />);

  await screen.findByText("Anime");
  fireEvent.click(screen.getByRole("button", { name: /удалить стиль anime/i }));

  await waitFor(() => {
    expect(deletePromptMock).toHaveBeenCalledWith(1);
  });

  expect(screen.queryByText("Anime")).not.toBeInTheDocument();
});
