import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { AdminRoomEditorPage } from "./AdminRoomEditorPage";

const loadAdminTokenMock = vi.fn();
const listRoomsMock = vi.fn();
const updateRoomModelMock = vi.fn();
const listRoomAdminPromptsMock = vi.fn();
const uploadRoomPromptPreviewMock = vi.fn();
const createRoomAdminPromptMock = vi.fn();
const updateRoomAdminPromptMock = vi.fn();
const deleteRoomAdminPromptMock = vi.fn();

vi.mock("../lib/auth", () => ({
  loadAdminToken: () => loadAdminTokenMock()
}));

vi.mock("../lib/api", () => ({
  listRooms: () => listRoomsMock(),
  updateRoomModel: (roomId: number, modelName: string) => updateRoomModelMock(roomId, modelName),
  listRoomAdminPrompts: (roomId: number) => listRoomAdminPromptsMock(roomId),
  uploadRoomPromptPreview: (roomId: number, file: File) => uploadRoomPromptPreviewMock(roomId, file),
  createRoomAdminPrompt: (roomId: number, payload: unknown) => createRoomAdminPromptMock(roomId, payload),
  updateRoomAdminPrompt: (roomId: number, promptId: number, payload: unknown) =>
    updateRoomAdminPromptMock(roomId, promptId, payload),
  deleteRoomAdminPrompt: (roomId: number, promptId: number) => deleteRoomAdminPromptMock(roomId, promptId)
}));

beforeEach(() => {
  loadAdminTokenMock.mockReset();
  listRoomsMock.mockReset();
  updateRoomModelMock.mockReset();
  listRoomAdminPromptsMock.mockReset();
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

test("updates model and manages prompts for selected room", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  listRoomAdminPromptsMock
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce([
      {
        id: 5,
        name: "Prompt A",
        description: "desc",
        prompt: "body",
        preview_image_url: "/p.jpg",
        icon_image_url: "/i.png"
      }
    ])
    .mockResolvedValueOnce([]);
  updateRoomModelMock.mockResolvedValue({ id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "new-model", is_active: true });
  uploadRoomPromptPreviewMock.mockResolvedValue({ url: "/media/previews/uploaded.jpg" });
  createRoomAdminPromptMock.mockResolvedValue({
    id: 5,
    name: "Prompt A",
    description: "desc",
    prompt: "body",
    preview_image_url: "/media/previews/uploaded.jpg",
    icon_image_url: "/media/previews/uploaded.jpg"
  });
  updateRoomAdminPromptMock.mockResolvedValue({
    id: 5,
    name: "Prompt Edited",
    description: "updated desc",
    prompt: "updated body",
    preview_image_url: "/p.jpg",
    icon_image_url: "/i.png"
  });
  deleteRoomAdminPromptMock.mockResolvedValue(undefined);

  render(<AdminRoomEditorPage roomSlug="aaaaaaaa" />);

  await screen.findByText(/room a/i);
  expect(screen.getByRole("heading", { name: /сводка комнаты/i })).toBeInTheDocument();
  expect(screen.queryByText(/идентификатор/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/^aaaaaaaa$/i)).not.toBeInTheDocument();
  expect(screen.getByText(/активна/i)).toBeInTheDocument();
  expect(screen.getByText(/^m$/i)).toBeInTheDocument();
  expect(screen.getByText(/^0$/i)).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /управление моделью/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /промпты комнаты/i })).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText(/модель/i), { target: { value: "new-model" } });
  fireEvent.click(screen.getByRole("button", { name: /сохранить модель/i }));
  expect(updateRoomModelMock).toHaveBeenCalledWith(7, "new-model");

  fireEvent.change(screen.getByLabelText(/название промпта/i), { target: { value: "Prompt A" } });
  fireEvent.change(screen.getByLabelText(/описание промпта/i), { target: { value: "desc" } });
  fireEvent.change(screen.getByLabelText(/текст промпта/i), { target: { value: "body" } });
  expect(screen.queryByLabelText(/url превью/i)).not.toBeInTheDocument();
  expect(screen.queryByLabelText(/url иконки/i)).not.toBeInTheDocument();
  const previewFile = new File(["x"], "preview.png", { type: "image/png" });
  fireEvent.change(screen.getByLabelText(/превью/i), { target: { files: [previewFile] } });
  fireEvent.click(screen.getByRole("button", { name: /добавить промпт/i }));
  await waitFor(() => {
    expect(uploadRoomPromptPreviewMock).toHaveBeenCalledWith(7, previewFile);
    expect(createRoomAdminPromptMock).toHaveBeenCalledWith(
      7,
      expect.objectContaining({
        preview_image_url: "/media/previews/uploaded.jpg",
        icon_image_url: "/media/previews/uploaded.jpg"
      })
    );
  });

  fireEvent.click(await screen.findByRole("button", { name: /^редактировать$/i }));
  expect(screen.getByLabelText(/название промпта/i)).toHaveValue("Prompt A");
  expect(screen.getByLabelText(/описание промпта/i)).toHaveValue("desc");
  expect(screen.getByLabelText(/текст промпта/i)).toHaveValue("body");

  fireEvent.change(screen.getByLabelText(/название промпта/i), { target: { value: "Prompt Edited" } });
  fireEvent.change(screen.getByLabelText(/описание промпта/i), { target: { value: "updated desc" } });
  fireEvent.change(screen.getByLabelText(/текст промпта/i), { target: { value: "updated body" } });
  fireEvent.click(screen.getByRole("button", { name: /сохранить изменения/i }));
  await waitFor(() => {
    expect(updateRoomAdminPromptMock).toHaveBeenCalledWith(
      7,
      5,
      expect.objectContaining({
        name: "Prompt Edited",
        description: "updated desc",
        prompt: "updated body",
        preview_image_url: "/p.jpg",
        icon_image_url: "/i.png"
      })
    );
  });

  expect(await screen.findByRole("heading", { name: /prompt edited/i })).toBeInTheDocument();
  expect(screen.queryByText(/превью:\s*\/p\.jpg/i)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /^удалить$/i }));
  await waitFor(() => {
    expect(deleteRoomAdminPromptMock).toHaveBeenCalledWith(7, 5);
    expect(screen.queryByRole("heading", { name: /prompt edited/i })).not.toBeInTheDocument();
  });
});

test("keeps existing icon when editing prompt with a new preview file", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  listRoomAdminPromptsMock.mockResolvedValue([
    {
      id: 5,
      name: "Prompt A",
      description: "desc",
      prompt: "body",
      preview_image_url: "/p.jpg",
      icon_image_url: "/icon.png"
    }
  ]);
  uploadRoomPromptPreviewMock.mockResolvedValue({ url: "/media/previews/replaced.jpg" });
  updateRoomAdminPromptMock.mockResolvedValue({
    id: 5,
    name: "Prompt A",
    description: "desc",
    prompt: "body",
    preview_image_url: "/media/previews/replaced.jpg",
    icon_image_url: "/icon.png"
  });

  render(<AdminRoomEditorPage roomSlug="aaaaaaaa" />);

  fireEvent.click(await screen.findByRole("button", { name: /^редактировать$/i }));
  const previewFile = new File(["y"], "replacement.png", { type: "image/png" });
  fireEvent.change(screen.getByLabelText(/превью/i), { target: { files: [previewFile] } });
  fireEvent.click(screen.getByRole("button", { name: /сохранить изменения/i }));

  await waitFor(() => {
    expect(uploadRoomPromptPreviewMock).toHaveBeenCalledWith(7, previewFile);
    expect(updateRoomAdminPromptMock).toHaveBeenCalledWith(
      7,
      5,
      expect.objectContaining({
        preview_image_url: "/media/previews/replaced.jpg",
        icon_image_url: "/icon.png"
      })
    );
  });
});

test("shows inline save state and richer prompt actions", async () => {
  const saveModelDeferred = createDeferred<{ id: number; slug: string; name: string; model_name: string; is_active: boolean }>();
  const deleteDeferred = createDeferred<void>();

  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  listRoomAdminPromptsMock
    .mockResolvedValueOnce([
      {
        id: 5,
        name: "Prompt A",
        description: "desc",
        prompt: "body",
        preview_image_url: "/p.jpg",
        icon_image_url: "/icon.png"
      }
    ])
    .mockResolvedValueOnce([
      {
        id: 5,
        name: "Prompt A",
        description: "desc",
        prompt: "body",
        preview_image_url: "/p.jpg",
        icon_image_url: "/icon.png"
      }
    ])
    .mockResolvedValue([]);
  updateRoomModelMock.mockReturnValueOnce(saveModelDeferred.promise);
  deleteRoomAdminPromptMock.mockReturnValueOnce(deleteDeferred.promise);

  render(<AdminRoomEditorPage roomSlug="aaaaaaaa" />);

  fireEvent.change(await screen.findByLabelText(/модель/i), { target: { value: "new-model" } });
  fireEvent.click(screen.getByRole("button", { name: /сохранить модель/i }));

  expect(screen.getByRole("button", { name: /сохраняем модель/i })).toBeDisabled();
  expect(screen.getByText(/сохраняем параметры комнаты/i)).toBeInTheDocument();

  saveModelDeferred.resolve({ id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "new-model", is_active: true });
  await waitFor(() => {
    expect(screen.getByRole("button", { name: /сохранить модель/i })).toBeEnabled();
  });

  fireEvent.click(screen.getByRole("button", { name: /^редактировать$/i }));
  expect(screen.getByRole("heading", { name: /редактирование промпта/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /сохранить изменения/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /отменить редактирование/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /отменить редактирование/i }));
  expect(screen.getByRole("heading", { name: /новый промпт/i })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /отменить редактирование/i })).not.toBeInTheDocument();
  expect(screen.getByLabelText(/название промпта/i)).toHaveValue("");

  fireEvent.click(screen.getByRole("button", { name: /^удалить$/i }));
  expect(screen.getByRole("button", { name: /^удаляем\.\.\.$/i })).toBeDisabled();

  deleteDeferred.resolve(undefined);
  await waitFor(() => {
    expect(screen.queryByRole("heading", { name: /prompt a/i })).not.toBeInTheDocument();
  });
});

test("resets edit mode after deleting the prompt currently being edited", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  listRoomAdminPromptsMock
    .mockResolvedValueOnce([
      {
        id: 5,
        name: "Prompt A",
        description: "desc",
        prompt: "body",
        preview_image_url: "/p.jpg",
        icon_image_url: "/icon.png"
      }
    ])
    .mockResolvedValueOnce([]);
  deleteRoomAdminPromptMock.mockResolvedValue(undefined);

  render(<AdminRoomEditorPage roomSlug="aaaaaaaa" />);

  fireEvent.click(await screen.findByRole("button", { name: /^редактировать$/i }));
  expect(screen.getByRole("heading", { name: /редактирование промпта/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /^удалить$/i }));

  await waitFor(() => {
    expect(deleteRoomAdminPromptMock).toHaveBeenCalledWith(7, 5);
    expect(screen.getByRole("heading", { name: /новый промпт/i })).toBeInTheDocument();
  });

  expect(screen.queryByRole("button", { name: /сохранить изменения/i })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /отменить редактирование/i })).not.toBeInTheDocument();
  expect(screen.getByLabelText(/название промпта/i)).toHaveValue("");
});

test("shows user-facing prompt CRUD errors", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  listRoomAdminPromptsMock.mockResolvedValue([
    {
      id: 5,
      name: "Prompt A",
      description: "desc",
      prompt: "body",
      preview_image_url: "/p.jpg",
      icon_image_url: "/icon.png"
    }
  ]);
  uploadRoomPromptPreviewMock.mockResolvedValue({ url: "/media/previews/uploaded.jpg" });
  createRoomAdminPromptMock.mockRejectedValueOnce(new Error("create failed"));
  updateRoomAdminPromptMock.mockRejectedValueOnce(new Error("update failed"));
  deleteRoomAdminPromptMock.mockRejectedValueOnce(new Error("delete failed"));

  render(<AdminRoomEditorPage roomSlug="aaaaaaaa" />);

  fireEvent.change(await screen.findByLabelText(/название промпта/i), { target: { value: "Prompt New" } });
  fireEvent.change(screen.getByLabelText(/описание промпта/i), { target: { value: "desc new" } });
  fireEvent.change(screen.getByLabelText(/текст промпта/i), { target: { value: "body new" } });
  fireEvent.change(screen.getByLabelText(/превью/i), {
    target: { files: [new File(["x"], "preview.png", { type: "image/png" })] }
  });
  fireEvent.click(screen.getByRole("button", { name: /добавить промпт/i }));

  expect(await screen.findByRole("alert")).toHaveTextContent(/create failed/i);

  fireEvent.click(screen.getByRole("button", { name: /^редактировать$/i }));
  fireEvent.change(screen.getByLabelText(/название промпта/i), { target: { value: "Prompt A+" } });
  fireEvent.click(screen.getByRole("button", { name: /сохранить изменения/i }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent(/update failed/i);
  });

  fireEvent.click(screen.getByRole("button", { name: /^удалить$/i }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent(/delete failed/i);
  });
});

test("keeps create form state when prompt creation succeeds but the refresh fails", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock
    .mockResolvedValueOnce([{ id: 7, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }])
    .mockRejectedValueOnce(new Error("refresh failed"));
  listRoomAdminPromptsMock.mockResolvedValue([]);
  uploadRoomPromptPreviewMock.mockResolvedValue({ url: "/media/previews/uploaded.jpg" });
  createRoomAdminPromptMock.mockResolvedValue({
    id: 9,
    name: "Prompt New",
    description: "desc new",
    prompt: "body new",
    preview_image_url: "/media/previews/uploaded.jpg",
    icon_image_url: "/media/previews/uploaded.jpg"
  });

  render(<AdminRoomEditorPage roomSlug="aaaaaaaa" />);

  fireEvent.change(await screen.findByLabelText(/название промпта/i), { target: { value: "Prompt New" } });
  fireEvent.change(screen.getByLabelText(/описание промпта/i), { target: { value: "desc new" } });
  fireEvent.change(screen.getByLabelText(/текст промпта/i), { target: { value: "body new" } });

  const previewFile = new File(["x"], "preview.png", { type: "image/png" });
  fireEvent.change(screen.getByLabelText(/превью/i), { target: { files: [previewFile] } });
  fireEvent.click(screen.getByRole("button", { name: /добавить промпт/i }));

  await waitFor(() => {
    expect(createRoomAdminPromptMock).toHaveBeenCalledWith(
      7,
      expect.objectContaining({
        name: "Prompt New",
        description: "desc new",
        prompt: "body new"
      })
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/refresh failed/i);
  });

  expect(screen.getByRole("heading", { name: /новый промпт/i })).toBeInTheDocument();
  expect(screen.getByLabelText(/название промпта/i)).toHaveValue("Prompt New");
  expect(screen.getByLabelText(/описание промпта/i)).toHaveValue("desc new");
  expect(screen.getByLabelText(/текст промпта/i)).toHaveValue("body new");
});
