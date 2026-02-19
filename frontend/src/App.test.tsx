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

test("renders gallery page for /gallery pathname", () => {
  window.history.pushState({}, "", "/gallery");

  render(<App />);

  expect(screen.getByText("gallery-page")).toBeInTheDocument();
  expect(screen.queryByText("capture-page")).not.toBeInTheDocument();
});
