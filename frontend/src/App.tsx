import React from "react";

import { CapturePage } from "./pages/CapturePage";
import { ResultPage } from "./pages/ResultPage";
import { SettingsPage } from "./pages/SettingsPage";
import { StylesPage } from "./pages/StylesPage";

function resolvePathname(): string {
  if (typeof window === "undefined") {
    return "/";
  }
  return window.location.pathname;
}

export default function App() {
  const pathname = resolvePathname();

  if (pathname === "/settings") {
    return <SettingsPage />;
  }

  if (pathname === "/result") {
    return <ResultPage />;
  }

  if (pathname === "/styles") {
    return <StylesPage />;
  }

  return <CapturePage />;
}
