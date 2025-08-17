import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ command }) => {
  const plugins = [react()];

  // Увага: жодних імпортів ./server на топ-рівні.
  // Якщо для dev потрібен якийсь код із ./server — роби це тільки в режимі serve
  // і лише динамічним імпортом (щоб build його не бачив):
  if (command === "serve") {
    // За потреби можна додати динамічний імпорт тут
    // import('./server').then(mod => mod.setupDev?.())
  }

  return {
    server: {
      host: "::",
      port: 5173,
      fs: {
        allow: ["./client", "./shared"],
        deny: [".env", ".env.*", "*.{crt,pem}", "**/.git/**", "server/**"],
      },
    },
    build: {
      outDir: "dist/spa",
    },
    plugins,
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./client"),
        "@shared": path.resolve(__dirname, "./shared"),
      },
    },
  };
});
