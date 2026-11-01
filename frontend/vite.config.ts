import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "VITE_");
  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,
      proxy: {
        "/api": { target: env.VITE_PROXY_TARGET || "http://127.0.0.1:8000" },
      },
    },
    test: { environment: "jsdom", setupFiles: ["./src/tests/setup.ts"] },
  };
});
