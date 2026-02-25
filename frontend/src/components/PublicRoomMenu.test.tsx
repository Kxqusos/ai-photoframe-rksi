import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import { PublicRoomMenu } from "./PublicRoomMenu";

const listPublicRoomsMock = vi.fn();
const navigateToMock = vi.fn();

vi.mock("../lib/api", () => ({
  listPublicRooms: () => listPublicRoomsMock()
}));

vi.mock("../lib/navigation", () => ({
  navigateTo: (path: string) => navigateToMock(path)
}));

beforeEach(() => {
  listPublicRoomsMock.mockReset();
  navigateToMock.mockReset();
});

test("opens dropdown menu from three-lines button and navigates to selected room", async () => {
  listPublicRoomsMock.mockResolvedValue([
    { id: 1, slug: "main", name: "Main" },
    { id: 2, slug: "room-a", name: "Room A" }
  ]);

  render(<PublicRoomMenu currentRoomSlug="main" />);

  expect(screen.getByRole("button", { name: "Меню" })).toBeInTheDocument();
  expect(screen.queryByLabelText("Комната")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Меню" }));

  await waitFor(() => {
    expect(screen.getByRole("option", { name: "Room A" })).toBeInTheDocument();
  });

  fireEvent.change(screen.getByLabelText("Комната"), { target: { value: "room-a" } });
  expect(navigateToMock).toHaveBeenCalledWith("/room-a");
});
