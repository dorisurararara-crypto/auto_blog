"""
D1 DB에서 모든 포스트를 조회하여 public/sitemap.xml 정적 파일을 생성합니다.
manager.py 파이프라인 실행 후 또는 단독 실행 가능.
"""
import json
import os
import shutil
import subprocess
import urllib.parse

SITE = "https://auto-blogs-7i9.pages.dev"
DB_NAME = "auto-blog-db"
OUTPUT_PATH = "public/sitemap.xml"

STATIC_PAGES = [
    {"url": "/", "changefreq": "daily", "priority": "1.0"},
    {"url": "/popular", "changefreq": "daily", "priority": "0.8"},
    {"url": f"/category/{urllib.parse.quote('IT테크')}", "changefreq": "daily", "priority": "0.7"},
    {"url": f"/category/{urllib.parse.quote('건강')}", "changefreq": "daily", "priority": "0.7"},
    {"url": f"/category/{urllib.parse.quote('라이프')}", "changefreq": "daily", "priority": "0.7"},
]


def fetch_posts_from_d1():
    """wrangler d1 execute로 모든 포스트 slug/날짜를 조회"""
    try:
        npx_path = shutil.which("npx") or "npx"
        result = subprocess.run(
            [npx_path, "wrangler", "d1", "execute", DB_NAME, "--remote",
             "--command=SELECT slug, created_at FROM posts ORDER BY created_at DESC",
             "--json"],
            capture_output=True, text=True, timeout=30, shell=(os.name == "nt")
        )
        data = json.loads(result.stdout)
        # wrangler --json 출력은 배열 형태, 첫 번째 항목의 results에 데이터
        if data and isinstance(data, list) and len(data) > 0:
            return data[0].get("results", [])
        return []
    except Exception as e:
        print(f"[!] D1 조회 실패: {e}")
        return []


def generate_sitemap(posts):
    """sitemap.xml 문자열 생성"""
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for page in STATIC_PAGES:
        xml += f"""  <url>
    <loc>{SITE}{page["url"]}</loc>
    <changefreq>{page["changefreq"]}</changefreq>
    <priority>{page["priority"]}</priority>
  </url>\n"""

    for post in posts:
        slug = urllib.parse.quote(post["slug"], safe="")
        lastmod = ""
        if post.get("created_at"):
            lastmod = f"\n    <lastmod>{post['created_at'].split(' ')[0]}</lastmod>"
        xml += f"""  <url>
    <loc>{SITE}/blog/{slug}</loc>{lastmod}
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>\n"""

    xml += '</urlset>\n'
    return xml


def main():
    print("[*] D1에서 포스트 목록 조회 중...")
    posts = fetch_posts_from_d1()
    print(f"[*] {len(posts)}개 포스트 발견")

    xml = generate_sitemap(posts)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"[+] {OUTPUT_PATH} 생성 완료 (총 {len(posts) + len(STATIC_PAGES)}개 URL)")


if __name__ == "__main__":
    main()
