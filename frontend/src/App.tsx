import React from "react";
import { useEffect, useState } from "react";

import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { AdminLoginPage } from "./pages/AdminLoginPage";
import { AdminRoomEditorPage } from "./pages/AdminRoomEditorPage";
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
  const [pathname, setPathname] = useState(resolvePathname);

  useEffect(() => {
    const onPopstate = () => setPathname(resolvePathname());
    window.addEventListener("popstate", onPopstate);
    return () => window.removeEventListener("popstate", onPopstate);
  }, []);

  if (pathname === "/admin/login") {
    return <AdminLoginPage />;
  }

  if (pathname === "/admin") {
    return <AdminDashboardPage />;
  }

  const adminRoomMatch = pathname.match(/^\/admin\/rooms\/(\d+)$/);
  if (adminRoomMatch) {
    return <AdminRoomEditorPage roomId={Number(adminRoomMatch[1])} />;
  }

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
