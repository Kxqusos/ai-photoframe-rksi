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

  const { container } = render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  expect(await screen.findByText(/собираем ваш финальный кадр/i)).toBeInTheDocument();
  expect(screen.getByText(/обычно это занимает меньше минуты/i)).toBeInTheDocument();
  expect(
    screen.queryByText(/не закрывайте страницу: как только изображение будет готово, здесь появится результат и ссылка для скачивания/i)
  ).not.toBeInTheDocument();
  expect(screen.queryByTestId("result-loading-preview")).not.toBeInTheDocument();

  const card = container.querySelector(".result-loading-card");
  expect(card?.querySelector(".result-loading-header")).not.toBeNull();
  expect(card?.querySelector(".result-loading-title")).not.toBeNull();
  expect(card?.querySelector(".result-loading-copy")).not.toBeNull();

  const progress = document.querySelector(".result-loading-bar__progress--indeterminate");
  expect(progress).toBeInTheDocument();
});

test("shows centered qr pickup guidance when job completes", async () => {
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
  expect(screen.queryByText(/результат готов/i)).not.toBeInTheDocument();
  expect(
    screen.queryByText(/ваш кадр готов\. заберите его на телефон через qr-код или сохраните прямо с этого экрана/i)
  ).not.toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /заберите фото на телефон/i })).toBeInTheDocument();
  expect(screen.getByText(/отсканируйте qr-код камерой телефона/i)).toBeInTheDocument();
  expect(screen.getByText(/после сканирования откроется страница с готовым кадром/i)).toBeInTheDocument();
  const backButton = screen.getByRole("button", { name: /назад/i });
  const qrLink = screen.getByRole("link", { name: /скачать фото через qr-код/i });
  expect(backButton).toBeInTheDocument();
  expect(qrLink).toBeInTheDocument();
  expect(qrLink.compareDocumentPosition(backButton) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(screen.getByAltText(/download qr/i)).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /открыть ссылку для скачивания/i })).not.toBeInTheDocument();
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

  expect(screen.getByRole("heading", { name: /заберите фото на телефон/i })).toBeInTheDocument();
  expect(getJobStatusMock).toHaveBeenCalledTimes(1);

  await act(async () => {
    await vi.advanceTimersByTimeAsync(5000);
  });

  expect(getJobStatusMock).toHaveBeenCalledTimes(1);
});
