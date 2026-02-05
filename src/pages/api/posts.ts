export const prerender = false;

export async function POST({ request, locals }) {
  try {
    const { title, summary, content, category, imageUrl, slug } = await request.json();
    const db = locals.runtime.env.DB;
    const finalSlug = slug || title.toLowerCase().replace(/ /g, '-').replace(/[^\w-]/g, '');

    await db.prepare(`
      INSERT INTO posts (title, summary, content, category, image_url, slug)
      VALUES (?, ?, ?, ?, ?, ?)
    `).bind(title, summary, content, category, imageUrl, finalSlug).run();

    return new Response(JSON.stringify({ success: true }), { status: 200 });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
}

export async function DELETE({ request, locals }) {
  try {
    const { id } = await request.json();
    const db = locals.runtime.env.DB;

    await db.prepare("DELETE FROM posts WHERE id = ?").bind(id).run();
    return new Response(JSON.stringify({ success: true }), { status: 200 });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
}
