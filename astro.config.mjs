import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';

// .env 파일 로드 (process.env가 안 먹힐 수 있으므로 직접 하드코딩하거나 dotenv 사용 권장)
// 여기서는 기본적으로 Cloudflare Pages URL을 가정하고, 나중에 수정 가능하도록 합니다.
const SITE_URL = 'https://your-blog.pages.dev'; 

export default defineConfig({
  site: SITE_URL, // 사이트 주소 필수!
  integrations: [react(), sitemap()],
  output: 'static'
});
