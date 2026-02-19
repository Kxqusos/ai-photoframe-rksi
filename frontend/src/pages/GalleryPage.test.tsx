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

test("renders duplicated image set for seamless circular scrolling", async () => {
  listGalleryResultsMock.mockResolvedValueOnce([
    { name: "loop-a.jpg", url: "/media/results/loop-a.jpg", modified_at: 20 },
    { name: "loop-b.jpg", url: "/media/results/loop-b.jpg", modified_at: 10 }
  ]);

  render(<GalleryPage />);

  await act(async () => {
    await Promise.resolve();
  });

  const groups = screen.getAllByTestId("gallery-masonry-group");
  expect(groups).toHaveLength(2);

  expect(within(groups[0]).getAllByAltText("loop-a.jpg")).toHaveLength(1);
  expect(within(groups[0]).getAllByAltText("loop-b.jpg")).toHaveLength(1);
  expect(within(groups[1]).getAllByAltText("loop-a.jpg")).toHaveLength(1);
  expect(within(groups[1]).getAllByAltText("loop-b.jpg")).toHaveLength(1);
});
