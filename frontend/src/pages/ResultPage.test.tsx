import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { ResultPage } from "./ResultPage";

const getJobStatusMock = vi.fn();

vi.mock("../lib/api", () => ({
  getJobStatus: (jobId: number) => getJobStatusMock(jobId)
}));

test("shows generated image and qr code when job completes", async () => {
  getJobStatusMock.mockResolvedValue({
    id: 77,
    status: "completed",
    result_url: "/qr/abc123",
    download_url: "/qr/abc123",
    qr_url: "/api/jobs/77/qr"
  });

  render(<ResultPage jobId={77} />);

  expect(await screen.findByAltText(/generated photo/i)).toBeInTheDocument();
  expect(screen.getByRole("main")).toHaveTextContent("Результат");
  expect(screen.getByText(/сканируйте qr-код/i)).toBeInTheDocument();
  expect(screen.getAllByRole("link", { name: /скачать фото/i })).toHaveLength(2);
  expect(screen.getByAltText(/download qr/i)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /продолжить/i })).not.toBeInTheDocument();
});
