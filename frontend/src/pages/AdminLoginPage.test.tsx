import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { AdminLoginPage } from "./AdminLoginPage";

const adminLoginMock = vi.fn();
const saveAdminTokenMock = vi.fn();

vi.mock("../lib/api", () => ({
  adminLogin: (username: string, password: string) => adminLoginMock(username, password)
}));

vi.mock("../lib/auth", () => ({
  saveAdminToken: (token: string) => saveAdminTokenMock(token)
}));

test("stores jwt and redirects to /admin after successful login", async () => {
  adminLoginMock.mockResolvedValue({ access_token: "jwt-token", token_type: "bearer" });
  window.history.pushState({}, "", "/admin/login");

  render(<AdminLoginPage />);

  fireEvent.change(screen.getByLabelText(/логин/i), { target: { value: "admin" } });
  fireEvent.change(screen.getByLabelText(/пароль/i), { target: { value: "password" } });
  fireEvent.click(screen.getByRole("button", { name: /войти/i }));

  await waitFor(() => {
    expect(window.location.pathname).toBe("/admin");
  });
  expect(saveAdminTokenMock).toHaveBeenCalledWith("jwt-token");
});
