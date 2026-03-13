import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { SettingsPage } from "./SettingsPage";

const loadAdminTokenMock = vi.fn();
const navigateToMock = vi.fn();
const listModelsMock = vi.fn();
const listRoomsMock = vi.fn();
const listRoomAdminPromptsMock = vi.fn();
const updateRoomModelMock = vi.fn();
const uploadRoomPromptPreviewMock = vi.fn();
const createRoomAdminPromptMock = vi.fn();
const updateRoomAdminPromptMock = vi.fn();
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
  updateRoomAdminPrompt: (roomId: number, promptId: number, payload: unknown) =>
    updateRoomAdminPromptMock(roomId, promptId, payload),
  deleteRoomAdminPrompt: (roomId: number, promptId: number) => deleteRoomAdminPromptMock(roomId, promptId)
}));

beforeEach(() => {
  loadAdminTokenMock.mockReset();
  navigateToMock.mockReset();
  listModelsMock.mockReset();
  listRoomsMock.mockReset();
  listRoomAdminPromptsMock.mockReset();
  updateRoomModelMock.mockReset();
  uploadRoomPromptPreviewMock.mockReset();
  createRoomAdminPromptMock.mockReset();
  updateRoomAdminPromptMock.mockReset();
  deleteRoomAdminPromptMock.mockReset();
});

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((nextResolve) => {
    resolve = nextResolve;
  });

  return { promise, resolve };
}

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
  updateRoomAdminPromptMock.mockResolvedValue({
    id: 12,
    name: "Watercolor Edited",
    description: "Sharper painterly style",
    prompt: "watercolor painting with contrast",
    preview_image_url: "/media/previews/preview.jpg",
    icon_image_url: "/media/icons/icon.png"
  });
  deleteRoomAdminPromptMock.mockResolvedValue(undefined);

  render(<SettingsPage />);

  await waitFor(() => {
    expect(listRoomAdminPromptsMock).toHaveBeenCalledWith(7);
  });
  expect(screen.getByRole("heading", { name: /параметры комнаты/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /промпты комнаты/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /новый промпт/i })).toBeInTheDocument();

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

  fireEvent.click(screen.getByRole("button", { name: /создать промпт/i }));

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

  expect(await screen.findByText(/превью: \/media\/previews\/preview.jpg/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /редактировать watercolor/i }));
  expect(screen.getByRole("heading", { name: /редактирование промпта/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /сохранить изменения/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /отменить редактирование/i })).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Watercolor Edited" } });
  fireEvent.change(screen.getByLabelText(/описание/i), { target: { value: "Sharper painterly style" } });
  fireEvent.change(screen.getByLabelText(/^промпт$/i), { target: { value: "watercolor painting with contrast" } });
  fireEvent.click(screen.getByRole("button", { name: /сохранить изменения/i }));
  await waitFor(() => {
    expect(updateRoomAdminPromptMock).toHaveBeenCalledWith(
      9,
      12,
      expect.objectContaining({
        name: "Watercolor Edited",
        description: "Sharper painterly style",
        prompt: "watercolor painting with contrast",
        preview_image_url: "/media/previews/preview.jpg",
        icon_image_url: "/media/previews/preview.jpg"
      })
    );
  });

  expect(await screen.findByRole("heading", { name: /watercolor edited/i })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /редактировать watercolor edited/i }));
  fireEvent.click(screen.getByRole("button", { name: /отменить редактирование/i }));
  expect(screen.getByRole("heading", { name: /новый промпт/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /удалить watercolor edited навсегда/i }));
  await waitFor(() => {
    expect(deleteRoomAdminPromptMock).toHaveBeenCalledWith(9, 12);
  });
});

test("shows richer empty state when selected room has no prompts", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listModelsMock.mockResolvedValue(["openai/gpt-5-image"]);
  listRoomsMock.mockResolvedValue([{ id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "openai/gpt-5-image", is_active: true }]);
  listRoomAdminPromptsMock.mockResolvedValue([]);

  render(<SettingsPage />);

  expect(await screen.findByRole("heading", { name: /промпты комнаты/i })).toBeInTheDocument();
  expect(screen.getByText(/в этой комнате пока нет промптов/i)).toBeInTheDocument();
  expect(screen.getByText(/добавьте первый стиль, чтобы команда сразу видела превью и описание/i)).toBeInTheDocument();
});

test("keeps prompts aligned with the latest selected room when requests resolve out of order", async () => {
  const roomAPrompts = createDeferred<
    Array<{
      id: number;
      name: string;
      description: string;
      prompt: string;
      preview_image_url: string;
      icon_image_url: string;
    }>
  >();
  const roomBPrompts = createDeferred<
    Array<{
      id: number;
      name: string;
      description: string;
      prompt: string;
      preview_image_url: string;
      icon_image_url: string;
    }>
  >();

  loadAdminTokenMock.mockReturnValue("jwt-token");
  listModelsMock.mockResolvedValue(["openai/gpt-5-image"]);
  listRoomsMock.mockResolvedValue([
    { id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "openai/gpt-5-image", is_active: true },
    { id: 9, slug: "bbbbbbbb", name: "Room B", model_name: "openai/gpt-5-image", is_active: true }
  ]);
  listRoomAdminPromptsMock.mockImplementation((roomId: number) => {
    if (roomId === 7) {
      return roomAPrompts.promise;
    }

    if (roomId === 9) {
      return roomBPrompts.promise;
    }

    return Promise.resolve([]);
  });

  render(<SettingsPage />);

  await screen.findByLabelText(/комната/i);
  fireEvent.change(screen.getByLabelText(/комната/i), { target: { value: "9" } });

  await waitFor(() => {
    expect(listRoomAdminPromptsMock).toHaveBeenCalledWith(7);
    expect(listRoomAdminPromptsMock).toHaveBeenCalledWith(9);
  });

  await act(async () => {
    roomBPrompts.resolve([
      {
        id: 12,
        name: "Room B Prompt",
        description: "desc b",
        prompt: "prompt b",
        preview_image_url: "/b.jpg",
        icon_image_url: "/b-icon.png"
      }
    ]);
    await Promise.resolve();
  });

  expect(await screen.findByRole("heading", { name: /room b prompt/i })).toBeInTheDocument();

  await act(async () => {
    roomAPrompts.resolve([
      {
        id: 5,
        name: "Room A Prompt",
        description: "desc a",
        prompt: "prompt a",
        preview_image_url: "/a.jpg",
        icon_image_url: "/a-icon.png"
      }
    ]);
    await Promise.resolve();
  });

  expect(screen.getByRole("heading", { name: /room b prompt/i })).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: /room a prompt/i })).not.toBeInTheDocument();
});
