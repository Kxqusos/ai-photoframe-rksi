import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
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
    },
    {
      id: 2,
      name: "Ghibli",
      description: "Watercolor palette and film grain inspired by classic animation aesthetics",
      prompt: "Turn input photo into ghibli portrait",
      preview_image_url: "/media/previews/ghibli.jpg",
      icon_image_url: "/media/icons/ghibli.png"
    }
  ]);
  createJobMock.mockReset();
});

test("renders fullscreen camera preview with overlay capture button", async () => {
  render(<CapturePage />);

  expect(screen.getByLabelText(/предпросмотр камеры/i)).toHaveClass("capture-screen");
  expect(screen.getByRole("heading", { name: /создайте стильный снимок/i })).toBeInTheDocument();
  expect(screen.getByText(/выберите стиль и сделайте фото без спешки/i)).toBeInTheDocument();
  expect(screen.getByTestId("camera-preview")).toHaveClass("capture-screen__preview");
  expect(screen.getByRole("button", { name: /сделать фото/i })).toBeInTheDocument();
  const menuButton = screen.getByRole("button", { name: /открыть меню стилей/i });
  expect(menuButton).toBeInTheDocument();
  expect(screen.queryByLabelText(/меню выбора стиля/i)).not.toBeInTheDocument();

  fireEvent.click(menuButton);

  const stylesPanel = await screen.findByLabelText(/меню выбора стиля/i);
  expect(stylesPanel).toHaveClass("capture-screen__styles-panel");
  expect(stylesPanel).toHaveClass("capture-screen__styles-panel--dropdown");
  expect(screen.queryByText(/выбран:/i)).not.toBeInTheDocument();
  expect(screen.getByText(/выберите стиль перед съемкой/i)).toBeInTheDocument();
  expect(screen.getByText("Выбран", { selector: ".capture-style-item__selected-badge" })).toBeInTheDocument();
  expect(screen.getByTestId("camera-preview")).not.toContainElement(stylesPanel);
  expect(screen.getByRole("button", { name: /anime/i })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /каталог стилей/i })).not.toBeInTheDocument();
  expect(screen.queryByText("AI Photoframe")).not.toBeInTheDocument();
});

test("renders style previews without crop helper classes and full description marker", async () => {
  render(<CapturePage />);
  fireEvent.click(screen.getByRole("button", { name: /открыть меню стилей/i }));

  const firstPreview = await screen.findByRole("img", { name: /anime превью/i });
  expect(firstPreview).toHaveClass("capture-style-item__preview--fit");

  const longDescription = screen.getByText(
    "Watercolor palette and film grain inspired by classic animation aesthetics"
  );
  expect(longDescription).toHaveClass("capture-style-item__description--expanded");
  expect(longDescription).toHaveAttribute("lang", "ru");
});

test("shows camera capture button instead of upload input", async () => {
  render(<CapturePage />);
  expect(screen.getByRole("button", { name: /открыть меню стилей/i })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /открыть меню стилей/i }));
  expect(await screen.findByLabelText(/меню выбора стиля/i)).toBeInTheDocument();
  expect(screen.queryByRole("combobox", { name: /меню выбора стиля/i })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: /сделать фото/i })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /generate/i })).not.toBeInTheDocument();
  expect(screen.queryByLabelText(/upload photo/i)).not.toBeInTheDocument();
});

test("switches selected style badge when selecting another style", async () => {
  render(<CapturePage />);
  fireEvent.click(screen.getByRole("button", { name: /открыть меню стилей/i }));

  const animeButton = await screen.findByRole("button", { name: /anime/i });
  const ghibliButton = screen.getByRole("button", { name: /ghibli/i });
  expect(animeButton).toHaveClass("is-selected");
  expect(ghibliButton).not.toHaveClass("is-selected");

  fireEvent.click(ghibliButton);

  expect(screen.queryByLabelText(/меню выбора стиля/i)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /открыть меню стилей/i }));

  const selectedGhibliButton = await screen.findByRole("button", { name: /ghibli/i });
  const unselectedAnimeButton = screen.getByRole("button", { name: /anime/i });
  expect(selectedGhibliButton).toHaveClass("is-selected");
  expect(unselectedAnimeButton).not.toHaveClass("is-selected");
  expect(screen.queryByText(/выбран:/i)).not.toBeInTheDocument();
  expect(screen.getByText("Выбран", { selector: ".capture-style-item__selected-badge" })).toBeInTheDocument();
});
