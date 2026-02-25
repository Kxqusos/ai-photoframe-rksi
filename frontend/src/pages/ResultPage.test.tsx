import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { ResultPage } from "./ResultPage";

const getJobStatusMock = vi.fn();

vi.mock("../lib/api", () => ({
  getRoomJobStatus: (roomSlug: string, jpgHash: string) => getJobStatusMock(roomSlug, jpgHash)
}));

test("shows generated image and qr code when job completes", async () => {
  getJobStatusMock.mockResolvedValue({
    id: 77,
    status: "completed",
    result_url: "/qr/abc123",
    download_url: "/qr/abc123",
    qr_url: "/api/jobs/77/qr"
  });

  render(<ResultPage roomSlug="room-a" jpgHash="77" />);

  expect(getJobStatusMock).toHaveBeenCalledWith("room-a", "77");

  expect(await screen.findByAltText(/generated photo/i)).toBeInTheDocument();
  expect(screen.getByRole("main")).toHaveTextContent("Результат");
  expect(screen.getByText(/сканируйте qr-код/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /назад/i })).toBeInTheDocument();
  expect(screen.getAllByRole("link", { name: /скачать фото/i })).toHaveLength(1);
  expect(screen.queryByText(/^скачать фото$/i)).not.toBeInTheDocument();
  expect(screen.getByAltText(/download qr/i)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /продолжить/i })).not.toBeInTheDocument();
});

test("shows smooth indeterminate progress bar while image is processing", async () => {
  getJobStatusMock.mockResolvedValue({
    id: 77,
    status: "processing"
  });

  render(<ResultPage roomSlug="room-a" jpgHash="77" />);

  expect(await screen.findByText(/обработка изображения/i)).toBeInTheDocument();
  const progress = document.querySelector(".result-loading-bar__progress--indeterminate");
  expect(progress).toBeInTheDocument();
});
