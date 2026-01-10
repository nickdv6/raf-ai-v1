import { defineConfig } from "astro/config";
import github from "@astrojs/github-pages";

export default defineConfig({
  site: "https://nickdv6.github.io",
  base: "/raf-ai-v1",
  output: "static",
  adapter: github(),
});

