export const prerender = false; // 이 페이지는 항상 서버에서 실행

export async function POST({ request, locals }) {
  try {
    const { type, path, label = null } = await request.json();
    const db = locals.runtime.env.DB; // Cloudflare D1 연결

    await db.prepare(
      "INSERT INTO stats (type, path, label) VALUES (?, ?, ?)"
    ).bind(type, path, label).run();

    return new Response(JSON.stringify({ success: true }), { status: 200 });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
}
