import React from "react";

import { CapturePage } from "./pages/CapturePage";
import { GalleryPage } from "./pages/GalleryPage";
import { ResultPage } from "./pages/ResultPage";
import { SettingsPage } from "./pages/SettingsPage";

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

  if (pathname === "/gallery") {
    return <GalleryPage />;
  }

  return <CapturePage />;
}
