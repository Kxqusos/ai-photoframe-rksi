import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { SettingsPage } from "./SettingsPage";

const loadAdminTokenMock = vi.fn();
const navigateToMock = vi.fn();
const listModelsMock = vi.fn();
const listRoomsMock = vi.fn();
const listRoomAdminPromptsMock = vi.fn();
const updateRoomModelMock = vi.fn();
const uploadRoomPromptPreviewMock = vi.fn();
const createRoomAdminPromptMock = vi.fn();
const deleteRoomAdminPromptMock = vi.fn();

vi.mock("../lib/auth", () => ({
  loadAdminToken: () => loadAdminTokenMock()
}));

vi.mock("../lib/navigation", () => ({
  navigateTo: (pathname: string) => navigateToMock(pathname)
}));

vi.mock("../lib/api", () => ({
  listModels: () => listModelsMock(),
  listRooms: () => listRoomsMock(),
  listRoomAdminPrompts: (roomId: number) => listRoomAdminPromptsMock(roomId),
  updateRoomModel: (roomId: number, modelName: string) => updateRoomModelMock(roomId, modelName),
  uploadRoomPromptPreview: (roomId: number, file: File) => uploadRoomPromptPreviewMock(roomId, file),
  createRoomAdminPrompt: (roomId: number, payload: unknown) => createRoomAdminPromptMock(roomId, payload),
  deleteRoomAdminPrompt: (roomId: number, promptId: number) => deleteRoomAdminPromptMock(roomId, promptId)
}));

test("redirects to admin login when token is missing", async () => {
  loadAdminTokenMock.mockReturnValue(null);

  render(<SettingsPage />);

  await waitFor(() => {
    expect(navigateToMock).toHaveBeenCalledWith("/admin/login");
  });
});

test("applies model and manages prompts for selected room", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listModelsMock.mockResolvedValue(["openai/gpt-5-image", "google/gemini-2.5-flash-image"]);
  listRoomsMock.mockResolvedValue([
    { id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "openai/gpt-5-image", is_active: true },
    { id: 9, slug: "bbbbbbbb", name: "Room B", model_name: "google/gemini-2.5-flash-image", is_active: true }
  ]);
  listRoomAdminPromptsMock
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce([
      {
        id: 12,
        name: "Watercolor",
        description: "Painterly style",
        prompt: "watercolor painting",
        preview_image_url: "/media/previews/preview.jpg",
        icon_image_url: "/media/icons/icon.png"
      }
    ])
    .mockResolvedValueOnce([]);
  updateRoomModelMock.mockResolvedValue({});
  uploadRoomPromptPreviewMock.mockResolvedValue({ url: "/media/previews/preview.jpg" });
  createRoomAdminPromptMock.mockResolvedValue({
    id: 12,
    name: "Watercolor",
    description: "Painterly style",
    prompt: "watercolor painting",
    preview_image_url: "/media/previews/preview.jpg",
    icon_image_url: "/media/previews/preview.jpg"
  });
  deleteRoomAdminPromptMock.mockResolvedValue(undefined);

  render(<SettingsPage />);

  await waitFor(() => {
    expect(listRoomAdminPromptsMock).toHaveBeenCalledWith(7);
  });

  fireEvent.change(screen.getByLabelText(/комната/i), { target: { value: "9" } });
  await waitFor(() => {
    expect(listRoomAdminPromptsMock).toHaveBeenCalledWith(9);
  });

  fireEvent.change(screen.getByLabelText(/модель комнаты/i), { target: { value: "openai/gpt-5-image" } });
  fireEvent.click(screen.getByRole("button", { name: /применить модель/i }));
  await waitFor(() => {
    expect(updateRoomModelMock).toHaveBeenCalledWith(9, "openai/gpt-5-image");
  });

  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Watercolor" } });
  fireEvent.change(screen.getByLabelText(/описание/i), { target: { value: "Painterly style" } });
  fireEvent.change(screen.getByLabelText(/^промпт$/i), { target: { value: "watercolor painting" } });

  const previewFile = new File(["x"], "preview.jpg", { type: "image/jpeg" });
  fireEvent.change(screen.getByLabelText(/пример результата/i), { target: { files: [previewFile] } });
  expect(screen.queryByLabelText(/иконка/i)).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /сохранить/i }));

  await waitFor(() => {
    expect(uploadRoomPromptPreviewMock).toHaveBeenCalledWith(9, previewFile);
    expect(createRoomAdminPromptMock).toHaveBeenCalledWith(
      9,
      expect.objectContaining({
        name: "Watercolor",
        description: "Painterly style",
        prompt: "watercolor painting",
        preview_image_url: "/media/previews/preview.jpg",
        icon_image_url: "/media/previews/preview.jpg"
      })
    );
  });

  fireEvent.click(await screen.findByRole("button", { name: /удалить стиль watercolor/i }));
  await waitFor(() => {
    expect(deleteRoomAdminPromptMock).toHaveBeenCalledWith(9, 12);
  });
});
