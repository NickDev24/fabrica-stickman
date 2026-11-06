import { defineConfig } from "vite";
import docsPlugin from "vitepress";

// Deps-only plugins that VitePress needs, with the root's "externalize-deps"
// esbuild interceptor disabled so ESM packages (vitepress/vite) can resolve.
export default defineConfig({
  plugins: [docsPlugin()],
  esbuild: {
    // Empty plugin list: do not load the root's externalize-deps esbuild hook.
    plugins: [],
  },
  build: {
    // Let Vite use its own rollup to bundle vitepress (ESM), bypassing
    // the root tooling's require()-based esbuild "externalize-deps" hook.
    // This is required because the root tooling's esbuild plugin can't
    // `require()` the ESM-only vitepress package.
  },
  optimizeDeps: {
    exclude: [],
  },
});
