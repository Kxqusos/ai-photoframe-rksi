import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { AdminDashboardPage } from "./AdminDashboardPage";

const loadAdminTokenMock = vi.fn();
const listRoomsMock = vi.fn();
const createRoomMock = vi.fn();
const patchRoomMock = vi.fn();
const deleteRoomMock = vi.fn();

vi.mock("../lib/auth", () => ({
  loadAdminToken: () => loadAdminTokenMock()
}));

vi.mock("../lib/api", () => ({
  listRooms: () => listRoomsMock(),
  createRoom: (payload: unknown) => createRoomMock(payload),
  patchRoom: (roomId: number, payload: unknown) => patchRoomMock(roomId, payload),
  deleteRoom: (roomId: number) => deleteRoomMock(roomId)
}));

beforeEach(() => {
  loadAdminTokenMock.mockReset();
  listRoomsMock.mockReset();
  createRoomMock.mockReset();
  patchRoomMock.mockReset();
  deleteRoomMock.mockReset();
});

test("redirects to /admin/login when token is missing", () => {
  loadAdminTokenMock.mockReturnValue(null);
  window.history.pushState({}, "", "/admin");

  render(<AdminDashboardPage />);

  expect(window.location.pathname).toBe("/admin/login");
});

test("loads rooms and allows creating a room", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 1, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  createRoomMock.mockResolvedValue({ id: 2, slug: "bbbbbbbb", name: "Room B", model_name: "m", is_active: true });

  render(<AdminDashboardPage />);

  expect(await screen.findByRole("heading", { name: /room a/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /новая комната/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /комнаты/i })).toBeInTheDocument();
  expect(screen.getByText(/aaaaaaaa/i)).toBeInTheDocument();
  expect(screen.getByText(/активна/i)).toBeInTheDocument();
  expect(screen.getByText(/^m$/i)).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /room a/i }).closest("article")).toHaveClass("room-card");
  expect(screen.getByRole("heading", { name: /room a/i }).closest("article")).not.toHaveClass("prompt-card");
  expect(screen.getByRole("button", { name: /редактировать room a/i })).toHaveClass("button-secondary");
  expect(screen.getByRole("button", { name: /удалить room a/i })).toHaveClass("button-danger");
  expect(screen.getByRole("link", { name: /открыть room a/i })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /открыть room a/i })).toHaveClass("button-secondary");

  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Room B" } });
  fireEvent.click(screen.getByRole("button", { name: /создать комнату/i }));

  return waitFor(() => {
    expect(createRoomMock).toHaveBeenCalledWith({
      name: "Room B",
      model_name: "openai/gpt-5-image",
      is_active: true
    });
  });
});

test("shows richer empty-state guidance when no rooms exist", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([]);

  render(<AdminDashboardPage />);

  expect(await screen.findByRole("heading", { name: /новая комната/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /комнаты/i })).toBeInTheDocument();
  expect(screen.getByText(/сначала создайте первую комнату/i)).toBeInTheDocument();
  expect(screen.getByText(/после создания здесь появятся карточки с быстрыми действиями/i)).toBeInTheDocument();
});

test("allows editing and deleting rooms from the dashboard", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock
    .mockResolvedValueOnce([{ id: 1, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }])
    .mockResolvedValueOnce([{ id: 1, slug: "aaaabbbb", name: "Room A Updated", model_name: "m", is_active: false }])
    .mockResolvedValueOnce([]);
  patchRoomMock.mockResolvedValue({
    id: 1,
    slug: "aaaabbbb",
    name: "Room A Updated",
    model_name: "m",
    is_active: false
  });
  deleteRoomMock.mockResolvedValue(undefined);

  render(<AdminDashboardPage />);

  expect(await screen.findByRole("heading", { name: /room a/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /редактировать room a/i }));
  expect(screen.getByRole("heading", { name: /редактирование комнаты/i })).toBeInTheDocument();
  expect(screen.getByLabelText(/название/i)).toHaveValue("Room A");
  expect(screen.getByLabelText(/slug/i)).toHaveValue("aaaaaaaa");

  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Room A Updated" } });
  fireEvent.change(screen.getByLabelText(/slug/i), { target: { value: "aaaabbbb" } });
  fireEvent.click(screen.getByLabelText(/комната активна/i));
  fireEvent.click(screen.getByRole("button", { name: /сохранить изменения/i }));

  await waitFor(() => {
    expect(patchRoomMock).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        name: "Room A Updated",
        slug: "aaaabbbb",
        model_name: "m",
        is_active: false
      })
    );
  });

  expect(await screen.findByRole("heading", { name: /room a updated/i })).toBeInTheDocument();
  expect(screen.getByText(/выключена/i)).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /удалить room a updated/i }));

  await waitFor(() => {
    expect(deleteRoomMock).toHaveBeenCalledWith(1);
    expect(screen.getByText(/сначала создайте первую комнату/i)).toBeInTheDocument();
  });
});

test("shows room patch/delete errors and allows cancelling edit mode", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 1, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  patchRoomMock.mockRejectedValueOnce(new Error("patch failed"));
  deleteRoomMock.mockRejectedValueOnce(new Error("delete failed"));

  render(<AdminDashboardPage />);

  expect(await screen.findByRole("heading", { name: /room a/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /редактировать room a/i }));
  fireEvent.click(screen.getByRole("button", { name: /отменить редактирование/i }));
  expect(screen.getByRole("heading", { name: /новая комната/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /редактировать room a/i }));
  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Room A+" } });
  fireEvent.click(screen.getByRole("button", { name: /сохранить изменения/i }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent(/patch failed/i);
  });

  fireEvent.click(screen.getByRole("button", { name: /удалить room a/i }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent(/delete failed/i);
  });
});
