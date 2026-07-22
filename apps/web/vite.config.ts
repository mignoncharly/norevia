import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react(), VitePWA({
    registerType: "autoUpdate",
    includeAssets: ["favicon.svg"],
    manifest: {
      name: "Norevia — Verifiable destination comparison",
      short_name: "Norevia", description: "Transparent destination comparisons grounded in verifiable data.",
      theme_color: "#173d34", background_color: "#f5f3eb", display: "standalone", start_url: "/",
      icons: [
        { src: "/pwa-192.svg", sizes: "192x192", type: "image/svg+xml", purpose: "any" },
        { src: "/pwa-512.svg", sizes: "512x512", type: "image/svg+xml", purpose: "any maskable" }
      ]
    },
    workbox: {
      globPatterns: ["**/*.{js,css,html,svg,woff2}"], navigateFallback: "/index.html",
      runtimeCaching: [{
        urlPattern: ({ url }) => url.pathname.startsWith("/api/v1/") && url.pathname !== "/api/v1/observations",
        handler: "NetworkFirst", options: { cacheName: "norevia-essential-metadata", networkTimeoutSeconds: 4, expiration: { maxEntries: 60, maxAgeSeconds: 86400 } }
      }]
    }
  })],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
  test: { environment: "jsdom", setupFiles: "./src/test-setup.ts" }
});
