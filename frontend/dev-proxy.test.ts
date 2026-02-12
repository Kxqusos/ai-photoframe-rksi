// @vitest-environment node
import { describe, expect, it } from "vitest";

import config from "./vite.config";

describe("vite dev proxy", () => {
  it("proxies api/media/qr routes to backend", () => {
    const server = config.server ?? {};
    const proxy = server.proxy ?? {};

    expect(proxy["/api"]).toBeDefined();
    expect(proxy["/media"]).toBeDefined();
    expect(proxy["/qr"]).toBeDefined();
  });

  it("allows production preview host for rksi domain", () => {
    const preview = config.preview ?? {};
    const allowedHosts = preview.allowedHosts ?? [];

    expect(allowedHosts).toContain("ии.ркси.рф");
    expect(allowedHosts).toContain("xn--h1aa.xn--h1adrf.xn--p1ai");
  });
});
