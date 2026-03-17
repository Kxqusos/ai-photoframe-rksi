import React from "react";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { CapturePage } from "./CapturePage";

const listPromptsMock = vi.fn();
const createJobMock = vi.fn();
const playMock = vi.fn();

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function mockCameraReady() {
  const stopMock = vi.fn();
  Object.defineProperty(window.navigator, "mediaDevices", {
    configurable: true,
    value: {
      getUserMedia: vi.fn().mockResolvedValue({
        getTracks: () => [{ stop: stopMock }]
      })
    }
  });
  return { stopMock };
}

vi.mock("../lib/api", () => ({
  listRoomPrompts: (roomSlug: string) => listPromptsMock(roomSlug),
  createRoomJob: (roomSlug: string, photo: File, promptId: number) => createJobMock(roomSlug, photo, promptId)
}));

beforeEach(() => {
  vi.useRealTimers();
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
  playMock.mockReset();
  playMock.mockResolvedValue(undefined);
  Object.defineProperty(HTMLMediaElement.prototype, "play", {
    configurable: true,
    value: playMock
  });
  Object.defineProperty(HTMLMediaElement.prototype, "srcObject", {
    configurable: true,
    writable: true,
    value: null
  });
  Object.defineProperty(window.navigator, "mediaDevices", {
    configurable: true,
    value: undefined
  });
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    drawImage: vi.fn()
  })) as unknown as typeof HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.toBlob = vi.fn((callback) => {
    callback(new Blob(["photo"], { type: "image/jpeg" }));
  });
});

test("renders fullscreen camera preview with overlay capture button", async () => {
  render(<CapturePage roomSlug="aaaaaaaa" />);

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
  render(<CapturePage roomSlug="aaaaaaaa" />);
  expect(await screen.findByLabelText(/style selection/i)).toBeInTheDocument();
  expect(screen.queryByRole("combobox", { name: /style selection/i })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: /сделать фото/i })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /generate/i })).not.toBeInTheDocument();
  expect(screen.queryByLabelText(/upload photo/i)).not.toBeInTheDocument();
});

test("loads styles for current room slug", async () => {
  render(<CapturePage roomSlug="aaaaaaaa" />);
  await screen.findByRole("button", { name: /anime/i });
  expect(listPromptsMock).toHaveBeenCalledWith("aaaaaaaa");
});

test("shows loading state and camera unavailable feedback before resources are ready", async () => {
  const deferred = createDeferred<
    Array<{
      id: number;
      name: string;
      description: string;
      prompt: string;
      preview_image_url: string;
      icon_image_url: string;
    }>
  >();
  listPromptsMock.mockReturnValue(deferred.promise);

  render(<CapturePage roomSlug="aaaaaaaa" />);

  const controls = screen.getByLabelText(/capture controls/i);
  expect(
    within(controls).getByText(/загружаем стили/i, { selector: ".capture-screen__eyebrow" })
  ).toBeInTheDocument();
  expect(
    within(controls).getByText(/камера недоступна/i, { selector: ".capture-screen__state--warning" })
  ).toBeInTheDocument();
  expect(within(controls).getByRole("button", { name: /сделать фото/i })).toBeDisabled();
});

test("announces capture status changes for assistive technology", async () => {
  mockCameraReady();

  render(<CapturePage roomSlug="aaaaaaaa" />);

  const controls = screen.getByLabelText(/capture controls/i);
  const liveRegion = within(controls).getByRole("status");

  expect(liveRegion).toHaveAttribute("aria-live", "polite");
  expect(liveRegion).toHaveAttribute("aria-atomic", "true");
  await waitFor(() => {
    expect(
      within(controls).getByText(/готово к съемке/i, { selector: ".capture-screen__eyebrow" })
    ).toBeInTheDocument();
  });
  expect(liveRegion).toHaveTextContent(/готово к съемке/i);
  expect(liveRegion).not.toHaveTextContent(/камера готова/i);
});

test("shows selected style summary and ready state when camera is available", async () => {
  mockCameraReady();

  render(<CapturePage roomSlug="aaaaaaaa" />);

  const controls = screen.getByLabelText(/capture controls/i);
  await waitFor(() => {
    expect(
      within(controls).getByText(/готово к съемке/i, { selector: ".capture-screen__eyebrow" })
    ).toBeInTheDocument();
  });
  expect(within(controls).getByRole("heading", { name: "Anime" })).toBeInTheDocument();
  expect(within(controls).getByText("Soft anime shading")).toBeInTheDocument();
  expect(within(controls).queryByText(/камера готова/i)).not.toBeInTheDocument();
  expect(within(controls).queryByText(/стиль выбран/i)).not.toBeInTheDocument();
  expect(within(controls).queryByText(/стиль не выбран/i)).not.toBeInTheDocument();
  await waitFor(() => {
    expect(within(controls).getByRole("button", { name: /сделать фото/i })).toBeEnabled();
  });
});

test("shows missing styles state when room has no prompts", async () => {
  mockCameraReady();
  listPromptsMock.mockResolvedValue([]);

  render(<CapturePage roomSlug="aaaaaaaa" />);

  const controls = screen.getByLabelText(/capture controls/i);
  const stylesPanel = await screen.findByLabelText(/style selection/i);
  await waitFor(() => {
    expect(
      within(controls).getByText(/для этой комнаты пока нет стилей/i, { selector: ".capture-screen__state" })
    ).toBeInTheDocument();
    expect(
      within(stylesPanel).getByText(/для этой комнаты пока нет стилей/i, {
        selector: ".capture-screen__styles-empty"
      })
    ).toBeInTheDocument();
  });
  expect(screen.getByRole("button", { name: /сделать фото/i })).toBeDisabled();
});

test("blocks capture while next room styles are loading and uses the new prompt id after rerender", async () => {
  vi.useFakeTimers();
  mockCameraReady();
  const nextRoomStyles = createDeferred<
    Array<{
      id: number;
      name: string;
      description: string;
      prompt: string;
      preview_image_url: string;
      icon_image_url: string;
    }>
  >();
  const createJobDeferred = createDeferred<{ id: string }>();
  createJobMock.mockReturnValue(createJobDeferred.promise);
  listPromptsMock.mockImplementation((slug: string) => {
    if (slug === "aaaaaaaa") {
      return Promise.resolve([
        {
          id: 1,
          name: "Anime",
          description: "Soft anime shading",
          prompt: "Turn input photo into anime portrait",
          preview_image_url: "/media/previews/anime.jpg",
          icon_image_url: "/media/icons/anime.png"
        }
      ]);
    }

    return nextRoomStyles.promise;
  });

  const { rerender } = render(<CapturePage roomSlug="aaaaaaaa" />);
  await act(async () => {});

  const video = document.querySelector("video");
  if (!video) {
    throw new Error("video element not found");
  }
  Object.defineProperty(video, "videoWidth", { configurable: true, value: 1280 });
  Object.defineProperty(video, "videoHeight", { configurable: true, value: 720 });

  const controls = screen.getByLabelText(/capture controls/i);
  expect(within(controls).getByRole("button", { name: /сделать фото/i })).toBeEnabled();

  rerender(<CapturePage roomSlug="bbbbbbbb" />);

  expect(
    within(controls).getByText(/загружаем стили/i, { selector: ".capture-screen__eyebrow" })
  ).toBeInTheDocument();
  expect(within(controls).getByRole("button", { name: /сделать фото/i })).toBeDisabled();

  await act(async () => {
    nextRoomStyles.resolve([
      {
        id: 9,
        name: "Cyber",
        description: "Neon portrait lighting",
        prompt: "Turn input photo into cyber portrait",
        preview_image_url: "/media/previews/cyber.jpg",
        icon_image_url: "/media/icons/cyber.png"
      }
    ]);
  });

  await act(async () => {});

  expect(within(controls).getByRole("heading", { name: "Cyber" })).toBeInTheDocument();
  expect(within(controls).getByRole("button", { name: /сделать фото/i })).toBeEnabled();

  fireEvent.click(within(controls).getByRole("button", { name: /сделать фото/i }));

  await act(async () => {
    await vi.advanceTimersByTimeAsync(3000);
  });

  expect(createJobMock).toHaveBeenCalledWith("bbbbbbbb", expect.any(File), 9);
});

test("shows countdown and generation state while creating a photo job", async () => {
  vi.useFakeTimers();
  mockCameraReady();
  const createJobDeferred = createDeferred<{ id: string }>();
  createJobMock.mockReturnValue(createJobDeferred.promise);

  render(<CapturePage roomSlug="aaaaaaaa" />);

  await act(async () => {});
  const button = screen.getByRole("button", { name: /сделать фото/i });
  expect(button).toBeEnabled();

  const video = document.querySelector("video");
  if (!video) {
    throw new Error("video element not found");
  }
  Object.defineProperty(video, "videoWidth", { configurable: true, value: 1280 });
  Object.defineProperty(video, "videoHeight", { configurable: true, value: 720 });

  fireEvent.click(button);
  expect(screen.getByText("3")).toBeInTheDocument();
  expect(
    within(screen.getByLabelText(/capture controls/i)).getByText(/таймер съёмки/i, {
      selector: ".capture-screen__eyebrow"
    })
  ).toBeInTheDocument();

  await act(async () => {
    await vi.advanceTimersByTimeAsync(3000);
  });

  expect(createJobMock).toHaveBeenCalledWith("aaaaaaaa", expect.any(File), 1);
  expect(
    within(screen.getByLabelText(/capture controls/i)).getByText(/генерируем кадр/i, {
      selector: ".capture-screen__eyebrow"
    })
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /генерация/i })).toBeDisabled();
});
