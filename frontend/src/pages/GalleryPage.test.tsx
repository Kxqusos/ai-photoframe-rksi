import React from "react";
import { act, render, screen, within } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { GalleryPage } from "./GalleryPage";

const listGalleryResultsMock = vi.fn();

vi.mock("../lib/api", () => ({
  listGalleryResults: () => listGalleryResultsMock()
}));

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal("requestAnimationFrame", vi.fn(() => 1));
  vi.stubGlobal("cancelAnimationFrame", vi.fn());
  listGalleryResultsMock.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

test("renders masonry gallery and appends new images from polling", async () => {
  listGalleryResultsMock
    .mockResolvedValueOnce([
      { name: "first.jpg", url: "/media/results/first.jpg", modified_at: 10 }
    ])
    .mockResolvedValueOnce([
      { name: "second.jpg", url: "/media/results/second.jpg", modified_at: 20 },
      { name: "first.jpg", url: "/media/results/first.jpg", modified_at: 10 }
    ]);

  render(<GalleryPage />);

  await act(async () => {
    await Promise.resolve();
  });

  expect(screen.getAllByAltText("first.jpg")).toHaveLength(2);

  await act(async () => {
    await vi.advanceTimersByTimeAsync(5000);
  });

  expect(screen.getAllByAltText("second.jpg")).toHaveLength(2);
  expect(listGalleryResultsMock).toHaveBeenCalledTimes(2);
});

test("renders one continuous masonry stream with duplicated cards for looping", async () => {
  listGalleryResultsMock.mockResolvedValueOnce([
    { name: "loop-a.jpg", url: "/media/results/loop-a.jpg", modified_at: 20 },
    { name: "loop-b.jpg", url: "/media/results/loop-b.jpg", modified_at: 10 }
  ]);

  render(<GalleryPage />);

  await act(async () => {
    await Promise.resolve();
  });

  const groups = screen.getAllByTestId("gallery-masonry-group");
  expect(groups).toHaveLength(1);

  const cards = within(groups[0]).getAllByRole("img");
  expect(cards).toHaveLength(4);
  expect(within(groups[0]).getAllByAltText("loop-a.jpg")).toHaveLength(2);
  expect(within(groups[0]).getAllByAltText("loop-b.jpg")).toHaveLength(2);
});

test("keeps auto scroll moving when browser stores scrollTop as integer", async () => {
  listGalleryResultsMock.mockResolvedValueOnce([
    { name: "loop-a.jpg", url: "/media/results/loop-a.jpg", modified_at: 20 },
    { name: "loop-b.jpg", url: "/media/results/loop-b.jpg", modified_at: 10 }
  ]);

  let rafCallback: FrameRequestCallback | null = null;
  vi.stubGlobal(
    "requestAnimationFrame",
    vi.fn((callback: FrameRequestCallback) => {
      rafCallback = callback;
      return 1;
    })
  );

  render(<GalleryPage />);

  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });

  const container = screen.getByLabelText("gallery auto scroll");
  const track = container.querySelector(".gallery-track");
  expect(track).not.toBeNull();

  Object.defineProperty(container, "clientHeight", {
    configurable: true,
    value: 300
  });
  Object.defineProperty(track, "scrollHeight", {
    configurable: true,
    value: 1000
  });

  let scrollTopValue = 0;
  Object.defineProperty(container, "scrollTop", {
    configurable: true,
    get: () => scrollTopValue,
    set: (next: number) => {
      scrollTopValue = Math.floor(next);
    }
  });

  await act(async () => {
    for (const timestamp of [0, 16, 32, 48, 64, 80, 96]) {
      rafCallback?.(timestamp);
    }
  });

  expect(scrollTopValue).toBeGreaterThan(0);
});

test("renders gallery without title header and keeps auto-scroll container", async () => {
  listGalleryResultsMock.mockResolvedValueOnce([
    { name: "photo.jpg", url: "/media/results/photo.jpg", modified_at: 10 }
  ]);

  render(<GalleryPage />);

  await act(async () => {
    await Promise.resolve();
  });

  expect(screen.queryByRole("heading", { name: "Галерея" })).not.toBeInTheDocument();
  expect(screen.getByLabelText("gallery auto scroll")).toBeInTheDocument();
});

test("applies mixed size variants to gallery cards", async () => {
  listGalleryResultsMock.mockResolvedValueOnce([
    { name: "photo-1.jpg", url: "/media/results/photo-1.jpg", modified_at: 60 },
    { name: "photo-2.jpg", url: "/media/results/photo-2.jpg", modified_at: 50 },
    { name: "photo-3.jpg", url: "/media/results/photo-3.jpg", modified_at: 40 },
    { name: "photo-4.jpg", url: "/media/results/photo-4.jpg", modified_at: 30 },
    { name: "photo-5.jpg", url: "/media/results/photo-5.jpg", modified_at: 20 },
    { name: "photo-6.jpg", url: "/media/results/photo-6.jpg", modified_at: 10 }
  ]);

  render(<GalleryPage />);

  await act(async () => {
    await Promise.resolve();
  });

  const primaryGroup = screen.getAllByTestId("gallery-masonry-group")[0];
  const cards = Array.from(primaryGroup.querySelectorAll(".gallery-card"));
  const variantNames = new Set(
    cards
      .map((card) => Array.from(card.classList).find((name) => name.startsWith("gallery-card--")))
      .filter((name): name is string => Boolean(name))
  );

  expect(variantNames.size).toBeGreaterThanOrEqual(3);
});
