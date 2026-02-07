import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  site: 'https://auto-blogs-7i9.pages.dev',
  integrations: [react(), sitemap()],
  output: 'static', 
  adapter: cloudflare({
    platformProxy: {
      enabled: true,
    },
  }),
});