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
});
