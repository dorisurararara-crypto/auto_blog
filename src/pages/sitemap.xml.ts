export const prerender = false;

export async function GET({ locals }) {
  const site = 'https://auto-blogs-7i9.pages.dev';

  let posts = [];
  try {
    const db = locals.runtime.env.DB;
    const { results } = await db.prepare(
      "SELECT slug, created_at, updated_at FROM posts ORDER BY created_at DESC"
    ).all();
    posts = results;
  } catch (e) {
    console.error("Sitemap DB error:", e);
  }

  const staticPages = [
    { url: '/', changefreq: 'daily', priority: '1.0' },
    { url: '/popular', changefreq: 'daily', priority: '0.8' },
    { url: '/category/IT테크', changefreq: 'daily', priority: '0.7' },
    { url: '/category/건강', changefreq: 'daily', priority: '0.7' },
    { url: '/category/라이프', changefreq: 'daily', priority: '0.7' },
  ];

  let xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">`;

  for (const page of staticPages) {
    xml += `
  <url>
    <loc>${site}${page.url}</loc>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
  </url>`;
  }

  for (const post of posts) {
    const lastmod = post.updated_at || post.created_at || '';
    const lastmodTag = lastmod ? `\n    <lastmod>${lastmod.split(' ')[0]}</lastmod>` : '';
    xml += `
  <url>
    <loc>${site}/blog/${post.slug}</loc>${lastmodTag}
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>`;
  }

  xml += `
</urlset>`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
