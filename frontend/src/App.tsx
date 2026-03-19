import { useEffect, useState } from "react";

import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { AdminLoginPage } from "./pages/AdminLoginPage";
import { AdminRoomEditorPage } from "./pages/AdminRoomEditorPage";
import { CapturePage } from "./pages/CapturePage";
import { GalleryPage } from "./pages/GalleryPage";
import { PublicLandingPage } from "./pages/PublicLandingPage";
import { ResultPage } from "./pages/ResultPage";
import { hasRoomAccessToken } from "./lib/roomAccess";
import { resolvePublicRoute } from "./lib/roomRouting";

function resolvePathname(): string {
  if (typeof window === "undefined") {
    return "/";
  }
  return window.location.pathname;
}

function renderShell(content: React.ReactNode, options?: { publicShell?: boolean }) {
  if (options?.publicShell) {
    return (
      <div className="app-shell app-shell--studio app-shell--public">
        <div className="app-shell__content app-shell__content--public">{content}</div>
      </div>
    );
  }

  return (
    <div className="app-shell app-shell--studio">
      <div className="app-shell__content">{content}</div>
    </div>
  );
}

export default function App() {
  const [pathname, setPathname] = useState(resolvePathname);

  useEffect(() => {
    document.title = "ИИ Фоторамка";
  }, []);

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

  if (pathname === "/") {
    return renderShell(<PublicLandingPage />);
  }

  const route = resolvePublicRoute(pathname);
  if (route && !hasRoomAccessToken(route.roomSlug)) {
    return renderShell(<PublicLandingPage initialRoomSlug={route.roomSlug} redirectPath={pathname} />);
  }
  if (route?.page === "result") {
    return renderShell(<ResultPage roomSlug={route.roomSlug} jpgHash={route.jpgHash} />, { publicShell: true });
  }
  if (route?.page === "gallery") {
    return renderShell(<GalleryPage roomSlug={route.roomSlug} />, { publicShell: true });
  }
  if (route?.page === "capture") {
    return renderShell(<CapturePage roomSlug={route.roomSlug} />, { publicShell: true });
  }

  return renderShell(<PublicLandingPage />);
}
