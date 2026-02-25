import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { AdminDashboardPage } from "./AdminDashboardPage";

const loadAdminTokenMock = vi.fn();
const listRoomsMock = vi.fn();
const createRoomMock = vi.fn();

vi.mock("../lib/auth", () => ({
  loadAdminToken: () => loadAdminTokenMock()
}));

vi.mock("../lib/api", () => ({
  listRooms: () => listRoomsMock(),
  createRoom: (payload: unknown) => createRoomMock(payload)
}));

test("redirects to /admin/login when token is missing", () => {
  loadAdminTokenMock.mockReturnValue(null);
  window.history.pushState({}, "", "/admin");

  render(<AdminDashboardPage />);

  expect(window.location.pathname).toBe("/admin/login");
});

test("loads rooms and allows creating a room", async () => {
  loadAdminTokenMock.mockReturnValue("jwt-token");
  listRoomsMock.mockResolvedValue([{ id: 1, slug: "room-a", name: "Room A", model_name: "m", is_active: true }]);
  createRoomMock.mockResolvedValue({ id: 2, slug: "room-b", name: "Room B", model_name: "m", is_active: true });

  render(<AdminDashboardPage />);

  expect(await screen.findByText(/room a/i)).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText(/слаг/i), { target: { value: "room-b" } });
  fireEvent.change(screen.getByLabelText(/название/i), { target: { value: "Room B" } });
  fireEvent.click(screen.getByRole("button", { name: /создать комнату/i }));

  return waitFor(() => {
    expect(createRoomMock).toHaveBeenCalled();
  });
});
