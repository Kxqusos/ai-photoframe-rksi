import React from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { CapturePage } from "./CapturePage";

const listPromptsMock = vi.fn();
const createJobMock = vi.fn();

vi.mock("../lib/api", () => ({
  listRoomPrompts: (roomSlug: string) => listPromptsMock(roomSlug),
  createRoomJob: (roomSlug: string, photo: File, promptId: number) => createJobMock(roomSlug, photo, promptId)
}));

beforeEach(() => {
  listPromptsMock.mockResolvedValue([
    {
      id: 1,
      name: "Anime",
      description: "Soft anime shading",
      prompt: "Turn input photo into anime portrait",
      preview_image_url: "/media/previews/anime.jpg",
      icon_image_url: "/media/icons/anime.png"
    }
  ]);
  createJobMock.mockReset();
});

test("renders fullscreen camera preview with overlay capture button", async () => {
  render(<CapturePage roomSlug="room-a" />);

  expect(screen.getByLabelText(/camera preview/i)).toHaveClass("capture-screen");
  expect(screen.getByTestId("camera-preview")).toHaveClass("capture-screen__preview");
  expect(screen.getByRole("button", { name: /сделать фото/i })).toBeInTheDocument();
  const stylesPanel = await screen.findByLabelText(/style selection/i);
  expect(stylesPanel).toHaveClass("capture-screen__styles-panel");
  expect(screen.getByTestId("camera-preview")).not.toContainElement(stylesPanel);
  expect(screen.getByRole("button", { name: /anime/i })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /каталог стилей/i })).not.toBeInTheDocument();
  expect(screen.queryByText("AI Photoframe")).not.toBeInTheDocument();
});

test("shows camera capture button instead of upload input", async () => {
  render(<CapturePage roomSlug="room-a" />);
  expect(await screen.findByLabelText(/style selection/i)).toBeInTheDocument();
  expect(screen.queryByRole("combobox", { name: /style selection/i })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: /сделать фото/i })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /generate/i })).not.toBeInTheDocument();
  expect(screen.queryByLabelText(/upload photo/i)).not.toBeInTheDocument();
});

test("loads styles for current room slug", async () => {
  render(<CapturePage roomSlug="room-a" />);
  await screen.findByRole("button", { name: /anime/i });
  expect(listPromptsMock).toHaveBeenCalledWith("room-a");
});
