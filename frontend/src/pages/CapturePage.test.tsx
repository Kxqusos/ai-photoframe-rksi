import React from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { CapturePage } from "./CapturePage";

const listPromptsMock = vi.fn();
const createJobMock = vi.fn();

vi.mock("../lib/api", () => ({
  listPrompts: () => listPromptsMock(),
  createJob: (photo: File, promptId: number) => createJobMock(photo, promptId)
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
  render(<CapturePage />);

  expect(screen.getByLabelText(/camera preview/i)).toHaveClass("capture-screen");
  expect(screen.getByRole("button", { name: /сделать фото/i })).toBeInTheDocument();
  expect(await screen.findByLabelText(/style selection/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /каталог стилей/i })).toBeInTheDocument();
  expect(screen.queryByText("AI Photoframe")).not.toBeInTheDocument();
});

test("shows camera capture button instead of upload input", async () => {
  render(<CapturePage />);
  expect(await screen.findByLabelText(/style selection/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /сделать фото/i })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /generate/i })).not.toBeInTheDocument();
  expect(screen.queryByLabelText(/upload photo/i)).not.toBeInTheDocument();
});
