import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { StylesPage } from "./StylesPage";

const listPromptsMock = vi.fn();

vi.mock("../lib/api", () => ({
  listPrompts: () => listPromptsMock()
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
    },
    {
      id: 2,
      name: "Comic",
      description: "Comic style",
      prompt: "Turn image into comic",
      preview_image_url: "/media/previews/comic.jpg",
      icon_image_url: "/media/icons/comic.png"
    }
  ]);
});

test("renders style catalog and allows selecting a style", async () => {
  render(<StylesPage />);

  expect(await screen.findByRole("heading", { name: /выберите стиль/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /anime/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /comic/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /comic/i }));
  expect(screen.getByRole("button", { name: /выбрать стиль и вернуться/i })).toBeInTheDocument();
});
