import React from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import { ResultPage } from "./ResultPage";

const getJobStatusMock = vi.fn();

vi.mock("../lib/api", () => ({
  getJobStatus: (jpgHash: string) => getJobStatusMock(jpgHash)
}));

beforeEach(() => {
  getJobStatusMock.mockReset();
});

test("shows generated image and qr code when job completes", async () => {
  window.history.pushState({}, "", "/result/abcdef1234567890");
  getJobStatusMock.mockResolvedValue({
    id: 77,
    status: "completed",
    result_url: "/qr/abc123",
    download_url: "/qr/abc123",
    qr_url: "/api/jobs/77/qr"
  });

  render(<ResultPage />);

  expect(await screen.findByAltText(/сгенерированное фото/i)).toBeInTheDocument();
  expect(getJobStatusMock).toHaveBeenCalledWith("abcdef1234567890");
  expect(screen.getByRole("main")).toHaveTextContent("Результат");
  expect(screen.getByText(/сканируйте qr-код/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /назад/i })).toBeInTheDocument();
  expect(screen.getAllByRole("link", { name: /скачать фото/i })).toHaveLength(1);
  expect(screen.queryByText(/^скачать фото$/i)).not.toBeInTheDocument();
  expect(screen.getByAltText(/qr-код для скачивания/i)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /продолжить/i })).not.toBeInTheDocument();
});

test("shows smooth indeterminate progress bar while image is processing", async () => {
  window.history.pushState({}, "", "/result/abcdef1234567890");
  getJobStatusMock.mockResolvedValue({
    id: 77,
    status: "processing"
  });

  render(<ResultPage />);

  expect(await screen.findByText(/обработка изображения/i)).toBeInTheDocument();
  const progress = document.querySelector(".result-loading-bar__progress--indeterminate");
  expect(progress).toBeInTheDocument();
});
