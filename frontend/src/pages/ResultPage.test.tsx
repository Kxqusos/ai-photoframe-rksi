import React from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

import { ResultPage } from "./ResultPage";

const connectRoomJobStatusSocketMock = vi.fn();

class FakeSocket {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  close = vi.fn();

  emitMessage(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) } as MessageEvent);
  }

  emitError() {
    this.onerror?.(new Event("error"));
  }
}

vi.mock("../lib/api", () => ({
  connectRoomJobStatusSocket: (roomSlug: string, jpgHash: string) => connectRoomJobStatusSocketMock(roomSlug, jpgHash)
}));

beforeEach(() => {
  connectRoomJobStatusSocketMock.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("shows intentional loading copy and stable placeholder while websocket waits for processing result", async () => {
  const socket = new FakeSocket();
  connectRoomJobStatusSocketMock.mockReturnValue(socket);

  const { container } = render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  expect(connectRoomJobStatusSocketMock).toHaveBeenCalledWith("aaaaaaaa", "dddddddd");

  await act(async () => {
    socket.emitMessage({
      id: "dddddddd",
      status: "processing"
    });
  });

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

test("shows centered qr pickup guidance when websocket reports completed job", async () => {
  const socket = new FakeSocket();
  connectRoomJobStatusSocketMock.mockReturnValue(socket);

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  await act(async () => {
    socket.emitMessage({
      id: "dddddddd",
      status: "completed",
      result_url: "/qr/dddddddd",
      download_url: "/qr/dddddddd",
      qr_url: "/api/jobs/hash/dddddddd/qr"
    });
  });

  expect(await screen.findByAltText(/generated photo/i)).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /заберите фото на телефон/i })).toBeInTheDocument();
  expect(screen.getByText(/отсканируйте qr-код камерой телефона/i)).toBeInTheDocument();
  expect(screen.getByText(/после сканирования откроется страница с готовым кадром/i)).toBeInTheDocument();
  expect(screen.getByAltText(/download qr/i)).toBeInTheDocument();
  expect(socket.close).toHaveBeenCalledTimes(1);
});

test("shows recovery state when completed result image cannot be loaded", async () => {
  const socket = new FakeSocket();
  connectRoomJobStatusSocketMock.mockReturnValue(socket);

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  await act(async () => {
    socket.emitMessage({
      id: "dddddddd",
      status: "completed",
      result_url: "/qr/dddddddd",
      download_url: "/qr/dddddddd",
      qr_url: "/api/jobs/hash/dddddddd/qr"
    });
  });

  const image = await screen.findByAltText(/generated photo/i);
  fireEvent.error(image);

  expect(await screen.findByRole("alert")).toHaveTextContent("Не удалось загрузить готовое фото");
  expect(screen.getByRole("button", { name: /вернуться и снять заново/i })).toBeInTheDocument();
});

test("shows visible recovery route when websocket reports generation error", async () => {
  const socket = new FakeSocket();
  connectRoomJobStatusSocketMock.mockReturnValue(socket);

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  await act(async () => {
    socket.emitMessage({
      id: "dddddddd",
      status: "error",
      error_message: "Сервис временно недоступен"
    });
  });

  expect(await screen.findByRole("alert")).toHaveTextContent("Сервис временно недоступен");
  expect(screen.getByRole("heading", { name: /не получилось завершить обработку/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /вернуться и снять заново/i })).toBeInTheDocument();
});

test("shows websocket connection error state", async () => {
  const socket = new FakeSocket();
  connectRoomJobStatusSocketMock.mockReturnValue(socket);

  render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);

  await act(async () => {
    socket.emitError();
  });

  expect(await screen.findByRole("alert")).toHaveTextContent("Не удалось подключиться к обновлениям статуса");
});

test("closes websocket on unmount", async () => {
  const socket = new FakeSocket();
  connectRoomJobStatusSocketMock.mockReturnValue(socket);

  const view = render(<ResultPage roomSlug="aaaaaaaa" jpgHash="dddddddd" />);
  view.unmount();

  expect(socket.close).toHaveBeenCalledTimes(1);
});
