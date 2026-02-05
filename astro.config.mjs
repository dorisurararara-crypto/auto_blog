import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  site: 'https://auto-blogs-7i9.pages.dev',
  integrations: [react(), sitemap()],
  output: 'static', // Astro 최신 버전에서는 static이 이전의 hybrid 역할을 수행합니다.
  adapter: cloudflare({
    platformProxy: {
      enabled: true,
    },
  }),
});