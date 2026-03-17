import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";

import App from "./App";

const hasRoomAccessTokenMock = vi.fn();

vi.mock("./pages/CapturePage", () => ({
  CapturePage: () => <div>capture-page</div>
}));
vi.mock("./pages/ResultPage", () => ({
  ResultPage: () => <div>result-page</div>
}));
vi.mock("./pages/GalleryPage", () => ({
  GalleryPage: () => <div>gallery-page</div>
}));
vi.mock("./pages/AdminLoginPage", () => ({
  AdminLoginPage: () => <div>admin-login-page</div>
}));
vi.mock("./pages/AdminDashboardPage", () => ({
  AdminDashboardPage: () => <div>admin-dashboard-page</div>
}));
vi.mock("./pages/AdminRoomEditorPage", () => ({
  AdminRoomEditorPage: () => <div>admin-room-editor-page</div>
}));
vi.mock("./pages/PublicLandingPage", () => ({
  PublicLandingPage: () => <div>public-landing-page</div>
}));
vi.mock("./lib/roomAccess", () => ({
  hasRoomAccessToken: (roomSlug: string) => hasRoomAccessTokenMock(roomSlug)
}));

beforeEach(() => {
  hasRoomAccessTokenMock.mockReset();
  hasRoomAccessTokenMock.mockReturnValue(true);
});

test("renders gallery page for /gallery pathname", () => {
  window.history.pushState({}, "", "/aaaaaaaa/gallery");

  render(<App />);

  expect(screen.getByText("gallery-page")).toBeInTheDocument();
  expect(screen.queryByText("capture-page")).not.toBeInTheDocument();
});

test("renders result page for room result pathname", () => {
  window.history.pushState({}, "", "/aaaaaaaa/result/dddddddd");

  render(<App />);

  expect(screen.getByText("result-page")).toBeInTheDocument();
  expect(screen.queryByText("capture-page")).not.toBeInTheDocument();
});

test("renders admin login page for /admin/login", () => {
  window.history.pushState({}, "", "/admin/login");

  const { container } = render(<App />);

  expect(screen.getByText("admin-login-page")).toBeInTheDocument();
  expect(container.firstElementChild).toHaveClass("app-shell", "app-shell--studio");
});

test("renders admin room editor page for slug route", () => {
  window.history.pushState({}, "", "/admin/rooms/aaaaaaaa");

  render(<App />);

  expect(screen.getByText("admin-room-editor-page")).toBeInTheDocument();
});

test("does not render public room menu on public routes", () => {
  window.history.pushState({}, "", "/aaaaaaaa/gallery");

  render(<App />);

  expect(screen.queryByText("public-room-menu")).not.toBeInTheDocument();
  expect(screen.getByText("gallery-page")).toBeInTheDocument();
});

test("wraps public routes in a floating public shell without a fixed sidebar column", () => {
  window.history.pushState({}, "", "/aaaaaaaa/gallery");

  const { container } = render(<App />);

  expect(container.firstElementChild).toHaveClass("app-shell", "app-shell--public");
  expect(container.querySelector(".app-shell__sidebar--public")).toBeNull();
  expect(container.textContent).not.toContain("public-room-menu");
  expect(container.querySelector(".app-shell__content--public")).not.toBeNull();
});

test("keeps capture route inside the same floating public shell", () => {
  window.history.pushState({}, "", "/aaaaaaaa");

  const { container } = render(<App />);

  expect(container.firstElementChild).toHaveClass("app-shell", "app-shell--public");
  expect(container.querySelector(".app-shell__sidebar--public")).toBeNull();
  expect(container.querySelector(".app-shell__content--public")).not.toBeNull();
});

test("does not expose /settings route and falls back to public capture page", () => {
  window.history.pushState({}, "", "/settings");
  hasRoomAccessTokenMock.mockReturnValue(true);

  render(<App />);

  expect(screen.getByText("capture-page")).toBeInTheDocument();
});

test("renders public landing page on root route", () => {
  window.history.pushState({}, "", "/");
  hasRoomAccessTokenMock.mockReturnValue(false);

  render(<App />);

  expect(screen.getByText("public-landing-page")).toBeInTheDocument();
});

test("keeps root route as default room capture when access token exists", () => {
  window.history.pushState({}, "", "/");
  hasRoomAccessTokenMock.mockImplementation((roomSlug: string) => roomSlug === "ph000000");

  render(<App />);

  expect(screen.getByText("capture-page")).toBeInTheDocument();
  expect(screen.queryByText("public-room-menu")).not.toBeInTheDocument();
});

test("renders public landing page instead of locked room route when access token is missing", () => {
  hasRoomAccessTokenMock.mockReturnValue(false);
  window.history.pushState({}, "", "/aaaaaaaa");

  render(<App />);

  expect(screen.getByText("public-landing-page")).toBeInTheDocument();
  expect(screen.queryByText("capture-page")).not.toBeInTheDocument();
  expect(screen.queryByText("public-room-menu")).not.toBeInTheDocument();
});

test("updates rendered route after navigation event", async () => {
  window.history.pushState({}, "", "/admin/login");

  render(<App />);
  expect(screen.getByText("admin-login-page")).toBeInTheDocument();

  act(() => {
    window.history.pushState({}, "", "/admin");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });

  await waitFor(() => {
    expect(screen.getByText("admin-dashboard-page")).toBeInTheDocument();
  });
});
