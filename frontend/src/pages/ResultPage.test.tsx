import React from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

import { ResultPage } from "./ResultPage";

const getJobStatusMock = vi.fn();

vi.mock("../lib/api", () => ({
  getRoomJobStatus: (roomSlug: string, jpgHash: string) => getJobStatusMock(roomSlug, jpgHash)
}));

beforeEach(() => {
  getJobStatusMock.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

test("shows intentional loading copy and stable placeholder while image is processing", async () => {
  getJobStatusMock.mockResolvedValue({
    id: "dddddddd",
    status: "processing"
  });

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  expect(await screen.findByText(/собираем ваш финальный кадр/i)).toBeInTheDocument();
  expect(screen.getByText(/обычно это занимает меньше минуты/i)).toBeInTheDocument();
  expect(screen.getByTestId("result-loading-preview")).toBeInTheDocument();
  const progress = document.querySelector(".result-loading-bar__progress--indeterminate");
  expect(progress).toBeInTheDocument();
});

test("shows download call to action as the next step when job completes", async () => {
  getJobStatusMock.mockResolvedValue({
    id: "dddddddd",
    status: "completed",
    result_url: "/qr/dddddddd",
    download_url: "/qr/dddddddd",
    qr_url: "/api/jobs/hash/dddddddd/qr"
  });

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  expect(getJobStatusMock).toHaveBeenCalledWith("aaaaaaaa", "dddddddd");

  expect(await screen.findByAltText(/generated photo/i)).toBeInTheDocument();
  expect(screen.getByRole("main")).toHaveTextContent("Результат готов");
  expect(screen.getByRole("heading", { name: /скачайте фото/i })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /открыть ссылку для скачивания/i })).toHaveAttribute(
    "href",
    "/qr/dddddddd"
  );
  expect(screen.getByText(/или отсканируйте qr-код камерой телефона/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /назад/i })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /скачать фото через qr-код/i })).toBeInTheDocument();
  expect(screen.getByAltText(/download qr/i)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /продолжить/i })).not.toBeInTheDocument();
});

test("shows recovery state when completed result image cannot be loaded", async () => {
  getJobStatusMock.mockResolvedValue({
    id: "dddddddd",
    status: "completed",
    result_url: "/qr/dddddddd",
    download_url: "/qr/dddddddd",
    qr_url: "/api/jobs/hash/dddddddd/qr"
  });

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  const image = await screen.findByAltText(/generated photo/i);
  fireEvent.error(image);

  expect(await screen.findByRole("alert")).toHaveTextContent("Не удалось загрузить готовое фото");
  expect(screen.getByRole("button", { name: /вернуться и снять заново/i })).toBeInTheDocument();
});

test("shows visible recovery route when generation fails", async () => {
  getJobStatusMock.mockResolvedValue({
    id: "dddddddd",
    status: "error",
    error_message: "Сервис временно недоступен"
  });

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  expect(await screen.findByRole("alert")).toHaveTextContent("Сервис временно недоступен");
  expect(screen.getByRole("heading", { name: /не получилось завершить обработку/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /вернуться и снять заново/i })).toBeInTheDocument();
});

test("recovers from a transient polling failure when a later poll succeeds", async () => {
  vi.useFakeTimers();
  getJobStatusMock
    .mockRejectedValueOnce(new Error("Сеть недоступна"))
    .mockResolvedValueOnce({
      id: "dddddddd",
      status: "processing"
    });

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  await act(async () => {
    await Promise.resolve();
  });

  expect(screen.getByRole("alert")).toHaveTextContent("Сеть недоступна");

  await act(async () => {
    await vi.advanceTimersByTimeAsync(1500);
  });

  expect(screen.getByText(/собираем ваш финальный кадр/i)).toBeInTheDocument();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

test("stops polling after the job reaches a completed terminal state", async () => {
  vi.useFakeTimers();
  getJobStatusMock.mockResolvedValue({
    id: "dddddddd",
    status: "completed",
    result_url: "/qr/dddddddd",
    download_url: "/qr/dddddddd",
    qr_url: "/api/jobs/hash/dddddddd/qr"
  });

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  await act(async () => {
    await Promise.resolve();
  });

  expect(screen.getByText(/результат готов/i)).toBeInTheDocument();
  expect(getJobStatusMock).toHaveBeenCalledTimes(1);

  await act(async () => {
    await vi.advanceTimersByTimeAsync(5000);
  });

  expect(getJobStatusMock).toHaveBeenCalledTimes(1);
});

test("locks room switching while result is still processing and unlocks after completion", async () => {
  vi.useFakeTimers();
  const onRoomMenuLockChange = vi.fn();
  getJobStatusMock
    .mockResolvedValueOnce({
      id: "dddddddd",
      status: "processing"
    })
    .mockResolvedValueOnce({
      id: "dddddddd",
      status: "completed",
      result_url: "/qr/dddddddd",
      download_url: "/qr/dddddddd",
      qr_url: "/api/jobs/hash/dddddddd/qr"
    });

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" onRoomMenuLockChange={onRoomMenuLockChange} />);

  await act(async () => {
    await Promise.resolve();
  });

  expect(onRoomMenuLockChange).toHaveBeenCalledWith(true);

  await act(async () => {
    await vi.advanceTimersByTimeAsync(1500);
    await Promise.resolve();
  });

  expect(screen.getByText(/результат готов/i)).toBeInTheDocument();
  expect(onRoomMenuLockChange).toHaveBeenCalledWith(false);
});
