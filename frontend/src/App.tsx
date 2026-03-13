import React from "react";
import { useEffect, useState } from "react";

import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { AdminLoginPage } from "./pages/AdminLoginPage";
import { AdminRoomEditorPage } from "./pages/AdminRoomEditorPage";
import { PublicRoomMenu } from "./components/PublicRoomMenu";
import { CapturePage } from "./pages/CapturePage";
import { GalleryPage } from "./pages/GalleryPage";
import { ResultPage } from "./pages/ResultPage";
import { DEFAULT_ROOM_SLUG, resolvePublicRoute } from "./lib/roomRouting";

function resolvePathname(): string {
  if (typeof window === "undefined") {
    return "/";
  }
  return window.location.pathname;
}

function renderShell(content: React.ReactNode, options?: { roomSlug?: string; showMenu?: boolean }) {
  const roomSlug = options?.roomSlug;
  const showMenu = options?.showMenu ?? false;

  return (
    <div className={`app-shell app-shell--studio${roomSlug ? " app-shell--public" : ""}`}>
      {showMenu ? (
        <div className="app-shell__header app-shell__header--public">
          <PublicRoomMenu currentRoomSlug={roomSlug ?? DEFAULT_ROOM_SLUG} />
        </div>
      ) : null}
      <div className="app-shell__content app-shell__content--public">{content}</div>
    </div>
  );
}

export default function App() {
  const [pathname, setPathname] = useState(resolvePathname);

  useEffect(() => {
    const onPopstate = () => setPathname(resolvePathname());
    window.addEventListener("popstate", onPopstate);
    return () => window.removeEventListener("popstate", onPopstate);
  }, []);

  if (pathname === "/admin/login") {
    return renderShell(<AdminLoginPage />);
  }

  if (pathname === "/admin") {
    return renderShell(<AdminDashboardPage />);
  }

  const adminRoomMatch = pathname.match(/^\/admin\/rooms\/([a-z0-9]{8})$/i);
  if (adminRoomMatch) {
    return renderShell(<AdminRoomEditorPage roomSlug={adminRoomMatch[1].toLowerCase()} />);
  }

  const route = resolvePublicRoute(pathname);
  if (route?.page === "result") {
    return renderShell(<ResultPage roomSlug={route.roomSlug} jpgHash={route.jpgHash} />, {
      roomSlug: route.roomSlug,
      showMenu: true
    });
  }
  if (route?.page === "gallery") {
    return renderShell(<GalleryPage roomSlug={route.roomSlug} />, {
      roomSlug: route.roomSlug,
      showMenu: true
    });
  }
  if (route?.page === "capture") {
    return renderShell(<CapturePage roomSlug={route.roomSlug} />, { roomSlug: route.roomSlug });
  }

  return renderShell(<CapturePage roomSlug={DEFAULT_ROOM_SLUG} />, { roomSlug: DEFAULT_ROOM_SLUG });
}
