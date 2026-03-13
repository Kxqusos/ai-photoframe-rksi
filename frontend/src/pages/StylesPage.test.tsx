import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

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
  expect(screen.getByText(/готово к съемке/i)).toBeInTheDocument();
  expect(screen.getByRole("heading", { level: 2, name: "Anime" })).toBeInTheDocument();
  expect(screen.getByText("Soft anime shading", { selector: ".styles-footer__selected" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /comic/i }));
  expect(screen.getByRole("heading", { level: 2, name: "Comic" })).toBeInTheDocument();
  expect(screen.getByText("Comic style", { selector: ".styles-footer__selected" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /выбрать стиль и вернуться/i })).toBeEnabled();
});

test("shows empty state when no styles are available", async () => {
  listPromptsMock.mockResolvedValue([]);

  render(<StylesPage />);

  expect(await screen.findByText(/пока нет стилей для выбора/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /выбрать стиль и вернуться/i })).toBeDisabled();
});

test("shows loading state before styles resolve without flashing empty state", () => {
  listPromptsMock.mockReturnValue(new Promise(() => undefined));

  render(<StylesPage />);

  expect(screen.getByText(/загружаем стили/i)).toBeInTheDocument();
  expect(screen.queryByText(/пока нет стилей для выбора/i)).not.toBeInTheDocument();
});

test("shows error state when styles fail to load", async () => {
  listPromptsMock.mockRejectedValue(new Error("boom"));

  render(<StylesPage />);

  expect(await screen.findByRole("alert")).toHaveTextContent(/не удалось загрузить стили/i);
});
