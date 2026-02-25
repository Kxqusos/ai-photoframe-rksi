import React from "react";
import { render, screen } from "@testing-library/react";

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

test("renders gallery page for /gallery pathname", () => {
  window.history.pushState({}, "", "/room-a/gallery");

  render(<App />);

  expect(screen.getByText("gallery-page")).toBeInTheDocument();
  expect(screen.queryByText("capture-page")).not.toBeInTheDocument();
});

test("renders result page for room result pathname", () => {
  window.history.pushState({}, "", "/room-a/result/abc123");

  render(<App />);

  expect(screen.getByText("result-page")).toBeInTheDocument();
  expect(screen.queryByText("capture-page")).not.toBeInTheDocument();
});

test("renders admin login page for /admin/login", () => {
  window.history.pushState({}, "", "/admin/login");

  render(<App />);

  expect(screen.getByText("admin-login-page")).toBeInTheDocument();
});
