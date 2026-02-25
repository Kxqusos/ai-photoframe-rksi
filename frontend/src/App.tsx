import React from "react";

import { CapturePage } from "./pages/CapturePage";
import { GalleryPage } from "./pages/GalleryPage";
import { ResultPage } from "./pages/ResultPage";
import { resolvePublicRoute } from "./lib/roomRouting";
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

  const route = resolvePublicRoute(pathname);
  if (route?.page === "result") {
    return <ResultPage roomSlug={route.roomSlug} jpgHash={route.jpgHash} />;
  }
  if (route?.page === "gallery") {
    return <GalleryPage roomSlug={route.roomSlug} />;
  }
  if (route?.page === "capture") {
    return <CapturePage roomSlug={route.roomSlug} />;
  }

  return <CapturePage roomSlug="main" />;
}
