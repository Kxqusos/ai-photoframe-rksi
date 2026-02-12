import { defineConfig } from "vite";

const devProxyTarget = process.env.VITE_DEV_PROXY_TARGET || "http://127.0.0.1:8000";

export default defineConfig({
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: devProxyTarget,
        changeOrigin: true
      },
      "/media": {
        target: devProxyTarget,
        changeOrigin: true
      },
      "/qr": {
        target: devProxyTarget,
        changeOrigin: true
      }
    }
  },
  preview: {
    host: true,
    port: 4173,
    allowedHosts: ["ии.ркси.рф", "xn--h1aa.xn--h1adrf.xn--p1ai"]
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts"
  }
});
