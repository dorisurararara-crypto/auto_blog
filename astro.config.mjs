import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  site: 'https://auto-blogs-7i9.pages.dev',
  integrations: [react(), sitemap()],
  output: 'hybrid', // 정적 페이지와 실시간 서버 페이지를 동시에 사용
  adapter: cloudflare({
    platformProxy: {
      enabled: true,
    },
  }),
});