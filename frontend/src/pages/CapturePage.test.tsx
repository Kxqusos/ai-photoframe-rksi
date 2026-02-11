import React from "react";
import { render, screen } from "@testing-library/react";

import { CapturePage } from "./CapturePage";

test("shows style cards with name, description and preview", async () => {
  render(<CapturePage />);
  expect(await screen.findByText("Anime")).toBeInTheDocument();
  expect(screen.getByText("Soft anime shading")).toBeInTheDocument();
  expect(screen.getByRole("img", { name: /anime preview/i })).toBeInTheDocument();
});
