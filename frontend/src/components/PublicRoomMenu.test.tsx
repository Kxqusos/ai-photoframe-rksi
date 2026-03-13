import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  window.history.pushState({}, "", "/");
});

test("opens dropdown menu from three-lines button and navigates to selected room", async () => {
  listPublicRoomsMock.mockResolvedValue([
    { id: 1, slug: "ph000000", name: "Main" },
    { id: 2, slug: "aaaaaaaa", name: "Room A" }
  ]);

  render(<PublicRoomMenu currentRoomSlug="ph000000" />);

  expect(screen.getByRole("button", { name: "Меню" })).toBeInTheDocument();
  expect(screen.queryByLabelText("Комната")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Меню" }));

  await waitFor(() => {
    expect(screen.getByRole("option", { name: "Room A" })).toBeInTheDocument();
  });
  expect(screen.getByText("Текущая комната")).toBeInTheDocument();
  expect(screen.getByText("Главная", { selector: ".public-room-menu__room-name" })).toBeInTheDocument();
  const roomPanel = screen.getByText("Главная", { selector: ".public-room-menu__room-name" }).closest(".public-room-menu__room-panel");
  expect(roomPanel).toBeTruthy();
  expect(within(roomPanel as HTMLElement).getByLabelText("Комната")).toBe(screen.getByLabelText("Комната"));
  expect(screen.getByRole("link", { name: "Съемка" })).toHaveAttribute("href", "/ph000000");
  expect(screen.getByRole("link", { name: "Галерея" })).toHaveAttribute("href", "/ph000000/gallery");

  fireEvent.change(screen.getByLabelText("Комната"), { target: { value: "aaaaaaaa" } });
  expect(navigateToMock).toHaveBeenCalledWith("/aaaaaaaa");
});

test("updates active section highlight after route change within the same room", async () => {
  listPublicRoomsMock.mockResolvedValue([{ id: 1, slug: "ph000000", name: "Main" }]);
  window.history.pushState({}, "", "/ph000000");

  const { rerender } = render(<PublicRoomMenu currentRoomSlug="ph000000" />);

  fireEvent.click(screen.getByRole("button", { name: "Меню" }));

  await waitFor(() => {
    expect(screen.getByRole("link", { name: "Съемка" })).toHaveAttribute("aria-current", "page");
  });
  expect(screen.getByRole("link", { name: "Галерея" })).not.toHaveAttribute("aria-current");

  window.history.pushState({}, "", "/ph000000/gallery");
  rerender(<PublicRoomMenu currentRoomSlug="ph000000" />);

  expect(screen.getByRole("link", { name: "Галерея" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByRole("link", { name: "Съемка" })).not.toHaveAttribute("aria-current");
});

test("shows API room name for non-default rooms and clears section highlight on result routes", async () => {
  listPublicRoomsMock.mockResolvedValue([{ id: 2, slug: "aaaaaaaa", name: "Room A" }]);
  window.history.pushState({}, "", "/aaaaaaaa/result/abcd1234");

  render(<PublicRoomMenu currentRoomSlug="aaaaaaaa" />);

  fireEvent.click(screen.getByRole("button", { name: "Меню" }));

  await waitFor(() => {
    expect(screen.getByText("Room A", { selector: ".public-room-menu__room-name" })).toBeInTheDocument();
  });
  expect(screen.getByText("Room A", { selector: ".public-room-menu__toggle-room" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Съемка" })).not.toHaveAttribute("aria-current");
  expect(screen.getByRole("link", { name: "Галерея" })).not.toHaveAttribute("aria-current");
});
