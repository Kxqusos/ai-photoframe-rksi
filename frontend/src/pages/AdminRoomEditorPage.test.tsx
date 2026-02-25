import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { AdminRoomEditorPage } from "./AdminRoomEditorPage";

const loadAdminTokenMock = vi.fn();
const listRoomsMock = vi.fn();
const updateRoomModelMock = vi.fn();
const listRoomAdminPromptsMock = vi.fn();
const createRoomAdminPromptMock = vi.fn();
const deleteRoomAdminPromptMock = vi.fn();

vi.mock("../lib/auth", () => ({
  loadAdminToken: () => loadAdminTokenMock()
}));

vi.mock("../lib/api", () => ({
  listRooms: () => listRoomsMock(),
  updateRoomModel: (roomId: number, modelName: string) => updateRoomModelMock(roomId, modelName),
  listRoomAdminPrompts: (roomId: number) => listRoomAdminPromptsMock(roomId),
  createRoomAdminPrompt: (roomId: number, payload: unknown) => createRoomAdminPromptMock(roomId, payload),
  deleteRoomAdminPrompt: (roomId: number, promptId: number) => deleteRoomAdminPromptMock(roomId, promptId)
}));

test("updates model and manages prompts for selected room", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 7, slug: "room-a", name: "Room A", model_name: "m", is_active: true }]);
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
  updateRoomModelMock.mockResolvedValue({ id: 7, slug: "room-a", name: "Room A", model_name: "new-model", is_active: true });
  createRoomAdminPromptMock.mockResolvedValue({
    id: 5,
    name: "Prompt A",
    description: "desc",
    prompt: "body",
    preview_image_url: "/p.jpg",
    icon_image_url: "/i.png"
  });
  deleteRoomAdminPromptMock.mockResolvedValue(undefined);

  render(<AdminRoomEditorPage roomId={7} />);

  await screen.findByText(/room a/i);

  fireEvent.change(screen.getByLabelText(/модель/i), { target: { value: "new-model" } });
  fireEvent.click(screen.getByRole("button", { name: /сохранить модель/i }));
  expect(updateRoomModelMock).toHaveBeenCalledWith(7, "new-model");

  fireEvent.change(screen.getByLabelText(/название промпта/i), { target: { value: "Prompt A" } });
  fireEvent.change(screen.getByLabelText(/описание промпта/i), { target: { value: "desc" } });
  fireEvent.change(screen.getByLabelText(/текст промпта/i), { target: { value: "body" } });
  fireEvent.change(screen.getByLabelText(/url превью/i), { target: { value: "/p.jpg" } });
  fireEvent.change(screen.getByLabelText(/url иконки/i), { target: { value: "/i.png" } });
  fireEvent.click(screen.getByRole("button", { name: /добавить промпт/i }));
  expect(createRoomAdminPromptMock).toHaveBeenCalled();

  fireEvent.click(await screen.findByRole("button", { name: /удалить prompt a/i }));
  expect(deleteRoomAdminPromptMock).toHaveBeenCalledWith(7, 5);
});
