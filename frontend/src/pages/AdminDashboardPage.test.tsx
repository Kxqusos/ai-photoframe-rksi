import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { AdminDashboardPage } from "./AdminDashboardPage";

const loadAdminTokenMock = vi.fn();
const listRoomsMock = vi.fn();
const createRoomMock = vi.fn();
const patchRoomMock = vi.fn();
const deleteRoomMock = vi.fn();
const getLlmRoutingMock = vi.fn();
const updateLlmRoutingConfigMock = vi.fn();
const testLlmRoutingMock = vi.fn();
const toggleLlmRoutingMock = vi.fn();

vi.mock("../lib/auth", () => ({
  loadAdminToken: () => loadAdminTokenMock()
}));

vi.mock("../lib/api", () => ({
  listRooms: () => listRoomsMock(),
  createRoom: (payload: unknown) => createRoomMock(payload),
  patchRoom: (roomId: number, payload: unknown) => patchRoomMock(roomId, payload),
  deleteRoom: (roomId: number) => deleteRoomMock(roomId),
  getLlmRouting: () => getLlmRoutingMock(),
  updateLlmRoutingConfig: (vlessUri: string) => updateLlmRoutingConfigMock(vlessUri),
  testLlmRouting: () => testLlmRoutingMock(),
  toggleLlmRouting: (enabled: boolean) => toggleLlmRoutingMock(enabled)
}));

beforeEach(() => {
  loadAdminTokenMock.mockReset();
  listRoomsMock.mockReset();
  createRoomMock.mockReset();
  patchRoomMock.mockReset();
  deleteRoomMock.mockReset();
  getLlmRoutingMock.mockReset();
  updateLlmRoutingConfigMock.mockReset();
  testLlmRoutingMock.mockReset();
  toggleLlmRoutingMock.mockReset();
  getLlmRoutingMock.mockResolvedValue({
    enabled: false,
    status: "disabled",
    vless_uri: "",
    last_error: null,
    last_checked_at: null,
    last_applied_at: null
  });
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
  expect(screen.queryByText(/aaaaaaaa/i)).not.toBeInTheDocument();
  expect(screen.getByText(/активна/i)).toBeInTheDocument();
  expect(screen.getByText(/^m$/i)).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /room a/i }).closest("article")).toHaveClass("room-card");
  expect(screen.getByRole("heading", { name: /room a/i }).closest("article")).not.toHaveClass("prompt-card");
  expect(screen.getByRole("button", { name: /^редактировать$/i })).toHaveClass("button-secondary");
  expect(screen.getByRole("button", { name: /^удалить$/i })).toHaveClass("button-danger");
  expect(screen.getByRole("button", { name: /^удалить$/i })).toHaveAccessibleName("Удалить");
  expect(screen.getByRole("link", { name: /^открыть$/i })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /^открыть$/i })).toHaveClass("button-secondary");

  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Room B" } });
  fireEvent.change(screen.getByLabelText(/пароль комнаты/i), { target: { value: "room-b-pass" } });
  fireEvent.click(screen.getByRole("button", { name: /создать комнату/i }));

  return waitFor(() => {
    expect(createRoomMock).toHaveBeenCalledWith({
      name: "Room B",
      model_name: "openai/gpt-5-image",
      is_active: true,
      password: "room-b-pass"
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

  fireEvent.click(screen.getByRole("button", { name: /^редактировать$/i }));
  expect(screen.getByRole("heading", { name: /редактирование комнаты/i })).toBeInTheDocument();
  expect(screen.getByLabelText(/название/i)).toHaveValue("Room A");
  expect(screen.queryByLabelText(/slug/i)).not.toBeInTheDocument();

  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Room A Updated" } });
  fireEvent.click(screen.getByLabelText(/комната активна/i));
  fireEvent.click(screen.getByRole("button", { name: /сохранить изменения/i }));

  await waitFor(() => {
    expect(patchRoomMock).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        name: "Room A Updated",
        model_name: "m",
        is_active: false
      })
    );
  });

  expect(await screen.findByRole("heading", { name: /room a updated/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /room a updated/i }).closest("article")).toHaveTextContent(/выключена/i);

  fireEvent.click(screen.getByRole("button", { name: /^удалить$/i }));
  expect(screen.getByRole("dialog", { name: /подтвердить удаление комнаты/i })).toBeInTheDocument();
  expect(deleteRoomMock).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole("button", { name: /удалить комнату/i }));

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

  fireEvent.click(screen.getByRole("button", { name: /^редактировать$/i }));
  fireEvent.click(screen.getByRole("button", { name: /отменить редактирование/i }));
  expect(screen.getByRole("heading", { name: /новая комната/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /^редактировать$/i }));
  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Room A+" } });
  fireEvent.click(screen.getByRole("button", { name: /сохранить изменения/i }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent(/patch failed/i);
  });

  fireEvent.click(screen.getByRole("button", { name: /^удалить$/i }));
  expect(screen.getByRole("dialog", { name: /подтвердить удаление комнаты/i })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /удалить комнату/i }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent(/delete failed/i);
  });
});

test("requires explicit confirmation before deleting a room and allows cancelling the modal", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 1, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  deleteRoomMock.mockResolvedValue(undefined);

  render(<AdminDashboardPage />);

  expect(await screen.findByRole("heading", { name: /room a/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /^удалить$/i }));
  expect(screen.getByRole("dialog", { name: /подтвердить удаление комнаты/i })).toBeInTheDocument();
  expect(deleteRoomMock).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole("button", { name: /отменить/i }));
  expect(screen.queryByRole("dialog", { name: /подтвердить удаление комнаты/i })).not.toBeInTheDocument();
  expect(deleteRoomMock).not.toHaveBeenCalled();
});

test("loads llm routing card, shows explicit russian statuses, and saves the current draft before test/toggle", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 1, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  updateLlmRoutingConfigMock.mockResolvedValue({
    enabled: false,
    status: "disabled",
    vless_uri: "vless://uuid@example.com:443",
    last_error: null,
    last_checked_at: "2026-03-17T12:00:00",
    last_applied_at: "2026-03-17T12:00:00"
  });
  testLlmRoutingMock.mockResolvedValue({
    enabled: false,
    status: "disabled",
    vless_uri: "vless://uuid@example.com:443",
    last_error: null,
    last_checked_at: "2026-03-17T12:01:00",
    last_applied_at: "2026-03-17T12:01:00"
  });
  toggleLlmRoutingMock.mockResolvedValue({
    enabled: true,
    status: "active",
    vless_uri: "vless://uuid@example.com:443",
    last_error: null,
    last_checked_at: "2026-03-17T12:02:00",
    last_applied_at: "2026-03-17T12:02:00"
  });

  render(<AdminDashboardPage />);

  expect(await screen.findByRole("heading", { name: /room a/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /llm routing/i })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /сохранить и применить/i })).not.toBeInTheDocument();
  expect(screen.queryByText(/статус подключения:/i)).not.toBeInTheDocument();
  const routingStatus = screen.getByText(/маршрутизация/i).closest(".routing-status-chip");
  expect(routingStatus).not.toBeNull();
  expect(routingStatus).toHaveClass("routing-status-chip", "routing-status-chip--disabled");
  expect(routingStatus).toHaveTextContent(/^маршрутизация/i);
  expect(routingStatus).toHaveTextContent(/выключена/i);
  expect(routingStatus?.querySelector(".routing-status-chip__dot")).not.toBeNull();

  fireEvent.change(screen.getByLabelText(/vless url/i), { target: { value: "vless://uuid@example.com:443" } });
  fireEvent.click(screen.getByRole("button", { name: /проверить подключение/i }));
  await waitFor(() => {
    expect(updateLlmRoutingConfigMock).toHaveBeenCalledWith("vless://uuid@example.com:443");
    expect(testLlmRoutingMock).toHaveBeenCalled();
    expect(screen.queryByText(/статус подключения:/i)).not.toBeInTheDocument();
    expect(screen.getByText(/ключ vless проверен/i)).toBeInTheDocument();
    expect(screen.queryByText(/подключение успешно проверено/i)).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveClass("routing-feedback", "routing-feedback--success");
  });

  fireEvent.click(screen.getByRole("button", { name: /включить маршрутизацию/i }));
  await waitFor(() => {
    expect(toggleLlmRoutingMock).toHaveBeenCalledWith(true);
    expect(screen.queryByText(/статус подключения:/i)).not.toBeInTheDocument();
    expect(screen.getByText(/маршрутизация/i).closest(".routing-status-chip")).toHaveClass(
      "routing-status-chip",
      "routing-status-chip--enabled"
    );
    expect(screen.getByText(/маршрутизация/i).closest(".routing-status-chip")).toHaveTextContent(/включена/i);
  });
});

test("groups routing controls into a dedicated stack so the status card spacing stays consistent", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 1, slug: "aaaaaaaa", name: "Room A", model_name: "m", is_active: true }]);
  getLlmRoutingMock.mockResolvedValue({
    enabled: false,
    status: "disabled",
    vless_uri: "vless://uuid@example.com:443",
    last_error: null,
    last_checked_at: "2026-03-17T12:01:00",
    last_applied_at: "2026-03-17T12:01:00"
  });

  const { container } = render(<AdminDashboardPage />);

  expect(await screen.findByRole("heading", { name: /room a/i })).toBeInTheDocument();

  const routingStack = container.querySelector(".routing-stack");
  expect(routingStack).not.toBeNull();
  expect(routingStack).toContainElement(screen.getByLabelText(/vless url/i));
  expect(routingStack).toContainElement(screen.getByText(/маршрутизация/i).closest(".routing-status-chip"));
  expect(routingStack).toContainElement(screen.getByRole("status"));
  expect(screen.queryByText(/подключение успешно проверено/i)).not.toBeInTheDocument();
  expect(routingStack).toContainElement(screen.getByRole("button", { name: /проверить подключение/i }));
});
