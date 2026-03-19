import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { PublicLandingPage } from "./PublicLandingPage";

const listPublicRoomsMock = vi.fn();
const accessRoomMock = vi.fn();
const navigateToMock = vi.fn();
const saveRoomAccessTokenMock = vi.fn();

vi.mock("../lib/api", () => ({
  listPublicRooms: () => listPublicRoomsMock(),
  accessRoom: (roomSlug: string, password: string) => accessRoomMock(roomSlug, password)
}));

vi.mock("../lib/navigation", () => ({
  navigateTo: (path: string) => navigateToMock(path)
}));

vi.mock("../lib/roomAccess", () => ({
  saveRoomAccessToken: (roomSlug: string, token: string) => saveRoomAccessTokenMock(roomSlug, token)
}));

beforeEach(() => {
  listPublicRoomsMock.mockReset();
  accessRoomMock.mockReset();
  navigateToMock.mockReset();
  saveRoomAccessTokenMock.mockReset();
});

test("loads rooms and unlocks selected room with password", async () => {
  listPublicRoomsMock.mockResolvedValue([
    { id: 1, slug: "ph000000", name: "Main" },
    { id: 2, slug: "aaaaaaaa", name: "Room A" }
  ]);
  accessRoomMock.mockResolvedValue({ access_token: "room-token", token_type: "bearer" });

  render(<PublicLandingPage />);

  expect(await screen.findByRole("button", { name: /room a/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /room a/i }));
  fireEvent.change(screen.getByLabelText(/пароль комнаты/i), { target: { value: "room-a-pass" } });
  fireEvent.click(screen.getByRole("button", { name: /открыть комнату/i }));

  await waitFor(() => {
    expect(accessRoomMock).toHaveBeenCalledWith("aaaaaaaa", "room-a-pass");
    expect(saveRoomAccessTokenMock).toHaveBeenCalledWith("aaaaaaaa", "room-token");
    expect(navigateToMock).toHaveBeenCalledWith("/aaaaaaaa");
  });
});

test("allows opening selected room gallery from the landing page", async () => {
  listPublicRoomsMock.mockResolvedValue([
    { id: 1, slug: "ph000000", name: "Main" },
    { id: 2, slug: "aaaaaaaa", name: "Room A" }
  ]);
  accessRoomMock.mockResolvedValue({ access_token: "room-token", token_type: "bearer" });

  render(<PublicLandingPage />);

  expect(await screen.findByRole("button", { name: /room a/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /room a/i }));
  fireEvent.click(screen.getByRole("button", { name: /галерея/i }));
  fireEvent.change(screen.getByLabelText(/пароль комнаты/i), { target: { value: "room-a-pass" } });
  fireEvent.click(screen.getByRole("button", { name: /открыть комнату/i }));

  await waitFor(() => {
    expect(navigateToMock).toHaveBeenCalledWith("/aaaaaaaa/gallery");
  });
});

test("separates room selection from the access controls instead of nesting both inside one inner box", async () => {
  listPublicRoomsMock.mockResolvedValue([
    { id: 1, slug: "ph000000", name: "Main" },
    { id: 2, slug: "aaaaaaaa", name: "Room A" }
  ]);

  const { container } = render(<PublicLandingPage />);

  expect(await screen.findByRole("button", { name: /room a/i })).toBeInTheDocument();
  expect(container.querySelector(".public-landing-page__content")).not.toBeNull();
  expect(screen.getByLabelText(/список комнат/i)).toHaveClass("public-landing-page__rooms");
  expect(screen.getByLabelText(/настройки входа/i)).toHaveClass("public-landing-page__form");
});

test("integrates the admin login action into the landing panel instead of leaving it in a detached top strip", async () => {
  listPublicRoomsMock.mockResolvedValue([{ id: 1, slug: "ph000000", name: "Main" }]);

  const { container } = render(<PublicLandingPage />);

  expect(await screen.findByRole("button", { name: /главная/i })).toBeInTheDocument();
  const panelHead = container.querySelector(".public-landing-page__panel-head");
  expect(panelHead).not.toBeNull();
  expect(panelHead).toContainElement(screen.getByRole("link", { name: /вход/i }));
});

test("navigates to the explicit default-room slug instead of keeping root", async () => {
  listPublicRoomsMock.mockResolvedValue([{ id: 1, slug: "ph000000", name: "Main" }]);
  accessRoomMock.mockResolvedValue({ access_token: "room-token", token_type: "bearer" });

  render(<PublicLandingPage initialRoomSlug="ph000000" />);

  expect(await screen.findByRole("button", { name: /главная/i })).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText(/пароль комнаты/i), { target: { value: "main-pass" } });
  fireEvent.click(screen.getByRole("button", { name: /открыть комнату/i }));

  await waitFor(() => {
    expect(navigateToMock).toHaveBeenCalledWith("/ph000000");
  });
});
