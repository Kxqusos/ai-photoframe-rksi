import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

import App from "./App";

vi.mock("./pages/CapturePage", () => ({
  CapturePage: () => <div>capture-page</div>
}));
vi.mock("./pages/ResultPage", () => ({
  ResultPage: () => <div>result-page</div>
}));
vi.mock("./pages/SettingsPage", () => ({
  SettingsPage: () => <div>settings-page</div>
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
vi.mock("./components/PublicRoomMenu", () => ({
  PublicRoomMenu: () => <div>public-room-menu</div>
}));

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

test("renders public room menu on public routes", () => {
  window.history.pushState({}, "", "/aaaaaaaa/gallery");

  render(<App />);

  expect(screen.getByText("public-room-menu")).toBeInTheDocument();
  expect(screen.getByText("gallery-page")).toBeInTheDocument();
});

test("wraps non-capture public routes in the shared public shell header", () => {
  window.history.pushState({}, "", "/aaaaaaaa/gallery");

  const { container } = render(<App />);

  expect(container.firstElementChild).toHaveClass("app-shell", "app-shell--public");
  expect(container.querySelector(".app-shell__header--public")).not.toBeNull();
  expect(container.querySelector(".app-shell__header--public")?.textContent).toContain("public-room-menu");
  expect(container.querySelector(".app-shell__content--public")).not.toBeNull();
});

test("keeps capture route inside public shell without detached header menu", () => {
  window.history.pushState({}, "", "/aaaaaaaa");

  const { container } = render(<App />);

  expect(container.firstElementChild).toHaveClass("app-shell", "app-shell--public");
  expect(container.querySelector(".app-shell__content--public")).not.toBeNull();
  expect(container.querySelector(".app-shell__header--public")).toBeNull();
});

test("does not expose /settings route and falls back to public capture page", () => {
  window.history.pushState({}, "", "/settings");

  render(<App />);

  expect(screen.getByText("capture-page")).toBeInTheDocument();
  expect(screen.queryByText("settings-page")).not.toBeInTheDocument();
});

test("updates rendered route after navigation event", async () => {
  window.history.pushState({}, "", "/admin/login");

  render(<App />);
  expect(screen.getByText("admin-login-page")).toBeInTheDocument();

  window.history.pushState({}, "", "/admin");
  window.dispatchEvent(new PopStateEvent("popstate"));

  await waitFor(() => {
    expect(screen.getByText("admin-dashboard-page")).toBeInTheDocument();
  });
});
