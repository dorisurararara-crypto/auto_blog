import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

// 50만 트래픽도 견디는 가장 안정적인 정적(Static) 배포 설정
export default defineConfig({
  integrations: [react()],
  output: 'static'
});